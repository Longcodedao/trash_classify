import cv2
import numpy as np
import time
import os
import torch
import torch.nn as nn
import torchvision.transforms as transforms
from torchvision.models import mobilenet_v3_small
from PIL import Image
from picamera2 import Picamera2

# --- CONFIGURATION ---
CHECKPOINT_PATH = "../checkpoints/best_model_finetune.pth" # Path to your trained model
LABELS = ['cardboard', 'glass', 'metal', 'paper', 'plastic', 'trash']
CONFIDENCE_THRESHOLD = 0.60
DEVICE = torch.device("cpu") # Raspberry Pi uses CPU


def load_model(path, num_classes):
    print(f"Loading model from {path}...")
    # IMPORTANT: We use mobilenet_v3_large because the training script used 'large'.
    # If you changed the training script to 'small', change this to mobilenet_v3_small!
    model = mobilenet_v3_small(weights=None)
    
    # Rebuild the classifier head to match your 6 classes
    in_features = model.classifier[3].in_features
    model.classifier[3] = nn.Linear(in_features, num_classes)
    
    # Load the weights
    try:
        model.load_state_dict(torch.load(path, map_location=DEVICE))
        print("Model loaded successfully!")
    except FileNotFoundError:
        print(f"ERROR: Could not find {path}")
        print("Please ensure the file exists or update CHECKPOINT_PATH.")
        exit()
    except RuntimeError as e:
        print(f"ERROR: Model mismatch! {e}")
        print("Did you train with MobileNetV3 SMALL but are trying to load LARGE here?")
        exit()
        
    model.to(DEVICE)
    model.eval()
    return model
    
    
   # --- PREPROCESSING ---
preprocess = transforms.Compose([
	transforms.CenterCrop((480, 480)),
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

def main():
	# 1. Load Model
    model = load_model(CHECKPOINT_PATH, len(LABELS))

    # 2. Setup Camera (Picamera2)
    print("Starting Camera...")
    picam2 = Picamera2()
    
    # Apply your specific Manual Control settings
    config = picam2.create_preview_configuration(
        main={"format": "RGB888", "size": (640, 480)},
        controls={
            "FrameRate": 30,
            "ExposureTime": 7276,  # 7276 microseconds (from your screenshot)
            "AnalogueGain": 1.0,   # 1.0x Gain
            "LensPosition": 7.02   # Focus distance
        }
    )
    picam2.configure(config)
    picam2.start()

    print("Camera started. Press 'q' to exit.")
    
    # 3. Main Loop
    try:
        while True:
            # Capture frame (RGB)
            frame = picam2.capture_array()
            
            # Create a copy for drawing (OpenCV expects BGR)
            display_frame = frame
            # display_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

            # --- INFERENCE ---
            # Convert to PIL Image
            pil_img = Image.fromarray(frame)
            
            # Prepare tensor
            input_tensor = preprocess(pil_img).unsqueeze(0).to(DEVICE)

            # Predict
            with torch.no_grad():
                outputs = model(input_tensor)
                probabilities = torch.nn.functional.softmax(outputs, dim=1)[0]

            # Get Result
            top_prob, top_catid = torch.max(probabilities, 0)
            confidence = top_prob.item()
            predicted_label = LABELS[top_catid.item()]

            # --- VISUALIZATION ---
            if confidence > CONFIDENCE_THRESHOLD:
                color = (0, 255, 0) # Green
                text = f"{predicted_label.upper()}: {confidence*100:.1f}%"
            else:
                color = (0, 0, 255) # Red
                text = f"Waiting... ({predicted_label}: {confidence*100:.1f}%)"

            # Draw text on the OpenCV window
            cv2.putText(display_frame, text, (10, 50), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2, cv2.LINE_AA)
            
            # Show the window
            cv2.imshow("Trash Sorter (Press 'q' to quit)", display_frame)

            # Check for exit key
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except KeyboardInterrupt:
        pass
    finally:
        picam2.stop()
        cv2.destroyAllWindows()
        print("Camera stopped.")

if __name__ == "__main__":
    main()
    
