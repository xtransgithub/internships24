from flask import Flask, render_template, jsonify
import time
import RPi.GPIO as GPIO

# Setup for Ultrasonic Sensor
TRIG = 19  # Trigger pin
ECHO = 26  # Echo pin
LED_PIN = 3  # LED pin

# Setup for Stepper Motor
StepPins = [13, 4, 6, 5]  # Stepper motor pins

# Sequence for stepper motor rotation
Seq = [
    [1, 0, 0, 1],
    [1, 0, 0, 0],
    [1, 1, 0, 0],
    [0, 1, 0, 0],
    [0, 1, 1, 0],
    [0, 0, 1, 0],
    [0, 0, 1, 1],
    [0, 0, 0, 1]
]

StepCount = len(Seq)
StepDir = 1  # 1 for clockwise, -1 for counter-clockwise
WaitTime = 0.01  # Stepper motor delay

# Flask setup
app = Flask(_name_)

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Setup ultrasonic sensor and LED pins
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)
GPIO.setup(LED_PIN, GPIO.OUT, initial=GPIO.LOW)

# Setup stepper motor pins
for pin in StepPins:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, False)

StepCounter = 0  # Initialize stepper sequence position

def measure_distance():
    """Measure distance using the ultrasonic sensor."""
    GPIO.output(TRIG, False)
    time.sleep(0.2)

    GPIO.output(TRIG, True)
    time.sleep(0.00001)
    GPIO.output(TRIG, False)

    while GPIO.input(ECHO) == 0:
        pulse_start = time.time()

    while GPIO.input(ECHO) == 1:
        pulse_end = time.time()

    pulse_duration = pulse_end - pulse_start
    distance = pulse_duration * 17150  # Speed of sound in cm/s
    return round(distance, 2)

def rotate_stepper():
    """Rotate the stepper motor continuously."""
    global StepCounter
    for pin in range(4):
        GPIO.output(StepPins[pin], Seq[StepCounter][pin])
    
    StepCounter += StepDir
    if StepCounter >= StepCount:
        StepCounter = 0
    elif StepCounter < 0:
        StepCounter = StepCount - 1
    
    time.sleep(WaitTime)

def stop_stepper():
    """Stop the stepper motor."""
    for pin in StepPins:
        GPIO.output(pin, False)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_data')
def get_data():
    # Get the current distance from the ultrasonic sensor
    distance = measure_distance()

    # Determine LED and motor status
    led_status = "ON" if GPIO.input(LED_PIN) else "OFF"
motor_status = "Rotating" if any(GPIO.input(pin) for pin in StepPins) else "Stopped"

    # Return the data as JSON
    return jsonify(distance=distance, led_status=led_status, motor_status=motor_status)

@app.route('/toggle_led')
def toggle_led():
    # Toggle LED on/off
    if GPIO.input(LED_PIN):
        GPIO.output(LED_PIN, GPIO.LOW)
    else:
        GPIO.output(LED_PIN, GPIO.HIGH)
    return jsonify(status="success")

@app.route('/rotate_motor')
def rotate_motor():
    # Start the stepper motor rotation for 10 steps
    for _ in range(10):  # Rotate for 10 steps
        rotate_stepper()
    return jsonify(status="success")

@app.route('/stop_motor')
def stop_motor():
    # Stop the stepper motor
    stop_stepper()
    return jsonify(status="success")

if _name_ == '_main_':
    try:
        app.run(host='0.0.0.0', port=5000, debug=True)  # Run Flask app
    finally:
        GPIO.cleanup()  # Clean up GPIO resources on exit