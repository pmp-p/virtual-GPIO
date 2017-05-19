#if USE_RPC
    import socket
    import websocket
    import ure

    import _webrepl
    import ujson as json

    RunTime.builtins.json = json

    if RunTime.urpc:
        RunTime.urpc.destroy()
        RunTime.urpc = None
        do_gc()



    do_gc()

    class URPC:

        class RPC_Handler:
            def __init__(self,cl):
                self.cl = cl
                self.ws = websocket.websocket(cl, True)
                self.wsr = _webrepl._webrepl(self.ws)
                print('ALLOC!')

            def handle(self,sock):
                data = self.ws.read()
                if not data: return
                data = data.decode()

                if data[0]!='#': return #repl

                if len(data)<4:
                    if data.startswith('#-'):
                        self.ws.write('#-2:{}\n')
                        self.destroy()
                        return

                serial = -1 ; rv = 'null'
                try:
                    data =json.loads(data[1:])
                    serial = data.pop('s',-1)
                    mak = data.pop('m').split('.') , data.pop('a',()), data.pop('k',{})
                    if RunTime.urpc.call:
                        rv= RunTime.to_json( RunTime.urpc.call(*mak) )
                    else:
                        print('RPC:',mak )
                except ValueError:
                        print('ERR:',data)
                finally:
                    self.ws.write('#%s:%s' % (serial, rv ) )

            def destroy(self):
                self.wsr.close();self.ws.close();self.cl.close()
                RunTime.urpc.clients.remove( self )
                del self.ws,self.wsr,self.cl
                print('closed',do_gc())

        Handler = RPC_Handler
        clients = []

        def __init__(self):
            self.listen_s = None
            self.call = None


        def accept(self,listen_sock):
            cl, remote_addr = listen_sock.accept()
            buf = RunTime.server_handshake(cl)
            if buf is not True:
                if RunTime.server_http_handler:
                    sh = RunTime.server_http_handler(cl)
                try:
                    print('\n-- http --')
                    sh.handle(buf)
                    sh.wfile.close()
                    print('/-- http --')
                except Exception as e: sys.print_exception(e,sys.stdout)
                finally: sh.wfile.close()

            handler =  self.Handler(cl)
            self.clients.append( handler  )
            cl.setblocking(False); cl.setsockopt(socket.SOL_SOCKET, 20, handler.handle )

        def stop(self):
            try:
                while len(self.clients):
                    self.clients.pop(0).destroy()
            finally:
                if self.listen_s: self.listen_s.close()

        def destroy(self):
            self.stop()
            self.listen_s = None

        def start(self,port=8266, password='password'):
            self.stop()
            _webrepl.password(password)

            self.listen_s = listen_s = socket.socket()
            listen_s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            ai = socket.getaddrinfo("0.0.0.0", port)
            addr = ai[0][4]

            listen_s.bind(addr)
            try:
                listen_s.listen(1)
                listen_s.setsockopt(socket.SOL_SOCKET, 20, self.accept )
            except OSError:
                print("Error: Socket port %s already in use" % port)
            return listen_s

    RunTime.urpc = URPC()

#endif
