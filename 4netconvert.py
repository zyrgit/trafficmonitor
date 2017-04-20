#!/usr/bin/env python

import os, sys
import subprocess
import random,time
import inspect
mypydir =os.path.abspath(os.path.dirname(inspect.getfile(inspect.currentframe())))
sys.path.append(mypydir+"/mytools")
from readconf import get_conf
import collections,math
from random import randint

random.seed(1)
iprint = 1
cfg = "conf.txt"

tlsy=int(get_conf(cfg,"tls.yellow.time"))#=3
tlslg1=int(get_conf(cfg,"tls.left-green.time-min"))#=5
tlslg2=int(get_conf(cfg,"tls.left-green.time-max"))#=12
tlsg1=int(get_conf(cfg,"tls.straight-green.time-min"))#=25
tlsg2=int(get_conf(cfg,"tls.straight-green.time-max"))#=50
tlsoffset = int(get_conf(cfg,"tls.offset.max"))#90

#netconvert --node-files=net.nod.xml --edge-files=net.edg.xml --connection-files=net.con.xml --type-files=net.typ.xml --tllogic-files=net.tls.xml --output-file=net.cnd.tls.net.xml -v --no-turnarounds.tls true
nf=get_conf(cfg,"node-files")
ef=get_conf(cfg,"edge-files")
cf=get_conf(cfg,"connection-files")
tpf=get_conf(cfg,"type-files")
tlsf=get_conf(cfg,"tllogic-files")
of=get_conf(cfg,"net-file")

def gen_net():
	cmd= "netconvert --node-files=%s --edge-files=%s --connection-files=%s --type-files=%s --tllogic-files=%s --output-file=%s -v --no-turnarounds.tls true"%(nf,ef,cf,tpf,tlsf,of)
	print(cmd)
	subprocess.call(cmd,shell=True)

	
if __name__ == "__main__":
	gen_net()