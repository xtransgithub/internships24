import smtplib
import RPi.GPIO as GPIO
import Adafruit_DHT 
from Adafruit_DHT import read_retry, DHT11
import time
from datetime import datetime

# Define pins for light sensor, ultrasonic sensor, LEDs, and DHT11
light_sensor_pin = 13
trig_pin = 19
echo_pin = 26
led_pin_1 = 18  # First streetlight
led_pin_2 = 12  # Second streetlight
led_pin_3 = 3   # Third streetlight
led_pin_4 = 5   # Fourth streetlight
dht_pin = 4     # Pin connected to DHT11 data

# Set up GPIO pins
GPIO.setmode(GPIO.BCM)
GPIO.setup(light_sensor_pin, GPIO.IN)
GPIO.setup(trig_pin, GPIO.OUT)
GPIO.setup(echo_pin, GPIO.IN)
GPIO.setup(led_pin_1, GPIO.OUT)
GPIO.setup(led_pin_2, GPIO.OUT)
GPIO.setup(led_pin_3, GPIO.OUT)
GPIO.setup(led_pin_4, GPIO.OUT)

# Define the DHT sensor type
DHT_SENSOR = Adafruit_DHT.DHT11

# Function to read the light sensor
def read_light():
    return GPIO.input(light_sensor_pin)

# Function to measure distance using the ultrasonic sensor
def measure_distance():
    GPIO.output(trig_pin, GPIO.LOW)
    time.sleep(0.0001)
    GPIO.output(trig_pin, GPIO.HIGH)
    time.sleep(0.0001)
    GPIO.output(trig_pin, GPIO.LOW)

    pulse_start = time.time()
    while GPIO.input(echo_pin) == 0:
        pulse_start = time.time()

    pulse_end = time.time()
    while GPIO.input(echo_pin) == 1:
        pulse_end = time.time()

    pulse_duration = pulse_end - pulse_start
    distance = pulse_duration * 17150
    return round(distance, 2)

# Function to read humidity from DHT11 sensor
def read_humidity():
    try:
        humidity, temperature = Adafruit_DHT.read(DHT_SENSOR, dht_pin)
        if humidity is None:
            raise ValueError("Sensor error")
        return humidity
    except Exception as e:
        print("Error reading humidity:", e)
        return None

# Function to send email alerts
def send_email_alert(subject, body):
    sender_email = "surajnaidu73@gmail.com"
    password = "kfzzgiogrcylptcw"
    receiver_email = "1825mahalakshmi@gmail.com"

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, password)
            message = f"Subject: {subject}

{body}"
            server.sendmail(sender_email, receiver_email, message)
        print("Alert email sent successfully!")
    except Exception as e:
        print("Failed to send email alert:", e)

# Alert function for non-responsive lights
def check_light_status(led_pin, light_name):
    if not GPIO.input(led_pin):
        alert_message = f"ALERT: {light_name} is not responding and did not turn ON as required."
        print(alert_message)
        send_email_alert(f"{light_name} Alert", alert_message)

# Main program loop
try:
    while True:
        light_state = read_light()
        distance = measure_distance()
        humidity = read_humidity()

        # Control LED 1 based on light sensor
        if light_state == 0:  # Light sensor detects darkness
            print("Darkness detected, turning on streetlights.")
            GPIO.output(led_pin_1, GPIO.HIGH)
            GPIO.output(led_pin_2, GPIO.HIGH)
            GPIO.output(led_pin_3, GPIO.HIGH)
            GPIO.output(led_pin_4, GPIO.HIGH)
        else:  # Light sensor detects sufficient light
            print("Sufficient light detected, turning off streetlights.")
            GPIO.output(led_pin_1, GPIO.LOW)
            GPIO.output(led_pin_2, GPIO.LOW)
            GPIO.output(led_pin_3, GPIO.LOW)
            GPIO.output(led_pin_4, GPIO.LOW)

        # Check and log sensor data
        print("Distance:", distance, "cm")
        if humidity is not None:
            print("Humidity:", humidity, "%")
        else:
            print("Failed to retrieve humidity data")

        # Add a small delay to prevent excessive resource usage
        time.sleep(2)

except KeyboardInterrupt:
    print("Program interrupted.")
finally:
    GPIO.cleanup()
    print("GPIO cleaned up.")
