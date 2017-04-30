import os
import sys
import time
import builtins
import machine
builtins.builtins = builtins
builtins.Time = time
builtins.os = os
builtins.sys = sys
builtins.machine = machine

from micropython import const

import esp
esp.osdebug(None)

#import machine
#machine.UART(0).init(1000000)


def isDefined(varname,name=None):
    if not hasattr(__import__(name or __name__),varname):
        try:
            eval(varname)
        except NameError:
            return False
    return True

builtins.isDefined = isDefined

protect = ['protect','excepthook','displayhook','i2ctx','USE_AUTORUN','_webrepl']


class RunTime:
    import builtins

    builtins = builtins
    IP = '0.0.0.0'

    urpc = None

    srv = 'http://192.168.1.66/mpy'

    ANSI_CLS = ''.join( map(chr, [27, 99, 27, 91, 72, 27, 91, 50, 74] ) )

    SSID = 'SSID'
    WPA = 'password'

    webrepl = None

    I2C_FOLLOWER = 0x0

    MEM_init = 32678

    @classmethod
    def add(cls,entry,value):
        global protect
        setattr(builtins,entry,value)
        if not entry in protect:
            protect.append(entry)


    class default(object):
        # kw comes with a self
        def __init__(_self_of_default_,defval=None,**kw):
            _self_of_default_.values = None
            if defval is None:
                for unwanted in ('self','kw','o'):
                    if unwanted in kw:kw.pop(unwanted)

                _self_of_default_.values = kw
            _self_of_default_.value = defval


        def __repr__(self):
            return repr( self.values)
        __str__ = __repr__


def do_gc(v=False):
    imem = fmem = gc.mem_free()
    while True :
        Time.sleep(0.04)
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

print(RunTime.ANSI_CLS)

def wlan_client(essid,password):
    print('SSID/PASS from /SSID file')
    Time.sleep(.4)
    try:
        if not os.path.isfile('/main.py'):
            print('not on board')
            RunTime.OffBoard = True
            return False
    except:
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


builtins.RunTime = RunTime
builtins.use = RunTime

if wlan_client(RunTime.SSID,RunTime.WPA):
    del wlan_client

if not isDefined('USE_EXIT'):
    print("_"*79)

    class URL:
        import urllib
        import urllib.urequest
        ureq = urllib.urequest

        def __init__(self,path,mode='rb'):
            self.u = self.ureq.urlopen(path)

        def readline(self):
            return self.u.readline().decode('utf-8','ignore')

        def readlines(self):
            while True:
                l =str( self.readline() )
                if l:yield l
                else: break

        def read(self):
            return self.u.read().decode('utf-8','ignore')

    RunTime.add('url','URL')

    def prepro(source):
        global protect
        ilines = []
        clines = []
        defs = []
        ifdef = False
        skipping = False


        INDENT = 0
        importmark = 'import '

        for l in source.readlines():
            l  = l.rstrip()
            if len(l)<4:
                clines.append('')
                continue

            if not ifdef :
                if l.startswith('#if '):
                    cmd=l.replace('#if ','').strip()

                    # PEP8 4 spaces !
                    INDENT = 4
                    importmark = '%simport ' % (' '*INDENT)

                    if not isDefined(cmd):
                        defs.append( "\t - %s"%cmd )
                        skipping = True
                    else:
                        defs.append( "\t + %s"%cmd )
                    ifdef = True

            if skipping :
                skipping = l.count('#endif')
                continue
            ll = l.lstrip()

            if ll[0]=='#':
                clines.append('#')
            elif l.startswith( importmark ):
                ilines.append(l[INDENT:])
                ll = ll.replace( importmark,'').strip().rsplit(' ',1)[-1]
                if not ll in protect:
                    protect.append(ll) #prevent cleanup from removing modules
                clines.append( '#%s' % ll )
            else:
                clines.append( l[INDENT:] )

        return '\n'.join(ilines),'\n'.join(clines),defs

    def zfill(i,places,char='0'):
        i=str(i)
        if len(i)<places:
            i = '%s%s' % (  char * ( places-len(i) ) , i )
        return i

    def report_run_error(lines,e=None,tip='<file>'):
        if e:
            print("="*10,tip,"="*10)
            sys.print_exception(e,sys.stdout)
        print("_"*40)
        for i,line in enumerate( lines.split('\n') ):
            print("%s: %s" % ( zfill(i,4), line) )
        print("="*79)

    def pyfilerun(file_like,tip='<file>'):
        do_gc()
        try:
            imports,maincode,defs = prepro( file_like )

        except Exception as error:
            print( error )
            return

        bmem = do_gc()

        if imports:
            #print('\t%s imports' % (1+imports.count('\n') ) )
            try:
                exec( imports , globals(),locals() )
            except Exception as e:
                report_run_error(imports,e,tip)
            imports=''
            del imports


        if maincode:
            print('<%s %s L, Sz %s >' % (tip, 1+maincode.count('\n'), len(maincode) ) )
            for d in defs:
                print(d)
            del defs
            bmem = do_gc()
            try:
                exec( maincode , globals(),locals() )
            except SyntaxError as e:
                report_run_error(maincode,e,tip)
            except Exception as e:
                report_run_error(maincode,e,tip)
            maincode=''
            del maincode
            do_gc()
            print('</%s B %s\n' % (tip, bmem - gc.mem_free() ) )

    for e in dir():
        if not e in protect:
            protect.append(e)

    import c_runtime
    RunTime.C = c_runtime

    for mod in URL(RunTime.srv + '/index').readlines():
        mod = mod.strip()
        if mod:
            if mod[0]!='#':
                RunTime.C.set_remote_file(mod[1:-3])
                pyfilerun( URL( RunTime.srv + mod ), mod[1:-3] )
                if isDefined('USE_EXIT'):
                    break
            else:
                print("\n%s\n"%mod)
    else:
        SHELL.start()


    if isDefined('USE_WEBREPL'):
        import webrepl
        webrepl.start()
        RunTime.webrepl = webrepl
        del USE_WEBREPL

    print('\nCleaning : ',end='')

    for f in dir():
        if not f in protect:
            print(f,end=', ')
            try:
                delattr( __import__(__name__) , f)
            except:
                delattr( builtins , f)
        else:
            protect.remove(f)
    del f, protect
    print()
    do_gc(True)


