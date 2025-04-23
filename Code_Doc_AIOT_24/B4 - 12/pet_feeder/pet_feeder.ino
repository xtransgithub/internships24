#include <Servo.h>

#define FEED_INTERVAL   1   

const byte servoPin = 9;      
const int waitingTime = FEED_INTERVAL;

Servo servo;

volatile unsigned long sec;
const unsigned long feedInterval = (unsigned long) FEED_INTERVAL * (unsigned long) 10;  



void feederClose() {
  servo.write(90); 
  delay(500); 
}


void feederOpen() {
  servo.write(0); 
  delay(1000); 
}


SIGNAL(TIMER0_COMPA_vect)
{
  if (millis() % 1000 == 0) { 
    sec++;  
    Serial.print("Second: ");
    Serial.print(sec);
    Serial.print(" of ");
    Serial.println(feedInterval);
  }
}

void setup() {
  Serial.begin(9600);
  OCR0A = 0xAF; 
  TIMSK0 |= _BV(OCIE0A);
  servo.attach(servoPin);
  Serial.println("System initialized");
}

void loop() {
  Serial.println("Waiting...");
  sec = 0;  
  while (feedInterval > sec);   
  Serial.println("Feeding the pet :)");
  tone(6,784,950); 
  delay(1000); 
  tone(6,660,950); 
  delay(1000); 
  tone(6,524,950); 
  delay(3000); 
  feederOpen(); 
  delay(150);
  feederClose();
}
