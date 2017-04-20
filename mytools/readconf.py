#!/usr/bin/env python

import os, sys
# import subprocess
# import random, time

import inspect
# mypydir =os.path.abspath(os.path.dirname(inspect.getfile(inspect.currentframe())))
# sys.path.append(mypydir)

# from hostip import host2ip, ip2host, host2userip
CUT='='

def get_conf(fpath,typ, firstbreak = False):
	res=''
	try:
		if not (fpath.startswith('.') or fpath.startswith('/')):
			fpath="./"+fpath
		if fpath.startswith('.'):
			abspath=os.path.abspath(os.path.dirname(inspect.getfile(inspect.currentframe())))
			fpath = abspath+"/../"+ fpath
			#print(fpath)
		conf=open(fpath,'r')
		for line in conf:
			if line.split(CUT,1)[0].strip()==typ: 
				res=line.split(CUT,1)[1].split('#')[0].strip()
				if firstbreak:
					break # last one wins
		conf.close()
	except:
		pass
	return res

def get_conf_int(fpath,typ):
	return int(get_conf(fpath,typ))

def get_conf_float(fpath,typ):
	return float(get_conf(fpath,typ))

def get_conf_str(fpath,typ):
	return (get_conf(fpath,typ))

if __name__ == "__main__":
	print(get_conf('./conf','rqps'))

# LOAD CONFIG at parent dir
	#dirname=os.path.dirname(sys.argv[0])
#	pathname=os.path.abspath(dirname)
	currentframe= inspect.getfile(inspect.currentframe()) # script filename
	print 'currentframe:'+currentframe
	abspath=os.path.abspath(os.path.dirname(currentframe))
	print 'abspath:'+abspath

#t make sure mysqld, lighttpd, haproxy, php-fpm, memcached 
#e make sure mysql, lighttpd, haproxy, php5-fpm, memcached