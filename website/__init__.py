from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path,mkdir
from pathlib import Path
from flask_login import LoginManager
from werkzeug.security import generate_password_hash


db = SQLAlchemy()
DB_NAME = "userdata"
ADMIN_EMAIL_ID = "classvisionAdmin@gmail.com"
ADMIN_PASSWORD = "classVision@Admin"

current_dir = path.dirname(path.abspath(__file__))
database_path = Path(current_dir) / Path("database")
classes_path = Path(current_dir) / Path("database") / Path("classes")
students_database_path = Path(current_dir) / Path("database") / Path("students")


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'hjshjhdjahkjshkjdhjghgghhjvhfgbbjiuyewscvs'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    db.init_app(app)

    from .views import views
    from .auth import auth
    from .facultyRoutes import facultyRoutes
    from .studentRoutes import studentRoutes
    from .adminRoutes import adminRoutes

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')
    app.register_blueprint(facultyRoutes, url_prefix='/')
    app.register_blueprint(studentRoutes, url_prefix='/')
    app.register_blueprint(adminRoutes, url_prefix='/')

    from .models import User, Database
    
    
    with app.app_context():
        db.create_all()
        #add the admin
        if not User.query.filter_by(email=ADMIN_EMAIL_ID).first() :
            admin = User(email=ADMIN_EMAIL_ID,password=generate_password_hash(ADMIN_PASSWORD),first_name="Admin",usertype="admin")
            db.session.add(admin)
            db.session.commit()
        
        #create the required folders
        if not path.exists(database_path) :
            mkdir(database_path)
        if not path.exists(classes_path) :
            mkdir(classes_path)
        if not path.exists(students_database_path) :
            mkdir(students_database_path) 
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))
    return app
