#!/usr/bin/python

# by tianming 2013-06-26

import Logger
import socket, select

class Event_handle_obj:
	def __init__(self, socket_obj, epoll_obj):
		self._socket_obj = socket_obj
		self._epoll_obj = epoll_obj
		
	def __del__(self):
		self._socket_obj.close()
		
	def on_readable(self, fd):
		raise "this is an abstract function"
		
	def on_writable(self, fd):
		raise "this is an abstract function"
		
	def on_error(self, fd):
		raise "this is an abstract function"
		
	def on_timer(self, fd):
		pass
		
'''
    EPOLLERR = 8
    EPOLLET = -2147483648
    EPOLLHUP = 16
    EPOLLIN = 1
    EPOLLMSG = 1024
    EPOLLONESHOT = 1073741824
    EPOLLOUT = 4
    EPOLLPRI = 2
    EPOLLRDBAND = 128
    EPOLLRDNORM = 64
    EPOLLWRBAND = 512
    EPOLLWRNORM = 256
'''

class Epoll_svr:
	def __init__(self, wait_timeout_secs = 1, logger = None):
		self._epoll = select.epoll()
		self._handles = {}
		self._time_out_secs = wait_timeout_secs
		self._logger = logger
		self._should_stop = False

	def __del__(self):
		self._epoll.close()
		self._handles.clear()
		self._should_stop = True

	def add_event(self, fd, event, event_obj):
		if fd > 0 and event&(select.EPOLLIN|select.EPOLLOUT) and event_obj:
			try:
				self._epoll.register(fd, event|select.EPOLLET)  #register with ET mode
			except Exception, e:
				print Exception,":",e
			self._handles[fd] = event_obj
		else:
			raise "invalid parameter for add_event"

	def del_event(self, fd, event):
		self._epoll.unregister(fd)
		del self._handles[fd]

	def modify_event(self, fd, event):
		if fd > 0 and event&(select.EPOLLIN|select.EPOLLOUT):
			if self._handles[fd]:
				self._epoll.modify(fd, event)
			else:
				if self._logger:
					self._logger.error("_handles[%d] not existed!!!" %fd)
		else:
				if self._logger:
					self._logger.error("invalid parameter for modify_event!!!")

	def run_loop(self):
		while not self._should_stop:
			event_list = self._epoll.poll(self._time_out_secs)
			for fd, event in event_list:
				if event & select.EPOLLIN:
					if fd in self._handles.keys() and self._handles[fd]:
						self._handles[fd].on_readable(fd)
					else:
						if self._logger:
							self._logger.error("event obj not existed when %d readable!!!" %fd)
				if event & select.EPOLLOUT:
					if fd in self._handles.keys() and self._handles[fd]:
						self._handles[fd].on_writable(fd)
					else:
						if self._logger:
							self._logger.error("event obj not existed when %d writable!!!" %fd)
				if event & (select.EPOLLHUP|select.EPOLLERR):
					if fd in self._handles.keys() and self._handles[fd]:
						self._handles[fd].on_error(fd)
					else:
						if self._logger:
							self._logger.error("event obj not existed when %d error!!!" %fd)			

	def stop_loop(self):
		self._should_stop = True

	#class property
	READ_EVENT = select.EPOLLIN
	WRITE_EVENT = select.EPOLLOUT







#for debug and example,this is an echo server
class Test_session_handle_obj(Event_handle_obj):
	def __init__(self, socket_obj, epoll_obj, logger):
		Event_handle_obj.__init__(self, socket_obj, epoll_obj)
		self._logger = logger
		self._data = b""
		
	def __del__(self):
		Event_handle_obj.__del__(self)
		
	def on_readable(self, fd):
		while True:
			temp_data = self._socket_obj.recv(1024)
			if len(temp_data) == 0:
				break
			else:
				self._data += temp_data
				if len(temp_data) < 1024:
					break
		if len(self._data) > 0:
			self.on_writable(fd)
		
	def on_writable(self, fd):
		if len(self._data) > 0:
			send_len = self._socket_obj.send(self._data)
			self._data = self._data[send_len:]
		
	def on_error(self, fd):
		self._socket_obj.close()
		self._epoll_obj.del_event(fd, Epoll_svr.READ_EVENT|Epoll_svr.WRITE_EVENT)
		
	def on_timer(self, fd):
		pass
		
class Test_server_handle_obj(Event_handle_obj):
	def __init__(self, socket_obj, epoll_obj, logger):
		Event_handle_obj.__init__(self, socket_obj, epoll_obj)
		self._logger = logger
		
	def __del__(self):
		Event_handle_obj.__del__(self)
		
	def on_readable(self, fd):
		while True:
			try:
				socket_obj,address_info = self._socket_obj.accept()
				if socket_obj:
					socket_obj.setblocking(0)
					self._epoll_obj.add_event(socket_obj.fileno(), Epoll_svr.READ_EVENT|Epoll_svr.WRITE_EVENT, Test_session_handle_obj(socket_obj, self._epoll_obj, self._logger) )
				else:
					break
			except Exception, e:
				print Exception,":",e
				break
		
	def on_writable(self, fd):
		pass
		
	def on_error(self, fd):
		self._socket_obj.close()
		self._epoll_obj.del_event(fd, Epoll_svr.READ_EVENT|Epoll_svr.WRITE_EVENT)
		
	def on_timer(self, fd):
		pass

if __name__ == "__main__":
		g_logger = Logger.Logger("./log.conf")
		
		svr_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		svr_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		svr_socket.bind(('127.0.0.1', 12345))
		svr_socket.listen(1)
		svr_socket.setblocking(0)
		
		test_Epoll_svr = Epoll_svr(1, g_logger)
		test_Epoll_svr.add_event(svr_socket.fileno(), Epoll_svr.READ_EVENT, Test_server_handle_obj(svr_socket, test_Epoll_svr, g_logger))
		test_Epoll_svr.run_loop()
		
else:
		pass
