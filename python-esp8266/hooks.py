#need readline alike
# import readline; print '\n'.join([str(readline.get_history_item(i)) for i in range(readline.get_current_history_length())])
# to get faulty syntax from history because traceback n/i

def displayhook(value):
    print("displayhook : %s" % value )
    #sys.__displayhook__(value)


def excepthook(exc_type, exc_value, exc_traceback):
    last = ''
    tbs = list( map( str , traceback.format_exception(exc_type, exc_value, exc_traceback) ) )
    if tbs[-1].startswith('SyntaxError:'):
        print("_______________________________________________")
        for tb in tbs:
            if tb:
                if tb.count('^'):
                    last = last.strip()
                    print("maybe shell:",last)
                    print("_______________________________________________")
                    return
                last = tb


    sys.__excepthook__(exc_type, exc_value, exc_traceback)

try:
    sys.displayhook = displayhook
except:
    print("displayhook failure, no pretty print")

if RunTime.OffBoard:
    import traceback
    sys.excepthook = excepthook
    RunTime.builtins.traceback = traceback
    print("*ALPHA* shell arguments")
else:
    def pe(*argv):
        print('{{{{ %s }}}}' % argv )
    try:
        import traceback
        sys.excepthook = excepthook
    except:
        print("traceback/excepthook failure, no shell arguments",sys.print_exception)

    try:
        sys.print_exception = pe
    except:
        print("total fail :p")


try:
    import ntptime
    ntptime.settime()
    del ntptime
except:
    pass



