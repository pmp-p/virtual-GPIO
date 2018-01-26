class Pin(robject):

    PMAP = {
        'A0' :  0,
        'D3' :  0,
        'D10' : 1,
        'D9' : 3,
        'LED_BUILTIN' : 2, #inverted
        'D4' :  2,
        'D2' :  4,

        'D1' :  5,
#6
#7
#8
        'SD0'  : 7,
        'SD1'  : 8,
        'SD2' : 9,
        'SDD2' : 9,
        'SDD3' : 10,
        'SD3' : 10,
        'CMD' : 11,
        'SDCMD' : 11,
        'HMOSI'  : 13,
        'HMISO'  : 12,
        'HCLK' : 14,
        'HCS'   : 15,
#11
        'D6' : 12,
        'D7' : 13,
        'D5' : 14,
        'D8' : 15,
        'D0' : 16,
    }

    Servo = None
    OUT = machine.Pin.OUT
    IN  = machine.Pin.IN

    @classmethod
    def get(cls,pin,default=-1):
        if isinstance(pin,str):
            pin = pin.upper()
            if default>=0:
                return cls.PMAP.setdefault(pin,default)
            return cls.PMAP.get(pin,default)
        return pin

    def __init__(self,pin,mode='r',value=0):
        thepin = self.get(pin)
        self.name = pin
        self.gpio = thepin
        self.mode = mode
        if 'w' in mode:
            self.instance = machine.Pin(thepin,mode=machine.Pin.OUT,value=value)
        elif 'r' in mode:
            self.instance = machine.Pin(thepin,mode=machine.Pin.IN)
        else:
            print('error no pin mode %s' % pin )
        self.pwm = self.servo = None

    def to_string(self):
        return '%s(%s)[%s]'%(self.name,self.gpio,self.mode)

    def up(self):pass
        #self.instance.pull( machine.Pin.PULL_UP )

    def down(self):pass
        #self.instance.pull( machine.Pin.PULL_DOWN )

    def as_servo(self,left=0,neutral=90,right=180):
        self.servo = self.Servo()
        self.servo.call( [ self.instance] )
        self.servo.set_table(left,neutral,right)
        self.set_pos = self.servo.set_pos
        self.remap = self.servo.remap

        return self

    def as_pwm(self,freq=50, duty=0):
        self.pwm = machine.PWM(self.instance ,freq=freq, duty=duty)
        return self

    def idle(self):
        if self.servo :
            self.servo.mcu_idle()

    def stop(self):
        if self.servo :
            self.servo.mcu_stop()
            self.servo = self.servo.free()

        if self.pwm:
            self.pwm.duty(0)
            self.pwm = None

        self.instance.value(0)

    def __call__(self,*argv):
        if self.pwm:
            return self.pwm.duty(*argv)
        if self.servo:
            return self.set_pos(*argv)
        return self.instance(*argv)

    def dw(self,v):
        self.instance.value( ( v and 1 ) or 0 )
        return self

    def dr(self):
        return self.instance.value()

    def hi(self):
        self.instance.value(1)
        return self

    def lo(self):
        self.instance.value(0)
        return self

    def invert(self):
        self.dw( not self.instance.value() )
        return self.instance.value()

    toggle = invert

export('Pin',Pin)
