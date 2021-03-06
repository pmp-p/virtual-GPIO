project on hold while exploring direct rpc mapping via c2ffi "over the wire"



virtual-GPIO [ WIP modded from official ]
============



___________
Micropython-ESP8266 Features :

testing:
  - socket access
  - websocket access
  
planned:
  - i2c
  
___________    
H3Droid Features :

testing:
  - socket access
  
planned:
  - websocket access
  - i2c
  - bidirectionnal .
    
___________    
Armbian Features :

testing:
  - all access types, bidirectionnal.
  - wiringX abstraction.

planned: 
  - arduino C interpreter.
  - coroutines / events.

____________________
Emscripten Features :

testing:
  - python console ( maybe brython too )

planned:
  - js editor for remote file on boards.
  - mcu 3D mockup with panda3d ( led / servo / motor )

__________________
Arduino Features :

testing:
  - non blocking loop, allowing embed_setup() , embed_loop() , embed_draw() to run while serving RPC
  - can use as a library , configured per-project with some #define before inclusion.
  - added: accelstepper , lcd16xx/lcd16xx_i2c, timers, debouncers
  
planned: 
  - i2c slave. ( currently adding :  at328 uno/nano i2c_slave handler <=> micropython esp8266 as master )



  
======= Original README follows =====

Arduino as a "GPIO" device attached to PC or MCU, which run python control script.

Give your *Pi precise counters, easy IR receiver, analog inputs.
Give your PC a virtual GPIO on a USB port. Add SPI, I2C, analog & digital pins, servo control, etc.

Supported:
  - GPIO digital in/out  D2-D13  A0-A5
  - PWM out  8bit - 6 pins
  - high performance PWM option, or as pulse generator 1Hz to 1MHz
  - analog Read  10bit  8 pins
  - SPI master, multiple choice for CE pin
  - pulseout 1-250 uSec [arduino coded]
  - pulsein   0-25 mSec [arduino coded, not native arduino version]
  - servo    pins3-10
  - ir remote rx
  - SMBus / I2C master
  - 2 software (arduino-polled) counters / quadEncoders
  - Hardware pin counter x 1 on d5
  - Twin INT0/INT1 counters on d2/d3
  - AVR raw register access
  - Auto-find for PC end serial port

Generally about 800 instructions/sec achievable on PC, depending on call type, and 200/sec on rPi.

"virtGPIO.py" is the PC end of "virtual-gpio", ie using arduino as a GPIO device on PC (python on linux).
This module uses USB serial to power and control the arduino.

The ARDUINO end is the sketch "VirtGPIO.ino".
Shields, attached modules etc are NOT generally coded at the arduino end. Such support is to be coded at the PC end.
(Exceptions:  infrared remote codes reader, and background stepper)

Atmega328 is assumed.

Main files:
  - /VirtGPIO/*
  - virtGPIO.py essential library at *Pi, µpython or PC.
  - collection of example python files demonstrating use of virtual GPIO.

Documentation on GPIO calls:  See http://virtgpio.blavery.com

  - Changes made V0.9 -> v0.9.5  :
  - Added serialConfig.py for port settings
  - Sonar removed from virtGPIO core, out to simple example script
  - SPI devices get individual control of mode
  - i2c - option to disable arduino's internal pullups
  - SPI.xfer2() out to 80 chars, and added unlimited SPI.writebytes()
  - Improved RPI syntax compatibility
  - Now Python 2.7 / Python 3.3 compatible

DISCLAIMER on the associated libraries (mcp23017, lcd16x2, nokia5110, nrf24, tft144) - these are a work in progress, and recently have been exercised more against virtual-GPIO than Raspberry Pi. There are sure to be various updates/corrections to those. The virtual-GPIO core library itself (v0.9.5) should be fairly intact.  BL 5 Nov 2014.

V0.9.5
November 2014
