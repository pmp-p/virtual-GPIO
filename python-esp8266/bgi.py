
def ClrScr():
    RunTime.fb_posx, RunTime.fb_posy = 0,0
    print(RunTime.ANSI_CLS)
    if display:
        display.fill(0)
        display.show()

def Write(*argv):pass

display=None

#if USE_SSD1306
    SW = 128
    CW = 8
    SH = 64
    CH = 8

    RunTime.fb_posx=0
    RunTime.fb_posy=0

    import ssd1306

    try:
        display = ssd1306.SSD1306_I2C(SW, SH, i2c, addr=0x3c)
    except OSError as error:
        display = None
        del sys.modules['ssd1306']
        print('module ssd1306 unloaded : ',error)


    def Write(text):
        if display is None: return
        global SW,CW

        print(text,end='')

        if display:
            for txt in text:
                nl = (txt=='\n')
                if nl or (RunTime.fb_posx>= SW/CW):
                    RunTime.fb_posx = 0
                    RunTime.fb_posy +=1
                    if nl:
                        continue

                display.text(txt, RunTime.fb_posx*CW, RunTime.fb_posy*CH)
                RunTime.fb_posx+=len(txt)

            display.show()


    if display:
        display.fill(0)

        tl = Time.localtime()
        tm = '%s-%s-%s %s:%s' % ( tl[0],tl[1],tl[2],tl[3]+TZ,tl[4])

        display.text(tm, 0, 0)
        display.text('>>>', 0, 10)
        #display.invert(True)
        display.contrast(1)
        display.set_pixel = display.pixel
        display.show()

#endif

for elem in ['display','ClrScr','Write']:
    RunTime.add(elem, getattr( __import__(__name__) , elem ) )

