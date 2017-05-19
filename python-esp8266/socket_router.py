#if USE_ROUTER
    import ubinascii as binascii
    import uhashlib as hashlib

    def server_handshake(sock):
        clr = sock.makefile("rwb", 0)
        buf=[clr.readline().decode()]
        webkey = None
        while 1:
            l = clr.readline()
            buf.append( l.decode() )
            if not l:
                raise OSError("EOF in headers")

            if l == b"\r\n":
                break

            h, v = [x.strip() for x in l.split(b":", 1)]
            if h == b'Sec-WebSocket-Key':
                webkey = v

        if not webkey:
            return buf

        d = hashlib.sha1(webkey)
        d.update(b"258EAFA5-E914-47DA-95CA-C5AB0DC85B11")
        respkey = d.digest()
        respkey = binascii.b2a_base64(respkey)[:-1]
        sock.send(b"""HTTP/1.1 101 Switching Protocols\r
    Upgrade: websocket\r
    Connection: Upgrade\r
    Sec-WebSocket-Accept: """)
        sock.send(respkey)
        sock.send("\r\n\r\n")
        return True



    class HTTP_Handler:
        def __init__(self,cl):
            self.cl = cl
            self.wfile = self.rfile = cl.makefile('rwb',0)

        def parseURL(self,url):
            self.parameters = {}
            self.path = ure.search("(.*?)(\?|$)", url)
            while True:
                vars = ure.search("(([a-z0-9]+)=([a-z0-8.]*))&?", url)
                if vars:
                    self.parameters[vars.group(2)] = vars.group(3)
                    url = url.replace(vars.group(0), '')
                else:
                    break

        def sendContent(self,content,ctype="text/html"):
            self.wfile.write("""HTTP/1.0 200 OK\r
    Content-type: %s\r
    Content-length: %d\r
    \r
    %s""" % (ctype,len(content), content) )

        def handle(self,buf):
            for l in buf:
                print(l,end='')

            while len(buf):
                line = buf.pop(0)
                match = ure.search("GET (.*?) HTTP\/1\.1",  str(line) )
                if match:
                    self.request = match.group(1)
                elif line == '\r\n':
                    break
                elif not line:
                    return False


            if match:
                self.parseURL( match.group(1) )

            self.sendContent('<html>Hi</html>')

    RunTime.server_handshake = server_handshake
    RunTime.server_http_handler = HTTP_Handler
#endif
