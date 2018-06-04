#!/usr/bin/python3

import sys
import subprocess
import getopt
import threading
import socket

recv_size = 4096
listen = False
target = ''
port = 0
command = False
upload_destination = ''
execute = ''

def usage():
    sys.exit(0)

def main():
    
    global listen
    global target
    global port
    global command
    global upload_destination
    global execute
    
    if not len(sys.argv[1:]):
        usage()
        
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hlt:p:cu:e:', ['help', 'listen', 'target', 'port', 'command', 'upload_destination', 'execute'])
    except getopt.GetoptError as e:
        print(e)
        sys.exit(0)
        
    for o, a in opts:
        if o in ('-h', '--help'):
            usage()
        elif o in ('-l', '--listen'):
            listen = True
        elif o in ('-t', '--target'):
            target = a
        elif o in ('-p', '--port'):
            port = int(a)
        elif o in ('-c', '--command'):
            command = True
        elif o in ('-u', '--upload'):
            upload_destination = a
        elif o in ('-e', '--execute'):
            execute = a
        else:
            assert False, "[-]Unhandled Option"
            
    if not listen and len(target) and port > 0:
        
        #read input from stdin, end with EOF
        buffer = sys.stdin.read()
        
        client_sender(buffer)
        
    if listen:
        server_loop()
        
def client_sender(buffer):
    global recv_size
    global target
    global port
    

    rfd = open('/dev/tty')
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


    try:
        sock.connect((target, port))
        #sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        
        if buffer:
            sock.send(buffer.encode('utf-8'))
            
        while True:
            recv_len = 4096
            response = ''
            
            while recv_len == recv_size:
                data = sock.recv(recv_size)
                recv_len = len(data)
                response += data.decode('utf-8')
            
            print(response, end='', flush=True)
            
            buffer = rfd.readline()

            if len(buffer) == 0:
                break
            sock.send(buffer.encode('utf-8'))
            
    except BaseException as e:
        print('[-]Exception:', e)
    finally:
        sock.close()
        rfd.close()

            
        
            
def server_loop():
    
    global target
    global port
    
    listenfd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    if not target:
        target = '0.0.0.0'
    
    listenfd.bind((target, port))
    
    listenfd.listen(5)
    
    while True:
        client, addr = listenfd.accept()
        
        client_thread = threading.Thread(target=client_handler, args=(client,))
        client_thread.start()
        
def client_handler(client):
    global upload_destination
    global execute
    global command
    global recv_size
    
    #client.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    
    try:
        if upload_destination:
            file_buffer = b''
            recv_len = recv_size
            while recv_len == recv_size:
         
                data = client.recv(recv_size)
                recv_len = len(data)
                file_buffer += data
            try:
                fd = open(upload_destination,'wb')
                fd.write(file_buffer)
                client.send(b'Successfully saved file to %s\n' % upload_destination)

            except:
                client.send(b'[-]Failed to save file')
                
            finally:
                fd.close()
            
            
        if len(execute):
            output = run_command(execute)
            client.send(output)
        
        if command:

            #clean socket buffer
            try:
                client.recv(recv_size, socket.MSG_DONTWAIT)
            except:
                pass
            

            while True:
                client.send(b'<BHP #> ')
                
                cmd_buffer = ''
                while '\n' not in cmd_buffer:
                    cmd_buffer += client.recv(recv_size).decode('utf-8')
                if len(cmd_buffer) == 1:
                    continue
                response = run_command(cmd_buffer)
                client.send(response)

    except BaseException as e:
        print(e)

def run_command(cmd):
    try:
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
    except:
        output = b'[-]Falied to execute cmd\n'

    return output

main()
