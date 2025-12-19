import tkinter as tk
from tkinter import ttk
import cv2
from picamera2 import Picamera2
import numpy as np
import time
import threading
import os

import torch
from libcamera import controls

# import torchvision.transforms as transforms
# from PIL import Image


# --- Global Variables ---
CAMERA_CONFIGURED = False
PICAM2 = None
CURRENT_RESOLUTION = (640, 480)
RESTART_STREAM = threading.Event()

# Default Camera Values
DEFAULT_EXPOSURE = 10000
DEFAULT_GAIN = 1.0
DEFAULT_FOCUS = 0.0  # 0.0 = Infinity, 3.33 = 30cm

# Thread-safe container
LATEST_FRAME_DATA = {"frame": None, "lock": threading.Lock()}

RESOLUTION_OPTIONS = [
    (640, 480),
    (1280, 720),
    (1920, 1080)
]
FOLDER_IMG = '../../images'
os.makedirs(FOLDER_IMG, exist_ok=True)

# --- Transforms ---
# Input: PIL Image (RGB)
# Output: PIL Image (RGB)
#save_transform = transforms.Compose([
#    transforms.Resize(256),
#    transforms.CenterCrop(224),
#])

# --- Camera Functions ---

def start_camera_stream():
    global PICAM2, CAMERA_CONFIGURED
    
    if PICAM2 is None:
        PICAM2 = Picamera2()
    
    if CAMERA_CONFIGURED:
        PICAM2.stop()
        CAMERA_CONFIGURED = False
        
    res_w, res_h = CURRENT_RESOLUTION
    print(f"Configuring camera for resolution: {res_w}x{res_h}")
    
    # Configured for RGB.
    # We will convert this to BGR only when handing it to OpenCV.
    config = PICAM2.create_video_configuration(
        main={"size": (res_w, res_h), "format": "RGB888"},
        controls={
            "AfMode": controls.AfModeEnum.Manual,
            "LensPosition": float(focus_var.get()),
            "AeEnable": False, 
            "ExposureTime": int(exposure_var.get()),
            "AnalogueGain": float(gain_var.get()) 
        }
    )
    PICAM2.configure(config)
    PICAM2.start()
    CAMERA_CONFIGURED = True
    time.sleep(1) 

def capture_image(resolution_label):
    """Saves the current frame safely."""
    
    # 1. Get the latest RGB frame
    with LATEST_FRAME_DATA["lock"]:
        if LATEST_FRAME_DATA["frame"] is None:
            print("Error: No frame available yet.")
            return
        frame_rgb = LATEST_FRAME_DATA["frame"].copy()

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    res_w, res_h = CURRENT_RESOLUTION

    filename = f"{FOLDER_IMG}/capture_{res_w}x{res_h}_{timestamp}.jpg"
    cv2.imwrite(filename, frame_rgb)
            

# --- Event Handlers ---

def on_resolution_change(*args):
    """Restart stream only when resolution changes."""
    global CURRENT_RESOLUTION
    selected_res_str = resolution_var.get()
    w, h = map(int, selected_res_str.split('x'))
    CURRENT_RESOLUTION = (w, h)
    
    # Signal thread to restart
    RESTART_STREAM.set()

def update_live_controls(val=None):
    """Updates Exposure, Gain, and Focus instantly without restarting."""
    # 1. Update Labels
    exp_val = int(float(exposure_var.get()))
    gain_val = float(gain_var.get())
    focus_val = float(focus_var.get())

    lbl_exp_val.config(text=f"{exp_val} µs")
    lbl_gain_val.config(text=f"{gain_val:.1f}x")
    lbl_focus_val.config(text=f"{focus_val:.2f} dp")

    # 2. Send controls to camera immediately
    if PICAM2 is not None and CAMERA_CONFIGURED:
        try:
            PICAM2.set_controls({
                "AfMode": controls.AfModeEnum.Manual,
                "LensPosition": focus_val,
                "ExposureTime": exp_val,
                "AnalogueGain": gain_val
            })
        except Exception as e:
            print(f"Control Update Error: {e}")

def camera_thread_loop():
    while True:
        if not root.winfo_exists():
            break
            
        # Handle Restart Request
        if RESTART_STREAM.is_set():
            start_camera_stream()
            RESTART_STREAM.clear()
            
        if not CAMERA_CONFIGURED:
            time.sleep(0.1)
            continue
            
        try:
            # Capture RGB
            frame_rgb = PICAM2.capture_array()
            
            with LATEST_FRAME_DATA["lock"]:
                LATEST_FRAME_DATA["frame"] = frame_rgb
            
            # Convert to BGR for OpenCV Display
            cv2.imshow("PiCamera2 Live Stream", frame_rgb)
            
            if cv2.waitKey(1) & 0xFF == ord('q') or \
                cv2.getWindowProperty("PiCamera2 Live Stream", cv2.WND_PROP_VISIBLE) < 1:
                break
            
        except Exception as e:
            print(f"Stream Error: {e}")
            time.sleep(0.1)
            
    cv2.destroyAllWindows()



def on_closing():
    if PICAM2 is not None and CAMERA_CONFIGURED:
        PICAM2.stop()
    cv2.destroyAllWindows()
    root.destroy()
    
    
    
# --- GUI Setup ---
root = tk.Tk()
root.title("PiCamera2 Manual Control")

# Variables
resolution_var = tk.StringVar(root)
exposure_var = tk.DoubleVar(root, value=DEFAULT_EXPOSURE) # DoubleVar for smooth sliding
gain_var = tk.DoubleVar(root, value=DEFAULT_GAIN)
focus_var = tk.DoubleVar(root, value=DEFAULT_FOCUS)

# Main Control Container
control_frame = ttk.LabelFrame(root, text="Camera Settings", padding="10")
control_frame.pack(fill='x', padx=10, pady=5)

# 1. Resolution (Restarts Stream)
res_frame = ttk.Frame(control_frame)
res_frame.pack(fill='x', pady=5)
ttk.Label(res_frame, text="Resolution:", width=10).pack(side=tk.LEFT)
res_options_str = [f"{w}x{h}" for w, h in RESOLUTION_OPTIONS]
resolution_var.set(res_options_str[0])
res_dropdown = ttk.OptionMenu(res_frame, resolution_var, res_options_str[0], *res_options_str, command=on_resolution_change)
res_dropdown.pack(side=tk.LEFT)

# 2. Exposure Control
exp_frame = ttk.Frame(control_frame)
exp_frame.pack(fill='x', pady=5)
ttk.Label(exp_frame, text="Exposure:", width=10).pack(side=tk.LEFT)
exp_scale = ttk.Scale(exp_frame, from_=500, to=50000, variable=exposure_var, command=update_live_controls, length=200)
exp_scale.pack(side=tk.LEFT, padx=5)
lbl_exp_val = ttk.Label(exp_frame, text=f"{DEFAULT_EXPOSURE} µs", width=10)
lbl_exp_val.pack(side=tk.LEFT)

# 3. Gain Control
gain_frame = ttk.Frame(control_frame)
gain_frame.pack(fill='x', pady=5)
ttk.Label(gain_frame, text="Gain:", width=10).pack(side=tk.LEFT)
gain_scale = ttk.Scale(gain_frame, from_=1.0, to=16.0, variable=gain_var, command=update_live_controls, length=200)
gain_scale.pack(side=tk.LEFT, padx=5)
lbl_gain_val = ttk.Label(gain_frame, text=f"{DEFAULT_GAIN}x", width=10)
lbl_gain_val.pack(side=tk.LEFT)

# 4. FOCUS Control (The new part)
focus_frame = ttk.Frame(control_frame)
focus_frame.pack(fill='x', pady=5)
ttk.Label(focus_frame, text="Focus (Diopter):", width=12).pack(side=tk.LEFT)
# Range 0.0 (Infinity) to 20.0 (5cm Close-up)
focus_scale = ttk.Scale(focus_frame, from_=0.0, to=20.0, variable=focus_var, command=update_live_controls, length=200)
focus_scale.pack(side=tk.LEFT, padx=5)
lbl_focus_val = ttk.Label(focus_frame, text=f"{DEFAULT_FOCUS} dp", width=10)
lbl_focus_val.pack(side=tk.LEFT)

# Capture & Status
btn_frame = ttk.Frame(root, padding="10")
btn_frame.pack(fill='x')
capture_button = ttk.Button(btn_frame, text="CAPTURE PHOTO", command=lambda: capture_image(status_label))
capture_button.pack(fill='x')

status_label = ttk.Label(root, text="Camera Ready", relief=tk.SUNKEN, anchor=tk.W)
status_label.pack(fill='x', padx=10, pady=5)

# Start System
start_camera_stream()
camera_thread = threading.Thread(target=camera_thread_loop, daemon=True)
camera_thread.start()

root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()
