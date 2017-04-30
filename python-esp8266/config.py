#your local time DST
builtins.TZ = +2

USE_SERVO = False
USE_MCP3008 = False
USE_SSD1306 = False
USE_WEBREPL = False
USE_I2C = False
USE_RPC = False
USE_SHIFTREG = False
#break auto-import loop
USE_EXIT = False

#==================================================================================================

# i2c = machine.I2C(SCL, SDA)  the 'default' values will be set in PINS table
SCL = 2
SDA = 0



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

if RunTime.IP.endswith('.64'):

    RunTime.I2C_FOLLOWER = 0 #0x66

    USE_SSD1306 = False

    USE_MCP3008 = False

    USE_WEBREPL = False










if RunTime.IP.endswith('.65'):
    pass

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

