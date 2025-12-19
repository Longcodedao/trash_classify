import time
from arduino_controller import ArduinoController
from trash_detect import TrashDetector

# --- CONFIGURATION ---
SERIAL_PORT = "/dev/ttyUSB0" # Check your port!
MODEL_PATH = "../checkpoints/best_model_finetune.pth"

def calculate_timeout(distance_cm):
    """
    Calculate the timeout based on the real-world data which is 
    ~0.19s/cm. We use 0.25s/cm for safety, plus a 2-second buffer
    """
    SECONDS_PER_CM = 0.19
    SECONDS_BUFFER = 2
    
    timeout_sec = (distance_cm * SECONDS_PER_CM) + SECONDS_BUFFER
    return timeout_sec

def main():
    # 1. Initialize Hardware and Model
    print("--- INITIALIZING SYSTEM ---")
    arduino = ArduinoController(port=SERIAL_PORT)
    vision = TrashDetector(checkpoint_path=MODEL_PATH)
    
    arduino.send_command("1 2")
    
    try:
        # 2. Go to Home Position to Receive Trash
        print("\n--- MOVING TO RECEIVE POSITION ---")
        # Ensure we home first to know where we are, then move to 37
        arduino.send_command("R", timeout_duration = 30) 
        time.sleep(1)
        # Move forward to the Receiver 
        arduino.send_command("D32 Forward", calculate_timeout(37)) 
        
        while True:
            print("\n" + "="*40)
            print("       TRASH SORTING ROBOT READY")
            print("="*40)
            
            # 3. Ask User Input
            user_input = input("Place trash and type 'yes' to start (or 'q' to quit): ").strip().lower()
            
            if user_input == 'q':
                break
                
            if user_input == 'yes':
                # 4. Go to Detect Section (Limit Switch / Home)
                print("\n[Step 1] Moving to Detection Zone...")
                # Distance from the Receiver and the Home is 37 cm
                arduino.send_command("R", calculate_timeout(37)) 
                
                # 5. Detect for 5 Seconds
                print("\n[Step 2] Identifying Object...")
                detected_class = vision.detect_for_duration(duration=5)
                
                # 6. Move based on Class
                print(f"\n[Step 3] Sorting Item: {detected_class.upper()}")
                
                if detected_class in ['cardboard', 'paper']:
                    # Move to Paper Bin
                    arduino.send_command("D32 Forward", calculate_timeout(37))
                    
                elif detected_class == 'plastic':
                    # Move to Plastic Bin
                    arduino.send_command("D64 Forward", calculate_timeout(74))
                    
                elif detected_class in ['glass', 'metal']:
                    # Move to Glass/Metal Bin
                    arduino.send_command("D96 Forward", calculate_timeout(115))
                    
                else: 
                    # 'trash' or unknown
                    print("Classified as General Trash. Staying at position.")
                    # Assuming the "R" position is the General Trash bin. 
                    # If not, add a command here.
                    pass 

                # 7. Drop the Trash
                print("\n[Step 4] Dropping Item...")
                arduino.send_command("OPEN")
                time.sleep(1) # Give it a moment
                arduino.send_command("CLOSE")
                time.sleep(1) # Give it a moment
                
                # 8. Reset Cycle (Return to Receive Position)
                print("\n[Step 5] Resetting to Receive Position...")
                arduino.send_command("R", timeout_duration = 30)           # Re-home to ensure accuracy
                arduino.send_command("D32 Forward", calculate_timeout(37)) # Go back to start
                
            else:
                print("Invalid input. Please type 'yes' or 'q'.")

    except KeyboardInterrupt:
        print("\nForce Exit detected.")
    
    finally:
        # Cleanup
        print("\n--- SHUTTING DOWN ---")
        arduino.close()
        vision.close()


if __name__ == "__main__":
    main()
