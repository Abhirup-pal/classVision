from flask import Blueprint, render_template, request, flash, jsonify, redirect, send_file
from flask_login import login_required, current_user
from .models import Database,User
from . import db
import json
import os
import zipfile
import shutil
from pathlib import Path
import time
from website.utils import get_attendance,clean_duplicate_attendance
from .password import password_generator
from werkzeug.security import generate_password_hash,check_password_hash

views = Blueprint('views', __name__)

current_dir = os.path.dirname(os.path.abspath(__file__))
database_path = Path(current_dir) / Path("database") / Path("classes")
buffer_path = Path(current_dir) / Path("buffer")
csv_path = Path(buffer_path) / Path("attendance.csv")

students_database_path = Path(current_dir) / Path("database") / Path("students")



## COMMON ROUTES

@views.route('/', methods=['GET', 'POST'])
def home():
    return render_template("home.html", user=current_user)

@views.route('/update_profile',methods=['GET','POST'])
@login_required
def update_profile() :
    if request.method=='POST' :
        email=request.form['email']
        first_name=request.form['first_name']

        try :    
            user_to_update=User.query.get_or_404(current_user.id)
            user_to_update.email=email
            user_to_update.first_name=first_name
            if current_user.usertype=='student' :
                # get the name of the zip file
                
                if 'zip_file' not in request.files :
                    flash('Please upload a file')
                    return redirect('/update_profile')

                zip_file = request.files['zip_file']
                filename, ext = os.path.splitext(zip_file.filename)
                roll_num=current_user.roll_number


                # Check that the file is a zip file
                if ext != '.zip':
                    flash('Please upload a .zip file only', category='error')
                    return render_template('upload.html', user=current_user)
                
                folder_name=os.path.join(students_database_path,roll_num)
                if os.path.isdir(folder_name) :
                    shutil.rmtree(folder_name,ignore_errors=True)

                zip_file_path = os.path.join(students_database_path, f'{roll_num}.zip')

                zip_file.save(zip_file_path)

                # extract and remove the zip file
                with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                    zip_ref.extractall(students_database_path)
                os.rename(os.path.join(students_database_path,filename),os.path.join(students_database_path,roll_num))
                os.remove(zip_file_path)
            db.session.commit()
            flash("Profile updated successfully")
        except :
            flash('There was an issue performing this task')
    return render_template('update_profile.html',user=current_user)

@views.route('/update_password',methods=['GET','POST'])
@login_required
def update_password() :
    if request.method=='POST' :
        old_password = request.form['old_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_new_password']
        try : 
            user_to_update = User.query.get_or_404(current_user.id)
            if check_password_hash(user_to_update.password,old_password) :
                if new_password==confirm_password :
                    if len(new_password)<7 :
                        flash('Password must be at least 7 characters.', category='error')
                    user_to_update.password=generate_password_hash(new_password)
                    db.session.commit()
                    flash('Password updated successfully')
                else :
                    flash('New password is not same as confirm new password', category='error')
            else :
                flash('You have entered a wrong current password')
        except :
            flash('There was an issue performing this task',category='error')
    return render_template('update_password.html',user=current_user)




## ROUTES FOR FACULTY ONLY

@views.route('/create_new_class', methods=['GET', 'POST'])
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


@views.route('/view_class', methods=['GET','POST'])
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

@views.route('/deleteClass/<string:class_name>')
@login_required
def deleteClass(class_name) :
    try :
        class_to_delete=Database.query.filter_by(class_name=class_name).first()
        if class_to_delete.user_id!=current_user.id :
            flash("You are not allowed to perform this task")
            return redirect('/')
        db.session.delete(class_to_delete)
        db.session.commit()
        flash('Class deleted successfully')
    except :
        flash('There was an issue performing this task')
    return redirect('/view_class')

@views.route('/attendance', methods=['POST', 'GET'])
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

@views.route('/download_csv/<class_name>')
@login_required
def download_csv(class_name):
    csv_file_path = os.path.join(buffer_path, f"{class_name}attendance.csv")
    return send_file(csv_file_path, as_attachment=True, download_name=f"{class_name}attendance.csv")


@views.route('/student_list',methods=['GET','POST'])
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
            temp=password_generator()
            
            #### Must be removed in the final version
            filetowrite=open("temp.txt","a")
            filetowrite.write(f"Email-id : {email}\nPassword : {temp}\nUsertype : Student\n\n")
            filetowrite.close


            student = User(email=email,roll_number=roll_number,password=generate_password_hash(temp),first_name="",usertype="student")
            db.session.add(student)
            db.session.commit()
            flash('Student added successfully')
            ### send email to student with their password
    student_list=User.query.filter_by(usertype='student')
    cnt=0
    for stud in student_list :
        cnt=1
        break
    return render_template('student_list.html',student_list=student_list,user=current_user,isEmpty=(cnt==0))

@views.route('/deleteStudent/<int:id>')
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



## ROUTES FOR STUDENTS ONLY

@views.route('/register',methods=['GET','POST'])
@login_required
def register():
    if current_user.usertype!='student' :
        flash('This route is only for students')
        return redirect('/')
    def copy_obj(database_obj):
        tempobj={}
        tempobj['id']=database_obj.id
        tempobj['class_name']=database_obj.class_name
        tempobj['class_database_path']=database_obj.class_database_path
        tempobj['user_id']=database_obj.user_id
        tempobj['students_list']=database_obj.students_list
        return tempobj
    Class=Database.query.all()
    Class_data=[]
    for cls in Class :
        stud_list=cls.students_list.split()
        tempobj=copy_obj(cls)
        try : 
            stud_list.index(current_user.roll_number)
            tempobj['registration_state']=1
        except :
            tempobj['registration_state']=0
        Class_data.append(tempobj)
    return render_template('register.html',user=current_user,Class_data=Class_data)

@views.route('/registration/<int:class_id>')
def registration(class_id):
    if current_user.usertype!='student' :
        flash('This route is only for students')
        return redirect('/')
    class_to_edit=Database.query.filter_by(id=class_id).first()
    student_list=class_to_edit.students_list.split()
    roll_number=current_user.roll_number
    try : 
        #deregistration
        student_list.remove(roll_number)
        class_to_edit.students_list=""
        for stud in student_list :
            class_to_edit.students_list+=stud
            class_to_edit.students_list+=' '
        db.session.commit()
        folder_to_delete = os.path.join(database_path,class_to_edit.class_name,roll_number)
        if os.path.isdir(folder_to_delete) :
            shutil.rmtree(folder_to_delete,ignore_errors=True)
    except :
        #registration
        folder_to_copy = os.path.join(students_database_path,roll_number)
        if not os.path.isdir(folder_to_copy) :
            flash("Complete your profile to start the registration process")
            return redirect('/register')
        shutil.copytree(folder_to_copy,os.path.join(database_path,class_to_edit.class_name,roll_number))
        class_to_edit.students_list+=f"{roll_number} "
        db.session.commit()
    return redirect('/register')



## ROUTES FOR ADMIN ONLY

@views.route('/faculty_list',methods=['GET','POST'])
@login_required
def faculty_list():
    if current_user.usertype!='admin' :
        flash('You are not allowed to access this page')
        return redirect('/')
    if request.method=='POST' :
        email=request.form['email']
        x=User.query.filter_by(email=email).first()
        if x :
            flash('Email id is already added to the database')
        else :
            temp=password_generator()
            #### Must be removed in the final version
            filetowrite=open('temp.txt','a')
            filetowrite.write(f"Email-id : {email}\nPassword : {temp}\nUsertype : Faculty\n\n")



            faculty = User(email=email,password=generate_password_hash(temp),first_name="",usertype="faculty")
            db.session.add(faculty)
            db.session.commit()
            flash('Faculty added successfully')
            ### send email to student with their password
    faculty_list=User.query.filter_by(usertype='faculty')
    cnt=0
    for stud in faculty_list :
        cnt=1
        break
    return render_template('faculty_list.html',faculty_list=faculty_list,user=current_user,isEmpty=(cnt==0))

@views.route('/deleteFaculty/<int:id>')
@login_required
def delete(id):
    if current_user.usertype!='admin':
        flash('You are not allowed to access this route')
        return redirect('/')
    try : 
        faculty_to_delete=User.query.get_or_404(id)
        db.session.delete(faculty_to_delete)
        Class=Database.query.all()
        for cls in Class :
            if cls.user_id==id :
                db.session.delete(cls)
        db.session.commit()
    except :
        flash('There was an issue performing this task')
    return redirect('/faculty_list')

@views.route('/all_users',methods=['GET'])
@login_required
def all_users() :
    if current_user.usertype!='admin' :
        flash('You are not allowed to access this page')
        return redirect('/')
    users=User.query.all()
    return render_template('view_users.html',user=current_user,users=users)