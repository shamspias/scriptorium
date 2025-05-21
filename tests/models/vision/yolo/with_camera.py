from ultralytics import YOLO

# Load a pre-trained YOLOv8 model
model = YOLO('../../../../models/best.pt')

model.predict(source=0, show=True, device='mps')
