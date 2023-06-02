"""
MIT License

Copyright (c) 2023 NOTMEE12

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import socket
import random
import json


class SocketWrapper:
	
	def __init__(self):
		"""
		Creates instance of SocketWrapper.
		SocketWrapper is used for sending and receiving packets, joining and hosting.
		"""
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.is_client = False
		self.hosting = False
		self.clients = []
		self.ids = []
	
	def end_hosting(self):
		"""stop hosting"""
		self.sock.close()
		self.hosting = False
	
	def send(self, packet):
		"""
		sends packet to all clients
		:param packet:
		"""
		if self.is_client:
			self.sock.sendall(bytes(packet))
		elif self.hosting:
			for client, id in self.clients.copy():
				try:
					client.send(bytes(packet))
				except ConnectionResetError | OSError:
					self.clients.remove({client, id})
					self.ids.remove(id)
	
	@staticmethod
	def send_to(conn, packet):
		"""this function is raw, so it doesn't handle when someone exits (it will still send data and it can raise an error), so BE CAREFUL"""
		conn.send(bytes(packet))
	
	def host(self, port):
		"""
		host at port
		:param port: it will host at that port
		:return: (True, hostname) or Error
		"""
		self.sock.bind((socket.gethostbyname(socket.gethostname()), port))
		self.sock.listen(15)
		print("Server listening on 0.0.0.0; 40_000")
		print("Server Host Name: ", socket.gethostname())
		self.hosting = True
		return True, socket.gethostname()
	
	def listen(self):
		"""
		listens for new connections
		**WARNING:** it will halt the execution of the program. It is best to run it threaded.
		"""
		conn, addr = self.sock.accept()
		id = random.random()
		while id in self.ids:
			id = random.random()
		self.clients.append((conn, id))
		self.ids.append(id)
		return conn, addr
	
	def connect_to_server(self, hostname):
		"""
		connects to server
		:param hostname: hostname that is returned by host method
		:return: True if connection is successful else False
		"""
		socket.setdefaulttimeout(5)
		try:
			e = socket.getaddrinfo(hostname, 40_000, 5)
		except (socket.gaierror, OSError, TimeoutError) as err:
			self.is_client = False
			return False
		try:
			self.sock.connect((e, 40_000))
			self.is_client = True
		except (ConnectionRefusedError, socket.gaierror) as err:
			self.is_client = False
			return False
		return True
	
	@staticmethod
	def receive_data(conn):
		"""
		receives data from connection (give it)
		:yield: PacketType, Json
		"""
		for line in conn.recv(16737).decode("utf-8").replace('\'', '\"').replace('(', '[').replace(')', ']') \
				            .split("\n")[:-1]:
			try:
				json_data = json.loads(line)
				yield json_data['PT'], json_data
			except json.JSONDecodeError:
				pass


class Packet:
	
	def __init__(self, datatype, data):
		"""Creates new packet
		:param datatype
		"""
		self.type = datatype
		self.dat = data
	
	def __bytes__(self):
		self.dat['PT'] = self.type  # SET PACKET TYPE
		return bytes(json.dumps(self.dat).encode("utf-8") + "\n".encode("utf-8"))