#!/usr/bin/python
# coding: utf-8

# by tianming 2013-06-27

import Logger

import struct	
import binascii
import traceback

'''
实现思路：
1. 设置协议包含的字段信息（字段类型/数组类型）
2. 传入数值进行编码（list结构）
3. 传入buffer进行解码

说明：
1. struct是按指定格式编解码的，fmt的第一个字符表示编码格式
			@: native order, size & alignment (default)
      =: native order, std. size & alignment
      <: little-endian, std. size & alignment
      >: big-endian, std. size & alignment
      !: same as >

2. fields格式说明：
			c:char; b:signed byte; B:unsigned byte;
			h:short; H:unsigned short;
			i:int; I:unsigned int;
			l:long; L:unsigned long;
			f:float; d:double.
			s:string (array of char);
			q:long long; Q:unsigned long long
			
			fields包含多个字段，每个单一的字段以tuple的格式表示，比如('cmd_id','I')，其中第一个是字段描述信息，第二个是字段类型；
					描述信息必须唯一，方便按描述信息进行自动解码；
					整体以list的方式作为参数传入，比如[('desc1','I'),('desc2','H'),('desc3','s'),[('desc4','I'), ('desc5','H')]]；
					如果fields中的字段是list类型，则认为该字段表示数组类型（可以有多个值），比如上面的第4个字段
			
			自定义几个字段：
			IT(Total size) -- 即整个包的长度，本身为一个unsigned int，只允许出现一次
			HT(Total size) -- 即整个包的长度，本身为一个unsigned short，只允许出现一次
			IA(After size) -- 该字段后面所有数据的长度， 本身为一个unsigned int ，只允许出现一次
			HA(After size) -- 该字段后面所有数据的长度， 本身为一个unsigned short，只允许出现一次
			
3. values格式说明：
			values和fields的顺序一致,比如对应上面的fields，我们可以设置values：
			[100,123,'str',[[124,100],[124,121],[12121,1212]]]
			
			对于自定义的字段，直接赋值 -1，处理时会忽略该传入值，自行计算填充
'''

class ProtocolHandle:
	def __init__(self, code_mode = '!', logger = None):
		self._code_mode = code_mode
		self._fmt = []
		self._params = []
		self._decode_list = []
		self._need_encode_self_field = False
		self._logger = logger
		self._fields = None
		
	def __del__(self):
		pass
		
	def set_field(self, fields):
		self._fields = fields
		if len(self._fields) == 0:
			raise "invalid fields"
			
	#################################################################encode##############################################################
	#private function
	def __encode_array(self, field_item, value_item):
		#to set array len
		self._fmt.append("I")
		self._params.append(",%d" %len(value_item))
		for value in value_item:
			if len(field_item) != len(value):
				print field_item
				print value
				raise "value len doesn't match field item len!!!"
			index = 0
			while index < len(field_item):
				self.__encode_item(field_item[index], value[index])
				index += 1
			
	#private function
	def __encode_string(self, field_item, value_item):
		if self._logger:
			self._logger.info("__encode_string,len=%d" %len(value_item));
		#to set string len and %ds
		len_str = len(value_item)
		self._fmt.append("I%ds" % len_str)
		temp_hex_str = binascii.b2a_hex(value_item)
		self._params.append(" ,%d, binascii.a2b_hex('%s')" %(len_str, temp_hex_str))
		
	#private function
	def __encode_base_type(self, field_item, value_item):
		self._fmt.append(field_item[1])
		self._params.append(" ,%s" %value_item)
		
	#private function,to set self define flag
	def __set_self_field_flag(self, field_item, value_item):
		if field_item[1] == 'IT' or field_item[1] == 'IA':
			self._fmt.append("I")
		else:
			self._fmt.append("H")
		self._params.append("%s" %field_item[1])
		
	#private function,to deal self define fields, such as IT/HT/IA/HA
	def __encode_self_fields(self):
		index = 0
		len_params = len(self._params)
		while index < len_params:
			if self._params[index] == 'IT' or self._params[index] == 'HT':
				temp_fmt = self._fmt[:]
				temp_fmt.insert(0, self._code_mode)
				total_len = struct.calcsize("".join(temp_fmt))
				self._params[index] = " ,%d" %total_len
			elif self._params[index] == 'IA' or self._params[index] == 'HA':
				if index == len_params - 1:
					raise "error!found IA or HA in the last fields!!!"
				temp_fmt = self._fmt[index+1:]
				temp_fmt.insert(0, self._code_mode)
				total_len = struct.calcsize("".join(temp_fmt))
				self._params[index] = " ,%d" %total_len
			index += 1
			
	#private function
	def __encode_item(self, field_item, value_item):
		if isinstance(field_item, list):
			self.__encode_array(field_item, value_item)
		elif field_item[1] == 's':
			self.__encode_string(field_item, value_item)
		elif field_item[1] == 'IT' or field_item[1] == 'HT' or field_item[1] == 'IA' or field_item[1] == 'HA':
			self._need_encode_self_field = True
			self.__set_self_field_flag(field_item, value_item)
		else:
			self.__encode_base_type(field_item, value_item)
		
	def encode(self, values):
		try:
			if not isinstance(values, list):
				raise "invalid protocol, need list here"
			len_fields = len(self._fields)
			len_values = len(values)
			if len_fields != len_values:
				raise "value len not match fields len,please check it"
				
			del self._fmt[:]
			del self._params[:]
			
			index = 0
			while index < len_fields:
				self.__encode_item(self._fields[index], values[index])
				index += 1
			
			if self._need_encode_self_field:
				self.__encode_self_fields()
			
			if len("".join(self._fmt)) < ProtocolHandle.MAX_FMT_LEN:
				#add first code
				self._fmt.insert(0, self._code_mode)
				#get rid of first ','
				self._params[0] = self._params[0].replace(',' , '')
				pack_cmd_str = "struct.pack('%s', %s)" %("".join(self._fmt), "".join(self._params))
				if self._logger:
					self._logger.info("ready to execut struct cmd=%s" %pack_cmd_str)
				data = eval(pack_cmd_str)
				return data
			else:
				data_list = []
				while len(self._fmt) > 0:
					end_index = 1
					while end_index <= len(self._fmt):
						if len("".join(self._fmt[0:end_index])) < ProtocolHandle.MAX_FMT_LEN:
							end_index += 1
						else:
							end_index -= 1
							break

					self._fmt.insert(0, self._code_mode)
					#self._params[0] = self._params[0].replace(',' , '')
					pack_cmd_str = "struct.pack('%s' %s)" %("".join(self._fmt[0:end_index+1]), "".join(self._params[0:end_index]))
					if self._logger:
						self._logger.info("ready to execut struct cmd=%s" %pack_cmd_str)
					data_list.append(eval(pack_cmd_str))
					del self._fmt[0:end_index+1]
					del self._params[0:end_index]
					
				return "".join(data_list)
					
		except Exception,e:
			if self._logger:
				self._logger.warn("%s:%s\n %s" %(Exception, e, traceback.format_exc()))
			return None
		
	#################################################################decode##############################################################
	#private function
	def __decode_array(self, field_item, data, offset, inout_list):
		try:
			#to get array len
			fmt = self._code_mode + "I"
			fmt_len = struct.calcsize(fmt)
			size = struct.unpack(fmt, data[offset:offset+fmt_len])
			offset += fmt_len
			#print "array size=%d" %size[0]
			
			index = 0
			while index < size[0]:
				temp_list = []
				for field in field_item:
					offset = self.__decode_item(field, data, offset, temp_list)
				inout_list.append(temp_list)
				index += 1
			return offset
		except Exception,e:
			raise
			
	#private function
	def __decode_string(self, field_item, data, offset, inout_list):
		try:
			if self._logger:
				self._logger.info("ready to __decode_string for field_item=%s" %("".join(field_item)))
				
			fmt = self._code_mode + "I"
			fmt_len = struct.calcsize(fmt)
			size = struct.unpack(fmt, data[offset:offset+fmt_len])
			offset += fmt_len
			
			fmt = self._code_mode + ("%ds" %size[0])
			fmt_len = struct.calcsize(fmt)
			inout_list.append(struct.unpack(fmt, data[offset:offset+fmt_len])[0])
			offset += fmt_len
			
			if self._logger:
				self._logger.info("succeed to __decode_string for field_item=%s" %("".join(field_item)))
				
			return offset
		except Exception,e:
			if self._logger:
				self._logger.warn("failed to __decode_string for field_item=%s" %("".join(field_item)))
			raise
		
	#private function
	def __decode_base_type(self, field_item, data, offset, inout_list):
		try:
			if self._logger:
				self._logger.info("ready to __decode_base_type for field_item=%s" %("".join(field_item)))
				
			fmt = self._code_mode + field_item[1]
			fmt_len = struct.calcsize(fmt) 
			inout_list.append(struct.unpack(fmt, data[offset:offset+fmt_len])[0])
			offset += fmt_len
			
			if self._logger:
				self._logger.info("succeed to __decode_base_type for field_item=%s,value=%s" %("".join(field_item), inout_list[-1]))
	
			return offset
		except Exception,e:
			if self._logger:
				self._logger.warn("failed to __decode_base_type for field_item=%s" %("".join(field_item)))
			raise
		
	#private function,to set self define flag
	def __decode_self_fields(self, field_item, data, offset, inout_list):
		try:
			if self._logger:
				self._logger.info("ready to __decode_self_fields for field_item=%s" %("".join(field_item)))
				
			fmt = self._code_mode + "I"
			if field_item[1] == 'HT' or field_item[1] == 'HA':
				fmt = self._code_mode + "H"
			fmt_len = struct.calcsize(fmt)
			inout_list.append(struct.unpack(fmt, data[offset:offset+fmt_len])[0])
			offset += fmt_len
	
			return offset
		except Exception,e:
			if self._logger:
				self._logger.warn("failed to __decode_self_fields for field_item=%s" %("".join(field_item)))
			raise

	#private function
	def __decode_item(self, field_item, data, offset, inout_list):
		try:
			new_offset = 0
			if isinstance(field_item, list):
				temp_list = []
				new_offset = self.__decode_array(field_item, data, offset, temp_list)
				inout_list.append(temp_list)
			elif field_item[1] == 's':
				new_offset = self.__decode_string(field_item, data, offset, inout_list)
			elif field_item[1] == 'IT' or field_item[1] == 'HT' or field_item[1] == 'IA' or field_item[1] == 'HA':
				new_offset = self.__decode_self_fields(field_item, data, offset, inout_list)
			else:
				new_offset = self.__decode_base_type(field_item, data, offset, inout_list)
			return new_offset
		except Exception,e:
			raise
		
	def decode(self, data):
		try:
			if self._logger:
				self._logger.info("ready to decode now,len(self._fields)=%d" %len(self._fields))
				
			offset = 0
			del self._decode_list[:]
			for field in self._fields:
				offset = self.__decode_item(field, data, offset, self._decode_list)
			
			return self._decode_list
		except Exception,e:
			if self._logger:
				self._logger.info("failed to decode %s:%s" %(Exception,e))
			return None
	
	#################################################################get_value##############################################################
	#private function
	def __get_value_item(self, field_desc, field_item, value_item, inout_list):
		if isinstance(field_item, list):
			if not isinstance(value_item, list):
				raise "not match value_list"
			else:
				for value in value_item:
					num = len(field_item)
					index = 0
					while index < num:
						self.__get_value_item(field_desc, field_item[index], value[index], inout_list)
						index += 1
		else:
			if field_desc == field_item[0]:
				inout_list.append(value_item)
				
	def get_value(self, field_desc, value_list):
		temp_list = []
		num = len(self._fields)
		index = 0
		while index < num:
			self.__get_value_item(field_desc, self._fields[index], value_list[index], temp_list)
			index += 1
		if len(temp_list) > 0:
			return temp_list
		else:
			return None
			
	#private function
	def __get_all_value_item(self, field_item, value_item, inout_map):
		if isinstance(field_item, list):
			if not isinstance(value_item, list):
				raise "not match value_list"
			else:
				for value in value_item:
					num = len(field_item)
					index = 0
					while index < num:
						self.__get_all_value_item(field_item[index], value[index], inout_map)
						index += 1
		else:
			if field_item[0] not in inout_map.keys():
				temp_list = []
				temp_list.append(value_item)
				inout_map[field_item[0]] = temp_list
			else:
				inout_map[field_item[0]].append(value_item)
			
	def get_all_values(self, value_list, inout_map):
		num = len(self._fields)
		index = 0
		while index < num:
			self.__get_all_value_item(self._fields[index], value_list[index], inout_map)
			index += 1
		if len(inout_map) > 0:
			return len(inout_map)
			
	MAX_FMT_LEN = 200

#for debug and example
if __name__ == "__main__":
		g_logger = Logger.Logger("./log.conf")
		handle = ProtocolHandle('!', g_logger)
		protocol_fields = [('total size','IT'),('version','I'),('magic num','I'),('timestamp','I'),('body_len','IA'),('cmd_id', 'I'),[('GCID','s'),('cid','s'),('filesize','Q')]]
		handle.set_field(protocol_fields)
		protocl_values = [-1,0,123456,23123123,-1,100,[['gcid_1','cid_1',100],['gcid_2','cid_2',200],['gcid_3','cid_3',300]]]
		data = handle.encode(protocl_values)
		print data," and len(data)=%d" %len(data)
		decode_list = handle.decode(data)
		if decode_list:
			for item in decode_list:
				print item
			value_list = handle.get_value("GCID", decode_list)
			print "values for GCID=", value_list
			value_list = handle.get_value("cid", decode_list)
			print "values for cid=", value_list
			value_list = handle.get_value("filesize", decode_list)
			print "values for filesize=", value_list
			value_list = handle.get_value("version", decode_list)
			print "version=", value_list
			value_list = handle.get_value("cmd_id", decode_list)
			print "cmd_id=", value_list
			test_map = {}
			if handle.get_all_values(decode_list, test_map) > 0:
				print test_map
				
		#test big data
		protocol_fields = [[('GCID','s')]]
		handle.set_field(protocol_fields)
		protocl_values = [[['3CF68F188C0C5DA5486D16756182279755751840']]*401]
		data = handle.encode(protocl_values)
		print binascii.b2a_hex(data)
else:
		pass