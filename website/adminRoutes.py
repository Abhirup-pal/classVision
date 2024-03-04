from flask import Blueprint, render_template, request, flash, jsonify, redirect, send_file
from flask_login import login_required, current_user
from .models import Database,User
from . import db
import os
from pathlib import Path
from .password import password_generator
from werkzeug.security import generate_password_hash
from .send_email import send_email

adminRoutes = Blueprint('adminRoutes', __name__)

current_dir = os.path.dirname(os.path.abspath(__file__))
database_path = Path(current_dir) / Path("database") / Path("classes")
buffer_path = Path(current_dir) / Path("buffer")
csv_path = Path(buffer_path) / Path("attendance.csv")

students_database_path = Path(current_dir) / Path("database") / Path("students")

## ROUTES FOR ADMIN ONLY

@adminRoutes.route('/faculty_list',methods=['GET','POST'])
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
            temp_password=password_generator()


            ### send email to faculty with their password
            try : 
                send_email(email,temp_password)
            except : 
                flash("Failed to send email to the specified email id")
                return redirect('/faculty_list')
            
            #### Must be removed in the final version
            filetowrite=open('temp.txt','a')
            filetowrite.write(f"Email-id : {email}\nPassword : {temp_password}\nUsertype : Faculty\n\n")
            filetowrite.close()

            
            faculty = User(email=email,password=generate_password_hash(temp_password),first_name="",usertype="faculty")
            db.session.add(faculty)
            db.session.commit()
            flash('Faculty added successfully')
            
    faculty_list=User.query.filter_by(usertype='faculty')
    cnt=0
    for facul in faculty_list :
        cnt=1
        break
    return render_template('faculty_list.html',faculty_list=faculty_list,user=current_user,isEmpty=(cnt==0))

@adminRoutes.route('/deleteFaculty/<int:id>')
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

@adminRoutes.route('/all_users',methods=['GET'])
@login_required
def all_users() :
    if current_user.usertype!='admin' :
        flash('You are not allowed to access this page')
        return redirect('/')
    users=User.query.all()
    isEmpty = 1
    for user in users :
        if user.usertype!='admin' :
            isEmpty=0
            break
    return render_template('view_users.html',user=current_user,users=users,isEmpty=isEmpty)