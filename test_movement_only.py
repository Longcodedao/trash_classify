import time
from arduino_controller import ArduinoController

# --- CONFIGURATION ---
SERIAL_PORT = "/dev/ttyUSB0"  # Check your port
BAUD_RATE = 9600

def main():
    print("--- DEBUGGING MOVEMENT SEQUENCE ---")
    arduino = ArduinoController(port=SERIAL_PORT, baud_rate=BAUD_RATE)
    
    # Give Arduino a moment to reset if it just connected
    time.sleep(2)

    try:
        # 1. LED ON (1 1)
        print("\n[Test 1] Sending '1 1' (LED ON)")
        response = arduino.send_command("1 1")
        print(f"Arduino Response: {response}")
        time.sleep(1)

        # 2. HOME (R)
        print("\n[Test 2] Sending 'R' (Homing)")
        # This usually takes 2-5 seconds depending on position
        response = arduino.send_command("R", timeout_duration=30) 
        print(f"Arduino Response: {response}")
        time.sleep(1)

        # 3. LONG MOVE (D115 Forward)
        # 115cm is a long distance. If speed is slow, this might take >10 seconds.
        print("\n[Test 3] Sending 'D37 Forward'")
        # CRITICAL: We increase timeout to 20 seconds to ensure we wait for it to finish.
        start_time = time.time()
        response = arduino.send_command("D37 Forward", timeout_duration=25) 
        duration = time.time() - start_time
        print(f"Arduino Response: {response}")
        print(f"Move took {duration:.2f} seconds")
        
        # Check if we actually got a DONE message or if we timed out
        if not response:
            print("!!! WARNING: Command Timed Out. Motor might still be moving! !!!")
        
        time.sleep(1)

        # 4. HOME AGAIN (R)
        print("\n[Test 4] Sending 'R' (Homing Again)")
        # If the previous move finished correctly, this should work.
        response = arduino.send_command("R", timeout_duration=25)
        print(f"Arduino Response: {response}")

    except KeyboardInterrupt:
        print("\nStopped by User")

    finally:
        arduino.close()
        print("\n--- TEST COMPLETE ---")

if __name__ == "__main__":
    main()
