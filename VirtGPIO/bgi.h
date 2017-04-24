#include "floatToString.h"


#if USE_LCD
    #define MAXCHARS LCDCHARS-1

    // display slot 0 1
    //              2 3
    int disp = 1 ;
    int fb_page =0  ;
    int fb_pos = 0 ;
    int fb_dirty = 0 ;


    void setVisualPage(int p){
      fb_page = p;
      fb_pos  = p * FB_PAGE_SIZE;
    }

    void out_str(int c_pos,char *txt){
        int out_len = strlen( txt );
        if ( (c_pos+out_len) >= MAXCHARS)
            out_len= MAXCHARS - c_pos;
        if (out_len>0){
            fb_pos = c_pos + out_len;
            byte saved = LB[fb_pos+1];
            strncpy( &LB[c_pos] , txt, out_len );
            LB[fb_pos+1] = saved;
        }

        fb_dirty = 1;
    }
    void out(int pos,const char *fmt,va_list argptr){
        char txt[FB_PAGE_SIZE+1];
        vsnprintf_P(txt, FB_PAGE_SIZE+1, fmt, argptr);
        txt[FB_PAGE_SIZE]=0;
        out_str(  fb_pos + pos, txt );
    }

    void WriteLn(const char *fmt, ...){
        va_list argptr;
        va_start (argptr, fmt );
        out(0,fmt,argptr);
        va_end (argptr);
        setVisualPage(fb_page+1);
    }

    void Write(const char *fmt, ...){
        va_list argptr;
        va_start (argptr, fmt );
        out(0,fmt,argptr);
        va_end (argptr);
    }


    #if USE_LCD1602
        #if USE_LCD1602_I2C // <<----- Add your address here.  Find it from I2C Scanner
            #include "LiquidCrystal_I2C_vg.h"
            #define BACKLIGHT_PIN     3
            #define En_pin  2
            #define Rw_pin  1
            #define Rs_pin  0
            #define D4_pin  4
            #define D5_pin  5
            #define D6_pin  6
            #define D7_pin  7

            LiquidCrystal_I2C DISP(USE_LCD1602_I2C,En_pin,Rw_pin,Rs_pin,D4_pin,D5_pin,D6_pin,D7_pin);
        #else
            #include "LiquidCrystal_vg.h"
            LiquidCrystal DISP(2, 3, 4, 5, 6, 7);
        #endif


        void blit(){
            if (fb_dirty){
                //safety
                LB[MAXCHARS] = 0;

                DISP.setCursor(0,1);
                DISP.print( &LB[16] );

                int mark = LB[16];
                LB[16]=0;
                DISP.setCursor(0,0);
                DISP.print( &LB[0] );
                LB[16]=mark;

                fb_dirty = 0;
            }
        }

        void ClrScr(int hard=0){
            if (hard>0){
                DISP.clear();
                DISP.noBlink();
                DISP.home();
            }

            fb_pos = 0 ;
            for (int cpos=0;cpos<LCDCHARS;cpos++){
                LB[cpos]='.';
            }
            LB[MAXCHARS] = 0;
            fb_dirty = 1 ;
        }

        void GotoXY(int x,int y){
            if (y>0)
                DISP.setCursor(x,1);
            else
                DISP.setCursor(x,0);
        }

        void lcd_setup(){
            DISP.begin(16,2);
            #if USE_LCD1602_I2C
                DISP.setBacklightPin(BACKLIGHT_PIN,POSITIVE);
                DISP.setBacklight(HIGH);
                DISP.home (); // go home
            #endif
            ClrScr(1);
        }


    #endif


    #if USE_SSD1306

        #include <U8glib.h>

        U8GLIB_SSD1306_128X64 u8g(12, 11, 8, 9, 10);

        void ClrScr(){
            for (int i=0;i<LCDCHARS;i++)
                LB[i]=0;
        };

        void lcd_setup(){};

        void GotoXY(int x,int y){
            u8g.setPrintPos(x,10+y);
        }

        void out(int pos, char *fmt, ...){};

        void blit(){ };
        #define USE_LCDFAKE 0

    #endif

#else
    #define LCDCHARS 33
    void ClrScr(){
        for (int i=0;i<LCDCHARS;i++)
            LB[i]=0;
    };
    void Write(const char *fmt, ...){};
    void WriteLn(const char *fmt, ...){};
    void blit(){};
    void out(int pos, char *fmt, ...){};
    void Write( char *fmt, ...){};
    void setVisualPage(int p){};
    void GotoXY(int x,int y){};
    void lcd_setup(){};
#endif
