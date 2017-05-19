
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
        protect.append( cmd )
del cmd

