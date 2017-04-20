#!/usr/bin/env python

import os, sys
import subprocess
import random,time
import inspect
mypydir =os.path.abspath(os.path.dirname(inspect.getfile(inspect.currentframe())))
sys.path.append(mypydir+"/mytools")
# from hostip import get_username
from readconf import get_conf
import collections
from random import randint

random.seed(1)
iprint = 1
cfg = "conf.txt"

st1="""<?xml version="1.0" encoding="UTF-8"?>
<edges xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
 xsi:noNamespaceSchemaLocation="http://sumo.sf.net/xsd/edges_file.xsd">
"""
st2="</edges>"
st3= '	<edge id="%s" from="%s" to="%s" type="a"/>'
#netgenerate --grid true --grid.x-length 300 --grid.y-length 300 --grid.x-number 5 --grid.y-number 4 --grid.attach-length 300 --tls.guess true --tls.yellow.time 3 --tls.left-green.time 7 --tls.default-type actuated 


def run():
	wfd = open("net.edg.xml",'w')
	wfd.write(st1)
	nx = int(get_conf(cfg,"grid.x-number"))
	ny = int(get_conf(cfg,"grid.y-number"))
	lx = int(get_conf(cfg,"grid.x-length"))
	ly = int(get_conf(cfg,"grid.y-length"))
	lout = int(get_conf(cfg,"grid.attach-length"))
	lvar = int(get_conf(cfg,"varlength"))

	# gen  vertical
	pref = "e"
	for j in range(0, ny+1): # 5
		for i in range(1,nx+1): #3
			fro = "nx"+str(i)+"y"+str(j)
			to = "nx"+str(i)+"y"+str(j+1)
			eid = pref+fro+to
			wfd.write(st3%(eid,fro,to)+"\n")
			eid = pref+to+fro
			wfd.write(st3%(eid,to,fro)+"\n")
	
	# gen horizontal
	for i in range(0,nx+1): # 6
		for j in range(1,ny+1): #2
			fro = "nx"+str(i)+"y"+str(j)
			to = "nx"+str(i+1)+"y"+str(j)
			eid = pref+fro+to
			# print(eid)
			wfd.write(st3%(eid,fro,to)+"\n")
			eid = pref+to+fro
			wfd.write(st3%(eid,to,fro)+"\n")
	

	wfd.write(st2)
	wfd.close()
		

if __name__ == "__main__":
	run()