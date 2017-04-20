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

nf=get_conf(cfg,"node-files")
ef=get_conf(cfg,"edge-files")
cf=get_conf(cfg,"connection-files")
tpf=get_conf(cfg,"type-files")
tlsf=get_conf(cfg,"tllogic-files")
netf=get_conf(cfg,"net-file")
tripf=get_conf(cfg,"trip-files")
rouf=get_conf(cfg,"route-files")

bt=get_conf(cfg,"simulationStartTime")
et=get_conf(cfg,"simulationEndTime")
pt=get_conf(cfg,"trip-depart-period")
pfx = get_conf(cfg,"prefix")
tripa = get_conf(cfg,"trip-attributes")
vtp = get_conf(cfg,"additional-files-vtype")
mind = get_conf(cfg,"min-distance")
frg = get_conf(cfg,"fringe-factor")
alg = get_conf(cfg,"routing-algorithm")
duarouter=get_conf(cfg,"duarouter-extra")
sumocfg=get_conf(cfg,"sumo-config-file")

wstr = '<?xml version="1.0" encoding="iso-8859-1"?>\n<configuration xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n xsi:noNamespaceSchemaLocation="http://sumo.sf.net/xsd/sumoConfiguration.xsd">\n    <input>\n        <net-file value="%s"/>\n        <additional-files value="net.det.xml"/>\n        <route-files value="%s"/>\n        <gui-settings-file value="net.setting.xml"/>\n        \n    </input>\n    <time>\n        <begin value="%s"/>\n        <end value="%s"/>\n    </time>\n    <time-to-teleport value="-1"/>\n</configuration>' % (netf,rouf,bt,et)

def gen_cfg():
	# gen trips
	cmd= wstr
	print(cmd)
	with open(sumocfg,'w') as fd:
		fd.write(wstr)

	
if __name__ == "__main__":
	gen_cfg()