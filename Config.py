#!/usr/bin/python

#ConfigParser ,maybe we should use this
# by tianming 2013-06-26

class Config:
	def __init__(self, file_path):
		#if self._conf_file == "" and file_path != "":
		self._conf_file = ""
		self._conf_items = {}
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
		except Exception,e:
			print Exception,":",e

	def get_string(self, key, default_value):
		if key in self._conf_items.keys():
			return self._conf_items[key]
		else:
			return default_value
			
	def get_int(self, key, default_value):
		if key in self._conf_items.keys():
			return int(self._conf_items[key])
		else:
			return default_value
			
	def get_conf_items_copy(self):
		return self._conf_items.copy()
			
	#_conf_file = ""
	#_conf_items = {}
	
#for debug and example
if __name__ == '__main__':
    g_config = Config("./server.conf")
    test_value1 = g_config.get_string("test_key1", "err")
    print "test_value1=%s" %test_value1
    test_value2 = g_config.get_int("test_key2", -1)
    print "test_value2=%d" %test_value2
    for key,value in g_config.get_conf_items_copy().items():
    	print "%s=%s" %(key,value)
else:
	pass