#if USE_SERVO

    class Servo_mcu:

        def mcu_init(self,pin, freq, duty):
            self.pwm = machine.PWM(pin, freq,duty)

        def mcu_duty(self,duty):
            self.pwm.duty(duty)

        def mcu_idle(self):
            self.pwm.duty(0)

        mcu_stop = mcu_idle


    class Servo(Servo_mcu):

        def call(self,o, freq=50, min_us=500, max_us=2300, angle=180 ):
            if o is use.default: return o(**locals())
            self.min_us = min_us
            self.max_us = max_us
            self.us = 0
            self.freq = freq
            self.angle = angle

            self.mcu_init(o[-1],freq,0)
            return [self]


        def free(self):
            self.pwm = None


        def write_us(self, us):

            if us == 0:
                self.pwm.duty(0)
                return
            us = min(self.max_us, max(self.min_us, us))
            duty = us * 1024 * self.freq // 1000000

            self.mcu_duty(duty)


        def set_angle(self, degrees=None, radians=None):
            if degrees is None:
                raise #degrees = math.degrees(radians)
            degrees = degrees % 360
            total_range = self.max_us - self.min_us
            us = self.min_us + total_range * degrees // self.angle
            self.write_us(us)

        def set_table(self,left=0,neutral=90,right=180):
            self.neutral = float(neutral)
            self.set_angle(neutral)
            self.lc = float(neutral - left)  / 90.0
            self.rc = float(right - neutral) / 90.0
            self.rn = None

        def remap(self,l,n,r):
            self.rl = -( 90.0 / (n-l) )
            self.rn = n
            self.rr = 90.0 / (r-n)


        def set_pos(self,orel=0):
            rel =orel
            if self.rn is not None:
                if rel<self.rn:
                    rel =  (self.rn - rel ) * self.rl
                elif rel>self.rn:
                    rel = (rel - self.rn ) * self.rr
                else:
                    rel=0.0

            if rel<0:
                rel = 90+rel
                rel= int(rel * self.lc)
            elif rel>0:
                rel = int( self.neutral + rel*self.rc  )
            else:
                rel = int(self.neutral)

            self.set_angle(rel)
            return orel

    Pin.Servo = Servo

#endif
