import cv2
import numpy as np
import time
import torch
import torch.nn as nn
import torchvision.transforms as transforms
from torchvision.models import mobilenet_v3_small
from PIL import Image
from picamera2 import Picamera2
from collections import Counter

class TrashDetector:
    def __init__(self, checkpoint_path="../checkpoints/best_model_finetune.pth"):
        self.device = torch.device("cpu")
        self.labels = ['cardboard', 'glass', 'metal', 'paper', 'plastic', 'trash']
        self.confidence_threshold = 0.60
        self.model = self.load_model(checkpoint_path, len(self.labels))
        
        # Preprocessing
        self.preprocess = transforms.Compose([
            transforms.CenterCrop((480, 480)),
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])

        # Setup Camera
        print("[Vision] Starting Camera...")
        self.picam2 = Picamera2()
        config = self.picam2.create_preview_configuration(
            main={"format": "RGB888", "size": (640, 480)},
            controls={
                "FrameRate": 30,
                "ExposureTime": 7276,
                "AnalogueGain": 1.0,
                "LensPosition": 7.02
            }
        )
        self.picam2.configure(config)
        self.picam2.start()
        print("[Vision] Camera Ready.")

    def load_model(self, path, num_classes):
        print(f"[Vision] Loading model from {path}...")
        model = mobilenet_v3_small(weights=None)
        in_features = model.classifier[3].in_features
        model.classifier[3] = nn.Linear(in_features, num_classes)
        try:
            model.load_state_dict(torch.load(path, map_location=self.device))
        except FileNotFoundError:
            print(f"[Vision] ERROR: Checkpoint not found at {path}")
            exit()
        except RuntimeError as e:
            print(f"[Vision] ERROR: Model mismatch! {e}")
            exit()
        model.to(self.device)
        model.eval()
        return model

    def detect_for_duration(self, duration=5):
        """
        Runs detection for 'duration' seconds.
        Returns the detected label with the highest frequency of occurrence.
        """
        print(f"[Vision] Analyzing for {duration} seconds...")
        start_time = time.time()
        
        # Array to save every detection (or np.nan)
        detection_history = []

        while time.time() - start_time < duration:
            try:
                # Capture
                frame = self.picam2.capture_array()
                display_frame = frame # No BGR conversion needed for Picamera2 usually, but adjust if colors are wrong
                
                # Inference
                pil_img = Image.fromarray(frame)
                input_tensor = self.preprocess(pil_img).unsqueeze(0).to(self.device)

                with torch.no_grad():
                    outputs = self.model(input_tensor)
                    probabilities = torch.nn.functional.softmax(outputs, dim=1)[0]

                top_prob, top_catid = torch.max(probabilities, 0)
                confidence = top_prob.item()
                predicted_label = self.labels[top_catid.item()]

                # --- LOGIC UPDATE: Store Data ---
                if confidence > self.confidence_threshold:
                    detection_history.append(predicted_label)
                    
                    # Visualization (Valid)
                    color = (0, 255, 0)
                    text = f"{predicted_label.upper()}: {confidence*100:.1f}%"
                else:
                    detection_history.append(np.nan)
                    
                    # Visualization (Low Confidence)
                    color = (0, 0, 255)
                    text = f"Waiting... ({predicted_label}: {confidence*100:.1f}%)"

                # Show Window
                # cv2.cvtColor might be needed if your display looks blue/orange swapped
                cv2.putText(display_frame, text, (10, 50), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2, cv2.LINE_AA)
                cv2.imshow("Trash Sorter", display_frame)
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

            except Exception as e:
                print(f"Frame Error: {e}")

        # --- FINAL VOTING LOGIC ---
        
        # 1. Filter out np.nan (undetected frames)
        valid_detections = [x for x in detection_history if x is not np.nan]
        
        # 2. Check if we have enough data
        total_valid_frames = len(valid_detections)
        print(f"[Vision] Total valid frames captured: {total_valid_frames}")

        if total_valid_frames == 0:
            print("[Vision] No confident detections made.")
            return "trash"

        # 3. Count frequencies
        vote_counts = Counter(valid_detections)
        most_common_label, count = vote_counts.most_common(1)[0]
        
        print(f"[Vision] Vote Results: {dict(vote_counts)}")

        # 4. THRESHOLD STRATEGY
        # We define a 'Consensus Threshold'. 
        # If the camera runs at ~10 FPS, 5 seconds = 50 frames.
        # We want the winner to appear in at least 15 frames to be sure.
        MIN_VOTE_THRESHOLD = 15 

        if count >= MIN_VOTE_THRESHOLD:
            print(f"[Vision] Winner: {most_common_label.upper()} with {count} votes.")
            return most_common_label
        else:
            print(f"[Vision] Winner {most_common_label} only had {count} votes (Threshold: {MIN_VOTE_THRESHOLD}). returning 'trash'")
            return "trash"

    def close(self):
        self.picam2.stop()
        cv2.destroyAllWindows()
        print("[Vision] Camera stopped.")
