/*
2017-04

Demonstrate how to use https://github.com/pmp-p/virtual-GPIO
for a clock, a freezeer or a dht11 display.

While the arduino is running embed_loop() it still fully responds to RPC by serial and soon I2C ( for esp micropython ).

*/

// Recommended 500000, other suitable options 250000 and 115200. use the same values in python lib.
//#define BAUDRATE 2000000
//#define BAUDRATE 1000000
//#define BAUDRATE  500000

#define BAUDRATE 115200

// str buffer com size , used by float2string, lcd line display, rftx rle seq and SPI
#define MAXLB 96

#define LCDCHARS 33

#define MAX_DEBOUNCE 2   // debounced digitalRead you intend to read
#define MAXUVAL 3       // how many computed values you loop store and return to master

#define FB_PAGE_SIZE 16

#define NUM_TXCOMPORTS 1

#define TIMERS 2

//the I2C address of of arduino, esp8266+micropython is always master
#define I2C_FOLLOWER 0x66

#define USE_COM 0

#define USE_SPI 0

#define USE_SERVO 0

// irremote, the pin is choosen python side.
#define USE_IR 0

#define USE_LCD 1
#define USE_LCD1602 1
#define USE_LCD1602_I2C 0x3F


#define USE_SSD1306 0

#define WD WDTO_4S

#define IRrr 0

#define IRrx2 0

// - VERY - BIG LIB watch your ... steps !,  AccSTEP number of steppers
#define USE_STEPPER 0
#define AccSTEP 0

// config done .

#include "VirtGPIO.h"
// =========================== begin your embedded routine here ======================

#define USE_dht 0

#define USE_ds18b20 0

#if USE_dht
    #define DHTPIN 11

    #include <DHT.h>

    #define DHTTYPE DHT11   // DHT 11
    //#define DHTTYPE DHT22   // DHT 22  (AM2302), AM2321
    //#define DHTTYPE DHT21   // DHT 21 (AM2301)

    DHT dht(DHTPIN, DHTTYPE);
#endif


#if USE_ds18b20
    #define ONE_WIRE_BUS 10

    #if USE_SSD1306
        #error 1wire not compatible with SPI LCD
    #endif

    #include <OneWire.h>
    #include <DallasTemperature.h>
    OneWire oneWire(ONE_WIRE_BUS);
    DallasTemperature ds18b20(&oneWire);

#endif

void embed_draw(){
    #if USE_SSD1306
          // graphic commands to redraw the complete screen should be placed here
        int steps = 16;
        int dx = 128/steps;
        int dy = 64/steps;
        int y = 0;
        for(int x=0; x<128; x+=dx) {
            u8g.drawLine(x, 0, 127, y);
            u8g.drawLine(127-x, 63, 0, 63-y);
           y+=dy;
        }
    #endif
};


#include <Time.h>

void embed_setup(void){

    // start RTC clock
    setTime(0);

    #if USE_dht
        dht.begin();
    #endif

    #if USE_ds18b20
        ds18b20.begin();
        ds18b20.requestTemperatures(); // Send the command to get temperature readings
        //execute somethingloop every  x mseconds
        tintv[0] = 5000;
        tslots[0] = 4900;
    #else
        tintv[0] = 1000;
        tslots[0] = 900;
    #endif


    #if USE_SSD1306
        u8g.setFont(u8g_font_profont12);
        u8g.setColorIndex(1);
    #else
        #if USE_LCD1602
            GotoXY(0,0);
            DISP.print("It's alive !");
        #endif
    #endif

/*
   #if USE_IR_STOCK
        IR.enableIRIn();
        IR_on = true;
   #endif
*/

}



void embed_loop(void){
    char f2s[6];
    char status[2] = {'A',0} ;
    static char blink[2] = { ':',0} ;

    #define ti 0

    if ( (tshots[ti]>=0) && ( tslots[ti] > tintv[ti]) ) {
        tslots[ti] -= tintv[ti];
        ClrScr();

        if (blink[0]==':'){
            blink[0]=' ';
        } else {
            blink[0]=':';
        }

        //select where display begin  actually  a page = a line on lcd1602, WriteLn call do page++ for you each call.
        setVisualPage(0);

        #if USE_ds18b20
            # a freezer with compressor relay control

            userdef[0] = ds18b20.getTempCByIndex(0);


            if (userdef[0]>-126){
                if (userdef[0]>-18) {
                    digitalWrite(8,1);
                    status[0] = 'M';
                } else {
                    digitalWrite(8,0);
                }
            } else {
                //ALARM !!
            }
            WriteLn( PSTR("%02i%s%02i T%s %s"), hour(),blink, minute(), ftos(f2s,userdef[0],1,2), status);

            ds18b20.requestTemperatures(); // Send the command to get temperature readings
        #else
            #or a clock

            WriteLn( PSTR("%02i%s%02i.%02i T%s %s"), hour(),blink, minute(),second(), ftos(f2s,userdef[0],1,2), status);
            if (i2c_char<0){
                Write( PSTR("I2C: %s"), IB );
                i2c_char = 0;
            }
            else
                Write( PSTR("%u[%i] %u %u") , debouncer[0],debounced( debouncer[0],false,false),analogRead(14),analogRead(15));
        #endif


        #if USE_dht
            char f2s1[6];

            float h = dht.readHumidity();

            // Read temperature as Celsius (the default)
            float t = dht.readTemperature();

            if (isnan(h) || isnan(t) ){ //|| isnan(f)) {
                // error
                userdef[1] = -127;
                userdef[2] = -127;
                Write(PSTR("DHT11 ERROR"));
            } else {
                userdef[1] = h;
                userdef[2] = t;
                Write(PSTR("O: %s H: %s%%"),ftos(f2s,t,1,2), ftos(f2s1,h,0,2) );
            }

        #endif

        // update the LCD if any
        blit();

    }

}



