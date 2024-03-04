from flask import Blueprint, render_template, request, flash, jsonify, redirect, send_file
from flask_login import login_required, current_user
from .models import Database,User
from . import db
import os
import shutil
from pathlib import Path
import time
from website.utils import get_attendance,clean_duplicate_attendance
from .password import password_generator
from werkzeug.security import generate_password_hash
from .send_email import send_email

facultyRoutes = Blueprint('facultyRoutes', __name__)

current_dir = os.path.dirname(os.path.abspath(__file__))
database_path = Path(current_dir) / Path("database") / Path("classes")
buffer_path = Path(current_dir) / Path("buffer")
csv_path = Path(buffer_path) / Path("attendance.csv")

students_database_path = Path(current_dir) / Path("database") / Path("students")

## ROUTES FOR FACULTY ONLY

@facultyRoutes.route('/create_new_class', methods=['GET', 'POST'])
@login_required
def create_new_class():
    if current_user.usertype!='faculty' :
        flash("You are not allowed to acess this page")
        return redirect('/')
    if request.method == 'POST':
        class_name = request.form.get('class_name')

        folder_path = database_path / Path(class_name)
        folder_path.mkdir(parents=True, exist_ok=True)
    
        if class_name == " ":
            flash('Please enter a class name.', category='error')
            return render_template("view_classes.html", user=current_user)
        else:
            # Assuming 'current_user' is the faculty creating the class
            new_class = Database(class_name=class_name, class_database_path=str(folder_path),user_id=current_user.id,students_list="")
            db.session.add(new_class)
            db.session.commit()
            flash('Class created successfully!', category='success')
            return render_template("view_classes.html", user=current_user)
    return render_template("view_classes.html",user=current_user)


@facultyRoutes.route('/view_class', methods=['GET','POST'])
@login_required
def view_class():
    if current_user.usertype!='faculty' :
        flash("You are not allowed to acess this page")
        return redirect('/')
    if request.method == 'POST':
        class_name = request.form.get('class_name')

        if class_name == " ":
            flash('Please enter a class name.', category='error')
            return redirect('/view_class')
        # Assuming 'current_user' is the faculty creating the class
        check=Database.query.filter_by(class_name=class_name).first()
        if check :
            flash('Class name already exists')
            return redirect('/view_class')
        folder_path = database_path / Path(class_name)
        folder_path.mkdir(parents=True, exist_ok=True)
        new_class = Database(class_name=class_name, class_database_path=str(folder_path),user_id=current_user.id,students_list="")
        db.session.add(new_class)
        db.session.commit()
        flash('Class created successfully!', category='success')
        return redirect('/view_class')

    class_list=Database.query.filter_by(user_id=current_user.id)
    class_data=[]
    for cls in class_list :
        tempobj={}
        tempobj['id']=cls.id
        tempobj['class_name']=cls.class_name
        tempobj['students_list']=cls.students_list.split()
        class_data.append(tempobj)
    return render_template('view_class.html', user=current_user, class_data=class_data)

@facultyRoutes.route('/deleteClass/<string:class_name>')
@login_required
def deleteClass(class_name) :
    if current_user.usertype!='faculty' :
        flash("You are not allowed to access this route")
        return redirect('/')
    try :
        class_to_delete=Database.query.filter_by(class_name=class_name).first()
        if class_to_delete.user_id!=current_user.id :
            flash("You are not allowed to perform this task")
            return redirect('/')
        db.session.delete(class_to_delete)
        db.session.commit()

        #delete folder of the class
        if os.isdir(os.path.join(database_path,class_name)) :
            shutil.rmtree(os.path.join(students_database_path,class_name))
            
        flash('Class deleted successfully')
    except :
        flash('There was an issue performing this task')
    return redirect('/view_class')

@facultyRoutes.route('/attendance', methods=['POST', 'GET'])
@login_required
def attendance():
    if request.method == 'POST':
        start_time = time.time()
        # get the name of the folder and the zip file
        class_name = request.form['class_name']
        image = request.files['class_image']
        attendance_date = request.form['attendance_date']  # Get the selected attendance date
        csv_path = Path(buffer_path) / Path(class_name+"attendance.csv")

        
        file_name, ext = os.path.splitext(image.filename)
        print(ext)
        # Check if the class_name is empty
        if class_name == '':
            flash('Please enter a name for the folder', category='error')
            return render_template('attendance.html', user=current_user)
        
        #Check that the file is a zip file
        # if ext != '.jpg':
        #     flash('Please upload .jpg / .jpeg / .png files', category='error')
        #     return render_template('attendance.html', user=current_user)

        image_save_path = os.path.join(buffer_path, f'{file_name}{ext}')  # Use os.path.join
        image.save(image_save_path)
        row = Database.query.filter_by(class_name=class_name).first()

        if row:
            if row.user_id == current_user.id:
                database_path = row.class_database_path
                # print("Database Path:", database_path)  # Add this line for debugging
            else:
                flash('No {class_name} database available', category='error')
                return render_template('attendance.html', user=current_user)
        else:
            flash('No {class_name} database available', category='error')
            return render_template('attendance.html', user=current_user)
        print("Image_save:",image_save_path)
        
        output = get_attendance(image_save_path, database_path, True, csv_path,attendance_date)
        clean_duplicate_attendance(csv_path,attendance_date)
        end_time = time.time()
        execution_time = (end_time-start_time)/60
        print(f"Execution Time: {execution_time:.2f} minutes")
        try:
            return redirect(f"/download_csv/{class_name}")
        except:
            flash('Something went wrong', category='error')
            return render_template('attendance.html', user=current_user)
    return render_template('attendance.html', user=current_user)

@facultyRoutes.route('/download_csv/<class_name>')
@login_required
def download_csv(class_name):
    csv_file_path = os.path.join(buffer_path, f"{class_name}attendance.csv")
    return send_file(csv_file_path, as_attachment=True, download_name=f"{class_name}attendance.csv")


@facultyRoutes.route('/student_list',methods=['GET','POST'])
@login_required
def student_list():
    if current_user.usertype!='faculty' :
        flash('You are not allowed to access this page')
        return redirect('/')
    if request.method=='POST' :
        email=request.form['email']
        roll_number=request.form['roll_number']
        x=User.query.filter_by(email=email).first()
        y=User.query.filter_by(roll_number=roll_number).first()
        if x :
            flash('Email id is already added to the database')
        elif y : 
            flash('Roll number is already added to the database')
        else :
            temp_password=password_generator()
            

            ### send email to student with their password
            try : 
                send_email(email,temp_password)
            except : 
                flash("Failed to send email to the specified email id")
                return redirect('/faculty_list')
            
            #### Must be removed in the final version
            filetowrite=open("temp.txt","a")
            filetowrite.write(f"Email-id : {email}\nPassword : {temp_password}\nUsertype : Student\n\n")
            filetowrite.close


            student = User(email=email,roll_number=roll_number,password=generate_password_hash(temp_password),first_name="",usertype="student")
            db.session.add(student)
            db.session.commit()
            flash('Student added successfully')
            
    student_list=User.query.filter_by(usertype='student')
    cnt=0
    for stud in student_list :
        cnt=1
        break
    return render_template('student_list.html',student_list=student_list,user=current_user,isEmpty=(cnt==0))

@facultyRoutes.route('/deleteStudent/<int:id>')
@login_required
def deleteStudent(id):
    if current_user.usertype!='faculty':
        flash('You are not allowed to access this page')
        return redirect('/')
    try : 
        student_to_delete=User.query.get_or_404(id)
        db.session.delete(student_to_delete)

        #Remove the student from all classes
        Class=Database.query.all()
        for cls in Class :
            v=cls.students_list.split()
            try :
                v.remove(student_to_delete.roll_number)
                cls.students_list=""
                for stud in v :
                    cls.students_list+=stud
                    cls.students_list+=' '
            except :
                pass
        db.session.commit()

        #Delete the folder of the student
        if os.isdir(os.path.join(students_database_path,student_to_delete.roll_number)) :
            shutil.rmtree(os.path.join(students_database_path,student_to_delete.roll_number))

        flash('Student deleted successfully')
    except :
        flash('There was an issue performing this task')
    return redirect('/student_list')

