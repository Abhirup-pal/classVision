from . import db
from flask_login import UserMixin

MAX_STUDENTS_IN_CLASS=100


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    first_name = db.Column(db.String(150))
    password = db.Column(db.String(150))
    roll_number = db.Column(db.String(10))
    usertype=db.Column(db.String(20), default="student")
    databases = db.relationship('Database')

class Database(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    class_name = db.Column(db.String(150))
    class_database_path = db.Column(db.String(1000))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    students_list = db.Column(db.String(MAX_STUDENTS_IN_CLASS*10))