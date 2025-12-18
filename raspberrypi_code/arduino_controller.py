import serial
import time

class ArduinoController:
    def __init__(self, port="/dev/ttyUSB0", baud_rate=9600):
        self.port = port
        self.baud_rate = baud_rate
        self.ser = None
        self.COMPLETION_SIGNALS = ["DONE_MOVE", "DONE_HOME", "DONE_OPEN",
									"DONE_CLOSE", "DONE_MOTOR_STOPPED",
									"DONE_COMMAND"]
        
        try:
            self.ser = serial.Serial(self.port, self.baud_rate, timeout=1)
            print(f"[Serial] Successfully connected to {self.port}")
            time.sleep(2) # Wait for Arduino reset
            self.ser.flushInput()
        except serial.SerialException as e:
            print(f"[Serial] Error: Could not open port {self.port}. {e}")
            self.ser = None
            
    def send_command(self, command, timeout_duration=5):
        """
        Sends a command to the Arduino and waits for a completion signal.
        Returns True if successful, False otherwise.
        
        Args:
            command (str): The string command to send (e.g., "D115 Forward").
            timeout_duration (int): How many seconds to wait before giving up.
                                    Increase this for long movements!
        """
        if not self.ser or not self.ser.is_open:
            print("[Serial] Port not open.")
            return False
        
        try:
            full_command = command + "\n"
            self.ser.write(full_command.encode("utf-8"))
            print(f"[Serial] Sent: '{command}'")

            start_time = time.time()

            # Wait for response
            while True:
                if self.ser.in_waiting:
                    try:
                        line = self.ser.readline().decode("utf-8", errors='ignore').strip()
                    except:
                        continue # Skip bad decoding bytes

                    if line:
                        print(f"      > {line}") 
                        
                        # Check for completion signals
                        if any(sig in line for sig in self.COMPLETION_SIGNALS):
                            return True
                
                # Check timeout
                # FIX: We now strictly use the passed 'timeout_duration' variable.
                if (time.time() - start_time) > timeout_duration:
                    print(f"[Serial] Timeout waiting for response (>{timeout_duration}s).")
                    return False

                time.sleep(0.01)
                
        except Exception as e:
            print(f"[Serial] Unexpected error: {e}")
            return False
            
    def close(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("[Serial] Connection closed")
