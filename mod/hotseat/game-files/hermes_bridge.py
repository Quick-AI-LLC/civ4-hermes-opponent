# hermes_bridge.py — Hotseat variant. P2 is a human slot controlled by the bridge.
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
_hermes_log("*** HERMES BRIDGE HOTSEAT ***")
import socket
try: import simplejson as json
except: import json
import CvUtil
from CvPythonExtensions import *
gc=CyGlobalContext()
HOST="172.29.235.138"; PORT=3334
PID=1
HUMAN_PID=0
_handled_key=None
_staged_key=None
_settle_frames=0
_last_active=-1
_tick_frames=0
_update_seen=False
_diag_counter=0
_SETTLE_DELAY=8
_HANDOFF_KEY=None
_WATCHER_STARTED=False
_HERMES_DIR=r"C:\Users\gainq\.hermes"
_GATE_FILE=os.path.join(_HERMES_DIR,"turn_gate.json")
_WATCHER_SCRIPT=r"C:\Users\gainq\civ4-hermes-opponent\bridge\hermes_gate_watcher.ps1"

def _hermes_paths():
    return [os.path.join(_HERMES_DIR,n) for n in ("turn_gate.json","civ4_gate_password.txt","civ4_commands.json")]

def _start_gate_watcher():
    global _WATCHER_STARTED
    if _WATCHER_STARTED: return
    _WATCHER_STARTED=True
    try:
        if not os.path.exists(_HERMES_DIR): os.makedirs(_HERMES_DIR)
    except: pass
    if not os.path.isfile(_WATCHER_SCRIPT):
        _hermes_log('Gate watcher script missing: '+_WATCHER_SCRIPT)
        return
    try:
        os.system('start "" /B powershell -ExecutionPolicy Bypass -WindowStyle Hidden -File "' + _WATCHER_SCRIPT + '"')
        _hermes_log('Gate watcher started (set password in '+os.path.join(_HERMES_DIR,"civ4_gate_password.txt")+')')
    except Exception, e:
        _hermes_log('Gate watcher failed: ' + str(e))

def _mark_gate_opened():
    try:
        g=gc.getGame()
        payload={'event':'gate_opened','status':'gate_opened','mode':'hotseat','player_id':PID,'turn':g.getGameTurn()}
        if not os.path.exists(_HERMES_DIR): os.makedirs(_HERMES_DIR)
        f=open(_GATE_FILE,'w'); f.write(json.dumps(payload)); f.close()
        _hermes_log('gate_opened: P%d turn %d'%(PID,g.getGameTurn()))
    except Exception,e:
        _hermes_log('gate_opened file failed: '+str(e))

def notify_handoff_pending():
    global _HANDOFF_KEY
    if not _should_automate(): return
    g=gc.getGame()
    key=(g.getGameTurn(),PID)
    if _HANDOFF_KEY==key: return
    _HANDOFF_KEY=key
    payload={'event':'handoff_pending','status':'awaiting_gate','mode':'hotseat','player_id':PID,'turn':g.getGameTurn()}
    try:
        if not os.path.exists(_HERMES_DIR): os.makedirs(_HERMES_DIR)
        f=open(_GATE_FILE,'w'); f.write(json.dumps(payload)); f.close()
        _hermes_log('handoff_pending: P%d turn %d (gate file written)'%(PID,g.getGameTurn()))
    except Exception,e:
        _hermes_log('handoff_pending file failed: '+str(e))
    try:
        send_state(payload)
    except: pass

def _should_automate():
    try:
        if gc.getPlayer(PID).isHuman(): return True
    except: pass
    return False

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
                tech=cmd.get('tech',-1)
                if tech>=0:
                    tid=p.getTeam()
                    pt=gc.getTeam(tid)
                    if pt and not pt.isHasTech(tech):
                        p.pushResearch(tech, True)
                        _hermes_log('Bridge: research set to %d'%tech)
                    else:
                        _hermes_log('Bridge: research %d already known or invalid'%tech)
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
                    else:
                        _hermes_log('Bridge: unknown unit type %s'%ut)
            elif a=='move':
                u=p.getUnit(cmd.get('unitId',-1))
                tx,ty=cmd.get('x',-1),cmd.get('y',-1)
                if u and not u.isDead():
                    u.setXY(tx,ty,False,True,True)
                    _hermes_log('Bridge: teleported unit %d to (%d,%d)'%(u.getID(),tx,ty))
        except Exception,e: _hermes_log('Cmd err %s: %s'%(cmd.get('action','?'),str(e)))

def _auto_end_turn():
    g=gc.getGame()
    ap=g.getActivePlayer()
    _hermes_log('Bridge: _auto_end_turn for P%d (active=%d turn=%d)'%(PID,ap,g.getGameTurn()))
    if ap!=PID:
        _hermes_log('Bridge: active player is not P%d, skipping sendTurnComplete'%PID)
        return
    try:
        CyMessageControl().sendTurnComplete()
        _hermes_log('Bridge: sendTurnComplete OK')
        return
    except Exception,e:
        _hermes_log('sendTurnComplete failed: %s'%str(e))
    try:
        g.setAIAutoPlay(1)
        g.setAIAutoPlay(0)
        _hermes_log('Bridge: setAIAutoPlay fallback OK')
    except Exception,e:
        _hermes_log('setAIAutoPlay failed: %s'%str(e))

def stage_orders():
    global _staged_key
    notify_handoff_pending()
    if not _should_automate(): return
    g=gc.getGame()
    key=(g.getGameTurn(), PID)
    if _staged_key==key: return
    cmds=_read_cmds()
    early=[]
    for c in cmds:
        if isinstance(c,dict) and c.get('action') in ('research','build'):
            early.append(c)
    if not early: return
    _staged_key=key
    _hermes_log('stage_orders: applying %d research/build cmds for turn %d'%(len(early),g.getGameTurn()))
    exec_cmds(early)

def get_state(i):
    pp=gc.getPlayer(i); g=gc.getGame()
    st={'mode':'hotseat','player_id':i,'leader':pp.getLeaderType(),'civ':pp.getCivilizationType(),'turn':g.getGameTurn(),'year':g.getGameTurnYear(),'gold':pp.getGold(),'numCities':pp.getNumCities(),'numUnits':pp.getNumUnits(),'units':[],'cities':[],'knownTechs':[],'currentResearch':-1,'isHotSeat':False}
    try: st['isHotSeat']=g.isHotSeat()
    except: pass
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
    c,i=pp.nextCity(False)
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
        _hermes_log('Hotseat state turn %d: %dc %du'%(st['turn'],st['numCities'],st['numUnits']))
        cmds=send_state(st)
        if cmds:
            _hermes_log('Got %d commands'%len(cmds))
            exec_cmds(cmds)
        else:
            _hermes_log('No commands from bridge')
        _auto_end_turn()
    except Exception,e: _hermes_log('Fatal: %s'%str(e))

def tick_hotseat():
    global _handled_key, _settle_frames, _last_active, _tick_frames, _update_seen, _diag_counter
    _tick_frames+=1
    if not _update_seen:
        _update_seen=True
        _hermes_log('tick_hotseat: onUpdate hook is alive')
    if not _should_automate():
        return
    g=gc.getGame()
    ap=g.getActivePlayer()
    if ap!=_last_active:
        _hermes_log('tick_hotseat: active player %d -> %d (turn %d)'%(_last_active,ap,g.getGameTurn()))
        _last_active=ap
        _settle_frames=0
    if ap!=PID:
        return
    key=(g.getGameTurn(), PID)
    if _handled_key==key: return
    _settle_frames+=1
    if _settle_frames<_SETTLE_DELAY: return
    _handled_key=key
    _hermes_log('tick_hotseat: P%d action phase after popup settle (turn %d)'%(PID,g.getGameTurn()))
    _mark_gate_opened()
    on_hermes_player_turn(PID)
    _diag_counter+=1
    if _diag_counter<=3:
        try:
            hs=g.isHotSeat()
        except:
            hs=False
        _hermes_log('tick_hotseat: diag hotseat=%s humans=%d'%(str(hs),g.countHumanPlayersAlive()))

def get_desired_research():
    return -1

def handle_ai_production(pCity):
    return False

_start_gate_watcher()
_hermes_log('Hotseat bridge ready on %s:%d (P%d=Hermes, P%d=human)'%(HOST,PORT,PID,HUMAN_PID))