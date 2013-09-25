#!/usr/bin/python

# by tianming 2013-06-26

import MySQLdb
import Logger
import Thread
import threading

#used conf keys:
# 	db_pool_size
#   db_host
#		db_user
#		db_pass
#		db_name
#		db_charset

class Mysql:
	def __init__(self, conn, logger = None):
		self._conn = conn
		self._cursor = conn.cursor()
		if logger:
			self._logger = logger
		else:
			self._logger = None
			
	def __del__(self):
		self._cursor.close()
		self._conn.close()
		
	def execute(self, sql):
		try:
			if self._cursor:
				self._cursor.execute(sql)
				return self._cursor.rowcount
			else:
				if self._logger:
					self._logger.error("_cursor not init!!!")
				return -1
		except Exception,e:
			print Exception,":",e
			if self._logger:
				self._logger.error("failed to execute %s" %sql)
	
	def results(self):
		if self._cursor.rowcount > 0:
			return self._cursor.fetchall()
		else:
			return None
	
#singleton
class MysqlPool:
	def __init__(self, conf_items, logger = None):
		auto_lock = Thread.AutoLock(self._lock)
		#if len(self._conf_items) > 0:
		#	pass
		#else:
		
		self._conf_items = {}
		self._lock = threading.RLock()
		self._logger = None
		self._mysql_pool = {}
		self._default_db_pool_size = 5
		self._default_db_host = "localhost"
		self._default_db_user = "root"
		self._default_db_pass = "sd-9898w"
		self._default_db_name = "test"
		self._default_db_charset = "utf8"
		self._IN_USE = 1
		self._NOT_IN_USE = 0
		self._has_init = 0
	
		self._conf_items = conf_items.copy()
		if logger:
			self._logger = logger
		
		#init pool
		if "db_pool_size" in self._conf_items.keys():
			self._default_db_pool_size = int(self._conf_items["db_pool_size"])
			
		if "db_host" in self._conf_items.keys():
			self._default_db_host = self._conf_items["db_host"]
			
		if "db_user" in self._conf_items.keys():
			self._default_db_user = self._conf_items["db_user"]
			
		if "db_pass" in self._conf_items.keys():
			self._default_db_pass = self._conf_items["db_pass"]
			
		if "db_name" in self._conf_items.keys():
			self._default_db_name = self._conf_items["db_name"]
			
		if "db_charset" in self._conf_items.keys():
			self._default_db_charset = self._conf_items["db_charset"]
			
		i = 0
		while i < self._default_db_pool_size:
			try:
				conn = MySQLdb.connect(host='%s' %self._default_db_host, user='%s' %self._default_db_user, passwd='%s' %self._default_db_pass, db='%s' %self._default_db_name, charset='%s' %self._default_db_charset)
				self._mysql_pool[Mysql(conn, self._logger)] = self._NOT_IN_USE
				i += 1
			except Exception,e:
				print Exception,":",e
				if self._logger:
					self._logger.error("failed to connect for host=%s,user=%s,pass=%s,db_name=%s,charset=%s" %(self._default_db_host, self._default_db_user, self._default_db_pass, self._default_db_name, self._default_db_charset))
				break
	
	def __del__(self):
		pass
		
	def get_sql(self, create_when_need = 0):
		auto_lock = Thread.AutoLock(self._lock)
		if len(self._mysql_pool) == 0:
			if self._logger:
				self._logger.error("len(_mysql_pool) == 0,why?")
			return None
			
		for key, value in self._mysql_pool.items():
			if value == self._NOT_IN_USE:
				self._mysql_pool[key] = self._IN_USE
				return key
				
		if create_when_need == 1:
			conn = MySQLdb.connect(self._default_db_host, self._default_db_user, self._default_db_pass, self._default_db_name, self._default_db_charset)
			obj = Mysql(conn, self._logger)
			self._mysql_pool[obj] = self._IN_USE
			return obj
		else:
			return None
			
	def release_sql(self, obj):
		auto_lock = Thread.AutoLock(self._lock)
		if obj in self._mysql_pool.keys():
			self._mysql_pool[obj] = self._NOT_IN_USE
		else:
			pass
		
	'''
	_conf_items = {}
	_lock = threading.RLock()
	_logger = None
	_mysql_pool = {}
	_default_db_pool_size = 5
	_default_db_host = "localhost"
	_default_db_user = "root"
	_default_db_pass = "sd-9898w"
	_default_db_name = "test"
	_default_db_charset = "utf8"
	_IN_USE = 1
	_NOT_IN_USE = 0
	_has_init = 0
	'''
	
#for debug and example
if __name__ == "__main__":
		g_logger = Logger.Logger("./log.conf")
		conf = {"db_pool_size":"5"}
		g_mysqlPool = MysqlPool(conf, g_logger)
		i = 0 
		while i < 11:
			i += 1
			table_name = "test%d" %i
			print "g_mysqlPool.get_sql()..."
			obj = g_mysqlPool.get_sql()
			sql = "drop table if exists %s" %table_name
			line = obj.execute(sql)
			if line >= 0:
				print "succeed to execute %s" %sql
			else:
				print "failed to execute %s" %sql
				exit
			sql = "create table if not exists %s(name varchar(20) not null default '')" %table_name
			line = obj.execute(sql)
			if line >= 0:
				print "succeed to execute %s" %sql
			else:
				print "failed to execute %s" %sql
				exit
			sql = "insert into %s(name) values('tianming1'),('tianming2')" %table_name
			line = obj.execute(sql)
			if line >= 0:
				print "succeed to execute %s" %sql
			else:
				print "failed to execute %s" %sql
				exit
			sql = "select * from %s" %table_name
			line = obj.execute(sql)
			if line >= 0:
				print "succeed to execute %s" %sql
			else:
				print "failed to execute %s" %sql
				exit
			for line in obj.results():
				print '%s' %line
			print "g_mysqlPool.release_sql()..."
			g_mysqlPool.release_sql(obj)
else:
		pass