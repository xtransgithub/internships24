import RPi.GPIO as GPIO
import time
import spidev  # For interfacing with the ADC (e.g., MCP3008)
import Adafruit_DHT  # For reading temperature and humidity
from flask import Flask, render_template
from flask_socketio import SocketIO
import threading

# LCD Pin Definitions
LCD_RS = 15
LCD_E = 12
LCD_D4 = 23
LCD_D5 = 21
LCD_D6 = 19
LCD_D7 = 24

# Stepper Motor Pin Definitions
MOTOR_PINS = [13, 4, 6, 5]  # GPIO pins connected to the stepper motor (BCM mode)
SOIL_MOISTURE_CHANNEL = 1  # ADC channel for soil moisture sensor
THRESHOLD = 900  # Soil moisture threshold (adjust based on calibration)

# ADC Setup (using MCP3008)
spi = spidev.SpiDev()  # Create an SPI object
spi.open(0, 0)  # Open SPI bus 0, device 0
spi.max_speed_hz = 1350000

# LCD Constants
LCD_WIDTH = 16
LCD_CHR = True
LCD_CMD = False
LCD_LINE_1 = 0x80
E_PULSE = 0.0005
E_DELAY = 0.0005

# Stepper Motor Step Sequence
STEP_SEQUENCE = [
    [1, 0, 0, 1],
    [1, 0, 0, 0],
    [1, 1, 0, 0],
    [0, 1, 0, 0],
    [0, 1, 1, 0],
    [0, 0, 1, 0],
    [0, 0, 1, 1],
    [0, 0, 0, 1],
]

# DHT Sensor Setup
SENSOR = Adafruit_DHT.DHT11  # Change to DHT22 if using that sensor
PIN = 4  # GPIO pin where the DHT sensor is connected

# Flask and SocketIO Setup
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

def read_adc(channel):
    """
    Reads the ADC value from the specified channel.
    """
    if channel < 0 or channel > 7:
        raise ValueError("ADC channel must be between 0 and 7.")
    adc = spi.xfer2([1, (8 + channel) << 4, 0])
    data = ((adc[1] & 3) << 8) + adc[2]
    return data

# LCD Functions
def lcd_init():
    lcd_byte(0x33, LCD_CMD)
    lcd_byte(0x32, LCD_CMD)
    lcd_byte(0x06, LCD_CMD)
    lcd_byte(0x0C, LCD_CMD)
    lcd_byte(0x28, LCD_CMD)
    lcd_byte(0x01, LCD_CMD)
    time.sleep(E_DELAY)

def lcd_byte(bits, mode):
    GPIO.output(LCD_RS, mode)
    GPIO.output(LCD_D4, bits & 0x10 == 0x10)
    GPIO.output(LCD_D5, bits & 0x20 == 0x20)
    GPIO.output(LCD_D6, bits & 0x40 == 0x40)
    GPIO.output(LCD_D7, bits & 0x80 == 0x80)
    lcd_toggle_enable()
    GPIO.output(LCD_D4, bits & 0x01 == 0x01)
    GPIO.output(LCD_D5, bits & 0x02 == 0x02)
    GPIO.output(LCD_D6, bits & 0x04 == 0x04)
    GPIO.output(LCD_D7, bits & 0x08 == 0x08)
    lcd_toggle_enable()

def lcd_toggle_enable():
    time.sleep(E_DELAY)
    GPIO.output(LCD_E, True)
    time.sleep(E_PULSE)
    GPIO.output(LCD_E, False)
    time.sleep(E_DELAY)

def lcd_string(message, line):
    message = message.ljust(LCD_WIDTH, " ")
    lcd_byte(line, LCD_CMD)
    for i in range(LCD_WIDTH):
        lcd_byte(ord(message[i]), LCD_CHR)

# Stepper Motor Functions
def setup_stepper():
    for pin in MOTOR_PINS:
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, False)

def step_motor(step_sequence, delay=0.005):
    for step in step_sequence:
        for i in range(4):
            GPIO.output(MOTOR_PINS[i], step[i])
        time.sleep(delay)

def rotate_motor(steps, direction=1):
    sequence = STEP_SEQUENCE if direction == 1 else STEP_SEQUENCE[::-1]
    for _ in range(steps):
        step_motor(sequence)

# DHT Sensor Functions
def read_temperature_and_humidity():
    """
    Reads temperature and humidity from the DHT sensor.
    Returns a tuple (temperature, humidity).
    """
    humidity, temperature = Adafruit_DHT.read_retry(SENSOR, PIN)
    return humidity, temperature

# Route to serve the HTML page
@app.route('/')
def index():
    return render_template('plant_monitor.html')

# Background thread for sensor data
def sensor_background_thread():
    while True:
        try:
            # Read soil moisture level
            soil_moisture = read_adc(SOIL_MOISTURE_CHANNEL)

            # Read temperature and humidity
            humidity, temperature = read_temperature_and_humidity()

            # Determine system status
            status = 'Dry' if soil_moisture > THRESHOLD else 'Normal'

            # Emit sensor data via WebSocket
            socketio.emit('sensor_update', {
                'soil_moisture': soil_moisture,
                'temperature': temperature or 0,
                'humidity': humidity or 0,
                'status': status
            })

            # Check if soil is dry and activate motor
            if soil_moisture > THRESHOLD:
                print("Soil is dry! Activating motor...")
                rotate_motor(steps=100, direction=1)  # Rotate motor for irrigation simulation
            
            time.sleep(5)  # Update every 5 seconds

        except Exception as e:
            print(f"Error in sensor background thread: {e}")
            time.sleep(5)

def setup_gpio():
    """
    Set up GPIO pins and initialize components
    """
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)

    # Setup LCD Pins
    GPIO.setup(LCD_E, GPIO.OUT)
    GPIO.setup(LCD_RS, GPIO.OUT)
    GPIO.setup(LCD_D4, GPIO.OUT)
    GPIO.setup(LCD_D5, GPIO.OUT)
    GPIO.setup(LCD_D6, GPIO.OUT)
    GPIO.setup(LCD_D7, GPIO.OUT)
    lcd_init()

    # Setup Stepper Motor
    setup_stepper()

def start_flask_server():
    """
    Start the Flask server with WebSocket support
    """
    try:
        # Setup GPIO before starting server
        setup_gpio()

        # Start sensor background thread
        socketio.start_background_task(sensor_background_thread)

        # Run the Flask application
        socketio.run(app, host='0.0.0.0', port=5000, debug=True)
    except Exception as e:
        print(f"Error starting server: {e}")
    finally:
        # Cleanup on exit
        GPIO.cleanup()
        spi.close()

if __name__ == '__main__':
    start_flask_server()
