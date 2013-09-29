#!/usr/bin/python
# coding: utf-8

# by tianming 2013-07-02

import socket
import os
import urllib
import distutils.dir_util
import distutils.file_util
import re
import commands
import sha
import traceback

from Codec import *
import Logger

class Utility:
	#static function
	@staticmethod
	def get_local_ip():
		try:
			names,aliases,ips = socket.gethostbyname_ex(socket.gethostname())
			for ip in ips:
				if not re.match('^192.', ip) and not re.match('^10.', ip) and not re.match('^172.', ip) and not re.match('^127.', ip):
					return ip
			return "127.0.0.1"
		except:
			return "127.0.0.1"

	@staticmethod
	def get_pid():
		return os.getpid()

	@staticmethod
	def set_working_dir(path):
		if path.startswith("/"):
			os.chdir(path)
			return True
		elif path.startswith("./") or path.startswith("../") :
			os.chdir(os.path.dirname(os.path.abspath(path)))
			return True
		else:
			return False

	@staticmethod
	def setenv(key, value):
		 os.environ[key] = value

	@staticmethod
	def unsetenv(key):
		 del os.environ[key]

	@staticmethod
	def recv_all(sock):
		data = ""
		while True:
			temp_data = sock.recv(1024)
			if len(temp_data) == 0:
				break
			else:
				print "received %d data" %len(temp_data)
				data += temp_data
				if len(temp_data) < 1024:
					break
		if len(data) > 0:
			return data
		else:
			return None
	
	@staticmethod
	def url_encode(url):
		return urllib.quote(url, ":?=/@")
		
	@staticmethod
	def rm(path):
		try:
			if os.path.isfile(path):
				os.remove(path)
				return True
			elif os.path.isdir(path):
				distutils.dir_util.remove_tree(path)
				return True
		except:
			return False
		
	@staticmethod
	def mkdir(path):
		if os.path.exists(path):
			return True
		try:
			distutils.dir_util.mkpath(path)
			return True
		except:
			return False
			
	@staticmethod
	def relate(from_path, to_path):
		try:
			os.link(from_path, to_path)
			return True
		except:
			pass

		try:
			os.symlink(from_path, to_path)
			return True
		except:
			pass

		return bool(distutils.file_util.copy_file(from_path, to_path)[1])
			
	#to get cmd return code and output info
	@staticmethod
	def getstatusoutput(cmd):
		return commands.getstatusoutput(cmd)
	
	@staticmethod
	def get_dir(path):
		return os.path.split(path)[0]

	@staticmethod
	def get_filename(path):
		return os.path.split(path)[1]

	@staticmethod
	def get_basename(path):
		return os.path.splitext(path)[0]
    
	@staticmethod
	def get_suffix(path):
		return os.path.splitext(path)[1]
		
	@staticmethod
	def get_prefix(path):
		return get_filename(get_basename(path))

	@staticmethod
	def random_read_data(fd, position, length):
		fd.seek(position, 0)
		return fd.read(length)
		
	@staticmethod
	def send_and_recv(ip, port, req_fields, req_value, resp_fields, code_mode = '!', logger = None):
		decode_list = None
		try:
			temp_socket = None
			try:
				#encode protocol data
				handle = ProtocolHandle(code_mode, logger)
				handle.set_field(req_fields)
				data = handle.encode(req_value)
				
				temp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				
				#connect
				if logger:
					logger.debug("ready to connect to %s:%d" %(ip,port))
				temp_socket.connect((ip, port))
				
				#send
				if logger:
					logger.debug("ready to send %d data" %len(data))
				temp_socket.sendall(data)
				if logger:
					logger.debug("finished to send %d data" %len(data))
				
				#recv
				if logger:
					logger.debug("ready to recv data")
				data = Utility.recv_all(temp_socket)
				if logger and data:
					logger.debug("received %d data" %len(data))
				
				#decode protocol data
				if data:
					handle.set_field(resp_fields)
					decode_list = handle.decode(data)
					logger.debug("%s" %decode_list)
					if decode_list:
						return decode_list
					else:
						if logger:
							logger.warn("failed to decode")
				else:
					if logger:
						logger.warn("failed to received data")
				
			finally:
				if temp_socket:
					temp_socket.close()
			
			return decode_list
			
		except Exception,e:
			#print Exception,":",e
			if logger:
				logger.warn("%s:%s\n %s" %(Exception, e, traceback.format_exc()))
			return decode_list
			
	@staticmethod
	def send_and_recv_no_decode(ip, port, req_fields, req_value, code_mode = '!', logger = None):
		try:
			temp_socket = None
			try:
				#encode protocol data
				handle = ProtocolHandle(code_mode, logger)
				handle.set_field(req_fields)
				data = handle.encode(req_value)
				
				logger.info("ready to send hex_data=%s" %(binascii.b2a_hex(data)))
				
				temp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				
				#connect
				if logger:
					logger.debug("ready to connect to %s:%d" %(ip,port))
				temp_socket.connect((ip, port))
				
				#send
				if logger:
					logger.debug("ready to send %d data" %len(data))
				temp_socket.sendall(data)
				if logger:
					logger.debug("finished to send %d data" %len(data))
				
				#recv
				if logger:
					logger.debug("ready to recv data")
				data = Utility.recv_all(temp_socket)
				if logger:
					logger.debug("received %d data" %len(data))
				
				#decode protocol data
				if data:
					return data
				else:
					if logger:
						logger.warn("failed to received data")
					return None
					
			finally:
				if temp_socket:
					temp_socket.close()
			
		except Exception,e:
			if logger:
				logger.warn("%s:%s\n %s" %(Exception, e, traceback.format_exc()))
			return None

	@staticmethod
	def getsize(full_path):
		return os.path.getsize(full_path)
		
	# 编码转换
	@staticmethod
	def convert_codec(data, from_codec, to_codec):
		try:
			return data.decode(from_codec).encode(to_codec)
		except:
			return None
	
	@staticmethod
	def convert_file_codec(fd, from_codec, to_codec):
		try:
			if not os.path.isfile(fd):
				return False
			origin_file = "%s.origin" % fd
			Utility.rm(origin_file)
			Utility.relate(fd, origin_file)
			data = Utility.convert_codec(open(origin_file, "r").read(), from_codec, to_codec)
			if data == None:
				return False
			open(fd, "w").write(data)
			return True
		except:
			return False
			
	@staticmethod
	def get_crc8(data, data_len):
		if data_len != len(data):
			return None
		else:
			crc8 = 0
			for ch in data:
				#print "index=%d" %(crc8^int(data[i]))
				crc8 = Utility.CRC8_TAB[crc8^ord(ch)]
			return crc8

	CRC8_TAB = [
			0x00, 0x5e, 0xbc, 0xe2, 0x61, 0x3f, 0xdd, 0x83, 
			0xc2, 0x9c, 0x7e, 0x20, 0xa3, 0xfd, 0x1f, 0x41, 
			0x9d, 0xc3, 0x21, 0x7f, 0xfc, 0xa2, 0x40, 0x1e, 
			0x5f, 0x01, 0xe3, 0xbd, 0x3e, 0x60, 0x82, 0xdc, 
			0x23, 0x7d, 0x9f, 0xc1, 0x42, 0x1c, 0xfe, 0xa0, 
			0xe1, 0xbf, 0x5d, 0x03, 0x80, 0xde, 0x3c, 0x62, 
			0xbe, 0xe0, 0x02, 0x5c, 0xdf, 0x81, 0x63, 0x3d, 
			0x7c, 0x22, 0xc0, 0x9e, 0x1d, 0x43, 0xa1, 0xff, 
			0x46, 0x18, 0xfa, 0xa4, 0x27, 0x79, 0x9b, 0xc5, 
			0x84, 0xda, 0x38, 0x66, 0xe5, 0xbb, 0x59, 0x07, 
			0xdb, 0x85, 0x67, 0x39, 0xba, 0xe4, 0x06, 0x58, 
			0x19, 0x47, 0xa5, 0xfb, 0x78, 0x26, 0xc4, 0x9a, 
			0x65, 0x3b, 0xd9, 0x87, 0x04, 0x5a, 0xb8, 0xe6, 
			0xa7, 0xf9, 0x1b, 0x45, 0xc6, 0x98, 0x7a, 0x24, 
			0xf8, 0xa6, 0x44, 0x1a, 0x99, 0xc7, 0x25, 0x7b, 
			0x3a, 0x64, 0x86, 0xd8, 0x5b, 0x05, 0xe7, 0xb9, 
			0x8c, 0xd2, 0x30, 0x6e, 0xed, 0xb3, 0x51, 0x0f, 
			0x4e, 0x10, 0xf2, 0xac, 0x2f, 0x71, 0x93, 0xcd, 
			0x11, 0x4f, 0xad, 0xf3, 0x70, 0x2e, 0xcc, 0x92, 
			0xd3, 0x8d, 0x6f, 0x31, 0xb2, 0xec, 0x0e, 0x50, 
			0xaf, 0xf1, 0x13, 0x4d, 0xce, 0x90, 0x72, 0x2c, 
			0x6d, 0x33, 0xd1, 0x8f, 0x0c, 0x52, 0xb0, 0xee, 
			0x32, 0x6c, 0x8e, 0xd0, 0x53, 0x0d, 0xef, 0xb1, 
			0xf0, 0xae, 0x4c, 0x12, 0x91, 0xcf, 0x2d, 0x73, 
			0xca, 0x94, 0x76, 0x28, 0xab, 0xf5, 0x17, 0x49, 
			0x08, 0x56, 0xb4, 0xea, 0x69, 0x37, 0xd5, 0x8b, 
			0x57, 0x09, 0xeb, 0xb5, 0x36, 0x68, 0x8a, 0xd4, 
			0x95, 0xcb, 0x29, 0x77, 0xf4, 0xaa, 0x48, 0x16, 
			0xe9, 0xb7, 0x55, 0x0b, 0x88, 0xd6, 0x34, 0x6a, 
			0x2b, 0x75, 0x97, 0xc9, 0x4a, 0x14, 0xf6, 0xa8, 
			0x74, 0x2a, 0xc8, 0x96, 0x15, 0x4b, 0xa9, 0xf7, 
			0xb6, 0xe8, 0x0a, 0x54, 0xd7, 0x89, 0x6b, 0x35 
		]

#for debug and example
if __name__ == "__main__":
	test_data = binascii.a2b_hex('0123456789')
	print Utility.get_crc8(test_data, len(test_data))
else:
	pass






