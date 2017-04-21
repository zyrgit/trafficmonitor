#!/usr/bin/env python

import os, sys, traceback
import subprocess
import random, time
import json
import inspect
mypydir =os.path.abspath(os.path.dirname(inspect.getfile(inspect.currentframe())))
# sys.path.append(mypydir+'/../mypy')
from copy import deepcopy
import logging,glob
from datetime import datetime, timedelta
import math

iprintbug = 1
iprintinfo =0
iprintverb =0
iprintspeed=0
iprintlane =0

class Car:
    VLen=4.0
    minGap =1.5
    minSpeed = 2.0
    maxSpeed =13.8
    maxAccel = 3.0
    maxDecel = 6.0
    tDischarge = 1.0 # 1s discharge delay
    idleGas=0.2 # when not moving.
    gasCoef=0.06  # 0.?*sqrt(v) is used when speed is steady. 
    dspd=1e-15  # dec spd by time*dspd according to expected gas.
    TimeBuf = 1.0
    id2car=None
    traci = None # shared static
    edge2tls=None
    tls2edges=None
    e2oppoe = None
    Ph2Move={0:[0,2],1:[1,3],2:[0,1],3:[2,3],4:[4,6],5:[5,7],6:[5,4],7:[6,7]}
    Ph2allMove={0:[0,2,-2,-4],1:[1,3,-2,-4],2:[0,1,-2,-4],3:[2,3,-2,-4],4:[4,6,-1,-3],5:[5,7,-1,-3],6:[5,4,-1,-3],7:[6,7,-1,-3]}
    move2Ph = {}
    for ph,mvs in Ph2allMove.items():
        for mov in mvs:
            if mov not in move2Ph.keys():
                move2Ph[mov]=[]
            move2Ph[mov].append(ph)
    ph2dir = {0:0,1:0,2:0,3:0,4:1,5:1,6:1,7:1}
    mov2dir = {0:0,1:0,2:0,3:0,4:1,5:1,6:1,7:1,-1:1,-3:1,-2:0,-4:0}
    mov2lane= {0:1,1:1,4:1,5:1,2:0,3:0,6:0,7:0,-1:0,-3:0,-2:0,-4:0} # stick to lane_# 

    def __init__(self,vid):
        self.id=vid
        self.time=0
        self.nowEdge=''
        self.lastEdge='' # this cannot be in cross
        self.nowLaneId = ""
        self.inCross = False # inside intersect 
        self.distance=0.0
        self.lanePos = 0.0
        self.laneLen = 100.0
        self.nowSpeed =0.0
        self.lastRealSpeed=0.0
        self.decnum =1
        self.lastSetSpeed=Car.maxSpeed
        self.speedLimit = Car.maxSpeed
        self.startTime=0.0
        self.endTime=0.0
        self.lastEdgeStartTime=0.0
        self.gas=0.0
        self.lastGas=0.0
        self.avgNonIdleGas=0.0
        self.avgGas=0.0
        self.lastWaitUpdateTime=-1
        self.lastTravelTimeUpdate=-1
        self.isStill = False
        self.isDead=False
        self.subscribed=False
        self.rou=[]
        self.changingEdge=False
        self.ofname=""  # append only, shared file.
        self.ofid = None
        self.edge2wait={}
        self.edge2travelTime={}
        self.edge2gas={}
        self.iprint =0
        self.wrongLane =0
        
    def process(self,time):
        if self.subscribed==False:
            return
        if self.isDead==True:
            return
        self.time=time
        res = self.getSubscriptionResults()
        if iprintverb: print(self.id, res)
        self.lastRealSpeed =self.nowSpeed
        self.nowSpeed = res[Car.traci.constants.VAR_SPEED]
        self.nowLaneId = res[Car.traci.constants.VAR_LANE_ID]
        self.lanePos = res[Car.traci.constants.VAR_LANEPOSITION]
        self.laneLen=Car.traci.lane.getLength(self.nowLaneId)
        self.lastGas = res[Car.traci.constants.VAR_FUELCONSUMPTION]
        if self.nowSpeed<0.1:
            self.lastGas=max(Car.idleGas,self.lastGas)
        self.gas+=self.lastGas
        self.avgGas = 0.2*(self.lastGas) + 0.8*self.avgGas
        if self.id=="a1":print("gas",self.avgGas,"spd",self.nowSpeed)
        self.updateNowEdge()
        self.updateWait()
        self.updateGas()

    def subscribe(self,varlist):
        Car.traci.vehicle.subscribe(self.id, varlist)
        self.subscribed=True
        self.getRoute()
    def setStartTime(self,time):
        self.startTime=time
    def getRoute(self,refresh=False):
        if self.rou==[] or refresh:
            self.rou=Car.traci.vehicle.getRoute(self.id)
        return self.rou
    def setDead(self,time=-1):
        self.subscribed=False
        self.isDead=True
        self.endTime=max(self.time,time)
        startt = self.startTime+self.edge2travelTime[self.rou[0]]
        endt = self.endTime-self.edge2travelTime[self.rou[-1]]
        wstr="v %s %d %d"%(self.id,startt,endt)
        self.appendToFile(wstr)
        self.writeGasResult()
        if iprintinfo:
            print("vid "+self.id)
            print("rou",self.rou)
            print("edge2travelTime",self.edge2travelTime)
            print("edge2wait",self.edge2wait)

    def remove(self,time=-1):
        Car.traci.vehicle.remove(self.id)
        self.setDead(time)

    def setOutputFile(self, fname):
        self.ofname=fname

    def appendToFile(self, wstr):
        if self.ofid is not None:
            self.ofid.close()
        if self.ofname !="":
            self.ofid = open(self.ofname,'a')
            if not wstr.endswith("\n"):
                wstr=wstr+"\n"
            self.ofid.write(wstr)
            self.ofid.close()
            self.ofid=None

    def updateNowEdge(self,):
        try:
            eid = self.nowLaneId.split("_")[0]
            if eid.startswith(':'):
                self.inCross =True
            else:
                self.inCross =False
            if (not self.inCross) and (eid!=''):
                self.nowEdge=eid
                if self.lastEdge=="":
                    self.lastEdge = self.nowEdge
                    self.lastEdgeStartTime=self.time
                    self.edge2travelTime[self.nowEdge]=0
                    self.lastTravelTimeUpdate=self.time
                elif self.lastEdge!=self.nowEdge:
                    self.changingEdge = True
                    self.changeEdgeCallback() #  appendToFile 
                    self.lastEdge=self.nowEdge
                    self.lastEdgeStartTime=self.time
                    self.edge2travelTime[self.nowEdge]=0
                    self.lastTravelTimeUpdate=self.time
                    self.speedLimit = Car.traci.lane.getMaxSpeed(self.nowLaneId)
                elif self.lastEdge==self.nowEdge:
                    self.changingEdge=False
                    self.edge2travelTime[self.nowEdge]+=self.time - self.lastTravelTimeUpdate
                    self.lastTravelTimeUpdate=self.time
        except:
            if iprintbug: print("!\nWrong %d updateNowEdge %s %s"%(self.time,self.id,self.nowEdge))
            pass

    def changeEdgeCallback(self,):
        if self.changingEdge:
            tmp=self.lastEdge
            ind = self.rou.index(tmp)
            if ind!=0 and ind!=len(self.rou)-1:
                edgetime = self.edge2travelTime[tmp]
                edgewait = self.edge2wait[tmp]
                ll = Car.traci.lane.getLength(tmp+"_0")
                sp = Car.traci.lane.getMaxSpeed(tmp+"_0")
                wstr="e %d %s %s %d %d %.1f"%(self.time,self.id,tmp,edgetime,edgewait,ll/sp)
                self.appendToFile(wstr)

    def updateWait(self,):
        spd  =  self.nowSpeed
        if not self.nowEdge in self.edge2wait.keys():
            self.edge2wait[self.nowEdge] =0
        if spd>=0.0 and spd<0.1:
            self.isStill=True
        else:
            self.isStill=False
        if self.isStill:
            if self.lastWaitUpdateTime<0:
                self.lastWaitUpdateTime=self.time
            else:
                self.edge2wait[self.nowEdge] += self.time-self.lastWaitUpdateTime
                self.lastWaitUpdateTime = self.time
        else: # moving
            if self.lastWaitUpdateTime>0:
                self.lastWaitUpdateTime=-1
                if iprintinfo: print("%s waited %d on %s"%(self.id,self.edge2wait[self.nowEdge],self.nowEdge))
    def updateGas(self,):
        if not self.nowEdge in self.edge2gas.keys():
            self.edge2gas[self.nowEdge] =0.0
        self.edge2gas[self.nowEdge] += self.lastGas
    def writeGasResult(self,):
        wstr="g "+self.id
        for k,v in self.edge2gas.items():
            if self.rou.index(k) not in [0,len(self.rou)-1]:
                wstr=wstr+" "+k+":"+str(v)
        wstr=wstr+" "+str(self.gas-self.edge2gas[self.rou[0]]-self.edge2gas[self.rou[-1]])
        self.appendToFile(wstr)
    
    def getTargetIntGivenPhaseSeq(self,phases): # [[phn,0,30],[phn,31,90]]
        mov = self.getMove()
        if mov<-4: # last edge.
            return []
        if iprintspeed or self.iprint: print("mov",mov)
        tpn = Car.move2Ph[mov]
        tdir = Car.mov2dir[mov]
        sp = self.speedLimit
        ll = self.laneLen-self.lanePos
        earliest = ll/sp+ self.time
        for i in range(len(phases)):
            phase = phases[i]
            if phase[0] in tpn:
                if phase[2]>=earliest:
                    break
                else:
                    if iprintspeed or self.iprint: print("cannot catch",phase)
            elif tdir == Car.ph2dir[phase[0]] and (i==len(phases)-1 or tdir!=Car.ph2dir[phases[i+1][0]]):
                if phase[2]>=earliest: # at least same direction, must take it.
                    break
                else:
                    if iprintspeed or self.iprint: print("cannot catch2",phase)
        return [phase[1],phase[2]]
    def setSpeedGivenTargetInt(self,intv,vlist):
        remdist=self.laneLen-self.lanePos
        if iprintspeed or self.iprint: print("rem dist",remdist)
        if remdist > 50 :
            tdisc = 0.0
            tacc = 0.0
            qlen=0.0
            if intv[0]<self.time: # start from now
                dequeuetime= self.time
            else:
                dequeuetime = intv[0]
            if len(vlist)>0:
                vlist.sort() # [[rem,spd,vid],[]] sort by remdist
                minspd=self.nowSpeed
                for i in range(len(vlist)):
                    minspd=min(minspd,vlist[i][1])
                    if vlist[i][1]<0.1: # find first stop car
                        break
                qlen = vlist[i][0]-(Car.VLen+Car.minGap)
                for j in range(i,len(vlist)):
                    minspd=min(minspd,vlist[j][1])
                    if minspd<0.1:
                        tdisc+=Car.tDischarge
                    if vlist[j][1]<0.1: 
                        qlen = vlist[j][0]
                    else:
                        qlen += Car.VLen+Car.minGap
                if tdisc>0:
                    tdisc-=Car.tDischarge
                tacc = math.sqrt(2*qlen/Car.maxAccel+(minspd/Car.maxAccel)*(minspd/Car.maxAccel))-minspd/Car.maxAccel

                if vlist[0][1]>minspd: # intv not yet, car already acc.
                    dequeuetime= self.time
            noquetime = dequeuetime+tdisc+tacc # when queue disappear 
            if noquetime<intv[0]: # queue gone before green phase.
                noquetime=intv[0]+Car.TimeBuf

            ll = remdist
            if iprintspeed or self.iprint: print("dequeuetime",dequeuetime,"noquetime",noquetime)
            if iprintspeed or self.iprint: print("intv",intv,"tdisc",tdisc,"tacc",tacc,"qlen",qlen)
            speed = ll/max(1,noquetime-self.time)
            speed = self.modifySpeed(speed)
            self.applySpeed(speed)
            self.lastSetSpeed = speed
            if iprintspeed or self.iprint: print("ll",ll,"tt",noquetime-self.time,"SetSpeed",speed)
        else:
            self.applySpeed(self.lastSetSpeed)
        return self.lastSetSpeed

    def adjustSpeedGivenPhasePred(self,phases,vlist):
        if self.inCross:
            self.applySpeed(self.lastSetSpeed)
            return
        self.checkLane()
        if self.wrongLane>0: return # conflict with lane re-assign spd 
        intv = self.getTargetIntGivenPhaseSeq(phases)
        if intv==[]: return # last edge.
        self.setSpeedGivenTargetInt(intv,vlist)

    def modifySpeed(self,spdcmd):
        if spdcmd<Car.minSpeed:
            spdcmd=Car.minSpeed
        if spdcmd>Car.maxSpeed:
            spdcmd=Car.maxSpeed
        if abs(spdcmd-self.lastSetSpeed)<0.1:
            if self.iprint:print("used lastSetSpeed",self.lastSetSpeed,spdcmd)
            return self.lastSetSpeed
        if self.iprint:print("update lastSetSpeed",spdcmd)
        return spdcmd
    
    def applySpeed(self,spdcmd):
        Car.traci.vehicle.setSpeed(self.id, spdcmd)

    def checkLane(self,):
        if self.inCross: return
        mv= self.getMove()
        if mv<-4: return
        ind = (Car.mov2lane[mv])
        st=self.nowLaneId.split("_")
        if ind!=int(st[-1]):
            if self.wrongLane==0:
                self.wrongLaneSeed = random.random()
            self.wrongLane+=1
            if iprintlane>=2: print(self.id,"change lane index to",ind)
        else:
            self.wrongLane=0
        if self.wrongLane>2:
            his = ind
            vlist=Car.traci.lane.getLastStepVehicleIDs(st[0]+"_"+str(his))
            if len(vlist)>0:
                ndist = 1000000
                nvid = ""
                for vid in vlist:
                    hisPos=Car.traci.vehicle.getLanePosition(Car.id2car[vid].id)
                    dis=abs(hisPos-self.lanePos)
                    if dis<ndist:
                        ndist=dis
                        nvid=vid
                if Car.id2car[nvid].wrongLane>0: # both fault
                    hisSpd = Car.traci.vehicle.getSpeed(nvid)
                    if hisSpd>self.nowSpeed:
                        self.applySpeed(self.nowSpeed-1)
                        if iprintlane: print(self.id,"give way to",nvid)
                    elif hisSpd==self.nowSpeed:
                        if hash(nvid)>hash(self.id):
                            self.applySpeed(self.nowSpeed-1)
                            if iprintlane: print(self.id,"give way to",nvid)
                    else:
                        if iprintlane: print(self.id,"expect slower",nvid)
                else: # my fault 
                    self.applySpeed(self.nowSpeed-1)
                    if iprintlane: print(self.id,"my bad, not his",nvid)
            else:
                if iprintlane: print(self.id,"no car but still wrong lane?")
        Car.traci.vehicle.changeLane(self.id,ind,0)

    def getSubscriptionResults(self,):
        return Car.traci.vehicle.getSubscriptionResults(self.id)
    def getLanePosSpeed(self,):
        return [self.nowLaneId,self.lanePos,self.nowSpeed]
    def getTls(self,):
        try:
            return Car.edge2tls[self.nowEdge]
        except:
            return ""
    def get2ndTls(self,):
        try:
            ind = self.rou.index(self.nowEdge)
            if ind>=len(self.rou)-2: 
                return ""
            return Car.edge2tls[self.rou[ind+1]]
        except:
            return ""
    def getMove(self,):
        ind = self.rou.index(self.nowEdge)
        if ind==len(self.rou)-1: 
            return -5
        nexteid = Car.e2oppoe[self.rou[ind+1]]
        elist= Car.tls2edges[self.getTls()]
        inn = elist.index(self.nowEdge)+1
        out = elist.index(nexteid)+1
        return self.getMovementNum(inn,out)
    def getMovementNum(self, inN, out):
        if (inN==1 and out==2 ): return 4
        elif(inN==3 and out==4 ):return 5
        elif(inN==1 and out==3 ):return 6
        elif(inN==3 and out== 1):return 7
        elif(inN==2 and out==3 ):return 0
        elif(inN==4 and out==1 ):return 1
        elif(inN==2 and out==4 ):return 2
        elif(inN==4 and out==2 ):return 3
        else: # all right turns 
            if inN==1: return -1
            elif inN==2: return -2
            elif inN==3: return -3
            return -4 
    def set_iprint(self,p):
        self.iprint=p

if __name__ == "__main__":
    m = Car("0")
    
# Car.traci.constants.VAR_SPEED
# Car.traci.constants.VAR_DISTANCE 
# Car.traci.constants.VAR_FUELCONSUMPTION 
# Car.traci.constants.VAR_ROAD_ID
# Car.traci.constants.VAR_WAITING_TIME
# Car.traci.constants.VAR_LANE_ID
# Car.traci.constants.VAR_LANEPOSITION
# Car.traci.constants.VAR_POSITION 