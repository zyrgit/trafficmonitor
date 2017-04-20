#!/usr/bin/env python
# http://www.sumo.dlr.de/wiki/TraCI/Traffic_Lights_Value_Retrieval
import os, sys, traceback
import subprocess
import random, time
import json
import inspect
mypydir =os.path.abspath(os.path.dirname(inspect.getfile(inspect.currentframe())))
sys.path.append(mypydir+'/mytools')
from copy import deepcopy
import logging,glob
from datetime import datetime, timedelta
from readconf import get_conf,get_conf_int
configfile = "conf.txt"
LinkPerLane = 4  # each in-edge has # connection links at tls.
YellowTime = get_conf_int(configfile,"tls.yellow.time")-1 # all dts reduce 1.

iprintinfo = 0

class Tls:
    traci=None
    itruth = 0  # log the ground truth
    DataSize=10
    tlslogic2phn=[6,4,5,7,-1,2,0,1,3,-1] # tls phase index -> my ph num
    tls2ph2time = None

    def __init__(self,tlsid):
        self.id=tlsid
        #[1:size][0-4], [0][0] store pos, [0][1] last sorted pos
        self.movement=[[0 for col in range(5)] for row in range(Tls.DataSize)]
        self.ofpath=""
        self.fdtruth=None
        self.phn2t = Tls.tls2ph2time[self.id]
        self.ctrlanes=Tls.traci.trafficlights.getControlledLanes(self.id)
        self.time=0
        self.lastPredPhaseSeqTime=0
        self.lastPredPhaseSeqEndTime=0
        self.predPhaseSeq=[]

    def setProgram(self,pid):
        Tls.traci.trafficlights.setProgram(self.id, pid)

    def updataPhase(self,time):
        self.time=time
        nowphase=Tls.traci.trafficlights.getPhase(self.id)
        if time == Tls.traci.trafficlights.getNextSwitch(self.id)/1000 -1: 
            if nowphase==0 or nowphase==1 or nowphase==2:
                Tls.traci.trafficlights.setPhase(self.id,3)
                if Tls.itruth: self.writeTruth(str(time+1)+' '+str(Tls.tlslogic2phn[3]))
            elif nowphase==5 or nowphase==6 or nowphase==7:
                Tls.traci.trafficlights.setPhase(self.id,8)
                if Tls.itruth: self.writeTruth(str(time+1)+' '+str(Tls.tlslogic2phn[8]))
            elif nowphase==3:
            	Tls.traci.trafficlights.setPhase(self.id,4) #yellow
            elif nowphase==8:
            	Tls.traci.trafficlights.setPhase(self.id,9) #yellow
            elif nowphase==4: #yellow
                left=[0,0]
                checkid=[2*LinkPerLane-1,4*LinkPerLane-1] # east and west
                for laneind in checkid:
                    # lane id equals to induction loop id
                    spd=Tls.traci.inductionloop.getLastStepMeanSpeed(self.ctrlanes[laneind])
                    if spd>=0 and spd<0.1:
                        left[laneind/(checkid[1]-1)]=1
                if left[0]==0 and left[1]==0:
                    Tls.traci.trafficlights.setPhase(self.id,8)
                    if Tls.itruth: self.writeTruth(str(time+1)+' '+str(Tls.tlslogic2phn[8]))
                elif left[0]==1 and left[1]==0:
                    Tls.traci.trafficlights.setPhase(self.id,6)
                    if Tls.itruth: self.writeTruth(str(time+1)+' '+str(Tls.tlslogic2phn[6]))
                elif left[0]==0 and left[1]==1:
                    Tls.traci.trafficlights.setPhase(self.id,7)
                    if Tls.itruth: self.writeTruth(str(time+1)+' '+str(Tls.tlslogic2phn[7]))
                else:
                    if Tls.itruth: self.writeTruth(str(time+1)+' '+str(Tls.tlslogic2phn[5]))
            elif nowphase==9: #yellow
                left=[0,0]
                checkid=[LinkPerLane-1,3*LinkPerLane-1] # north and south
                for laneind in checkid:
                    # lane id equals to induction loop id
                    spd=Tls.traci.inductionloop.getLastStepMeanSpeed(self.ctrlanes[laneind])
                    if spd>=0 and spd<0.1:
                        left[laneind/(checkid[1]-1)]=1
                if left[0]==0 and left[1]==0:
                    Tls.traci.trafficlights.setPhase(self.id,3)
                    if Tls.itruth: self.writeTruth(str(time+1)+' '+str(Tls.tlslogic2phn[3]))
                elif left[0]==1 and left[1]==0:
                    Tls.traci.trafficlights.setPhase(self.id,1)
                    if Tls.itruth: self.writeTruth(str(time+1)+' '+str(Tls.tlslogic2phn[1]))
                elif left[0]==0 and left[1]==1:
                    Tls.traci.trafficlights.setPhase(self.id,2)
                    if Tls.itruth: self.writeTruth(str(time+1)+' '+str(Tls.tlslogic2phn[2]))
                else:
                    if Tls.itruth: self.writeTruth(str(time+1)+' '+str(Tls.tlslogic2phn[0]))
    

    def setOutputDir(self, fpath="tls/"):
        self.ofpath=fpath

    def writeTruth(self, wstr):
        if self.fdtruth is None:
            self.fdtruth = open(self.ofpath+"/tls-"+self.id+"-truth.txt",'w')
        if not wstr.endswith("\n"):
            wstr=wstr+"\n"
        self.fdtruth.write(wstr)

    def getFuturePhaseSeq(self,futuretime):
        if self.time==self.lastPredPhaseSeqTime and futuretime==self.lastPredPhaseSeqEndTime:
            return self.predPhaseSeq
        self.lastPredPhaseSeqTime=self.time
        self.lastPredPhaseSeqEndTime=futuretime
        res=[]
        tmp=Tls.traci.trafficlights.getPhase(self.id)
        if Tls.tlslogic2phn[tmp]<0:
        	isyellow=1
        else:
        	isyellow=0
        nowphase=Tls.tlslogic2phn[tmp-isyellow]
        if iprintinfo>=1 :print("time",self.time,"nowphase",nowphase)
        if (nowphase==3 or nowphase==7):
        	if isyellow==0:
        		nextt = Tls.traci.trafficlights.getNextSwitch(self.id)/1000+YellowTime
        	if isyellow==1:
        		nextt = Tls.traci.trafficlights.getNextSwitch(self.id)/1000
        else:
        	nextt = Tls.traci.trafficlights.getNextSwitch(self.id)/1000
        res.append([nowphase, nextt-1-self.phn2t[nowphase], nextt-2])
        noleft = [] # possibly add left into future.
        while nextt<=futuretime:
            if nowphase>=0 and nowphase<=2:
                nextphn = 3
            elif nowphase>=4 and nowphase<=6:
                nextphn = 7
            elif nowphase==7:
                if nowphase not in noleft:
                    noleft.append(nowphase)
                    left=[0,0]
                    checkid=[2*LinkPerLane-1,4*LinkPerLane-1] # east and west
                    for laneind in checkid:
                        spd=Tls.traci.inductionloop.getLastStepMeanSpeed(self.ctrlanes[laneind])
                        if spd>=0 and spd<0.1:
                            left[laneind/(checkid[1]-1)]=1
                    if left[0]==0 and left[1]==0:
                        nextphn = 3
                    elif left[0]==1 and left[1]==0:
                        nextphn = 0
                    elif left[0]==0 and left[1]==1:
                        nextphn = 1
                    else:
                        nextphn = 2
                else:
                    nextphn = 3
            elif nowphase==3:
                if nowphase not in noleft:
                    noleft.append(nowphase)
                    left=[0,0]
                    checkid=[LinkPerLane-1,3*LinkPerLane-1] # north and south
                    for laneind in checkid:
                        spd=Tls.traci.inductionloop.getLastStepMeanSpeed(self.ctrlanes[laneind])
                        if spd>=0 and spd<0.1:
                            left[laneind/(checkid[1]-1)]=1
                    if left[0]==0 and left[1]==0:
                        nextphn = 7
                    elif left[0]==1 and left[1]==0:
                        nextphn = 4
                    elif left[0]==0 and left[1]==1:
                        nextphn = 5
                    else:
                        nextphn = 6
                else:
                    nextphn = 7
            dura = self.phn2t[nextphn]
            res.append([nextphn, nextt-1, nextt+dura-2])
            nextt=nextt+dura
            nowphase=nextphn
        self.predPhaseSeq=res
        return self.predPhaseSeq

def get_tls2duration():
    tls2ph2time={}
    with open(get_conf(configfile,"tllogic-files"),'r') as fd:
        tlsid = ""
        ind=0
        for l in fd:
            l=l.strip()
            if l.startswith("<tlLogic id="):
                tlsid = l.split('"')[1]
                ind=0
                tls2ph2time[tlsid]={}
            if l.startswith("<phase duration="):
                t = int(l.split('"')[1])
                if Tls.tlslogic2phn[ind]!=-1:
                    tls2ph2time[tlsid][Tls.tlslogic2phn[ind]]=t-1
                else:
                	tls2ph2time[tlsid][Tls.tlslogic2phn[ind-1]]+=YellowTime
                ind+=1
    return tls2ph2time


if __name__ == "__main__":
    Tls.tls2ph2time = get_tls2duration()
    m = Tls("nx1y4")
    print(m.phn2t)
