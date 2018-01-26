#if USE_SHIFTREG
#   GND  7   6         5           4       3               2  1
#   Q7S  MR  SHCP(CLK) STCP(Latch) OE(gnd) DS(data/serial) Q0 VCC(+5)
    class ShiftReg:

        def __init__(self,  rclk='D2', latch='D1', serial='D0', oe=None, invert=False, left=0):
            """ 11 12 14 """
            self.r = Pin(rclk,'w')
            self.s = Pin(serial,'w')
            self.l = Pin(latch,'w')
            # output enable
            if oe:
                self.oe = Pin(oe,'w')
                self.oe(0)

            self.left = left
            self.mode(invert)
            self.shift_out(0)

        def mode(self,invert=False):
            if invert:
                self.value = self.shift_inv
                return
            self.value =  self.shift_out

#pin0(s) data/ser  pin1(r)/se_rclk pin2(l)/latch

        def shift(self,bits):
            r=self.r.instance.value
            s=self.s.instance.value
            r(0)
            self.l(0)
            for bit in [bits >> i & 1 for i in range(7,-1,-1)]:
                s( bit )
                r(1)
                r(0)
            self.l(1)

        def shift_out(self, bits):
            self.shift(bits << self.left)

        def shift_inv(self, bits):
            self.shift(~ bits << self.left)

        def __call__(self,bits):
            self.value(bits)

    RunTime.add('ShiftReg',ShiftReg)
#endif



