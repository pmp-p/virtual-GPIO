

if not isDefined('USE_EXIT'):
    import urllib
    import urllib.urequest

    class URL:
        ureq = urllib.urequest

        def __init__(self,path,mode='rb'):
            self.u = self.ureq.urlopen(path)

        def readline(self):
            return self.u.readline().decode('utf-8','ignore')

        def readlines(self):
            while True:
                l =self.readline()
                if l:yield l
                else: break

        def read(self):
            return self.u.read().decode('utf-8','ignore')

    RunTime.add('url','URL')

    def prepro(source):
        global protect

        def imark(im): return im,'%simport ' % (' '*im)

        ilines = [] ; clines = [] ; defs = [] ; ifdef = False ; skipping = False

        INDENT , importmark = imark(0)

        for l in source.readlines():
            l  = l.rstrip()
            if len(l)<4:
                clines.append('')
                continue

            if not ifdef :
                if l.startswith('#if '):
                    cmd=l.replace('#if ','').strip()

                    # PEP8 4 spaces !
                    INDENT , importmark = imark(4)

                    if not isDefined(cmd):
                        defs.append( "\t - %s"%cmd )
                        skipping = True
                    else:
                        defs.append( "\t + %s"%cmd )
                    ifdef = True

            if skipping :
                if l.count('#endif'):
                    INDENT , importmark = imark(0)
                    skipping = False
                continue
            ll = l.lstrip()

            if ll[0]=='#':
                clines.append('#')
            elif l.startswith( importmark ):
                ilines.append(l[INDENT:])
                ll = ll.replace( importmark,'').strip().rsplit(' ',1)[-1]
                if not ll in protect:
                    protect.append(ll) #prevent cleanup from removing modules
                clines.append( '#%s' % ll )
            else:
                clines.append( l[INDENT:] )

        return '\n'.join(ilines),'\n'.join(clines),defs

    def zfill(i,places,char='0'):
        i=str(i)
        if len(i)<places:  i = '%s%s' % (  char * ( places-len(i) ) , i )
        return i

    def report_run_error(lines,e=None,tip='<file>'):
        if e:
            print("="*10,tip,"="*10)
            sys.print_exception(e,sys.stdout)
        print("_"*40)
        for i,line in enumerate( lines.split('\n') ):
            print("%s: %s" % ( zfill(i,4), line) )
        print("="*79)

    def pyfilerun(file_like,tip='<file>'):
        do_gc()
        try:
            imports,maincode,defs = prepro( file_like )

        except Exception as error:
            print( error )
            return

        bmem = do_gc()

        if imports:
            #print('\t%s imports' % (1+imports.count('\n') ) )
            try:
                exec( imports , globals(),locals() )
            except Exception as e:
                report_run_error(imports,e,tip)
            imports=''
            del imports


        if maincode:
            print('<%s %s L, Sz %s >' % (tip, 1+maincode.count('\n'), len(maincode) ) )
            for d in defs:
                print(d)
            del defs
            bmem = do_gc()

            RunTime.C.set_remote_file(tip)
            try:
                exec( maincode , globals(),locals() )
            except SyntaxError as e:
                report_run_error(maincode,e,tip)
            except Exception as e:
                report_run_error(maincode,e,tip)
            maincode=''
            del maincode
            do_gc()
            print('</%s B %s\n' % (tip, bmem - gc.mem_free() ) )

    for e in dir():
        if not e in protect:
            protect.append(e)

    import c_runtime
    RunTime.C = c_runtime

    for mod in URL(RunTime.srv + '/index').readlines():
        mod = mod.strip()
        if mod:
            if mod[0]!='#':
                pyfilerun( URL( RunTime.srv + mod ), mod[1:-3] )
                if isDefined('USE_EXIT'):
                    break
            else:
                print("\n%s\n"%mod)
    else:
        SHELL.start()


    if isDefined('USE_WEBREPL'):
        import webrepl
        webrepl.start()
        RunTime.webrepl = webrepl
        del USE_WEBREPL

    print('\nCleaning : ',end='')

    for f in dir():
        if not f in protect:
            print(f,end=', ')
            try:
                delattr( __import__(__name__) , f)
            except:
                delattr( builtins , f)
        else:
            protect.remove(f)
    del f
    print()
    do_gc(True)


