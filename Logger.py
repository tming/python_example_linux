#!/usr/bin/python
# coding: utf-8

# by tianming 2013-06-26

import sys
import time
import logging
import os

# switch:
# 		rootLogger=OFF/ON
# log level:
# 		logging.CRITICAL
# 		logging.ERROR
# 		logging.WARNING
# 		logging.INFO
# 		logging.DEBUG
#			logging.NOTSET      

# log function:
#			logger.critical("")
#			logger.error("")
#			logger.warn("")
#			logger.info("")
#			logger.debug("")

class Logger:
	def __init__(self, file_path):
		#if self._conf_file == "" and file_path != "":
		#	self.__load_config(file_path)
		self._conf_file = ""
		self._conf_items = {}
		self._logger = None
		self._default_path = "./log"
		self._default_name = "python_log"
		self._default_level = logging.DEBUG
		self._default_format = "%(asctime)s %(levelno)d %(filename)32s:%(lineno)04d >>>> %(message)s"
		self._default_mode = "ON"
		self.__load_config(file_path)
	
	#private function
	def __load_config(self, file_path):
		self._conf_file = file_path
		try:
			f = open(self._conf_file, "rb")
			for i in f.readlines():
				i1 = i.lstrip().rstrip()
				if i1 == "" or i1[0] == '#':
					continue
				info = i.split("=")
				if len(info) == 2:
					self._conf_items[info[0].lstrip().rstrip()] = info[1].lstrip().rstrip()
			f.close()
			
			self.__init_logger()
			
		except Exception,e:
			print Exception,":",e
	
	#private function
	def __init_logger(self):
		try:
			if "rootLogger" in self._conf_items.keys():
				self._default_mode = self._conf_items["rootLogger"]
				
			if self._default_mode == "OFF":
				return
				 
			if "log_level" in self._conf_items.keys():
				self._default_level = eval(self._conf_items["log_level"])
				
			if "log_format" in self._conf_items.keys():
				self._default_format = self._conf_items["log_format"]
				
			if "log_name" in self._conf_items.keys():
				self._default_name = "%d_%s" %(os.getpid(),self._conf_items["log_name"])
			else:
				self._default_name = "%d" %(os.getpid())
				
			if "log_path" in self._conf_items.keys():
				self._default_path = self._conf_items["log_path"]
				
			self._logger = logging.getLogger("%s.%s" % (self._default_name, time.time()))
			self._logger.setLevel(self._default_level)

			file_path = "%s/%s.log" % (self._default_path, self._default_name)
			file_handler = logging.FileHandler(file_path, "wb", "utf-8")
			file_handler.setLevel(self._default_level)
			file_handler.setFormatter(logging.Formatter(self._default_format))
			self._logger.addHandler(file_handler)

		except Exception, e:
			print Exception,":",e
			
	def critical(self, msg):
		if self._logger:
			return self._logger.critical(msg)
		
	def error(self, msg):
		if self._logger:
			return self._logger.error(msg)
		
	def warn(self, msg):
		if self._logger:
			return self._logger.warn(msg)
		
	def info(self, msg):
		if self._logger:
			return self._logger.info(msg)
		
	def debug(self, msg):
		if self._logger:
			return self._logger.debug(msg)

	'''
	_conf_file = ""
	_conf_items = {}
	_logger = None
	_default_path = "./log"
	_default_name = "python_log"
	_default_level = logging.DEBUG
	_default_format = "%(asctime)s %(levelno)d %(filename)32s:%(lineno)04d >>>> %(message)s"
	_default_mode = "ON"
	'''

#for debug and example
if __name__ == "__main__":
		g_logger = Logger("./log.conf")
		g_logger.critical("this is one test critical message");
		g_logger.error("this is one test error message");
		g_logger.warn("this is one test warn message");
		g_logger.info("this is one test info message");
		g_logger.debug("this is one test debug message");
else:
		pass