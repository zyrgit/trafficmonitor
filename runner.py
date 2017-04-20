#!/usr/bin/env python
'''
Created on Mar 7, 2017
@author: yiranzhao
'''
import os, sys
import optparse
import subprocess
import random
import inspect
mypydir =os.path.abspath(os.path.dirname(inspect.getfile(inspect.currentframe())))
sys.path.append(mypydir+"/mytools")
from readconf import get_conf,get_conf_int

configfile = "conf.txt"

try:
    SUMOPATH=str(os.environ.get("SUMO_HOME"))
    if SUMOPATH.endswith('/'):
        sys.path.append(os.path.join(SUMOPATH, "tools")) # */sumo/
    else:
        sys.path.append(os.path.join(SUMOPATH+'/', "tools")) # has to end with '/'
    from sumolib import checkBinary
except ImportError:
    sys.exit("$SUMO_HOME/tools not defined...")

import traci
from sumo_car import Car
from sumo_tls import Tls,get_tls2duration

PORT = int(get_conf(configfile,"port"))

PRINT_debug = True
iprintstep = 1
iprintinfo = 1
iprintverb = 0

# 64 speed, 132 dist, 101 fuel, 80 road id, 122 wait time, 86 lane pos, 66 pos(x,y)
VarSpeed = traci.constants.VAR_SPEED
VarDist = traci.constants.VAR_DISTANCE 
VarFuel = traci.constants.VAR_FUELCONSUMPTION 
VarEdgeId= traci.constants.VAR_ROAD_ID
VarWaitTime=traci.constants.VAR_WAITING_TIME
VarLaneId = traci.constants.VAR_LANE_ID
VarLanePos= traci.constants.VAR_LANEPOSITION
VarPosXY = traci.constants.VAR_POSITION 
var2str={
 traci.constants.VAR_SPEED: "spd",
 traci.constants.VAR_DISTANCE : "dist",
 traci.constants.VAR_FUELCONSUMPTION : "fuel",
 traci.constants.VAR_ROAD_ID: "road",
 traci.constants.VAR_WAITING_TIME: "wait",
 traci.constants.VAR_LANE_ID: "lane",
 traci.constants.VAR_LANEPOSITION: "lpos",
 traci.constants.VAR_POSITION : "xy",
}

edge2tls={}
tls2edges={}
e2oppoe={}
lane2vq={}
lane2len={}

varlistroute=[VarSpeed, VarEdgeId, VarDist, VarFuel, VarWaitTime, VarLanePos,VarLaneId]
in2leftph={1:[4,6],2:[0,2],3:[5,6],4:[1,2]}
out2ph={1:[5,7,1,2,0,3],2:[4,6,1,3,5,7],3:[4,7,0,2,1,3],4:[5,6,0,3,4,7]}

id2tls={}
id2car={}
simulationEndTime = int(get_conf(configfile,"simulationEndTime"))
simulationStartTime = int(get_conf(configfile,"simulationStartTime"))
numlog = int(get_conf(configfile,"num-log-files"))

def run():
    global id2tls,id2car,edge2tls,tls2edges,e2oppoe

    traci.init(PORT)
    step = simulationStartTime

    Tls.traci = traci
    Car.traci = traci
    Tls.tls2ph2time = get_tls2duration()

    tlslist=traci.trafficlights.getIDList()
    if iprintinfo>0: print '>>> tlslist\n',tlslist
    
    directory='outfile'+str(PORT)
    if not os.path.exists(directory):
        os.makedirs(directory)
    # fd=open(directory+'/tlslist.txt','w')
    for tls in tlslist:
        tmp = Tls(tls)
        tmp.setProgram('p1')
        tmp.setOutputDir(directory+'/')
        id2tls[tls]=tmp
        # fd.write(tls+'.txt\n')
    # fd.close()

    edge2tls=get_edge2tls()
    if iprintinfo>1: print '>>> edge2tls',edge2tls
    tls2edges=get_tls2edges()
    if iprintinfo>1: print '>>> tls2edges',tls2edges
    alledges = traci.edge.getIDList()
    for eid in alledges[:]: # deep copy!
        if eid.startswith(":"):
            alledges.remove(eid)
        else:
            getoppositeedge(eid)
    Car.edge2tls = edge2tls
    Car.tls2edges = tls2edges
    Car.e2oppoe = e2oppoe
    Car.id2car = id2car
    tmpcar = None
    
    while step <= simulationEndTime:
        traci.simulationStep()
        step+=1
        print "\n>> -- step: ",step

        teleport = traci.simulation.getStartingTeleportIDList() 
        for vid in teleport:
            if iprintstep>=2: print('teleport=',teleport)
            id2car[vid].remove(step)

        try:
            deadlist=traci.simulation.getArrivedIDList()
            if iprintstep>=2: print('deadlist=',deadlist)
            for vid in deadlist:
                id2car[vid].setDead(step)
            vnum=traci.vehicle.getIDCount()
            if iprintstep>0: print('vnum='+str(vnum))
        except:
            if iprintstep>0: print('traci deadlist WRONG step=',step)
        
        newcars = traci.simulation.getDepartedIDList()
        if iprintstep>=2: print('newcars=',newcars)
        for vid in newcars:
            tmp = Car(vid)
            tmp.subscribe(varlistroute)
            tmp.setStartTime(step)
            tmp.setOutputFile(directory+"/"+str(hash(vid)%numlog))
            id2car[vid]=tmp

        for tlsid in tlslist: # all tls list
            id2tls[tlsid].updataPhase(step)
        
        for vid in traci.vehicle.getIDList():
            id2car[vid].process(step)
            lid,lpo,spd = id2car[vid].getLanePosSpeed()
            if lid not in lane2len.keys():
                lane2len[lid]=traci.lane.getLength(lid)
            if spd<2*Car.minSpeed and lpo>100 and lane2len[lid]-lpo<100: # candidate 
                if lid not in lane2vq.keys():
                    lane2vq[lid]=[] # remdist, spd, vid
                lane2vq[lid].append([lane2len[lid]-lpo+Car.VLen,spd,vid])
        
        vp = "a1"
        for vid in traci.vehicle.getIDList():
            tmpcar = id2car[vid]
            tlsid = tmpcar.getTls()
            tls2 =  ""#tmpcar.get2ndTls()
            if tlsid!="":
                lid,lpo,spd = tmpcar.getLanePosSpeed()
                pred = id2tls[tlsid].getFuturePhaseSeq(step+150)
                if iprintverb or vp==vid: print(tmpcar.id,tlsid,pred)
                if lid not in lane2vq.keys():
                    vq=[]
                else:
                    vq=lane2vq[lid]
                    if iprintverb or vp==vid: print("Queue",lid,sorted(vq))
                if tls2=="":
                    tmpcar.adjustSpeedGivenPhasePred(pred,vq)
                else:
                    pred = id2tls[tls2].getFuturePhaseSeq(step+300)
                    tmpcar.adjustSpeedGivenPhasePred(pred,vq)
                    
            if iprintverb or vp==vid: 
                print(var_dic_to_str(tmpcar.getSubscriptionResults()))
                id2car[vid].set_iprint(1)

        for lid in lane2vq.keys(): # need to refresh queue len 
            lane2vq[lid]=[]
    
    traci.close()
    sys.stdout.flush()
    

def get_dist(stls,sind,dtls,dind): # src,dst: if has ind(1-4) of tls, faster
    global edge2tls
    if sind>0:
        ctrlanes=traci.trafficlights.getControlledLanes(stls)
        opeid=getoppositeedge(ctrlanes[(sind-1)*3].split('_')[0])
        distn=traci.lane.getLength(opeid+'_0')
        return distn
    if dind>0:
        ctrlanes=traci.trafficlights.getControlledLanes(dtls)
        distn=traci.lane.getLength(ctrlanes[(dind-1)*3])
        return distn
    distn=-1.0
    ctrlanes=traci.trafficlights.getControlledLanes(dtls)
    for n in [0,4,8,12]:
        opeid=getoppositeedge(ctrlanes[n].split('_')[0])
        if opeid in edge2tls.keys() and stls==edge2tls[opeid]:
            distn=traci.lane.getLength(ctrlanes[n])
        break
    if PRINT_debug:
        print 'get_dist()  from: ',stls,' ', sind,'  to ',dtls,' ',dind,' dist=',distn
    return distn

def get_dts(tls):
    dtsf=open(patfname+'/'+tls+'.txt-dts')
    DTS=[[0 for col in range(3)] for row in range(2)]
    # DTS = { {25,32,38}, {30,38,42}};
    d=1
    for line in dtsf:
        st=line.split(' ')
        DTS[d][0]=int(float(st[0])*1000) #ms
        DTS[d][1]=int(float(st[1])*1000)
        DTS[d][2]=int(float(st[2])*1000)
        d-=1
    dtsf.close()
    #print DTS
    return DTS

def get_nbrtlslist(tgt):
    global edge2tls
    nbrtlslist=['','','','']
    ctrlanes=traci.trafficlights.getControlledLanes(tgt)
    for lid in [0,4,8,12]:
        opeid=getoppositeedge(ctrlanes[lid].split('_')[0])
        if opeid in edge2tls:
            nbrtlslist[lid/4]=edge2tls[opeid]
        else:
            nbrtlslist[lid/4]='~'
    return nbrtlslist

def which_turn(nexteid,noweid,tlsid): # 0 straight, 1 left, 2 right
    global tls2edges
    edges=tls2edges[tlsid]
    nextoppo=getoppositeedge(nexteid)
    if nextoppo in edges and noweid in edges:
        indnow=edges.index(noweid)+1
        indnext=edges.index(nextoppo)+1
        move=getMovementNum(indnow, indnext)
        if move in [2,3,6,7]: # straight
            return [0,move]
        elif move in [0,1,4,5]: # left
            return [1,move]
        else:
            return [2,move]
    
            
def get_edge2tls(): # tls at end of edge
    edge2tls_tmp={}
    for tlsid in traci.trafficlights.getIDList():
        ctrlanes=traci.trafficlights.getControlledLanes(tlsid)
        for ctrlane in ctrlanes:
            edgid=ctrlane.split('_')[0]
            edge2tls_tmp[edgid]=tlsid
    return edge2tls_tmp
    
def get_tls2edges(): # only edges end at tls
    tls2edges_tmp={}
    for tlsid in traci.trafficlights.getIDList():
        ctrlanes=traci.trafficlights.getControlledLanes(tlsid)
        tls2edges_tmp[tlsid]=[]
        for ctrlane in ctrlanes:
            edge=ctrlane.split('_',1)[0]
            if not (edge in tls2edges_tmp[tlsid]):
                tls2edges_tmp[tlsid].append(edge)
    return tls2edges_tmp
    
def is_rightturn(nowedge,lastedge,tlsid):
    global tls2edges
    edges=tls2edges[tlsid]
    #print tlsid
    if not nowedge in edges:
        return True
    if not lastedge in edges: # prevent teleporting to this edge
        return True
    indnowedge=edges.index(nowedge)+1
    indlastedge=edges.index(lastedge)+1
    if indlastedge == 1 and indnowedge==4:
            return True
    else:
        if indlastedge-indnowedge==1:
            return True
    return False

def getoppositeedge(eid):
    global e2oppoe,configfile
    if eid in e2oppoe.keys():
        return e2oppoe[eid]
    ef=open(get_conf(configfile,"edge-files"),'r')
    for line in ef:
        line=line.strip()
        if iprintinfo>1: print(line)
        if line.startswith('<edge id="'+eid+'"'):
            st=line.split(' ')
            toid=st[3].lstrip("to=")
            fromid=st[2].lstrip("from=")
            opst='from='+toid+' to='+fromid
            break
    ef.seek(0,0)
    for line in ef:
        if line.find(opst)!=-1:
            idstr=line.lstrip().split(' ',2)[1]
            opeid=idstr.split('"')[1]
            break
    ef.close()
    e2oppoe[eid]=opeid
    if not opeid in e2oppoe.keys():
        e2oppoe[opeid]=eid
    return opeid

def write_dic(fname,dic):
    with open(fname,'w') as fd:
        for k,v in dic.items():
            fd.write(k)
            for vv in v:
                fd.write(" "+vv)
            fd.write("\n")

def var_dic_to_str(dic):
    global var2str
    res={}
    if dic is not None:
        for k,v in dic.items():
            res[var2str[k]]=v
    return res

def get_options():
    optParser = optparse.OptionParser()
    optParser.add_option("-n","--nogui", action="store_true", default=False, help="run the commandline version of sumo")
    options, args = optParser.parse_args()
    return options

# this is the main entry point of this script
if __name__ == "__main__":
    options = get_options()

    if options.nogui:
        sumoBinary = checkBinary('sumo')
    else:
        sumoBinary = checkBinary('sumo-gui')


    cfg = get_conf(configfile,"sumo-config-file")
    sumoProcess = subprocess.Popen([sumoBinary, "-c", cfg, "--remote-port", str(PORT)], stdout=sys.stdout, stderr=sys.stderr)
    
    run()
    sumoProcess.wait()
