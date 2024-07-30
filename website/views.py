from flask import Blueprint, render_template, request, flash, redirect
from flask_login import login_required, current_user
from .models import User
from . import db
import os
import zipfile
import shutil
from pathlib import Path
from werkzeug.security import generate_password_hash,check_password_hash
from ultralytics import YOLO
import yaml
import shutil

views = Blueprint('views', __name__)

current_dir = os.path.dirname(os.path.abspath(__file__))
database_path = Path(current_dir) / Path("database") / Path("classes")
students_database_path = Path(current_dir) / Path("database") / Path("students")

buffer_path = Path(current_dir) / Path("buffer")
csv_path = Path(buffer_path) / Path("attendance.csv")




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
        if len(email)<4 :
            flash('Please enter a valid email id')
            return redirect('/update_profile')
        if len(first_name) < 2 :
            flash('There must be more than 1 character in your name')
            return redirect('/update_profile')
        try :    
            user_to_update=User.query.get_or_404(current_user.id)
            user_to_update.email=email
            user_to_update.first_name=first_name

            #Checking for zipfile only for students
            if current_user.usertype=='student' :
                # get the name of the zip file
                
                if 'zip_file' not in request.files :
                    flash('Please upload a zip file')
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
                    zip_ref.extractall(os.path.join(students_database_path,roll_num,"images"))
                
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