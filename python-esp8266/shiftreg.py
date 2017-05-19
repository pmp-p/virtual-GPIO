#if USE_SHIFTREG
    class ShiftReg:
        def __init__(self,  rclk='D2', latch='D1', serial='D0', oe=None):
            """ 11 12 14 """
            self.rclk = Pin(rclk,'w')
            self.oe = oe
            self.ser = Pin(serial,'w')
            self.latch = Pin(latch,'w')
            if oe:
                self.oe.lo() # output enable

            self.latch.lo()
            self.clear()
            self.latch.hi()

            self(0)


        def clear(self):
            self.rclk.lo()
            self.latch.lo()
            self.ser.lo()


        def shift(self,bits):
            for bit in [bits >> i & 1 for i in range(7,-1,-1)]:
                self.rclk.lo()
                self.ser.dw( bit )
                self.rclk.hi()
                self.ser.lo()

        def begin(self):
            self.latch.lo()
            self.ser.lo()
            self.rclk.lo()

        def end(self):
            self.rclk.lo()
            self.latch.hi()

        def shift_out(self, bits):
            self.begin()
            self.shift(bits)
            self.end()

        def __call__(self,bits):
            self.shift_out(bits)


    RunTime.add('ShiftReg',ShiftReg)
#endif
