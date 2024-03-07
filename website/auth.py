from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models import User
from werkzeug.security import check_password_hash,generate_password_hash
from flask_login import login_user, login_required, logout_user, current_user


auth = Blueprint('auth', __name__)


@auth.route('/authority_login', methods=['GET', 'POST'])
def authority_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                flash('Logged in successfully!', category='success')
                login_user(user, remember=True)
                return redirect(url_for('views.home'))
            else:
                flash('Incorrect password, try again.', category='error')
        else:
            flash('Email does not exist.', category='error')
        

    return render_template("authority_login.html", user=current_user)

@auth.route('/student_login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        emailorrollnumber = request.form.get('emailorrollnumber')
        password = request.form.get('password')
        user=None
        if emailorrollnumber.__contains__('@') :
            user = User.query.filter_by(email=emailorrollnumber,usertype="student").first()
        else :
            user = User.query.filter_by(roll_number=emailorrollnumber,usertype="student").first()
        if user:
            if check_password_hash(user.password, password):
                flash('Logged in successfully!', category='success')
                login_user(user, remember=True)
                return redirect(url_for('views.home'))
            else:
                flash('Incorrect password, try again.', category='error')
        else:
            if emailorrollnumber.__contains__('@'):
                flash('Email does not exist.', category='error')
            else :
                flash('Roll number does not exist.',category='error')
        

    return render_template("student_login.html", user=current_user)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')

@auth.route('/forgot_password',methods=['GET', 'POST'])
def forgot_password() :
    if request.method=='POST' :
        email=request.form['email']
        user = User.query.filter_by(email=email).first()
        if user :
            from .password import password_generator
            from .send_email import send_email
            from . import db
            temp_password = password_generator()
            try :
                send_email(email,temp_password)
            except :
                flash("Failed to send email to the specified email id")
                return redirect('/forgot_password')
            user.password = generate_password_hash(temp_password)
            db.session.commit()
            flash('You received an email containing your new password')
            return redirect('/')
        else :
            flash("Email id is not registered")
            return redirect('/forgot_password')
    return render_template("forgot_password.html", user=current_user)
