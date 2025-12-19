import serial 
import time

# --- CONFIGURATION ---
ARDUINO_PORT = "/dev/ttyUSB0" # Double check if it's ttyUSB0 or ttyUSB1
BAUD_RATE = 9600

# Updated to match the strings sent by the new Arduino code
COMPLETION_SIGNALS = ["DONE_MOVE", "DONE_HOME", "DONE_OPEN", "DONE_CLOSE"]

ser = None

# Attempt to open the serial port
try:
    ser = serial.Serial(ARDUINO_PORT, BAUD_RATE, timeout=1)
    print(f"Successfully connected to Arduino Nano at {ARDUINO_PORT}")
    time.sleep(2) 
    ser.flushInput() 
except serial.SerialException as e:
    print(f"Error: Could not open serial port {ARDUINO_PORT}. {e}")
    exit()

def send_command(command):
    if ser and ser.is_open:
        try:
            full_command = command + "\n"
            ser.write(full_command.encode("utf-8"))
            print(f"Sent: '{command}'")
            
            # Start timer for timeout logic
            start_time = time.time()
            
            # Read response loop
            while True:
                if ser.in_waiting:
                    line = ser.readline().decode("utf-8").strip()
                    if line:
                        print(f"        > {line}")
                        
                        # Check if any of our completion signals are in the line
                        if any(sig in line for sig in COMPLETION_SIGNALS):
                            print("\n--- ACTION COMPLETED SUCCESSFULLY ---")
                            break # Exit the waiting loop
                
                # Safety timeout (for commands like LED that don't send a DONE signal)
                if time.time() - start_time > 0.5 and not any(x in command for x in ['D', 'R', 'OPEN', 'CLOSE']):
                    break
                
                time.sleep(0.01)

        except Exception as e:
            print(f"Unexpected error: {e}")
    else:
        print("Serial port is not open.")

def main_menu():
    print("\n--- Trash Cabinet Control Menu ---")
    print("0: Turn LED OFF")
    print("1: Turn LED ON (Set %)")
    print("2: Run Motor 1 Rev")
    print("3: Emergency Stop Motor")
    print("M: Move Motor by Distance")
    print("R: Home Motor (Run to Limit)")
    print("O: OPEN Cabinet Servos")
    print("C: CLOSE Cabinet Servos")
    print("Q: Quit")

def get_led_intensity():
    while True:
        try:
            val = input("Enter brightness % (0-100): ").strip()
            if 0 <= int(val) <= 100:
                return f"1 {val}"
            print("Please enter a value between 0 and 100.")
        except ValueError:
            print("Invalid input.")

def get_distance_and_direction():
    while True:
        try:
            dist = input("Enter distance in cm: ").strip()
            direction = input("Enter direction (Forward/Reverse): ").strip().upper()
            if direction in ['FORWARD', 'REVERSE']:
                return f"D{dist} {direction}"
            print("Invalid direction.")
        except Exception as e:
            print(f"Error: {e}")

# --- MAIN EXECUTION LOOP ---
try:
    while True:
        main_menu()
        choice = input("Choice: ").strip().upper()

        if choice == '1':
            cmd = get_led_intensity()
            send_command(cmd)
        elif choice == '0':
            send_command('0')
        elif choice == '2':
            send_command('2')
        elif choice == '3':
            send_command('3')
        elif choice == 'R':
            send_command('R')
        elif choice == 'M':
            cmd = get_distance_and_direction()
            send_command(cmd)
        elif choice == 'O':
            send_command('OPEN')
        elif choice == 'C':
            send_command('CLOSE')
        elif choice == 'Q':
            break
        else:
            print("Invalid choice.")

except KeyboardInterrupt:
    print("\nExiting...")

finally:
    if ser and ser.is_open:
        ser.close()
        print("Serial port closed.")
