#!/usr/bin/env python

import os, sys
import subprocess
import random,time
import inspect
mypydir =os.path.abspath(os.path.dirname(inspect.getfile(inspect.currentframe())))
sys.path.append(mypydir+"/mytools")
from readconf import get_conf,get_conf_int
import collections,math
from random import randint
from namehostip import get_my_ip


MYIP = get_my_ip()
print("my IP= "+MYIP)
try:
    SUMOPATH=str(os.environ.get("SUMO_HOME"))
    if SUMOPATH.endswith('/'):
        sys.path.append(os.path.join(SUMOPATH, "tools")) # */sumo/
    else:
        sys.path.append(os.path.join(SUMOPATH+'/', "tools")) # has to end with '/'
    from sumolib import checkBinary
except ImportError:
    sys.exit("$SUMO_HOME/tools not defined...")
    
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
et=get_conf(cfg,"tripEndTime")
pt=get_conf(cfg,"trip-depart-period")
pfx = get_conf(cfg,"prefix")
tripa = get_conf(cfg,"trip-attributes")
vtp = get_conf(cfg,"additional-files-vtype")
mind = get_conf(cfg,"min-distance")
frg = get_conf(cfg,"fringe-factor")
alg = get_conf(cfg,"routing-algorithm")
duarouter=get_conf(cfg,"duarouter-extra")

# gen trips
#/Users/yiranzhao/Downloads/sumo-0.28.0/tools/randomTrips.py  -b 0 -e 5000 -n net.cnd.tls.net.xml -p 1 -o net.trips.xml --prefix=a --trip-attributes="type=\"vt1\" departLane=\"best\" departSpeed=\"random\" departPos=\"random\" arrivalPos=\"random\"" --additional-files=vtype.add.xml --min-distance=1100 --seed 1 --fringe-factor 5

# gen routes
#/opt/local/bin/duarouter -n net.cnd.tls.net.xml -t net.trips.xml --additional-files=vtype.add.xml -o net.rou.xml --routing-algorithm 'CH' --weight-period 300 --weight-files net.weight.xml

st1 = "<meandata>\n"
st2 = "</meandata>\n"
st3= '   <interval begin="%d" end="%d" id="w%d">\n'
st4 = '      <edge id="%s" traveltime="%d"/>\n'
st5 = '   </interval>\n'

def gen_routes():
	# gen trips
	cmd= SUMOPATH+"/tools/randomTrips.py -b %s -e %s -n %s -p %s -o %s --prefix=%s --trip-attributes=%s --additional-files=%s --min-distance=%s --fringe-factor %s --seed 1 "%(bt,et,netf,pt,tripf,pfx,tripa,vtp,mind,frg)
	print(cmd)
	subprocess.call(cmd,shell=True)

	if duarouter!="" :
		elist = []
		with open(ef,'r') as fd:
			for line in fd:
				line=line.strip()
				if line.startswith("<edge id"):
					eid = line.split('"')[1]
					elist.append(eid)
		wtime = int(duarouter.split(" ")[1])
		begt = int(bt)
		endt = int(et)
		disturb_edge_num = get_conf_int(cfg,'disturb_edge_num')
		weight_traveltime_min = get_conf_int(cfg,'weight_traveltime_min')
		weight_traveltime_max = get_conf_int(cfg,'weight_traveltime_max')
		#duarouter-extra = --weight-period 1000 --weight-files net.weight.xml
		with open('net.weight.xml','w') as fd:
			fd.write(st1)
			cnt=0
			while begt+wtime<= endt:
				fd.write(st3%(begt,begt+wtime,cnt))
				cnt+=1
				avoid = []
				for i in range(disturb_edge_num):
					ind = randint(0,len(elist)-1)
					while ind in avoid:
						ind = randint(0,len(elist)-1)
					avoid.append(ind)
					ee = elist[ind]
					tt = randint(weight_traveltime_min,weight_traveltime_max)
					fd.write(st4%(ee,tt))
				fd.write(st5)
				begt+=wtime
			fd.write(st2)


	# gen routes
	cmd="duarouter -n %s -t %s --additional-files=%s -o %s --routing-algorithm %s %s"%(netf,tripf,vtp,rouf,alg,duarouter)
	print(cmd)
	subprocess.call(cmd,shell=True)

	
if __name__ == "__main__":
	gen_routes()