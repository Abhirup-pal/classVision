from ultralytics import YOLO
import os


current_dir = os.path.dirname(os.path.abspath(__file__))
print(current_dir)

new_model = YOLO('yolov8n.pt')
new_model.train(data=os.path.join(current_dir,'database','data.yaml'),epochs=1,imgsz=640)
