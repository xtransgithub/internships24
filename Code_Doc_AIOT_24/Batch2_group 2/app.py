import Adafruit_GPIO.SPI as SPI
import Adafruit_MCP3008
import time
import RPi.GPIO as GPIO
from flask import Flask, render_template, jsonify
import threading


# --- Flask Web Server Setup ---
app = Flask(__name__)

# --- Soil Moisture Sensor Configuration ---
SPI_PORT   = 0
SPI_DEVICE = 0
mcp = Adafruit_MCP3008.MCP3008(spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE))
moisture_threshold = 180

# --- Stepper Motor Configuration ---
GPIO.setmode(GPIO.BCM)
StepPins = [13, 4, 6, 5]
for pin in StepPins:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, False)
Seq = [[1,0,0,1], [1,0,0,0], [1,1,0,0], [0,1,0,0], [0,1,1,0], [0,0,1,0], [0,0,1,1], [0,0,0,1]]
StepCount = len(Seq)
StepDir = 2 # 1 or 2 for clockwise, -1 or -2 for anticlockwise
WaitTime = 10/float(100)
StepCounter = 0

# --- Ultrasonic Sensor Configuration ---
TRIG = 19
ECHO = 26
ALERT_PIN = 20
BUZZER_PIN = 21
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)
GPIO.setup(ALERT_PIN, GPIO.OUT)
GPIO.setup(BUZZER_PIN, GPIO.OUT)
distance = None
alert_message = ""

# --- Shared Variables for Thread Communication ---
moisture_value = 0 #Added to share with the other thread
stop_threads = False #added to allow graceful exit


def measure_distance():
    global distance, alert_message, stop_threads
    while not stop_threads:
        GPIO.output(TRIG, False)
        time.sleep(0.1) #Reduced delay
        GPIO.output(TRIG, True)
        time.sleep(0.00001)
        GPIO.output(TRIG, False)
        while GPIO.input(ECHO)==0 and not stop_threads:
            pulse_start = time.time()
        while GPIO.input(ECHO)==1 and not stop_threads:
            pulse_end = time.time()
        pulse_duration = pulse_end - pulse_start
        distance = pulse_duration * 17150
        distance = round(distance, 2)
        if distance < 2 or distance > 400:
            distance = None
            alert_message = ""
            GPIO.output(BUZZER_PIN, GPIO.LOW)
        else:
            if distance < 10:
                alert_message = "Warning: Bin is almost filled!"
                GPIO.output(ALERT_PIN, 1)
                GPIO.output(BUZZER_PIN, GPIO.HIGH)
            else:
                alert_message = ""
                GPIO.output(ALERT_PIN, 0)
                GPIO.output(BUZZER_PIN, GPIO.LOW)
        time.sleep(1)


# --- Irrigation Control Function ---
def control_irrigation():
    global StepCounter, StepDir, moisture_value, stop_threads, current_motor_direction
    while not stop_threads:
        moisture_value = mcp.read_adc(1)
        print("Moisture Value:", moisture_value)
        if moisture_value < moisture_threshold:
            print("Moisture low - turning motor left")
            StepDir = -2
            current_motor_direction = "Left"  # Update direction
        else:
            print("Moisture high - turning motor right")
            StepDir = 2
            current_motor_direction = "Right"  # Update direction
        for pin in range(0, 4):
            xpin = StepPins[pin]
            if Seq[StepCounter][pin] != 0:
                GPIO.output(xpin, True)
            else:
                GPIO.output(xpin, False)
        StepCounter += StepDir
        if StepCounter >= StepCount:
            StepCounter = 0
        if StepCounter < 0:
            StepCounter = StepCount + StepDir
        time.sleep(WaitTime)

# --- Flask Routes ---
@app.route('/')
def index():
    return render_template('index1.html')

current_motor_direction = "None"  # Initialize with no direction

@app.route('/get_motor_direction')
def get_motor_direction():
    global current_motor_direction
    return jsonify({"direction": current_motor_direction})

@app.route('/get_data')
def get_data():
    global distance, alert_message, moisture_value
    return jsonify(distance=distance, alert_message=alert_message, moisture=moisture_value)

if __name__ == '__main__':
    distance_thread = threading.Thread(target=measure_distance)
    irrigation_thread = threading.Thread(target=control_irrigation)
    distance_thread.daemon = True
    irrigation_thread.daemon = True
    distance_thread.start()
    irrigation_thread.start()
    try:
        app.run(host='0.0.0.0', port=5000, debug=True)
    except KeyboardInterrupt:
        stop_threads = True  # Added to signal the threads to exit gracefully
        time.sleep(1)  # Give threads some time to finish
        pass
    finally:
        GPIO.cleanup()
