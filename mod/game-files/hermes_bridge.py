# hermes_bridge.py — Final. No more changes.
import os
def _hermes_log(msg):
    msg=str(msg)
    try: CvUtil.pyPrint("Hermes: "+msg)
    except: pass
    for p in (os.path.join(os.path.dirname(__file__),"HermesDebug.log"), r"C:\Users\gainq\OneDrive\Documents\My Games\beyond the sword\Logs\HermesBridge.log"):
        try:
            d=os.path.dirname(p)
            if d and not os.path.exists(d): os.makedirs(d)
            f=open(p,"a"); f.write(msg+"\n"); f.flush(); f.close()
        except: pass
_hermes_log("*** HERMES BRIDGE FINAL ***")
import socket
try: import simplejson as json
except: import json
import CvUtil
from CvPythonExtensions import *
gc=CyGlobalContext()
HOST="172.29.235.138"; PORT=3334; PID=1

def _read_cmds():
    paths=[os.path.join(os.path.dirname(__file__),"..","..","..","..",".hermes","civ4_commands.json"),
           os.path.join(os.path.expanduser("~"),".hermes","civ4_commands.json"),
           r"C:\Users\gainq\.hermes\civ4_commands.json"]
    try:
        try: import simplejson as jm
        except: import json as jm
        for p in paths:
            ap=os.path.abspath(p)
            if os.path.exists(ap):
                f=open(ap,'r'); c=f.read(); f.close()
                if c.strip(): return jm.loads(c)
    except: pass
    return []

def send_state(st):
    for h in [HOST,'127.0.0.1','localhost']:
        try:
            s=socket.socket(); s.settimeout(4)
            s.connect((h,PORT)); s.sendall(json.dumps(st)+'\n')
            r=s.recv(8192); s.close()
            if r: return json.loads(r)
            return []
        except Exception,e: _hermes_log('Conn fail %s: %s'%(h,str(e)))
    return []

def exec_cmds(cmds):
    if not cmds: return
    p=gc.getPlayer(PID)
    for cmd in cmds:
        try:
            a=cmd.get('action','')
            if a=='research':
                _hermes_log('Bridge: research set to %d'%cmd.get('tech',-1))
            elif a=='found':
                u=p.getUnit(cmd.get('unitId',-1))
                if u and not u.isDead():
                    tx=int(cmd.get('x', u.getX()))
                    ty=int(cmd.get('y', u.getY()))
                    u.getGroup().pushMission(MissionTypes.MISSION_FOUND,tx,ty,0,False,True,MissionAITypes.NO_MISSIONAI,CyMap().plot(tx,ty),u)
                    _hermes_log('Bridge: found city unit %d at (%d,%d)'%(u.getID(),tx,ty))
            elif a=='build':
                dc=p.getCity(cmd.get('cityId',-1))
                ut=cmd.get('unit',None)
                if dc and ut:
                    utype=gc.getInfoTypeForString(str("UNIT_"+ut.upper()))
                    if utype>=0:
                        dc.pushOrder(OrderTypes.ORDER_TRAIN,utype,-1,0,False,True,True)
                        _hermes_log('Bridge: ordered %s in %s'%(ut,dc.getName()))
            elif a=='move':
                u=p.getUnit(cmd.get('unitId',-1))
                tx,ty=cmd.get('x',-1),cmd.get('y',-1)
                if u and not u.isDead():
                    u.setXY(tx,ty,False,True,True)
                    _hermes_log('Bridge: teleported unit %d to (%d,%d)'%(u.getID(),tx,ty))
        except Exception,e: _hermes_log('Cmd err %s: %s'%(cmd.get('action','?'),str(e)))

def get_state(i):
    pp=gc.getPlayer(i); g=gc.getGame()
    st={'player_id':i,'leader':pp.getLeaderType(),'civ':pp.getCivilizationType(),'turn':g.getGameTurn(),'year':g.getGameTurnYear(),'gold':pp.getGold(),'numCities':pp.getNumCities(),'numUnits':pp.getNumUnits(),'units':[],'cities':[],'knownTechs':[],'currentResearch':-1}
    try: st['currentResearch']=pp.getCurrentResearch()
    except: pass
    tid=pp.getTeam(); pt=gc.getTeam(tid)
    if pt:
        for t in range(gc.getNumTechInfos()):
            if pt.isHasTech(t): st['knownTechs'].append(t)
    u,i=pp.firstUnit(False)
    while u:
        if not u.isDead():
            st['units'].append({'id':u.getID(),'x':u.getX(),'y':u.getY(),'unitType':u.getUnitType(),'movesLeft':u.getMoves(),'damage':u.getDamage()})
        u,i=pp.nextUnit(i,False)
    c,i=pp.firstCity(False)
    while c:
        cd={'id':c.getID(),'x':c.getX(),'y':c.getY(),'name':c.getName(),'population':c.getPopulation()}
        _enhance_city(cd,c)
        st['cities'].append(cd)
        c,i=pp.nextCity(i,False)
    st['diplo']=_get_diplo_snapshot(i)
    st['visibleEnemies']=_get_visible_enemies(i)
    return st

def _format_trade_item(item):
    try:
        t=int(item.getItemType()); d=item.getData()
        if t==0: return "Tech_%d"%d
        if t==1: return "Resource_%d"%d
        if t==2: return "Gold_%d"%d
        if t==3: return "GoldPerTurn_%d"%d
        if t==4: return "Map"
        if t==7: return "OpenBorders"
        if t==10: return "Peace"
        if t==13: return "City_%d"%d
        if t==5: return "Vassal"
        if t==6: return "Surrender"
        if t==14: return "Embassy"
        if t==15: return "Contact_%d"%d
        if t==16: return "Corporation_%d"%d
        return "TradeItem_%d"%t
    except: return "Unknown"

def _get_diplo_snapshot(pid):
    res={"metCivs":[],"attitudes":[],"warStatus":[],"activeDeals":[]}
    try:
        pp=gc.getPlayer(pid); mt=pp.getTeam(); pt=gc.getTeam(mt)
        for i in range(gc.getMAX_CIV_PLAYERS()):
            if i==pid: continue
            pl=gc.getPlayer(i)
            if not pl.isAlive() or pl.isBarbarian(): continue
            lt=pl.getTeam()
            if not pt.isHasMet(lt): continue
            res["metCivs"].append(i)
            try: res["attitudes"].append({"playerId":i,"level":int(pp.AI_getAttitude(i))})
            except: pass
            try: res["warStatus"].append({"playerId":i,"atWar":bool(pt.isAtWar(lt))})
            except: pass
        try:
            g=gc.getGame()
            for di in range(g.getIndexAfterLastDeal()):
                deal=g.getDeal(di)
                if deal.isNone(): continue
                fst=deal.getFirstPlayer(); snd=deal.getSecondPlayer()
                if fst!=pid and snd!=pid: continue
                if fst==pid: ptn=snd
                else: ptn=fst
                oi=[]; ti=[]; dt="trade"
                for j in range(deal.getLengthFirstTrades()):
                    try:
                        item=deal.getFirstTrade(j); it=int(item.getItemType())
                        if it==7: dt="openBorders"
                        elif it==10: dt="peace"
                        elif it==5 or it==6: dt="vassal"
                        s=_format_trade_item(item)
                        if fst==pid: oi.append(s)
                        else: ti.append(s)
                    except: pass
                for j in range(deal.getLengthSecondTrades()):
                    try:
                        item=deal.getSecondTrade(j); it=int(item.getItemType())
                        if it==7: dt="openBorders"
                        elif it==10: dt="peace"
                        elif it==5 or it==6: dt="vassal"
                        s=_format_trade_item(item)
                        if snd==pid: oi.append(s)
                        else: ti.append(s)
                    except: pass
                res["activeDeals"].append({"partner":ptn,"type":dt,"ourItems":oi,"theirItems":ti})
        except Exception,e: _hermes_log("Deal err: "+str(e))
    except Exception,e: _hermes_log("Diplo err: "+str(e))
    return res

def _get_visible_enemies(pid):
    res={"byOwner":{},"totalVisible":0}
    try:
        pp=gc.getPlayer(pid); mt=pp.getTeam()
        for i in range(gc.getMAX_CIV_PLAYERS()):
            if i==pid: continue
            pl=gc.getPlayer(i)
            if not pl.isAlive(): continue
            vis=[]
            u,it=pl.firstUnit(False)
            while u:
                try:
                    if not u.isDead() and u.isVisible(mt,False):
                        vis.append({"id":u.getID(),"owner":i,"unitType":u.getUnitType(),"x":u.getX(),"y":u.getY(),"damage":u.getDamage(),"movesLeft":u.getMoves()})
                        res["totalVisible"]+=1
                except: pass
                u,it=pl.nextUnit(it,False)
            if vis:
                res["byOwner"][str(i)]={"units":vis,"summary":"%d visible units"%len(vis)}
    except Exception,e: _hermes_log("Vis err: "+str(e))
    return res

def _enhance_city(cd,pc):
    try:
        pname=""; turns=-1; isUnit=False
        try:
            pname=str(pc.getProductionName()); turns=pc.getGeneralProductionTurnsLeft()
            try: isUnit=(pc.getOrderType(0)==0)
            except: pass
        except: pass
        cd["production"]={"name":pname,"turnsLeft":turns,"isBuildingUnit":isUnit}
        try:
            fpt=pc.getYieldRate(0); stored=pc.getFood(); needed=pc.growthThreshold()
            starving=(fpt<0); tg=-1
            if fpt>0:
                rem=needed-stored
                if rem<=0: tg=0
                else: tg=(rem+fpt-1)/fpt
            cd["growth"]={"foodPerTurn":fpt,"foodStored":stored,"foodNeeded":needed,"turnsToGrow":tg,"isStarving":starving}
        except: pass
    except: pass
    return cd

def on_hermes_player_turn(iPlayer):
    if iPlayer!=PID: return
    try:
        st=get_state(iPlayer)
        _hermes_log('State turn %d: %dc %du'%(st['turn'],st['numCities'],st['numUnits']))
        cmds=send_state(st)
        if cmds:
            _hermes_log('Got %d commands'%len(cmds))
            exec_cmds(cmds)
    except Exception,e: _hermes_log('Fatal: %s'%str(e))

_hermes_log('Bridge ready on %s:%d'%(HOST,PORT))

def get_desired_research():
    cmds=_read_cmds()
    for c in cmds:
        if isinstance(c,dict) and c.get('action')=='research': return c.get('tech',-1)
    return -1

def handle_ai_production(pCity):
    cmds=_read_cmds()
    for c in cmds:
        if isinstance(c,dict) and c.get('action')=='build' and c.get('cityId')==pCity.getID():
            ut=c.get('unit',None)
            if ut:
                utype=gc.getInfoTypeForString(str("UNIT_"+ut.upper()))
                if utype>=0:
                    pCity.pushOrder(OrderTypes.ORDER_TRAIN,utype,-1,0,False,True,True)
                    _hermes_log('AI_chooseProduction: %s in %s'%(ut,pCity.getName()))
                    return True
    return False
