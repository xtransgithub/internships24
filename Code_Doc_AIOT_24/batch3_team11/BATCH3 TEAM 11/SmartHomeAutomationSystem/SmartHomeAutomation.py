from flask import Flask, Response, request, jsonify
from flask_socketio import SocketIO
from flask_cors import CORS
import Adafruit_DHT
import RPi.GPIO as GPIO
import threading
import picamera
import io
import time
import random
import hashlib
import os
from twilio.rest import Client

app = Flask(_name_)
socketio = SocketIO(app)
CORS(app, resources={r"/": {"origins": ""}})

# DHT11 Sensor setup
DHT_PIN = 4  # Pin where DHT sensor is connected

# Light sensor setup
LIGHT_PIN = 33  # Board number for the light sensor
GPIO.setmode(GPIO.BOARD)
GPIO.setup(LIGHT_PIN, GPIO.IN)

# LED and Switch Setup
LED2_PIN = 12
LED3_PIN = 3
LED4_PIN = 5
SWITCH2_PIN = 19
SWITCH3_PIN = 21
SWITCH4_PIN = 23

# Setup LEDs as output
GPIO.setup(LED2_PIN, GPIO.OUT, initial=0)
GPIO.setup(LED3_PIN, GPIO.OUT, initial=0)
GPIO.setup(LED4_PIN, GPIO.OUT, initial=0)

# Setup switches as input
GPIO.setup(SWITCH2_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(SWITCH3_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(SWITCH4_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# Buzzer Setup
BUZZER_PIN = 38
GPIO.setup(BUZZER_PIN, GPIO.OUT)

# Sensor data dictionary
sensor_data = {
    'temperature': None,
    'humidity': None,
    'light': None,
    'gas': None,
    'led2': False,  # LED2 state
    'led3': False,  # LED3 state
    'led4': False   # LED4 state
}

# Twilio setup
TWILIO_ACCOUNT_SID = 'ACa0e976c42259ff8d37adc49b9e180dc7'
TWILIO_AUTH_TOKEN = '2914e1e2e3fee939a261c42327a9a21b'
TWILIO_PHONE_NUMBER = '+17753064477'
ALERT_PHONE_NUMBER = '+917013745445'

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

def send_alert(message_body):
    """Send an alert message using Twilio."""
    message = client.messages.create(
        body=message_body,
        from_=TWILIO_PHONE_NUMBER,
        to=ALERT_PHONE_NUMBER
    )
    print(f"Alert sent: {message.sid}")

def activate_buzzer():
    """Activates the buzzer for 1 second."""
    GPIO.output(BUZZER_PIN, GPIO.HIGH)
    time.sleep(1)
    GPIO.output(BUZZER_PIN, GPIO.LOW)

def read_dht_sensor():
    """Reads temperature and humidity from the DHT11 sensor."""
    dht_sensor = Adafruit_DHT.DHT11
    while True:
        humidity = random.randint(30, 80)  # Simulated value
        temperature = random.randint(20, 50)  # Simulated value
        sensor_data['temperature'] = temperature
        sensor_data['humidity'] = humidity
        print(f"Temperature: {temperature}°C")
        print(f"Humidity: {humidity}%")
        if temperature > 40:
            send_alert(f"High temperature detected: {temperature}°C")
            activate_buzzer()
        time.sleep(1)  # Take readings every 1 second

def read_light_sensor():
    """Reads the light sensor status."""
    while True:
        light_state = GPIO.input(LIGHT_PIN)
        sensor_data['light'] = light_state == 0  # True if light is detected
        print("Light Detected" if sensor_data['light'] else "Light Not Detected")
        time.sleep(0.3)  # Read every 0.3 seconds

def read_gas_sensor():
    """Generates random gas values and checks for leakage."""
    while True:
        gas_value = random.randint(100, 1000)  # Random value between 100 and 1000
        sensor_data['gas'] = gas_value
        print(f"Gas Value: {gas_value}")
        if gas_value > 500:
            print("Gas leakage detected! Sending alert...")
            send_alert(f"Gas leakage detected! Value: {gas_value}")
            activate_buzzer()
        time.sleep(2)  # Take readings every 2 seconds

@app.route('/sensor-data', methods=['GET'])
def get_sensor_data():
    """Endpoint to return sensor data as JSON."""
    return jsonify(sensor_data)

@app.route('/led-control', methods=['POST'])
def control_led():
    """Control the LED state via POST request."""
    led2_state = request.json.get('led2', None)
    led3_state = request.json.get('led3', None)
    led4_state = request.json.get('led4', None)

    if led2_state is not None:
        GPIO.output(LED2_PIN, GPIO.HIGH if led2_state else GPIO.LOW)
        sensor_data['led2'] = bool(led2_state)

    if led3_state is not None:
        GPIO.output(LED3_PIN, GPIO.HIGH if led3_state else GPIO.LOW)
        sensor_data['led3'] = bool(led3_state)

    if led4_state is not None:
        GPIO.output(LED4_PIN, GPIO.HIGH if led4_state else GPIO.LOW)
        sensor_data['led4'] = bool(led4_state)

    return jsonify({'led2': sensor_data['led2'], 'led3': sensor_data['led3'], 'led4': sensor_data['led4']})

def monitor_switches():
    """Monitors the states of the switches and controls the LEDs accordingly."""
    def glow_led(channel):
        """Callback function to turn on LED based on switch event."""
        if channel == SWITCH2_PIN:
            GPIO.output(LED2_PIN, True)
            time.sleep(0.2)
            GPIO.output(LED2_PIN, False)
            sensor_data['led2'] = True
        elif channel == SWITCH3_PIN:
            GPIO.output(LED3_PIN, True)
            time.sleep(0.2)
            GPIO.output(LED3_PIN, False)
            sensor_data['led3'] = True
        elif channel == SWITCH4_PIN:
            GPIO.output(LED4_PIN, True)
            time.sleep(0.2)
            GPIO.output(LED4_PIN, False)
            sensor_data['led4'] = True

    GPIO.add_event_detect(SWITCH2_PIN, GPIO.RISING, callback=glow_led, bouncetime=200)
    GPIO.add_event_detect(SWITCH3_PIN, GPIO.RISING, callback=glow_led, bouncetime=200)
    GPIO.add_event_detect(SWITCH4_PIN, GPIO.RISING, callback=glow_led, bouncetime=200)

    while True:
        time.sleep(1)  # Avoid high CPU usage

if _name_ == '_main_':
    threading.Thread(target=read_dht_sensor, daemon=True).start()
    threading.Thread(target=read_light_sensor, daemon=True).start()
    threading.Thread(target=read_gas_sensor, daemon=True).start()
    threading.Thread(target=monitor_switches, daemon=True).start()

    socketio.run(app, host='0.0.0.0', port=5000, debug=True)