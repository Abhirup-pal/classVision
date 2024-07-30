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
from ultralytics import YOLO
import yaml


studentRoutes = Blueprint('studentRoutes', __name__)

current_dir = os.path.dirname(os.path.abspath(__file__))
database_path = Path(current_dir) / Path("database") / Path("classes")
buffer_path = Path(current_dir) / Path("buffer")
csv_path = Path(buffer_path) / Path("attendance.csv")

students_database_path = Path(current_dir) / Path("database") / Path("students")

face_detection = YOLO(os.path.join(current_dir,"database/best.torchscript"))

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
        ## new code start ##
        # class_folder = tempobj['class_name']
        # class_folder = 'database/models/' + class_folder
        # if os.path.exists(class_folder):
        #     model_file = "best.pt"
        #     model_file = class_folder + "/" + model_file
        #     model = YOLO(model_file)
        #     model.train(data='database/data.yaml',epochs=20,imgsz=640)

        ## new code end ##
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

def copy_images(source_folder, destination_folder):
    # Check if the destination folder exists, if not, create it
    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)

    # Iterate through files in the source folder
    for filename in os.listdir(source_folder):
        # Check if the file is an image (you can adjust the condition based on your specific requirements)
        if filename.endswith(('.jpg', '.jpeg', '.png')):
            # Construct full paths for source and destination
            source_path = os.path.join(source_folder, filename)
            destination_path = os.path.join(destination_folder, filename)
            # Copy the file to the destination folder
            shutil.copy2(source_path, destination_path)

@studentRoutes.route('/registration/<int:class_id>')
def registration(class_id):
    if current_user.usertype!='student' :
        flash('This route is only for students')
        return redirect('/')
    class_to_edit=Database.query.filter_by(id=class_id).first()
    student_list=class_to_edit.students_list.split()
    roll_number=current_user.roll_number
    if roll_number in student_list :
        #deregistration
        student_list.remove(roll_number)
        class_to_edit.students_list=""
        for stud in student_list :
            class_to_edit.students_list+=stud
            class_to_edit.students_list+=' '
        db.session.commit()
        # folder_to_delete = os.path.join(database_path,class_to_edit.class_name,roll_number)
        # if os.path.isdir(folder_to_delete) :
        #     shutil.rmtree(folder_to_delete,ignore_errors=True)
    else :
        #registration
        folder_to_copy = os.path.join(students_database_path,roll_number)
        if not os.path.isdir(folder_to_copy) :
            flash("Complete your profile to start the registration process")
            return redirect('/register')
        flash("Please wait for a few minutes for the model to train")
        ### new code start ###
        class_name = class_to_edit.class_name
        class_folder = os.path.join(current_dir,'database','models', class_name)
        roll_num = current_user.roll_number
        if os.path.exists(class_folder):
            print("Model exists")
            model_file = "best.pt"
            model_file = os.path.join(class_folder,model_file)
            model = YOLO(model_file)
            # Get a list of all files in the folder
            images_to_be_trained = os.path.join(current_dir,"database","students",roll_num,"images")
            label_folder = os.path.join(current_dir,"database","students",roll_num,"labels")
            file_list = [file[:-4] for file in os.listdir(images_to_be_trained) if os.path.isfile(os.path.join(images_to_be_trained, file))]
            print(file_list)
            if not os.path.exists(os.path.join(current_dir,"database","students",roll_num,"labels")):
                os.makedirs(os.path.join(current_dir,"database","students",roll_num,"labels"))

            for image in file_list:
                image_name = image + '.jpg'
                result = face_detection([os.path.join(images_to_be_trained , image + '.jpg')])
                print(result)
                print("File: ",image)
                print(result[0].boxes.xywhn[0][1])
                # os.makedirs(os.path.join(current_dir,"database","students",roll_num,"labels"))
                with open(os.path.join(label_folder , image + '.txt'), 'w') as file:
                    file.write(f"1 {result[0].boxes.xywhn[0][0]} {result[0].boxes.xywhn[0][1]} {result[0].boxes.xywhn[0][2]} {result[0].boxes.xywhn[0][3]}")
                print("Label file ", image," saved")
            
            source_folder = os.path.join(current_dir,'database','students',roll_num,'images')
            destination_folder_train = os.path.join(current_dir,'detect-1','train','images')
            destination_folder_test = os.path.join(current_dir,'detect-1','test','images')
            destination_folder_valid = os.path.join(current_dir,'detect-1','valid','images')
            copy_images(source_folder, destination_folder_train)
            copy_images(source_folder, destination_folder_test)
            copy_images(source_folder, destination_folder_valid)

            source_folder = os.path.join(current_dir,'database','students',roll_num,'labels')
            destination_folder_train = os.path.join(current_dir,'detect-1','train','labels')
            destination_folder_test = os.path.join(current_dir,'detect-1','test','labels')
            destination_folder_valid = os.path.join(current_dir,'detect-1','valid','labels')
            copy_images(source_folder, destination_folder_train)
            copy_images(source_folder, destination_folder_test)
            copy_images(source_folder, destination_folder_valid)

            dataset_location = os.path.join(current_dir,'detect-1','data.yaml')
            model.train(data=dataset_location,epochs=30,imgsz=640)
            model.export()

            parent_di = os.path.dirname(current_dir)
            parent_directory = os.path.join(parent_di,"runs","detect")

            # Get a list of directories in the parent directory
            directories = [d for d in os.listdir(parent_directory) if os.path.isdir(os.path.join(parent_directory, d))]

            # Sort the directories based on their names
            sorted_directories = sorted(directories, key=lambda x: 0 if len(x)==5 else int(x[5:]) if x.startswith("train") else -1)
            
            # folder with latest trained model
            latest_model_folder = sorted_directories[-1]

            source_folder = os.path.join(parent_di,"runs/detect", latest_model_folder, "weights")
            # print(os.path.dirname(current_dir))
            destination = os.path.join(current_dir,"database/models/" ,class_folder)
            if not os.path.exists(destination):
                os.makedirs(destination)
            file_name = "best.pt"

            source_file = os.path.join(source_folder,file_name)
            destination_file = os.path.join(destination,file_name)

            # copies the latest model file to the class model folder
            shutil.copy(source_file, destination_file)




            # parent_directory = os.path.join(current_dir,"runs","detect")

            # Get a list of directories in the parent directory
            # directories = [d for d in os.listdir(parent_directory) if os.path.isdir(os.path.join(parent_directory, d))]

            # Sort the directories based on their names
            # sorted_directories = sorted(directories, key=lambda x: int(x[5:]) if x.startswith("train") else -1)
            # latest_model_folder = sorted_directories[-1]
            # source_folder = "runs/detect/" + latest_model_folder + "/weights/"
            # source_folder = os.path.join("runs","detect",latest_model_folder,"weights")
            # destination = "database/models/" + class_folder
            # destination = os.path.join(current_dir,"database","models",class_folder)
            # file_name = "best.pt"
            # source_file = os.path.join(source_folder,file_name)
            # destination_file = os.path.join(destination,file_name)
            # shutil.copy(source_file, destination_file)

        else:
            print("Model does exists")
            new_model = YOLO('yolov8n.pt')
            images_to_be_trained = os.path.join(current_dir,"database","students",roll_num,"images")
            label_folder = os.path.join(current_dir,"database","students",roll_num,"labels")
            file_list = [file[:-4] for file in os.listdir(images_to_be_trained) if os.path.isfile(os.path.join(images_to_be_trained, file))]
            if not os.path.exists(os.path.join(current_dir,"database","students",roll_num,"labels")):
                os.makedirs(os.path.join(current_dir,"database","students",roll_num,"labels"))

            for image in file_list:
                image_name = image + '.jpg'
                result = face_detection([os.path.join(images_to_be_trained , image + '.jpg')])
                print("File: ",image)
                print(result[0].boxes.xywhn[0][1])
                with open(os.path.join(label_folder , image + '.txt'), 'w') as file:
                    file.write(f"1 {result[0].boxes.xywhn[0][0]} {result[0].boxes.xywhn[0][1]} {result[0].boxes.xywhn[0][2]} {result[0].boxes.xywhn[0][3]}")
                print("Label file ", image," saved")
            # import os
            # import shutil

            # Example usage
            source_folder = os.path.join(current_dir,'database','students',roll_num,'images')
            destination_folder_train = os.path.join(current_dir,'detect-1','train','images')
            destination_folder_test = os.path.join(current_dir,'detect-1','test','images')
            destination_folder_valid = os.path.join(current_dir,'detect-1','valid','images')
            copy_images(source_folder, destination_folder_train)
            copy_images(source_folder, destination_folder_test)
            copy_images(source_folder, destination_folder_valid)

            source_folder = os.path.join(current_dir,'database','students',roll_num,'labels')
            destination_folder_train = os.path.join(current_dir,'detect-1','train','labels')
            destination_folder_test = os.path.join(current_dir,'detect-1','test','labels')
            destination_folder_valid = os.path.join(current_dir,'detect-1','valid','labels')
            copy_images(source_folder, destination_folder_train)
            copy_images(source_folder, destination_folder_test)
            copy_images(source_folder, destination_folder_valid)

            dataset_location = os.path.join(current_dir,'detect-1','data.yaml')
            new_model.train(data=dataset_location,epochs=30,imgsz=640)
            new_model.export()
            parent_di = os.path.dirname(current_dir)
            parent_directory = os.path.join(parent_di,"runs","detect")

            # Get a list of directories in the parent directory
            directories = [d for d in os.listdir(parent_directory) if os.path.isdir(os.path.join(parent_directory, d))]

            # Sort the directories based on their names
            sorted_directories = sorted(directories, key=lambda x: 0 if len(x)==5 else int(x[5:]) if x.startswith("train") else -1)
            
            # folder with latest trained model
            latest_model_folder = sorted_directories[-1]

            source_folder = os.path.join(parent_di,"runs/detect", latest_model_folder, "weights")
            # print(os.path.dirname(current_dir))
            destination = os.path.join(current_dir,"database/models/" ,class_folder)
            if not os.path.exists(destination):
                os.makedirs(destination)
            file_name = "best.pt"

            source_file = os.path.join(source_folder,file_name)
            destination_file = os.path.join(destination,file_name)

            # copies the latest model file to the class model folder
            shutil.copy(source_file, destination_file)
        ### new code end ###
        # shutil.copytree(folder_to_copy,os.path.join(database_path,class_to_edit.class_name,roll_number))
        class_to_edit.students_list+=f"{roll_number} "
        db.session.commit()
        flash("Registered successfully for the class")
    return redirect('/register')
