# This file is executed on every boot (including wake-boot from deepsleep)
import esp
esp.osdebug(None)
import gc, machine
#machine.UART(0).init(460800)
#machine.UART(0).init(1000000)
import sys, time, builtins
builtins.Time = time ; builtins.sys = sys ; builtins.machine = machine ; builtins.gc = gc

def isDefined(varname,name=None):
    if not hasattr(__import__(name or __name__),varname):
        try: eval(varname)
        except NameError: return False
    return True

class robject(object):
    def ref(self):
        RunTime.CPR[id(self)]=self
        try:
            tips=self.to_string()
        except:
            try: tips= str( self )
            except: tips=object.__repr__(self)
        return 'µO|%s|%s' % ( id(self) , tips )

#TODO: unref

    def __repr__(self):
        if not RunTime.SerFlag:
            try: return self.to_string()
            except: return object.__repr__(self)
        return self.ref()

builtins.protected = ['protected','excepthook','displayhook','i2ctx','USE_AUTORUN','_webrepl']

class Unset(object):
    def __nonzero__(self):
        return False
    def __repr__(self):
        return '<Unset>'
    __str__ = __repr__

class RunTime:

    @classmethod
    def woke_up():
        return machine.reset_cause() == machine.DEEPSLEEP_RESET

    @classmethod
    def poweroff(wake_in=0):
        if wake_in:
            rtc=machine.RTC();rtc.irq( trigger = rtc.ALARM0 , wake= machine.DEEPSLEEP)
            rtc.alarm( rtc.ALARM0, int(wake_in*10000) )
        machine.deepsleep()

    class turbo:
        def __enter__(self):
            machine.freq(160000000)
        def __exit__(self, exc_type, exc_val, exc_tb):
            machine.freq(80000000)

    turbo = turbo()


    SerFlag = 0

    CPR = {}

    Timers = {}

    builtins = builtins
    IP = '0.0.0.0'

    urpc = None

    unset = Unset()

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
    def add(cls,sym,value):
        setattr(builtins,sym,value)
        if sym in protected:
            print("WARNING: %s was already defined" % sym)
        else:
            protected.append(sym)
        return value

    @classmethod
    def to_json(cls,data):
        cls.SerFlag += 1
        try:
            return json.dumps(data)
        finally:
            cls.SerFlag -= 1


def export(sym,val=RunTime.unset):
    if val is RunTime.unset:
        return RunTime.add(sym, eval(sym) )
    return RunTime.add(sym, val)

def zfill(i,places,char='0'):
    i=str(i)
    if len(i)<places:  i = '%s%s' % (  char * ( places-len(i) ) , i )
    return i

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

builtins.zfill = zfill
builtins.export = export
builtins.RunTime = RunTime
builtins.use = RunTime
builtins.isDefined = isDefined
builtins.robject = robject
builtins.do_gc = do_gc
builtins.reboot = machine.reset


with open('SSID','rb') as f:
    RunTime.SSID  = f.readline().decode().strip()
    RunTime.WPA  = f.readline().decode().strip()


def wlan_client(essid,password,ap=False):
    #print(RunTime.ANSI_CLS)
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

    import network;
    if not ap: network.WLAN(network.AP_IF).active(False)
    wlan = network.WLAN(network.STA_IF) ; wlan.active(True);

    print("="*79)

    builtins.wlan0 = wlan

    if not wlan.isconnected():
        print('Connecting to wlan [ %s ]' % essid , end=' ' )
        wlan.connect(essid, password)
        while not wlan.isconnected():
            Time.sleep(.1)
            print('.',end='')

    RunTime.IP = wlan.ifconfig()[0]
    print('\nConnected as',RunTime.IP)
    return True

if wlan_client(RunTime.SSID,RunTime.WPA):
    del wlan_client

do_gc()

