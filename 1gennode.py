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
<nodes xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
 xsi:noNamespaceSchemaLocation="http://sumo.sf.net/xsd/nodes_file.xsd">
 """
st2="</nodes>"
st3= '	<node id="%s" x="%d" y="%d" type="traffic_light"/>'
#netgenerate --grid true --grid.x-length 300 --grid.y-length 300 --grid.x-number 5 --grid.y-number 4 --grid.attach-length 300 --tls.guess true --tls.yellow.time 3 --tls.left-green.time 7 --tls.default-type actuated 


def run():
	wfd = open("net.nod.xml",'w')
	wfd.write(st1)
	nx = int(get_conf(cfg,"grid.x-number"))
	ny = int(get_conf(cfg,"grid.y-number"))
	lx = int(get_conf(cfg,"grid.x-length"))
	ly = int(get_conf(cfg,"grid.y-length"))
	lout = int(get_conf(cfg,"grid.attach-length"))
	lvar = int(get_conf(cfg,"varlength"))

	# gen  nodes
	pref = "n"
	for j in range(0, ny+2):
		for i in range(1,nx+1):
			x = i*lx + randint(-lvar,lvar)
			y = j*ly + randint(-lvar,lvar)
			nid = pref+"x"+str(i)+"y"+str(j)
			wfd.write(st3%(nid,x,y)+"\n")
	for i in [0, nx+1]:
		for j in range(1,ny+1):
			x = i*lx + randint(-lvar,lvar)
			y = j*ly + randint(-lvar,lvar)
			nid = pref+"x"+str(i)+"y"+str(j)
			wfd.write(st3%(nid,x,y)+"\n")


	wfd.write(st2)
	wfd.close()
		

if __name__ == "__main__":
	run()