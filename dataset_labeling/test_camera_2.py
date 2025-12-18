import cv2
from picamera2 import Picamera2
import numpy as np
import time
import os

# Initialize the picamera
picam2 = Picamera2()
# Configure for fast, lower-resolution video stream
# The main buffer is used for processing/display, lores is ignored here
video_config = picam2.create_video_configuration(
    # The 'main' stream is the highest resolution, used for final capture
    main={"size": (1280, 720)},

)
picam2.configure(video_config)
picam2.start()

# Give the camera a moment to warm up and adjust exposure
time.sleep(2)

print("Camera stream started. Press SPACEBAR to capture an image. Press 'q' to quit.")
images_path = "images/"
os.makedirs(images_path, exist_ok = True)
while True:
    
    frame_array = picam2.capture_array()
    
    bgr_frame = cv2.cvtColor(frame_array, cv2.COLOR_RGB2BGR)
    
    # 3. Display the frame in an OpenCV window
    cv2.imshow("PiCamera2 Live Stream (SPACE to Capture)", bgr_frame)
    
    # 4. Handle Key Presses (The Capture Button Logic)
    # cv2.waitKey(1) waits 1ms for a key press
    key = cv2.waitKey(1) & 0xFF
    
    # --- Capture Button (Spacebar) ---
    if key == ord(' '):
        
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"capture_{timestamp}.jpg"
        
        # Save the BGR image captured from the stream
        cv2.imwrite(filename, bgr_frame)
        print(f"--- Captured image saved as {bgr_frame} ---")
        
        # Optional: Add a small pause or flash effect
        # For a simple flash, you could display a white image briefly

    # --- Quit Button (Q) ---
    elif key == ord('q'):
        break


# --- Cleanup ---
picam2.stop()
cv2.destroyAllWindows()

print("Camera stream closed.")

