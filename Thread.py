#!/usr/bin/python

# by tianming 2013-06-26

import threading
import time

class AutoLock:
	def __init__(self, lock):
		self._lock = lock
		self._lock.acquire()
		#print "AutoLock __init__"
		
	def __del__(self):
		self._lock.release()
		#print "AutoLock __del__"
	
#threading is good enought, do not package any more,just give an example
g_int = 0
g_lock = threading.RLock()
class MyTestThread(threading.Thread):
	def __init__(self):	
		threading.Thread.__init__(self)
		
	def run(self):
		global g_int
		while g_int < 10:
			auto_lock = AutoLock(g_lock)
			print "ouput %d for thread %d" %(g_int, threading.current_thread().ident)
			g_int += 1
			print "ready to sleep for %d" %threading.current_thread().ident
			time.sleep(1)
			print "end to sleep for %d" %threading.current_thread().ident
			
#for debug and example
if __name__ == "__main__":
		thread_set = set()
		thread_num = 10
		while thread_num > 0:
			thread_handle = MyTestThread()
			thread_handle.start()
			thread_set.add(thread_handle)
			thread_num -= 1
		for i in thread_set:
			i.join()
else:
		pass
