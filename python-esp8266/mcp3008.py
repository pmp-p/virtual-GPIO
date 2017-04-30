

if isDefined('USE_MCP3008'):
    print("\tESP ADC set to",end=' ')
    adc_esp = 0

    if not RunTime.OffBoard:
        if machine.ADC(1).read()>65534:
            print("pin A0 (0), not VCC (1)")
        else:
            print("VCC (1), not pin A0 (0)")
            adc_esp = 1

    #builtins.hspi = machine.SPI(1, baudrate=100000, polarity=0, phase=0)

    print('\tMCU ',end='')
    # set up the SPI interface pins

    class MCP3008:

        def __init__(self):
            self.mosipin = Pin('HMOSI', 'w')
            self.misopin = Pin('HMISO', 'r')
            self.clockpin = Pin('HCLK','w')
            self.cspin = Pin('HCS','w')
            self.adc0 = machine.ADC(adc_esp)


        # 0/1 A0 pin of esp or VCC
        # read SPI data from MCP3008 chip, 8 possible adc's (0 thru 7)
        def readadc(self,adcnum, clockpin, mosipin, misopin, cspin):
            if ((adcnum > 7) or (adcnum < 0)):
                    return -1
            cspin.hi()

            clockpin.lo()  # start clock low
            cspin.lo()   # bring CS low

            commandout = adcnum
            commandout |= 0x18  # start bit + single-ended bit
            commandout <<= 3    # we only need to send 5 bits here
            for i in range(5):
                    if (commandout & 0x80):
                            mosipin.hi()
                    else:
                            mosipin.lo()
                    commandout <<= 1
                    clockpin.hi()
                    clockpin.lo()

            adcout = 0
            # read in one empty bit, one null bit and 10 ADC bits
            for i in range(12):
                    clockpin.hi()
                    clockpin.lo()
                    adcout <<= 1
                    if ( misopin.dr()):
                        adcout |= 0x1

            cspin.hi()

            adcout /= 2       # first bit is 'null' so drop it
            return adcout

        # have A0-A7 behave like arduino , negative index will call ESP integrated adc
        def __call__(self,adcnum=-1):
            if adcnum<0:
                return self.adc0.read()
            return self.readadc(adcnum, self.clockpin, self.mosipin, self.misopin, self.cspin )

    def tspi(chan=1):
        cs= Pin('CS','w').hi()
        Time.sleep(0.01)
        hspi.write( b'\x01')
        hspi.write( b'%s' % chr( (8+chan) <<4 ) )
        hspi.write( b'\x00')
        print( hspi.read(3) )


    adc_esp = MCP3008()
    RunTime.add('ADC',adc_esp)
    RunTime.add('analogRead',adc_esp)

    print('\t+ MCP3008')

        #FIXME: use CD74HC4067 and digipot to feed ESP adc(0)
    del adc_esp

