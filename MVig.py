import RPi.GPIO as GPIO
import time
import os
import random
from escpos import *

GPIO.setmode(GPIO.BCM)

p = printer.Usb(0x28e9,0x0289, in_ep=0x81, out_ep=0x03)

p.text("READY\n\n\n")

#PINS
#10,9,8,7,6
#1,2,3,4,5

#Display (1 to turn on)
#26 = left, pin10
#19 = right, pin5

#Segment (0 to turn on)
#5 = Top Right, pin6
#6 = Top Left, pin8
#7 = Dot, pin2
#12= Bot Right, pin4
#13= Top, pin7
#16= Bot Left, pin3
#20= Bot, pin1
#21= Mid, pin9

segments = (5,6,7,12,13,16,20,21)
displays = (26,19)

for segment in segments:
    GPIO.setup(segment, GPIO.OUT)
    GPIO.output(segment,1)

for display in displays:
    GPIO.setup(display, GPIO.OUT)
    GPIO.output(display,0)
    
GPIO.setup(4, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)


#(TR,TL,D,BR,T,BL,B,M)
num= [
    [0,0,1,0,0,0,0,1],
    [0,1,1,0,1,1,1,1],
    [0,1,1,1,0,0,0,0],
    [0,1,1,0,0,1,0,0],
    [0,0,1,0,1,1,1,0],
    [1,0,1,0,0,1,0,0],
    [1,0,1,0,0,0,0,0],
    [0,1,1,0,0,1,1,1],
    [0,0,1,0,0,0,0,0],
    [0,0,1,0,0,1,0,0]]

s1 = 18
s2 = 27
sw = 22

CW = 0
CCW = 1

counter = 0
direction = CW
s1_state = 0
s1_prev = 0

sw_press = False
sw_prev = GPIO.HIGH

GPIO.setup(s1,GPIO.IN)
GPIO.setup(s2,GPIO.IN)
GPIO.setup(sw,GPIO.IN, pull_up_down=GPIO.PUD_UP)

s1_prev = GPIO.input(s1)
path='/home/haplo/python/cards/'

def print_card(cmc):
    full_path = path + str(cmc) + '/converted_files/'
    try:
        image_path = full_path + random.choice(os.listdir(full_path))
        p.image(image_path)
        p.text("\n\n\n")
    except Exception as e:
        print("Something went wrong: ", e, "\n\n\n")

def button_push(gpio):
    
    #stop detection until finished
    GPIO.remove_event_detect(4)
    print_card(counter)
    time.sleep(1)
    GPIO.add_event_detect(4, GPIO.RISING, callback=button_push, bouncetime=300)
    
GPIO.add_event_detect(4, GPIO.RISING, callback=button_push, bouncetime=300)




try:
    while True:
        s1_state = GPIO.input(s1)
        if s1_state != s1_prev and s1_state == GPIO.HIGH:
            if GPIO.input(s2) == GPIO.HIGH:
                counter += 1
            else:
                counter -= 1
            
            if(counter < 0):
                counter = 0
            if(counter > 16):
                counter = 16
        s1_prev = s1_state
            
        remain = counter % 10
        for dig in range(0,8):
            GPIO.output(segments[dig],num[remain][dig])

        #Turn on ones digit
        GPIO.output(displays[1],1)
        time.sleep(0.001)
        GPIO.output(displays[1],0)
        
        #Turn on tens digit
        if counter>9:
            for dig in range(0,8):
                GPIO.output(segments[dig],num[1][dig])
                
            GPIO.output(displays[0],1)
            time.sleep(0.001)
            GPIO.output(displays[0],0)

finally:
    GPIO.cleanup()
