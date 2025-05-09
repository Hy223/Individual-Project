from ultralytics import YOLO

if __name__ == '__main__':
    # Load a model
    model = YOLO("ultralytics/cfg/models/v8/yolov8n.yaml")  # build a new model from scratch
    # train
    model.train(data='dataset/data.yaml',
                cache='disk',
                imgsz=640,
                epochs=120,
                batch=32,
                patience=100,
                save_period=10,
                device=0,
                close_mosaic=0,
                workers=4,
                optimizer='SGD',
                amp=False,
                project='runs/train',
                name='exp',
                )
