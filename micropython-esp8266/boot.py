# This file is executed on every boot (including wake-boot from deepsleep)
import esp
esp.osdebug(None)
import gc
#import webrepl
#webrepl.start()

#import machine
#machine.UART(0).init(1000000)


import sys
import time
import builtins
import machine
builtins.Time = time
builtins.sys = sys
builtins.machine = machine

#from micropython import const


def isDefined(varname,name=None):
    if not hasattr(__import__(name or __name__),varname):
        try:
            eval(varname)
        except NameError:
            return False
    return True

class robject(object):
    def ref(self):
        RunTime.CPR[id(self)]=self
        try:
            tips=self.to_string()
        except:
            try:
                tips= str( self )
            except:
                tips=object.__repr__(self)
        return 'µO|%s|%s' % ( id(self) , tips )

#TODO: unref

    def __repr__(self):
        if not RunTime.SerFlag:
            try:
                return self.to_string()
            except:
                return object.__repr__(self)
        return self.ref()


protect = ['protect','excepthook','displayhook','i2ctx','USE_AUTORUN','_webrepl']


class RunTime:

    SerFlag = 0

    CPR = {}

    Timers = {}

    builtins = builtins
    IP = '0.0.0.0'

    urpc = None

    srv = 'http://192.168.1.66/mpy'

    ANSI_CLS = ''.join( map(chr, [27, 99, 27, 91, 72, 27, 91, 50, 74] ) )

    SSID = 'SSID'
    WPA = 'password'

    webrepl = None
    server_handshake = None
    server_http_handler = None

    I2C_FOLLOWER = 0x0

    MEM_init = 32678

    @classmethod
    def add(cls,entry,value):
        global protect
        setattr(builtins,entry,value)
        if not entry in protect:
            protect.append(entry)

    @classmethod
    def to_json(self,data):
        self.SerFlag += 1
        try:
            return json.dumps(data)
        finally:
            self.SerFlag -= 1


builtins.RunTime = RunTime
builtins.use = RunTime
builtins.isDefined = isDefined
builtins.robject = robject


def do_gc(v=False):
    imem = fmem = gc.mem_free()
    while True :
        Time.sleep(0.02)
        gc.collect()
        tmem = gc.mem_free()
        if tmem==fmem:
            break
        if v:
            print('was',imem,'now',tmem)
        fmem= tmem

    if v:
        v=int( (tmem - imem)/1024 )
        print(imem, ' +',v ,'K  = ', tmem)
    return tmem

with open('SSID','rb') as f:
    RunTime.SSID  = f.readline().decode().strip()
    RunTime.WPA  = f.readline().decode().strip()



def wlan_client(essid,password):
    print(RunTime.ANSI_CLS)
    print('SSID/PASS from /SSID file')
    Time.sleep(.4)

    if not sys.platform=='esp8266':
        print('not on board')
        RunTime.OffBoard = True
        return False

    RunTime.OffBoard = False

    import gc
    gc.collect()


    RunTime.MEM_init = do_gc()

    import network; wlan = network.WLAN(network.STA_IF); wlan.active(True)

    print("="*79)

    builtins.wlan0 = wlan

    if not wlan.isconnected():
        print('Connecting to wlan [ %s ]' % essid )
        wlan.connect(essid, password)
        while not wlan.isconnected():
            Time.sleep(.1)

    cnf = wlan.ifconfig()
    RunTime.IP = cnf[0]
    return True



if wlan_client(RunTime.SSID,RunTime.WPA):
    del wlan_client

do_gc()

