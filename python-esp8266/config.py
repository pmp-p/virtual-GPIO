
# i2c = machine.I2C(SCL, SDA)  the 'default' values will be set in PINS table
SCL = 2 #D4
SDA = 0 #D3

#your local time DST
builtins.TZ = +2

#========= sane defaults ===========================================================================

USE_SERVO = False
USE_MCP3008 = False
USE_SSD1306 = False
USE_WEBREPL = False
USE_I2C = False
USE_SHIFTREG = False
USE_EXIT = False
USE_TIMERS = False

USE_RPC = None
#break auto-import loop
USE_ROUTER = False

#==================================================================================================
if RunTime.IP.endswith('.48'):
    USE_WEBREPL = False

    def test():
        start('src/iliscr')
    export('test',test)

    #USE_AUTORUN = 'src/rvb_sr'


if RunTime.IP.endswith('.56'):
    #wemos
    USE_SHIFTREG = 1
    USE_TIMERS = 1
    RunTime.I2C_FOLLOWER = 0 #0x66

    def test():
        start('src/rvb_sr')
    export('test',test)

    USE_AUTORUN = 'src/rvb_sr'


if RunTime.IP.endswith('.57'):

    RunTime.I2C_FOLLOWER = 0 #0x66
    USE_SSD1306 = False
    USE_MCP3008 = False
    USE_AUTORUN = 'src/tank'

    USE_WEBREPL = True
    USE_RPC = True


if RunTime.IP.endswith('.64'):
    RunTime.I2C_FOLLOWER = 0 #x66
    USE_WEBREPL = False
    USE_SHIFTREG = 0
    USE_TIMERS = 1
    USE_I2C = 1
    USE_SSD1306 = 1

#    def test():
#        start('src/digits')
#    export('test',test)

    #USE_AUTORUN = 'src/digits'


if RunTime.IP.endswith('.65'):
    RunTime.I2C_FOLLOWER = 0 #0x66
    USE_SSD1306 = False
    USE_MCP3008 = False
    USE_AUTORUN = 'src/tank'

    USE_WEBREPL = True
    USE_RPC = True


if RunTime.IP.endswith('.63'):

    USE_SERVO = True
    USE_AUTORUN = 'src/car'
    USE_WEBREPL = False
    USE_RPC = True
    import webrepl
    RunTime.webrepl = webrepl

    def test():
        start('test')

    RunTime.add('test',test)

    RunTime.add('export',export)

if USE_WEBREPL:
    import webrepl
    RunTime.webrepl = webrepl
    if USE_ROUTER is None:
        USE_ROUTER = True
    if USE_RPC is None:
        USE_RPC =True
#==============================================================================================


if RunTime.OffBoard:
    USE_MCP3008 = False
    USE_SERVO = True

USE_I2C = USE_I2C or USE_SSD1306 or RunTime.I2C_FOLLOWER

for usedef in dir():
    if usedef.startswith('USE_'):
        if getattr( __import__(__name__) , usedef ):
            print('\t + %s' % usedef )
        else:
            delattr( __import__(__name__) , usedef );
del usedef

