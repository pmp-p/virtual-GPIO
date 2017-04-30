#if USE_I2C
    Pin.get('SCL',SCL)
    Pin.get('SDA',SDA)

    SCL = Pin( 'SCL','r' )
    SDA = Pin( 'SDA','r' )

    print("I2C: SCL: %s SDA: %s" %  (SCL,SDA) )

    RunTime.add('i2c', machine.I2C(-1, SCL.instance, SDA.instance ) )



    if RunTime.I2C_FOLLOWER:
        def i2ctx(cmd,target=RunTime.I2C_FOLLOWER):
            i2c.writeto(target,cmd)

        # <=0.6 corruption with nano when sending greeter
        Time.sleep(0.8)

        try:
            i2ctx('connected')
        except:
            print("error with I2C follower at %s" % hex(RunTime.I2C_FOLLOWER) )

        Time.sleep(0.8)
#endif
