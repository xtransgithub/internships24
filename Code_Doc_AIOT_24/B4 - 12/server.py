from flask import Flask, render_template, jsonify
from flask_cors import CORS
import RPi.GPIO as GPIO
import time
from threading import Thread

app = Flask(_name_)
CORS(app)  # Enable CORS for all routes

# GPIO setup for dispensing
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
dispense_pin = 17  # Example GPIO pin (change this to the pin controlling your feeder)
GPIO.setup(dispense_pin, GPIO.OUT)

# GPIO setup for stepper motor control
StepPins = [13, 4, 6, 5]  # Stepper motor pins (change these to your actual pins)
for pin in StepPins:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, False)

# Define the stepper motor sequence (as provided in the original code)
Seq = [[1, 0, 0, 1],
       [1, 0, 0, 0],
       [1, 1, 0, 0],
       [0, 1, 0, 0],
       [0, 1, 1, 0],
       [0, 0, 1, 0],
       [0, 0, 1, 1],
       [0, 0, 0, 1]]

StepCount = len(Seq)
StepDir = 2  # Direction: 1 for clockwise, -1 for anti-clockwise

# New, decreased wait time for faster motor movement
WaitTime = 0.02  # Reduced interval time between steps (faster)

# Number of steps to open and close
open_steps = 60  # Steps to "open" (dispense)
close_steps = 60  # Steps to "close" (stop dispensing)

# Variable to control the stepper motor loop
stop_motor = False  # This flag will be used to stop the motor

# Route for home page
@app.route('/')
def home():
    return render_template("index.html")

# Route for About page
@app.route('/about')
def about():
    return render_template("about.html")

# Function to control stepper motor rotation for open/close actions
def stepper_motor_rotation(steps, direction):
    global stop_motor
    StepCounter = 0
    for _ in range(steps):
        if stop_motor:
            break
        print(StepCounter)
        print(Seq[StepCounter])

        for pin in range(0, 4):
            xpin = StepPins[pin]
            if Seq[StepCounter][pin] != 0:
                GPIO.output(xpin, True)
            else:
                GPIO.output(xpin, False)

        StepCounter += direction

        # If we reach the end of the sequence, start again
        if StepCounter >= StepCount:
            StepCounter = 0
        if StepCounter < 0:
            StepCounter = StepCount + direction

        # Wait before moving to the next step
        time.sleep(WaitTime)

    print("Stepper motor stopped.")

# Function to perform the dispensing cycle (open and close)
def automatic_dispensing_cycle():
    print("Opening...")
    # Activate dispensing (open the mechanism)
    GPIO.output(dispense_pin, GPIO.HIGH)
    motor_thread = Thread(target=stepper_motor_rotation, args=(open_steps, StepDir))  # Open
    motor_thread.start()
    motor_thread.join()  # Wait for motor to finish

    print("Dispensing...")
    time.sleep(1)  # Simulate dispensing food for 5 seconds (adjust as needed)

    print("Closing...")
    # Deactivate dispensing (close the mechanism)
    GPIO.output(dispense_pin, GPIO.LOW)
    motor_thread = Thread(target=stepper_motor_rotation, args=(close_steps, -StepDir))  # Close
    motor_thread.start()
    motor_thread.join()  # Wait for motor to finish

    print("Cycle complete.")

# Route for starting the dispensing cycle
@app.route('/start', methods=['POST'])
def start_dispensing():
    print("Starting dispensing...")
    
    # Start the dispensing cycle (open and close)
    dispensing_thread = Thread(target=automatic_dispensing_cycle)
    dispensing_thread.start()

    return jsonify(message="Dispensing started!")

if _name_ == '_main_':
    try:
        app.run(host='0.0.0.0', port=3000, debug=True)
    except KeyboardInterrupt:
        print("Server stopped")
    finally:
        GPIO.cleanup()  # Clean up GPIO pins when the server is stopped