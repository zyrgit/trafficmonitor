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
iprint = 0
cfg = "conf.txt"

st4="<additional>\n"
st5="</additional>"
st6 = '	<inductionLoop id="%s_1" lane="%s_1" pos="-2" file="/dev/null" freq="1"/>\n'
st1="""<?xml version="1.0" encoding="UTF-8"?>
<connections xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
 xsi:noNamespaceSchemaLocation="http://sumo.sf.net/xsd/connections_file.xsd">
"""
st2="</connections>"
st3= '	<connection from="%s" to="%s" fromLane="%d" toLane="%d"/>\n'
# <edge id="-enx3y0nx3y1" from="nx3y1" to="nx3y0" type="a"/>
# <node id="nx2y0" x="563" y="35" type="traffic_light"/>

st7 = ' <tlLogic id="%s" programID="p1" offset="%d" type="static">\n'
st8 = '      <phase duration="%d" state="grrGgrrrgrrGgrrr"/>\n      <phase duration="%d" state="gGGGgrrrgrrrgrrr"/>\n      <phase duration="%d" state="grrrgrrrgGGGgrrr"/>\n      <phase duration="%d" state="gGGggrrrgGGggrrr"/>\n      <phase duration="%d" state="gyyygrrrgyyygrrr"/>\n      <phase duration="%d" state="grrrgrrGgrrrgrrG"/>\n      <phase duration="%d" state="grrrgGGGgrrrgrrr"/>\n      <phase duration="%d" state="grrrgrrrgrrrgGGG"/>\n      <phase duration="%d" state="grrrgGGggrrrgGGg"/>\n      <phase duration="%d" state="grrrgyyygrrrgyyy"/>\n'
st9=' </tlLogic>\n'

tlsy=int(get_conf(cfg,"tls.yellow.time"))#=3
tlslg1=int(get_conf(cfg,"tls.left-green.time-min"))#=5
tlslg2=int(get_conf(cfg,"tls.left-green.time-max"))#=12
tlsg1=int(get_conf(cfg,"tls.straight-green.time-min"))#=25
tlsg2=int(get_conf(cfg,"tls.straight-green.time-max"))#=50
tlsoffset = int(get_conf(cfg,"tls.offset.max"))#90

def run():
	wfd = open("net.con.xml",'w')
	fdet = open("net.det.xml",'w')
	ftls = open("net.tls.xml",'w')
	wfd.write(st1)
	fdet.write(st4)
	ftls.write(st4)
	nx = int(get_conf(cfg,"grid.x-number"))
	ny = int(get_conf(cfg,"grid.y-number"))
	lx = int(get_conf(cfg,"grid.x-length"))
	ly = int(get_conf(cfg,"grid.y-length"))
	lout = int(get_conf(cfg,"grid.attach-length"))
	lvar = int(get_conf(cfg,"varlength"))

	nlist=[]
	n2xy={}
	with open("net.nod.xml",'r') as nf:
		for line in nf:
			line=line.strip()
			if line.startswith("<node id"):
				nlist.append(line.split('"')[1])
				x=float(line.split('"')[3])
				y=float(line.split('"')[5])
				n2xy[line.split('"')[1]]=[x,y]

	# print(nlist)
	# print(n2xy)
	n2e={nd:[[],[]] for nd in nlist} # {nid:[ [ein,],[eout,] ] }
	with open("net.edg.xml",'r') as ef:
		for line in ef:
			line=line.strip()
			if line.startswith("<edge id"):
				eid = line.split('"')[1]
				fro= line.split('"')[3]
				to = line.split('"')[5]
				n2e[fro][1].append(eid)
				n2e[to][0].append(eid)
	# print(n2e)
	# connect lanes
	for nd,eio in n2e.items():
		# if nd!='nx1y3':
		# 	continue
		# print(nd)
		x, y = n2xy[nd]
		addtls=0
		for ei in eio[0]:
			# if ei!="enx2y4nx1y3":
			# 	continue
			print("\n"+ei)
			nin = ei.split("n")[1].strip()
			ix,iy = n2xy["n"+nin] # coord of node from
			degi = getdeg(ix,iy,x,y)
			dx1=float(x-ix)
			dy1=float(y-iy)
			dd=math.sqrt(dx1*dx1+dy1*dy1)
			dx1/=dd
			dy1/=dd
			tmp = eio[1][:]
			if len(tmp)<2:
				continue # peripheral nodes.
			fdet.write(st6%(ei,ei)) # induction loop 
			# tls
			if addtls==0:
				addtls=1
				offset = randint(0,tlsoffset)
				ftls.write(st7%(nd,offset))
				t1=randint(tlslg1,tlslg2)
				t2=randint(tlsg1,tlsg2)
				t3=randint(tlslg1,tlslg2)
				t4=randint(tlsg1,tlsg2)
				ftls.write(st8%(t1,t1,t1,t2,tlsy,t3,t3,t3,t4,tlsy))
				ftls.write(st9)
			tmp.remove("e"+nd+"n"+nin) # no turnaround

			crpd = {} # vec cross product 
			dotp = {} # dot product
			for eo in tmp:
				no = eo.split("n")[2].strip()
				ox,oy = n2xy["n"+no] # coord of node to
				dx2=ox-x
				dy2=oy-y
				dd=math.sqrt(dx2*dx2+dy2*dy2)
				dx2/=dd
				dy2/=dd
				crpd[dx1*dy2-dx2*dy1] = eo
				dotp[eo] = dx1*dx2+dy1*dy2

			cps = crpd.keys()
			cps.sort()
			# cps [ right straight left ]
			i=len(cps)-1 
			if cps[i]<=0:# left found
				wfd.write(st3%(ei,crpd[cps[i]],1,1))
			else: # dot smallest is left
				candi = []
				for j in range(len(cps)):
					if cps[j]>=0:
						candi.append(crpd[cps[j]])
				# find min dot
				target=""
				tmp=10000
				for eid,dot in dotp.items():
					if eid in candi and dot<tmp:
						tmp=dot
						target=eid
				if iprint:print("left ",target)
				del dotp[target]
				wfd.write(st3%(ei,target,1,1))

			cps = crpd.keys()
			cps.sort()
			i=0 # right turn
			if cps[i]>=0:# right found
				wfd.write(st3%(ei,crpd[cps[i]],0,0))
			else: # dot smallest is right
				candi = []
				for j in range(len(cps)):
					if cps[j]<=0:
						candi.append(crpd[cps[j]])
				# find min dot
				target=""
				tmp=10000
				for eid,dot in dotp.items():
					if eid in candi and dot<tmp:
						tmp=dot
						target=eid
				if iprint:print("right ",target)
				del dotp[target]
				wfd.write(st3%(ei,target,0,0))

			# go straight, dot largest is
			target=""
			tmp=-10000
			for eid,dot in dotp.items():
				if dot>tmp:
					tmp=dotp[eid]
					target=eid
			if iprint:print("straight ",target)
			wfd.write(st3%(ei,target,0,0))
			wfd.write(st3%(ei,target,0,1))

			# angles = [degi + ang for ang in [-90,90,0]]
			# for i in range(len(angles)):
			# 	if angles[i]<0:
			# 		angles[i]=angles[i]+360.0
			# 	if angles[i]>360:
			# 		angles[i]=angles[i]-360.0
			# for i in range(len(angles)): # first left, then right, last straight.
			# 	print(i,tmp)
			# 	target=""
			# 	dego=-1
			# 	diff = 100000
			# 	for eo in tmp:
			# 		no = eo.split("n")[2].strip()
			# 		ox,oy = n2xy["n"+no] # coord of node to
			# 		deg2 = getdeg(x,y,ox,oy)
			# 		print(eo,deg2,angles[i])
			# 		if abs(deg2-angles[i])<diff or abs(deg2-angles[i]+360)<diff or abs(deg2-angles[i]-360)<diff:
			# 			diff=min([abs(deg2-angles[i]),abs(deg2-angles[i]+360),abs(deg2-angles[i]-360)])
			# 			target=eo
			# 			dego = deg2
			# 	if target!="":
			# 		print(degi,dego)
			# 		tmp.remove(target)
			# 		print(ei,target,i)
			# 		if i==0: # left found
			# 			wfd.write(st3%(ei,target,1,1))
			# 		if i==1: # right turn
			# 			wfd.write(st3%(ei,target,0,0))
			# 		if i==2: # go straight
			# 			wfd.write(st3%(ei,target,0,0))
			# 			wfd.write(st3%(ei,target,0,1))
			# break
		# break				

	wfd.write(st2)
	wfd.close()
	fdet.write(st5)
	fdet.close()
	ftls.write(st5)
	ftls.close()
		
def getdeg(x0,y0,x,y): # angle to north, [0,360]
    dx=float(x)-float(x0)
    dy=float(y)-float(y0)
    deg=math.atan2(dy,dx)/math.pi*180.0 #between -pi and pi
    if deg>90 and deg<=180:
        return 450.0-deg
    else:
        return 90.0-deg

if __name__ == "__main__":
	run()