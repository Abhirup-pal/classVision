from flask import Blueprint, render_template, request, flash, jsonify, redirect, send_file
from flask_login import login_required, current_user
from .models import Database
from . import db
import os
import shutil
from pathlib import Path
from website.utils import get_attendance,clean_duplicate_attendance
from .password import password_generator
from werkzeug.security import generate_password_hash,check_password_hash
from .send_email import send_email

studentRoutes = Blueprint('studentRoutes', __name__)

current_dir = os.path.dirname(os.path.abspath(__file__))
database_path = Path(current_dir) / Path("database") / Path("classes")
buffer_path = Path(current_dir) / Path("buffer")
csv_path = Path(buffer_path) / Path("attendance.csv")

students_database_path = Path(current_dir) / Path("database") / Path("students")

## ROUTES FOR STUDENTS ONLY

@studentRoutes.route('/register',methods=['GET','POST'])
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

@studentRoutes.route('/registration/<int:class_id>')
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
