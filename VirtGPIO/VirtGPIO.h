// VirtGPIO.ino   V0.9.6

#ifndef __AVR_ATmega328P__
    #error This sketch expects an atmega 328 (Uno, Nano, Pro mini 328)
#endif

//#define _Version 96
#define XSTR(x) STR(x)
#define STR(x) #x


#ifndef NUM_TXCOMPORTS
    #define NUM_TXCOMPORTS 2
#endif

#ifndef BAUDRATE
    #define BAUDRATE 115200
#else
    #pragma message "BAUDRATE: " XSTR(BAUDRATE)
#endif

#ifndef I2C_FOLLOWER
    #define I2C_FOLLOWER 0
#else
    #pragma message "I2C Address: " XSTR(I2C_FOLLOWER)
#endif


#include "Arduino.h"


static char LB[MAXLB]; // for SPI too
static char IB[32] ; // for i2c
static float userdef[MAXUVAL];

static byte debouncer[MAX_DEBOUNCE];
static int debouncer_trig[MAX_DEBOUNCE];
static int debouncer_cnt[MAX_DEBOUNCE];
static long debouncer_millis[MAX_DEBOUNCE];


// This is the arduino end of virtual-gpio, using arduino as a GPIO device on PC or Raspberry Pi
// This sketch is designed to support specifically the atmega328 (eg Nano or Uno)
// If you use USB between PC and Arduino, be aware the USB/UART is required to work at high baudrate (500000 default).
// For me, FTDI types have worked flawlessly. CH340 has failed miserably. YMMV.

// Want to connect your Raspberry Pi via Rpi UART instead of USB?  Refer to notes at top of "virtGPIO.py"

// Want additionally to use arduino IDE on rPi, with sketch upload via rPi UART instead of USB cable?
// (Perhaps you use Pro-Mini arduino with no USB function?)
// Install "arduino" software on rPi using apt-get or synaptic.
// At rPi terminal enter:     ~$    "sudo ln /dev/ttyAMA0 /dev/ttyS1"
// Then Arduino IDE will recognise the UART serial port under alias of "/dev/ttyS1" (It can't handle AMA0)
// That is good for current session. To make the alias permanent, look here:
// <http://www.linuxcircle.com/2013/04/23/install-and-test-arduino-ide-with-raspberry-pi-and-gertboard/>
// You'll need to learn (a) to be patient while recompiling on RPi - it's slow
//                      (b) to become expert in releasing the arduino reset button EXACTLY at upload start time


// Libraries expected in default Arduino IDE installation:
#if USE_SPI
    #include <SPI.h>
#endif

// OPTIONAL library - this one should be installed conventionally in .../sketchbook/libraries/
//#include <MemoryFree.h>
// Optional, use at development, not included in production

// Custom and 3rd-party libraries. Note ALL the following are NOT in "...sketchbook/libraries/",
// rather they are in virtGPIO project space. That way, you don't need to install them in libraries folder,
// and in any case nearly all of them are specially tweaked for virtGPIO.

#include "Wire_vg.h"
#include "TimerOne_vg.h"

#if USE_STEPPER
    #if AccSTEP
        #include "AccelStepper_vg.h"
        AccelStepper stepper[AccSTEP];
    #else
        #include "Stepper_vg.h"
        Stepper stepper[2];

    #endif
#endif


#if TIMERS
    #include <elapsedMillis.h>
    elapsedMillis tslots[TIMERS];
    int tshots[TIMERS];
    uint16_t tintv[TIMERS];
#endif


#include "bgi.h"


#include "Serial0.h"

#if USE_COM

    #include "AltSoftSerial_vg.h"
    // Create various device objects. They don't really do anything yet:
    BBSerial Serial1[NUM_TXCOMPORTS];   //  (we will waste [0])
    AltSoftSerial Serial2;
#endif


#if USE_IR
    #include "IRremote_vg.h"
    IRrecv  IR(USE_IR);   // dummy pin# for original constructor
    decode_results IRresult;
#endif


#if USE_SERVO
    #include <Servo.h>
    Servo servos[USE_SERVO+2];   // for pins 2 - 11 - we will keep those matched. Bottom 2 wasted
#endif



volatile unsigned int d2_pulses=0, d3_pulses=0; // counters for INTcounter on 2 or 3
int quadpin[2];   // the pin #s (if existing) for quad pins of QuadEncoder (ie INTcounter)

bool SPI_on = false;
bool IR_on = false;
bool I2C_on = false;
unsigned int flags = 1;  // b0 is resetFlag.  16 bit flags to log pin collisions etc.
long int IRvalue = 0L;   // one value IR read buffer

int i2c_char=0;

enum {
    F_reset=0,
    F_spi,
    F_svo,
    F_ir,
    F_i2c,
    F_intctr,
    F_pwm,
    F_stepr,
    F_actled,
    F_nospi,
    F_TxCom,
    F_RxCom,
    F_badchar=15
};

// bits in this flag register can be fetched to PC. logs failures to assign pins to devices.

// Some shortcut macros used later:
#define SERIALWRITE2(v)        {Serial.write(v & 0xff);Serial.write((v >> 8)&0xff);}
#define SERIALWRITE3(v)        {Serial.write(v & 0xff);Serial.write((v >> 8)&0xff);Serial.write((v>>16)&0xff);}
#define LOGFAIL(x)             bitSet(flags, x)

#ifndef cbi
    #define cbi(sfr, bit) (_SFR_BYTE(sfr) &= ~_BV(bit))
#endif

#ifndef sbi
    #define sbi(sfr, bit) (_SFR_BYTE(sfr) |= _BV(bit))
#endif

//------------------------------------------------------------------------------------

// Reserved Pins control:

long GPpins = 0b00011111111111111111100 ;
// pins d0(lsb) - d13 - a0 - a5(bit19) bit pattern of "good" pins, ie still available for general I/O
// pins d0,d1 (tx & rx) are OFF, also everything above A5.  Remaining pins are "good"


void reservePin(int pin) {
    GPpins &= ( ~ (1L<<(pin&0x1f)));    // use _BV?
    // no longer available as general I/O
}

void releasePin(int pin) {
    GPpins |= ( 1L<<(pin&0x1f));
}

bool pinGood(int pin) {
    return (GPpins & (1L<<(pin&0x1f))) > 0L ;
    // is this pin still available for general I/O?
}


//------------------------------------------------------------------------------------
int debounced(byte pin,bool serwrite=false,bool reset=true){
    byte bidx;

    for (bidx=0;bidx < MAX_DEBOUNCE;bidx++){
        if (debouncer[bidx]==pin){
            //nothing pressed
            if (debouncer_cnt[bidx]>0){
                if (serwrite)
                    Serial.write(0);
                return 0;
            }
            //some was

            //restart monitoring reset counter
            if (reset){
                debouncer_millis[bidx] = millis();
                debouncer_cnt[bidx] = abs(debouncer_trig[bidx]);
            }

            if (serwrite)
                Serial.write(1);
            return 1;
        }
    }
    //no such pin
    if (serwrite)
        Serial.write(100+pin);
    return -pin;
}

void receiveData(int byteCount){
    byte pos=0;

    while(Wire.available()) {
        i2c_char = Wire.read();
        IB[pos++] = (byte)i2c_char;
    }
    IB[pos]=0;
    i2c_char = -1;
}

// callback for sending data
void sendData(){
    Wire.write(i2c_char);
}




void ACK(int code=0){
    Serial.write( (byte)( 128 + code ) );
}

long readVcc() {
  long result;
  // Read 1.1V reference against AVcc
  ADMUX = _BV(REFS0) | _BV(MUX3) | _BV(MUX2) | _BV(MUX1);
  delay(2); // Wait for Vref to settle
  ADCSRA |= _BV(ADSC); // Convert
  while (bit_is_set(ADCSRA,ADSC))
    ;
  result = ADCL;
  result |= ADCH<<8;
  result = 1126400L / result; // Back-calculate AVcc in mV
  ADMUX = (DEFAULT << 6);     // Aref back to default for every future read
  return result;
}

long int pulse_In(int pin, int level, unsigned long timeout1, unsigned long timeout2)
{
  unsigned long t2, t1 = micros();
  if (digitalRead(pin) == level)
    return 0xFFFFFFFd;     // fail code: not idle, or missed the start
  while (digitalRead(pin) != level)
    if ((micros()-t1) > timeout1)
      return 0xFFFFFFFE;    // fail code . Failed to start on time
  t2=micros();
  while (digitalRead(pin) == level)
    if ((micros()-t2) > timeout2)
      return 0xFFFFFFFA;    // fail code : overlong pulse - Failed to finish on time
  return  (micros()-t2);
}


int serGetchar ()
{
  // nonblocking
  long tim0 = micros();
  int x ;
  while (((x = Serial.read ()) == -1) && ((micros()-tim0) < 100L ));
  return x ;
}

//------------------------------------------------------------------------------------

// interrupt handlers for INT0 and INT1:
void countD2Pulses() {
    char pind = PIND;  // read both pin conditions
    char pinlevel = (pind & _BV(2)) > 0;
    char qlevel = pinlevel;   // default for non-quad
    if (quadpin[0] >0)
        qlevel = (pind & _BV(quadpin[0])) > 0;
    d2_pulses = d2_pulses + ((pinlevel == qlevel) ? 1 : (-1));
}

void countD3Pulses() {
    char pind = PIND;
    char pinlevel = (pind & _BV(3)) > 0;
    char qlevel = pinlevel;   // default for non-quad
    if (quadpin[1] >0)
        qlevel = (pind & _BV(quadpin[1])) > 0;
    d3_pulses = d3_pulses + ((pinlevel == qlevel) ? 1 : (-1));
}


void (*softReset)() = 0;
// "dirty reset" - peripherals & registers not reset.

// objects created by now: spi, wire, IRrecv + decode_results struct, encoders[], servos[], COM ports,
// but no "activity" or code for those yet.


//------------------------------------------------------------------------------------
void embed_setup(void);
void embed_loop(void);
void embed_draw(void);


void setup(void)
{
    byte k;
    for(k=2; k<=19; k++)
        pinMode(k, INPUT);

    Serial.begin(BAUDRATE);

    for (int k=0;k< MAXUVAL;k++){
        userdef[k]=0;
    }

    for (int k=0;k< MAX_DEBOUNCE;k++){
        debouncer[k]=0;
    }

#if I2C_FOLLOWER
    // initialize i2c as ****
    Wire.begin(I2C_FOLLOWER);

    // define callbacks for i2c communication
    Wire.onReceive(receiveData);
    Wire.onRequest(sendData);
#endif


#if USE_LCD
    lcd_setup();

#endif


#if TIMERS
    for (int i=0; i<TIMERS; i++){
        tshots[i] = 0;
        tslots[i] = 0;
    }
    tintv[TIMERS-1]=1000;
#endif


    pinMode(LED_BUILTIN, OUTPUT);

    quadpin[0]=0;
    quadpin[1]=0;

    embed_setup();
}




void loop ()
{

#if USE_SPI
    static int SPI_modes[4] = { SPI_MODE0, SPI_MODE1, SPI_MODE2, SPI_MODE3 };
    unsigned int k, bufIndex, port; //spi
    unsigned char d1, d2;
#endif

#if USE_STEPPER
    unsigned int speed, id, SPR;
    int  steps;
#endif

    unsigned int pin, mode; //, pin2, p[7];
    unsigned int aVal, dVal, ln, icount, registAddr, quad;
    long int usec;

    unsigned char cmd, c;
    unsigned long timeo1, timeo2;
    //static unsigned long tim;
    static unsigned int idleCounter = 0;

    //debouncing digitalread(pin)
    usec = millis();
    for (byte bidx=0;bidx<MAX_DEBOUNCE;bidx++){
        //pin defined but not yet triggered
        if ( (debouncer[bidx]>0) and (debouncer_cnt[bidx]>0) ){
            if ( (debouncer_millis[bidx]>=0) and (debouncer_millis[bidx]!=usec) ){
                bool state;
                state = digitalRead( debouncer[bidx] );
                if ( debouncer_trig[bidx] > 0 )
                    state = !state;

                if (state){
                    //assume input was high meanwhile so speedup countdown a bit if busy
                    debouncer_cnt[bidx] -= ( usec-debouncer_millis[bidx] );
                } else {
                    //was noise, reset the counter !
                    debouncer_cnt[bidx] = debouncer_trig[bidx];
                }
                debouncer_millis[bidx]=usec;
            }
        }

    }

    #if TIMERS
        //heatbeat
        int ti = TIMERS-1;
        if ( (tshots[ti]>=0) && ( tslots[ti] > tintv[ti]) ) {
            tslots[ti] -= tintv[ti];
            if (!SPI_on){
                int ledPin = digitalRead(LED_BUILTIN);
                digitalWrite( LED_BUILTIN, !ledPin );
            }
        }
    #endif


    #if USE_STEPPER
        // every pass, if Steppers are installed, service them:

        #if AccSTEP
        for (id=0; id<AccSTEP; id++)
            if (stepper[id]._interface)
                stepper[id].run();
        #else
            for (id=0; id<=sizeof(stepper); id++)
                stepper[id].run();
        #endif
    #endif

    #if USE_IR
        // Every pass, if IR chr came in (under interrupt!), stow it, & resume looking.
        // No multi-chr buffer.  A new code overwrites earlier one if not retrieved by user.
        if (IR_on)
            if(IR.decode(&IRresult)) {
                if(IRresult.value != 0xFFFFFFFF)   // "fast repeat chr" code  ignore
                    IRvalue = IRresult.value;
            IR.resume();
        }
    #endif


    if (idleCounter>10)   // are we looking fairly "idle"?
        printf_run();  // transmit 1 buffered character to Serial0, if available

    embed_loop();

    if (Serial.available () > 0) {

        // serGetcharB was blocking
        cmd = serGetchar();
        idleCounter = 0;

        switch (cmd) {

    #if USE_SPI
            case 'S':
                // SPI open/init
                pin = serGetchar() & 0x1f;    //    CE pin
                //mode = SPI_modes[serGetchar() & 3];
                if (!pinGood(pin))
                {
                    LOGFAIL(F_spi);
                    break;   // CE pin not free?   (& this inhibits a 2nd "open" for that CE# too)
                }

                if ((!SPI_on) && (!(pinGood(MISO) && pinGood(MOSI)) ))
                {
                    LOGFAIL(F_spi);
                    break;
                }

                /*
                if ((!SPI_on) && !(pinGood(SCK) ) )   // SCK is pin13
                {

                    if(activityLED != SCK)
                    {
                        // ActivityLed wasn't the reason
                        LOGFAIL(F_spi);
                        break;
                    }
                    // Ah, the reason pin13 is reserved is that it is activity LED. Kick it out!
                    activityLED = 0;

                }*/
                if (!SPI_on){
                    digitalWrite(13,0); // turn 13 off
                    pinMode(13, INPUT);   // then let SPI system sort 13 out.
                }

                pinMode(pin, OUTPUT);
                digitalWrite(pin, HIGH);
                reservePin(pin);

                // first "open"?
                if(!SPI_on)
                {
                    SPI.begin();   // start the SPI engine
                    SPI.setBitOrder(MSBFIRST);
                    SPI.setDataMode(mode);
                    SPI.setClockDivider(SPI_CLOCK_DIV4);
                    reservePin(SCK);  // 13
                    reservePin(MOSI); // 11
                    reservePin(MISO); // 12
                    delay(1);
                }
                SPI_on = true;
                break;

            case 'X':
                // SPI transfer block. CSN/CEx asserted down around the block of transfers
                //  timings: 100 uSec @ 1 char,   1700 uSec @ 32 char
                pin = serGetchar() & 0x1f;
                //  actual pin# for CE arrives here  (= 10-7)
                mode = SPI_modes[serGetchar() & 3];
                ln = serGetchar() & 0x7f;
                for (k=0; k<ln; k++)
                    LB[k] = serGetchar();
                if (!SPI_on)
                {
                    LOGFAIL(F_nospi);
                    break;    // yeah! the caller is going to timeout waiting!! Someone will tweak!
                }
                // This function buffers all the incoming Serial chars, then does exchange with SPI
                SPI.setDataMode(mode);
                digitalWrite(pin, LOW);
                for (bufIndex=0; bufIndex<ln; bufIndex++)
                    Serial.write(SPI.transfer(LB[bufIndex]));
                // exact reply from SPI - send it straight out
                digitalWrite(pin, HIGH);
                break;


            case 'x':
                // SPI transfer block OUT ONLY. CSN/CEx asserted down around the block of transfers
                // Further, the block can be marked "multi" and then CE remains asserted waiting for next portion.
                pin = serGetchar() & 0x1f;

                //  actual pin# for CE arrives here  (= 10-7)
                mode = serGetchar();
                c = mode >> 4;   // "multi: to be continued later" flag
                ln = serGetchar() & 0x3f;  // 63 max

                if (!SPI_on) {
                    LOGFAIL(F_nospi);
                    Serial.write(1);
                    break;
                }

                mode = SPI_modes[mode & 3];
                SPI.setDataMode(mode);
                digitalWrite(pin, LOW);

                // This function does not buffer incoming. Sent to SPI as fast as received from Serial
                for (k=0; k<ln; k++)
                    SPI.transfer(serGetchar());

                if (!c)   // Multi?  are we going to get more for this transmission?
                    digitalWrite(pin, HIGH);  // not continuing. de-assert CE
                Serial.write(1);
                break;

            case 'g':
                // SPI FILL write. Repetitive send of one or 2 bytes to SPI
                pin = serGetchar() & 0x1f;
                mode = serGetchar();
                icount = serGetchar();
                icount += 256*serGetchar();
                d1 = serGetchar();
                d2 = serGetchar();

                if (!SPI_on)
                {
                    LOGFAIL(F_nospi);
                    Serial.write(1);
                    break;
                }

                mode = SPI_modes[mode & 3];
                SPI.setDataMode(mode);
                digitalWrite(pin, LOW);

                for (k=0; k<icount; k++)
                {
                    SPI.transfer(d2);
                    SPI.transfer(d1);
                }

                digitalWrite(pin, HIGH);
                Serial.write(1);
                break;

    #endif

            case 's':
                // set digital pin mode to INPUT/OUTPUT
                pin = serGetchar () & 0x1f;
                mode = serGetchar() & 0x03;
                if (pinGood(pin))
                    pinMode (pin, mode) ;
                break ;

            case 'w':
                // digital write  hi lo
                pin = serGetchar () &0x1f ;
                mode = serGetchar() & 0x0003;
                if (pinGood(pin))
                    digitalWrite (pin, mode) ;
                Serial.write(1);  // just for sync
                break ;

            case 'U':
                // Upwards strobe pulse on digital pin
                pin = serGetchar () &0x1f ;
                mode = serGetchar() & 1;   // 0 or 1: HI or LO pulse?
                ln = serGetchar() & 0x00ff;
                if (pinGood(pin))
                {
                    digitalWrite (pin, mode) ;
                    delayMicroseconds(ln);
                    digitalWrite (pin, 1-mode) ;
                }
                break ;

            case 'I':
                // pulseIn   - custom version, not arduino native
                pin = serGetchar() & 0x0f;
                mode = serGetchar() & 1;
                timeo1 = serGetchar() * 20;   // 1-255 = 20uSec - 5mSec
                timeo2 = serGetchar() * 100;  // 1-255 = 100uSec - 25mSec
                if (pinGood(pin))
                    dVal = (int)pulse_In(pin, mode, timeo1, timeo2);
                else
                    dVal = 0xFFE3;  // = error
                SERIALWRITE2(dVal);   // returning only 16 bit. (to 65 mSec)
                break ;

            case 'n':
                // Read all the Flags register
                SERIALWRITE2(flags);
                break;

            case 'r':
                // digital read
                pin = serGetchar () & 0x1f ;
                if (!pinGood(pin))
                    dVal = 0x00fe;  // = error
                else
                    dVal = digitalRead (pin) ;
                Serial.write (dVal ) ;
                break ;

            case 'a':
                // analog read
                // expects pins A0 - A7 ie 14 - 21 (not 0-7)
                pin = serGetchar () & 0x1f ;
                if ((pinGood(pin) && pin>= 14) || pin==20 || pin==21)  // A6 A7 always useable
                    aVal = analogRead (pin) ;
                else
                    aVal = 0xFFEE; // = error
                SERIALWRITE2(aVal);
                break ;


            case 'A':
                // 8 x analog read ALL
                for (pin=14; pin<=21; pin++)
                {
                    SERIALWRITE2(analogRead (pin));
                }
                break ;

            case 'j':
                unsigned int slen;
                uint16_t k;
                slen = serGetchar();
                #if 0
                    GotoXY(0,1);

                    if (slen>=MAXLB){
                        DISP.print("error");
                        slen =16;
                    } else
                        DISP.print( slen );

                    int c;
                    GotoXY(3,1);

                    for (k=0; k<slen ; k++){
                        c = serGetchar();
                        if (c>=0)
                            LB[k] = c; // 64; // c;
                        else
                            LB[k] = 63; // '?'
                    }
                    LB[slen ]=0;
                    GotoXY(0,1);
                    DISP.print( LB) ;
                #else
                    if (slen>=MAXLB)
                        slen =MAXLB-1;
                    for (k=0; k<slen ; k++)
                        LB[k] = (byte)serGetchar();
                    LB[slen]=0;
                #endif

                ACK( (int)slen);
                break;

            case 'J':
                Serial.write( strlen(LB) );
                //ACK( (int)LB);
                Serial.write( LB );
                break;

            case 0xf1:
                mode = serGetchar();

                #if USE_SSD1306
                u8g.firstPage();
                do {
                #endif
                    //echo line 1/2
                    if (mode<2){
                        #if USE_LCD1602
                            GotoXY(0,mode);
                            DISP.print( LB );
                        #endif
                        #if USE_SSD1306
                            u8g.drawStr(0,12, LB);
                        #endif
                    }

                #if USE_SSD1306
                } while(u8g.nextPage());
                #endif
                ACK();
                break;

            case 'i':
                // Kill the "has been reset" flag
                bitClear(flags, F_reset);            // resetflag
                break;

            case 'p':
                // PWM write to digital pin - pin 2 up to pin 11
                pin  = serGetchar () & 0x0f ;
                dVal = serGetchar () ;
                if (pin > 11 || !pinGood(pin) || pin==4 || pin==7 || pin==8)
                    break;
                analogWrite (pin, dVal& 0xff) ;
                break ;

#if USE_SERVO
            case 'V':
                // attach & run servo
                pin = serGetchar() & 0x0f;
                dVal = serGetchar();

                if (!servos[pin].attached()){
                    if (!pinGood(pin))
                    {
                        LOGFAIL(F_svo);
                        break;
                    }
                    servos[pin].attach(pin);
                    reservePin(pin);
                }

                servos[pin].write(dVal);
                break;


            case 'v':
                // stop a servo
                pin = serGetchar() & 0xff;
                if (pin>128){
                    pin -= 128;
                }

                if (servos[pin].attached())
                {
                    servos[pin].detach();
                    releasePin(pin);
                }
                break;

#endif

#if USE_IR
/*
            case 'G':
                pin = serGetchar();
                if (IR_on){
                    ACK(pin);
                    break;
                }
                IR.blink13(false);
                ACK(pin);
                break;
*/
            case 'F':
                // infrared start
                pin = serGetchar();

                if (IR_on){
                    ACK(pin);
                    break;
                }

                IR.blink13(false);  // we do not use blink

                if(!pinGood(pin)) {
                    LOGFAIL(F_ir);
                    break;
                }

                IR.enableIRIn(pin);   // here is where we over-ride the preset pin#
                IR_on = true;
                reservePin(pin);
                ACK(pin);
                break;

            case 'f':
                // infrared rx
                SERIALWRITE2(IRvalue >> 16);
                SERIALWRITE2(IRvalue & 0x0000FFFF);
                IRvalue = 0L;
                break;
#endif

            case '=':
                // sync / ping
                Serial.write('=');
                break;

/*
            case 't':
                // compilation date
                Serial.print(((float)_Version)/100.0);
                Serial.print(" VirtGPIO ");
                Serial.print( __DATE__);
                break;

            case 'T':
                // version #
                Serial.write (_Version);
                break;
*/
            case '+':
                // Read Arduino Supply volts VCC
                SERIALWRITE2((int)readVcc());
                break;

            case 'q':
                // Read set of reserved pins
                SERIALWRITE2((int)(GPpins & 0xffff));
                SERIALWRITE2((int)(GPpins >>16));
                break;

            case '!':
                // i2c begin()
                mode = serGetchar() & 1;  // = enable pullups?
                if (I2C_on)
                  break;  // Not illegal to make a duplicate start to I2C system.

                if (I2C_on || !pinGood(18) || !pinGood(19))
                // A4 & A5 are i2c pins
                {
                    LOGFAIL(F_i2c);
                    break;
                }
                Wire.begin();
                if (mode)
                {
                    // modified TWI library code no longer enables pullups by default (special mod for virtual GPIO)
                    // here is where we now get the option, pullups or not.
                    // this new option is for 3.3V i2c devices on 5V arduino i2c pins, where 3.3v device has own pullups
                    // we are now hoping that the 3.3v logic can operate 5v arduino i2c input - slightly out of spec!
                    sbi(PORTC, 4);   // enable internal pullups
                    sbi(PORTC, 5);
                }
                I2C_on = true;

                reservePin(18);
                reservePin(19);
                break;


            case 'W':
                // Write byte(s) to i2c
                // simply not going to work if i2c failed to start
                icount = serGetchar();
                Wire.beginTransmission(serGetchar());  // port address
                for (k=0; k<icount; k++)
                    Wire.write(serGetchar());
                Serial.write(1); // dummy for syncing only
                Wire.endTransmission();
                break;


            case 'c':
                // Read byte(s) from i2c
                // simply not going to work if i2c failed to start
                icount = serGetchar();
                Wire.requestFrom(serGetchar(), icount);
                for (k=0; k<icount; k++) {
                    while(!Wire.available())    /////////////////// timeout logic not ok
                        delayMicroseconds(5);
                    Serial.write(Wire.read());
                }
                break;


            case '?':
                // find I2C addresses
                // "scanner" code
                if(! I2C_on) {
                    Serial.write(0xfe); // = error
                    break;
                }
                for(k = 1; k < 127; k++ ) {
                    Wire.beginTransmission((byte)k);
                    if (Wire.endTransmission() ==0)
                        Serial.write (k);
                }
                break;


            case '@':
                // AVR register read16
                registAddr = serGetchar();
                SERIALWRITE2(  *(volatile uint16_t *) registAddr );
                break;

            case '#':
                // AVR register read8
                registAddr = serGetchar();
                Serial.write(  *(volatile uint8_t *) registAddr );
                break;

            case '*':
                // AVR register write8
                registAddr = serGetchar();
                dVal = serGetchar();
                *(volatile uint8_t *) registAddr = dVal;
                break;

            case '&':
                // AVR register write16
                registAddr = serGetchar();
                dVal = serGetchar();
                dVal = (dVal<<8) + serGetchar();   // check endian ?!!!
                *(volatile uint16_t *) registAddr = dVal;
                break;

            case '[':
                // AVR register8 bitset
                registAddr = serGetchar();
                k = serGetchar() & 0x07;  // the bit
                c = *(volatile uint8_t *) registAddr;
                *(volatile uint8_t *) registAddr = ( c | _BV(k));
                break;


            case ']':
                // AVR register8 bitclear
                registAddr = serGetchar();
                k = serGetchar() & 0x07;
                c = *(volatile uint8_t *) registAddr;
                *(volatile uint8_t *) registAddr = ( c & (~ _BV(k)));
                break;


            case '2':

                // d2/d3 pulses by int0 / int1 - INIT
                pin = serGetchar() & 3;    // 2 or 3
                mode = serGetchar() & 7;   //  00 low (bad!), 01 change, 10 falling, 11 rising,  101 quad_changing

                // bad pin#, bad LOW mode, pins busy
                if (pin<2 || pin>3 || !pinGood(pin) || (mode&3) ==0) {
                    LOGFAIL(F_intctr);
                    break;
                }

                quad = mode >>2;    // test isquad bit

                // quad pin busy?
                if (quad && !pinGood(pin+2))   {
                    LOGFAIL(F_intctr);
                    break;
                }

                mode &= 3;   // only 01  10  11 now
                if(quad) {
                    //reservePin(pin+2);  // NO don't reserve
                    quadpin[pin-2] = pin+2;
                }

                //reservePin(pin);
                attachInterrupt(pin&1, (pin&1)? countD3Pulses : countD2Pulses, mode);
                break;

            case ',':
                // int0 and int1 counter reads (together), Optional clear
                mode = serGetchar() & 1;
                noInterrupts();
                SERIALWRITE2(d2_pulses);
                SERIALWRITE2(d3_pulses);  // return both
                if (mode)   // clear? true/false
                {
                    d2_pulses = 0;
                    d3_pulses = 0;
                }
                interrupts();
                break;


            case 0x81:
                // init hi def pwm
                Timer1.initialize();
                break;

            case 0x82:
                // set pwm period
                usec = serGetchar();
                usec += (serGetchar()<<8);
                usec += (((long int)serGetchar())<<16);
                Timer1.setPeriod(usec);
                break;

            case 0x83:
                // init pwm pin
                pin = serGetchar() & 0x1F;
                mode = serGetchar();
                mode += (serGetchar()<<8);
                if (pinGood(pin)) {
                    Timer1.pwm(pin, mode);
                    reservePin(pin);
                }
                else
                    LOGFAIL(F_pwm);
                break;

            case 0x84:
                // change pwm duty
                pin = serGetchar() & 0x1F;
                mode = serGetchar();
                mode += (serGetchar()<<8);
                Timer1.setPwmDuty(pin, mode);
                break;

            case 0x85:
                // release pwm pin
                pin = serGetchar() & 0x1F;
                Timer1.disablePwm(pin);
                releasePin(pin);
                break;

            case 0x86:
                mode = serGetchar() & 1;
                if (mode)
                    Timer1.restart();
                else
                    Timer1.stop();
                break;

#if USE_STEPPER

        case 0xb1:
            // stepper init
            id = serGetchar() & 1;
            mode = serGetchar()  &6;  // wires 2 or 4
            pin = serGetchar() & 0x1f;    // first of 2 or 4 pins
            SPR = serGetchar();
            SPR += (serGetchar()<<8);    // Steps/revolution

    /*
            // 2 pin
            if (!pinGood(pin) || !pinGood(pin+1)) {
                LOGFAIL(F_stepr);
                break;
            }

            // 4 pin
            if ((!pinGood(pin+2) || !pinGood(pin+3)) &&  (mode ==4)) {
                LOGFAIL(F_stepr);
                break;
            }
    */
            reservePin(pin);
            reservePin(pin+1);

            if (mode == 4) {
                #if AccSTEP

                if (!stepper[id]._interface){
                    stepper[id].__init__( AccelStepper::HALF4WIRE ,  pin, pin+2, pin+1, pin+3, true );
                    stepper[id].setMaxSpeed(500.0);
                    stepper[id].setAcceleration(100.0);
                    stepper[id].setSpeed(200);
                }

                #else
                    stepper[id].init((int)SPR, pin, pin+1, pin+2, pin+3);
                #endif
                reservePin(pin+2);
                reservePin(pin+3);
            } else {
                #if AccSTEP
                    stepper[id].__init__(  AccelStepper::HALF4WIRE ,  pin, pin+1, 0, 0, true );
                    stepper[id].setMaxSpeed(1000.0);
                    stepper[id].setAcceleration(100.0);
                    stepper[id].setSpeed(200);

                #else
                    stepper[id].init((int)SPR, pin, pin+1);
                #endif
            }
            break;


        case 0xb2:
            // set stepper speed (in RPM)   positive only
            id = serGetchar()&1;
            speed = serGetchar();
            speed += (serGetchar()<<8);    // int16

            #if AccSTEP
                if (speed==0){
                    stepper[id].disableOutputs();
                } else
                    stepper[id].setMaxSpeed( (float)speed );

            #else
              if (speed==0){
                digitalWrite(4,0);
                digitalWrite(5,0);
                digitalWrite(6,0);
                digitalWrite(7,0);
              } else
                stepper[id].setSpeed((long)speed);
            #endif

            break;

        case 0xb3:
            // stepper move
            id = serGetchar()&1;
            steps = serGetchar();
            steps += (serGetchar()<<8);    // + or -  int16
            #if AccSTEP
                stepper[id].moveTo(steps);
            #else
                stepper[id].step(steps);
            #endif

          break;

        case 0xb4:
            // get steps left
            id = serGetchar()&1;
            #if AccSTEP
                SERIALWRITE2( stepper[id].distanceToGo() );
            #else
                SERIALWRITE2(stepper[id].stepsLeft());
            #endif
            break;

#endif


#if USE_COM
        case 0xc0:
            // set up COM port
            port = serGetchar() & 0x0f;
            pin = serGetchar() & 0x1f;
            if (port >= NUM_TXCOMPORTS)
                break;

            if (!pinGood(pin)) {
                // uh oh that pin currently lists as "reserved"
                for (k=0; k<=NUM_TXCOMPORTS; k++)   // scan all serial ports
                    if (pin == (k ? Serial1[k].txpin : Serial0.txpin)) // that pin already used for serial??
                        break;
                // ie we found no pin match among the serial ports?
                if (k >= NUM_TXCOMPORTS) {
                    LOGFAIL(F_TxCom);
                    break;  // fail to install new port: reserved pin
                }
                // that pin is used for COM.  Re-use is OK, so continue on ...
            }

            if (port ==0) {
                Serial0.begin(pin);
                // this MAY rewrite the pin# for Serial0.  Legal.  Bad luck for any developer diags.
                Serial0Printf_begin();

            } else
                Serial1[port].begin(pin);

            reservePin(pin);
            break;

        case 0xc1:
            // write to TxCOM port
            port = serGetchar() & 0x0f;
            ln = serGetchar();
            // note, if port not set up, the write function of port will return without action
            for (k=0; k<ln; k++) {
                if (port ==0)
                    Serial0BufWrite(serGetchar());
                else
                    Serial1[port].write(serGetchar());
            }
            Serial.write(ln);
            break;

        case 0xd0:
            // Initialise RXSerial port
            mode = serGetchar();
            if (pinGood(8)) {
                Serial2.begin(2400);
                reservePin(8);
            } else
                LOGFAIL(F_RxCom);
            break;

        case 0xd1:
            // RxSerial   chrs available?
            Serial.write( Serial2.available());
            break;

        case 0xd2:
            // return characters from RxSerial
            icount = serGetchar();
            for (k=0; k<= icount; k++)
                Serial.write(Serial2.read() & 0xff);
            // NOTE: requesting more than in buffer will result in FF characters to fill the quota!
            break;
/*
        case '^':
            // trace on
            tracing = 1;
            //traceCtr = 0;
            break;

        case '<':
            // trace off
            tracing = 0;
            Serial0BufPrintf("OK %d\n", 44);
            break;

        case '>':
            // trace off & dump
            tracing = 0;
            if(Serial0.txpin == 0)
                break;   // Serial0 is not initialised. abort.

            // whole trace buffer is now sent to Serial0's buffer for transmission/display:
            Serial0.print("< ");
            for (int k=0; k<traceCtr; k++) {
                Serial0.print(traceBuf[k], HEX);
                Serial0.print(" ");
            }
            Serial0.print('>');
            traceCtr = 0;
            break;
*/
#endif
        case 'b':
            pin = serGetchar();

            //passive read
            if (pin>=128){

                pin -=128;
                debounced( pin , true, false);
                break;
            }
            //write to serial , reset reading
            debounced( pin , true, true);
            break;


        case 'B':
            int pmode;

            pin = serGetchar();  // digital read pin
            pmode = 128-serGetchar(); // if debouncing time  >0 will use pullup
            byte bidx;
            for (bidx=0;bidx < MAX_DEBOUNCE;bidx++){
                if (debouncer[bidx]==pin)
                    break;

                if (debouncer[bidx]==0){
                    pinMode(pin, INPUT);
                    if (pmode>0)
                        digitalWrite(pin, HIGH);

                    debouncer[bidx]=pin;
                    debouncer_trig[bidx] = pmode;
                    debouncer_millis[bidx] = millis();
                    debouncer_cnt[bidx]= abs(pmode);
                    break;
                }
            }
            break;


        // tx anything
        case 0xf2:
            pin = serGetchar();
            mode = serGetchar();

            //som*y rle encoded 640 us pulses
            if (mode==3){
                //som*y pulse width
                int pl = 640;

                //repeat msg 4 because crappy FS1000a rf sender
                for (int repeat=0;repeat<4;repeat++){
                    // wake up
                    digitalWrite(pin,1);
                    delayMicroseconds(10750);

                    digitalWrite(pin,0);
                    delayMicroseconds(17750);

                    // rle compressed header/frame/footer
                    byte current = 1;
                    for (uint8_t rle=0; rle<strlen(LB);rle+=2) {
                        int pulsegap =  ( (byte)LB[rle] - 64 );
                        int repeats =   ( (byte)LB[rle+1] - 64 );

                        for (uint8_t i=0;i<repeats;i++) {
                            digitalWrite(pin,current);
                            delayMicroseconds(  pl * pulsegap );

                            //invert level
                            if (current>0){
                                current=0 ;
                            } else {
                                current = 1;
                            }
                    }
                    }
                }
            }
            break;


        case 0xfd:
            for (int ud=0;ud<MAXUVAL;ud++){
                SERIALWRITE2( (uint16_t)(100*userdef[ud]) );
            }
            break;

        case '0':
            // Arduino reset
            mode = serGetchar();
            if (mode == '-')
            softReset();
            break;

        default:
                // unknown/unexpected cmd codes are discarded
                LOGFAIL(F_badchar);   // can be detected at PC by fetching flags register
                break;

    }
    // End of CMD processing
    } else {
        // this loop was idle, no command was processed
        idleCounter ++;
    }

}

// End of loop()
//------------------------------------------------------------------------------------

//------------------------------------------------------------------------------------

/*
 *  * Copyright (c) 2014 Brian Lavery <vgpio@blavery.com>   http://virtgpio.blavery.com
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 * THE SOFTWARE.
 *
 * Library functions used alongside this file retain (as always) the copywrite
 * or free software provisions of their respective authors.
 *
*/
