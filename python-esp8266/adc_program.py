#if USE_ADCPROG
        def adc1_mode(mode=255,write=False):
            import flashbdev
            sector_size = flashbdev.bdev.SEC_SIZE
            flash_size = esp.flash_size() # device dependent
            init_sector = int(flash_size / sector_size - 4)
            data = bytearray(esp.flash_read(init_sector * sector_size, sector_size))
            if data[107] == mode:
                return True  # flash is already correct; nothing to do
            elif write:
                data[107] = mode  # re-write flash
                esp.flash_erase(init_sector)
                esp.flash_write(init_sector * sector_size, data)
                print("ADC mode changed in flash; restart to use it!")
                os.remove('/adc')
            return False
        try:
            open('/adc','rb')
            if adc1_mode(mode=255,write=False):
                print("ESP ADC(1) set to read VCC, , reflash with : adc1_mode(mode=0,write=True)")
            else:
                print("ESP ADC(1) cannot read VCC, reflash with : adc1_mode(mode=255,write=True)")
            global USE_EXIT
            builtins.adc1_mode=adc1_mode
            USE_EXIT=True
            return
        except:
            pass

#endif

