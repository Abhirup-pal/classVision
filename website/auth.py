from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models import User
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
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


@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        email = request.form.get('email')
        first_name = request.form.get('firstName')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')
        inputtype = request.form.get('usertype')

        print(email, first_name, password1, password2,inputtype)

        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exists.', category='error')
        elif len(email) < 4:
            flash('Email must be greater than 3 characters.', category='error')
        elif len(first_name) < 2:
            flash('First name must be greater than 1 character.', category='error')
        elif password1 != password2:
            flash('Passwords don\'t match.', category='error')
        elif len(password1) < 3:
            flash('Password must be at least 7 characters.', category='error')
        else:
            print(email, first_name, password1, password2,inputtype)
            new_user = User(email=email, roll_number=None,first_name=first_name, password=generate_password_hash(
                password1, method='sha256'),usertype="admin")
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user, remember=True)
            flash('Account created!', category='success')
            return redirect(url_for('views.home'))

    return render_template("sign_up.html", user=current_user)



'''
classvisionAdmin@gmail.com
classVision@Admin
'''