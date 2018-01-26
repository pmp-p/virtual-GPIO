display=None
RunTime.echo = True


def ClrScr(echo=RunTime.echo):
    RunTime.fb_posx, RunTime.fb_posy = 0,0
    if echo:
        print(RunTime.ANSI_CLS)
    if display:
        display.fill(0)
        display.show()

def Write(text,echo=RunTime.echo):
    if echo:
        print(text,end='')

def WriteLn(text,echo=RunTime.echo):Write("%s\n"%text,echo=echo)

def tmp_setnames():
    for elem in ['display','ClrScr','Write','WriteLn']:
        RunTime.add(elem, getattr( __import__(__name__) , elem ) )

tmp_setnames()

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
        display.SW = SW
        display.CW = CW
        display.CH = CH
    except OSError as error:
        display = None
        del sys.modules['ssd1306']
        print('module ssd1306 unloaded : ',error)


    def Write(text,echo=RunTime.echo):
        if display is None: return
        SW = display.SW
        CW = display.CW
        CH = display.CH
        if echo:
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
        display.contrast(1)
        display.set_pixel = display.pixel
        display.show()
    tmp_setnames()

#endif


