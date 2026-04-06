import os
import time
import serial
from serial import SerialException

PORT = "COM9"                          # monitor port
BAUD = 115200                          # baud rate should be synced with microcontroller
HEADER = "time_us,ax,ay,az,gx,gy,gz"   # csv file headers
PREFIX = "right_"                      # output signal file prefix (up_, down_, ...)
CAPTURE_LAST_TIME_US = 3996000         # (SAMPLE_COUNT - 1) * SAMPLE_PERIOD_US

current_file = None
current_filename = None
file_index = 0
ser = None
capture_active = False
last_data_time = None

while os.path.exists(f"{PREFIX}{file_index:02d}.txt"):
    file_index += 1

def connect_serial():
    while True: # the esp32 will drop connection, try to reacquire
        try:
            s = serial.Serial(PORT, BAUD, timeout=1)
            print(f"Connected. port:{PORT} at baud:{BAUD}")
            print("Press RESET to start capture.") # it will print this and hold when ready
            return s
        except SerialException: # the ESP
            print(f"Waiting for {PORT}") # will preint "press reset" and this when dropped
            time.sleep(1)

ser = connect_serial()

while True:
    try:
        line = ser.readline().decode(errors="ignore").strip() # capture line of serial monitor output

        if not line:
            continue

        if line == HEADER: # detected a new file (because the header printed to monitor)
            if current_file is not None:
                current_file.close()
                print(f"Previous file closed: {current_filename}")

            current_filename = f"{PREFIX}{file_index:02d}.txt"
            file_index += 1

            current_file = open(current_filename, "w")
            current_file.write(line + "\n")
            current_file.flush()

            capture_active = True
            last_data_time = None

            print(f"Started new file: {current_filename}")
            print("Capture in progress.") 
            continue    # want to use the next conditional block

        if current_file is not None:
            first = line.split(",")[0]
            if first.isdigit():
                current_file.write(line + "\n")
                current_file.flush()

                t_us = int(first)
                last_data_time = t_us

                if capture_active and t_us >= CAPTURE_LAST_TIME_US: # if we reached last timestamp:
                    current_file.close()
                    print(f"Capture complete: {current_filename}") # note that capture is complete
                    print("Press RESET for the next capture.")
                    current_file = None # reset variables
                    current_filename = None
                    capture_active = False
                    last_data_time = None

    except SerialException:
        print("Serial connection lost. Reconnecting...") # when pritn starts connection may be lost
        try:
            if ser is not None:
                ser.close()
        except:
            pass
        time.sleep(1)
        ser = connect_serial()