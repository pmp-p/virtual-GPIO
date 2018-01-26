#if USE_TIMERS

    class Beat:
        TID = 0
        def __init__(self,callback,period=0,halt=None):
            self.tid = self.__class__.TID
            self.__class__.TID+=1
            self.cb = callback
            self.halt = halt

            if period:
                tm=machine.Timer(self.tid)
                RunTime.Timers[self.tid]=tm
                tm.init(period=int(period), mode=machine.Timer.PERIODIC, callback= self.callback )

        def callback(self,*info):
            try:
                self.cb()
            except Exception as e:
                self.stop()
                print(e)

        def stop(self):
            tm = RunTime.Timers.get(self.tid,None)
            if tm:tm.deinit()
            if self.halt:
                self.halt()


    class Lapse:
        def __init__(self,intv=1.0,oneshot=None):
            self.cunit = intv
            self.intv = int( intv * 1000000 )
            self.next = self.intv
            self.last = Time.ticks_us()
            self.count = 1.0
            if oneshot:
                self.shot = False
                return
            self.shot = None

    #FIXME: pause / resume(reset)

        def __bool__(self):
            if self.shot is True:
                return False

            t = Time.ticks_us()
            self.next -= ( t - self.last )
            self.last = t
            if self.next <= 0:
                if self.shot is False:
                    self.shot = True
                self.count+= self.cunit
                self.next = self.intv
                return True

            return False

    export('Beat')
    export('Lapse')

#endif
