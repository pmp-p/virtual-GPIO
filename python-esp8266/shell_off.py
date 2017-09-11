
if 0:
        def nmap(self,*argv,**kw):
            def get_secure(num):
                try: return 'Open/WEP/WPA-PSK/WP2-PSK/WPA-WPA2-PSK'.split('/')[int(num)]
                except:pass
                return str(num)
            try:
                for wlan in wlan0.scan():
                    yield "[ %s ] Ch: %s %s dBm lck: %s" % ( str(wlan[0],'utf8') , wlan[2], wlan[3], get_secure(wlan[4]) )
            except Exception as error:
                print(error)

        def ls(self,*argv,**kw):
            import os
            for f in os.listdir(): yield "%s\t%s" % (os.stat(f)[6],f)

        def i2cdetect(self,*argv,**kw):
            for sla in  i2c.scan(): yield hex(sla)

        def touch(self,*argv,**kw):
            for fname in argv:
                try: open(fname,'rb').close()
                except: open(fname,'wb').close()
            return []

        def cat(self,*argv,**kw):
            for arg in argv:
                with open(arg.replace('/','\\'),'rb') as f: yield f.readline().decode('utf-8','ignore')


        def ifconfig(self,*argv,**kw):
            return [wlan0.ifconfig()]
