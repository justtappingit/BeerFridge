#! /usr/bin/python
import sys, traceback
import threading
import socket
import time
from collections import deque
import logging

run  = False
class myServer(threading.Thread):
	

	
	def log(self, line):
        	logline = time.ctime()+" "+line
        	print logline
	        logging.info(logline)

	def __init__(self, logging):
		threading.Thread.__init__(self)
		self.HOST  = "192.168.0.101"
		self.PORT = 6969
		self.BUFFER_SIZE = 1024
		self.runConnections = 1
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.connections = {}
		self.checkConns = True
		self.acceptThread = threading.Thread(target=self.acceptConnections)
		self.connLock = threading.Lock()
		self.commands = deque("") #This is suppose to be a thread safe object
		self.logging = logging
		
	def acceptConnections(self):
		while self.checkConns:
	                conn, addr = self.sock.accept()
        	        conn.setblocking(False)
			self.connLock.acquire()
			self.connections[conn] = addr
			self.connLock.release()
			conn.send("Welcome to the beer fridge!\n")

	def shutdown(self):
		self.log("Telling the sock to shutdown!")

		if len(self.connections.keys()) > 0: #only bother acquiring the lock if there are connections
			self.connLock.acquire()
			for conn in self.connections.keys():
				conn.shutdown(socket.SHUT_RDWR)	
				conn.close()
				del self.connections[conn]
			self.connLock.release()

		self.sock.shutdown(socket.SHUT_RDWR)
		self.sock.close()
		self.checkConns = False

	def sendMessage(self, message):
		if len(self.connections.keys()) > 0: #only bother acquiring the lock if there are connections
			self.connLock.acquire()
			for conn in self.connections.keys():
				conn.send(message+"\n")
			self.connLock.release()


	def run(self):
		self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.sock.bind((self.HOST, self.PORT))
		self.sock.listen(5)
		self.acceptThread.start()
		while self.checkConns:

			if len(self.connections.keys()) == 0:
				time.sleep(1)
				continue
			for conn in self.connections.keys():
	
				try:
					data = conn.recv(self.BUFFER_SIZE)
					
	                                if not data:
        	                                #client has disconnected, remove from the list
                	                        self.log("Closing connections")
                        	                conn.close()
						self.connLock.acquire()
                                	        del self.connections[conn]
						self.connLock.release()
                                        	continue
	                                else:
						d = data.strip()
						self.commands.append(d)
        	                                self.log("recieved "+data.strip())
						

				except socket.error, msg:
					#this just happens when there is nothing to read from the socket... stupid
					pass
if run:
	logging.basicConfig(filename="/home/pi/beer_fridge/logFile.log",level=logging.DEBUG)
	print "logging is a go"		
	serv = myServer(logging)
	try:
	 serv.start()
	 while 1:
		print "Maing loop"
		while len(serv.commands) > 0:
			command = serv.commands.popleft()
			print "Processing command "+command
			serv.sendMessage("Message b")
 		time.sleep(1)
	except:
	 print "Unexpected error: "+str(sys.exc_info()[0])
	 serv.shutdown() 
	 traceback.print_exc(file=sys.stdout)
	
	print "End"


