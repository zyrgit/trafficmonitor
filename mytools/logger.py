#!/usr/bin/env python

import os, sys
import subprocess
import random, time
import inspect
mypydir =os.path.abspath(os.path.dirname(inspect.getfile(inspect.currentframe())))
sys.path.append(mypydir)
from namehostip import get_my_ip
from hostip import ip2tarekc
import datetime

iprint = 1
iprintverb =0
fnamePrefix = "log-"

class Logger: 
	def __init__(self ):
		self.lg_index=0
		self.my_ip = get_my_ip()
		try:
			self.my_tname = ip2tarekc[self.my_ip]
		except:
			self.my_tname = self.my_ip
		self.fd_list=[]
		self.fnames =[]
		fmain = fnamePrefix+self.my_tname+".txt"
		fd = open(fmain,"w")
		self.fd_list.append(fd)
		self.fnames.append(fmain)
		self.lg(self.my_tname)
		self.lg(self.my_ip)
		self.lg(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
		self.lg(time.time())
		self.lg("\n")

	def lg(self, st, i=-1):
		if i<0:
			i=self.lg_index
		st=str(st)
		if not st.endswith("\n"):
			st=st+"\n"
		self.fd_list[i].write(st)

	def overwrite(self,st,i=-1):
		if i<0:
			i=self.lg_index
		self.fd_list[i].close()
		self.fd_list[i] = open(self.fnames[i],"w")
		self.lg(self.my_tname,i)
		self.lg(self.my_ip,i)
		self.lg(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),i)
		self.lg(time.time(),i)
		self.lg("\n",i)
		self.lg(st,i)

	def lg_new(self, st=""):
		ind = len(self.fd_list)
		fn =fnamePrefix+self.my_tname+"-"+str(ind)+".txt"
		self.fd_list.append(open(fn,"w"))
		self.fnames.append(fn)
		self.lg(self.my_tname,ind)
		self.lg(self.my_ip,ind)
		self.lg(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),ind)
		self.lg(time.time(),ind)
		self.lg("\n",ind)
		if st!="":
			self.lg(st,ind)
		return ind

	def set_lg_index(self,ind):
		if ind>=0:
			self.lg_index=ind

	def lg_list(self,ls,i=-1):
		st=""
		for x in ls:
			st = st+ str(x) + " "
		self.lg(st,i)
	def lg_dict(self,dic,i=-1):
		for k,v in dic.items():
			self.lg(str(k)+" = "+str(v),i)

	def __del__(self):
		for fd in self.fd_list:
			fd.close()

if __name__ == "__main__":
	l = Logger()
	l.lg("hello")
	l.lg(time.time())
	ind  = l.lg_new("another msg")
	l.lg("in another",ind)
	l.set_lg_index(ind)
	l.overwrite("overwrite another")
	l.set_lg_index(l.lg_new("3rd"))
	l.lg("")
	l.lg_list(["fads",23,3,"--"])
	l.set_lg_index(ind)
	l.lg_dict({1:2,"d":3})
