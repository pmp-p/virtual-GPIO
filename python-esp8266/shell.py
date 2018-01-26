
class SHELL(str):
    @classmethod
    def start(self,*argv,**kw):
        argv=list(argv)
        if not len(argv) and isDefined('USE_AUTORUN'):
            argv.append( USE_AUTORUN )
        while argv:
            pyfilerun( URL( RunTime.srv +'/'+ argv[0] +'.py','rb'), argv.pop(0) )
        return []

    def reboot(self,*argv,**kw):
        machine.reset()
        return []

    def clear(self,*argv,**kw):
        return [RunTime.ANSI_CLS]

    def t(self,*argv,**kw):
        do_gc(1); test(); do_gc(1)
        return []

    def ls(self,*argv,**kw):
        import os
        for f in os.listdir(): yield "%s\t%s" % (os.stat(f)[6],f)

    def ifconfig(self,*argv,**kw):
        return [wlan0.ifconfig()]

    def cat(self,*argv,**kw):
        for arg in argv:
            with open(arg.replace('/','\\'),'rb') as f: yield f.readline().decode('utf-8','ignore')

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

    def i2cdetect(self,*argv,**kw):
        for sla in i2c.scan(): yield hex(sla)

    def touch(self,*argv,**kw):
        for fname in argv:
            try: open(fname,'rb').close()
            except: open(fname,'wb').close()
        return []


    def __call__(self,*argv,**kw):
        try:
            for l in  getattr(self,"%s" % self)(*argv,**kw):
                print(l)

        except Exception as error:
            return '%s: command not found (%s)' % (self,error)

    def __repr__(self):
        try:
            for l in getattr(self,"%s" % self)(): print(l)
        except Exception as error:
            return '%s: command not found (%s)' % (self,error)
        return ''

for cmd in dir(SHELL):
    if cmd[0]!='_' and not cmd in dir(str):
        print("\t+ %s" % cmd)
        setattr(__import__(__name__),cmd, SHELL(cmd) )
        protected.append( cmd )
del cmd

