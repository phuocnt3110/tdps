"""
3-ZONE ANALYSIS: BTL / ETL / ATL
BTL = Below The Line | ETL = Emerging Through the Line | ATL = Above The Line
"""
import sys, os, io, time, numpy as np, pandas as pd
from datetime import datetime, timedelta
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
_vp = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'vnstock')
if os.path.exists(_vp): sys.path.insert(0, _vp)
try:
    from vnstock import Quote
except ImportError:
    print("ERROR: pip install vnstock"); sys.exit(1)

OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "zone_output_v4.txt")
class Tee:
    def __init__(self, *s): self.s = s
    def write(self, d):
        for x in self.s: x.write(d); x.flush()
    def flush(self):
        for x in self.s: x.flush()
_lf = open(OUTPUT_FILE, "w", encoding="utf-8")
sys.stdout = Tee(sys.stdout, _lf)

ANALYSIS_START = "2025-03-10"
ANALYSIS_END   = "2026-03-10"

USER_JOURNAL = {
    "NAF":["atl"],"PVT":["atl"],"BSR":["atl"],"POW":["atl"],"NT2":["atl"],
    "MSR":["atl"],"PVS":["atl"],"BIG":["atl"],"PVB":["atl"],"HHP":["atl"],
    "MWG":["atl"],"PNJ":["atl"],"BAF":["atl"],"CTG":["atl"],"DCL":["atl"],
    "HDB":["atl"],"FPT":["atl"],"OIL":["atl"],"PVD":["atl"],"DCM":["atl"],
    "GSP":["btl"],"EVF":["btl"],"TD6":["btl"],"PAC":["btl"],"BFC":["btl"],
    "CTD":["btl"],"SZC":["btl"],"VHC":["btl"],"BIC":["btl"],"PSX":["btl"],
    "FIT":["btl"],"TTF":["btl"],"NDN":["btl"],"PHR":["btl"],"G36":["btl"],
    "STB":["btl"],"HPG":["btl"],
    "DPM":["atl","btl"],"PLX":["atl","btl"],"PVC":["atl","btl"],
    "GMD":["atl","btl"],"DGW":["atl","btl"],
    "MST":["none"],"HAG":["none"],
}

STOCKS = sorted(set(list(USER_JOURNAL.keys()) + [
    "DPM","DCM","GSP","GMD","NAF","EVF","OIL","POW","BFC","PAC",
    "PLX","MSR","MWG","PVT","PVD","BSR","NT2","PVS","PVC",
    "BIG","DGW","HPG","SZC","CTD","BIC","PVB","VHC","PNJ",
    "HHP","DCL","NDN","BAF","TTF","FIT","G36","HAG","PHR",
    "CTG","HDB","STB","MST",
]))
SKIP = {"TD6","TCX","PSX","FPT"}

BASE_LEN=30; VCP_SEG_LEN=7; PIVOT_LOOK=5; BARS_52=252
VOL_SURGE_MIN=150; NEAR_HIGH_PCT=25.0; HTF_MIN_GAIN=80.0
FWD_HORIZONS = {"T+2":2,"T+7":7,"T+14":14,"T+30":30,"T+60":60}
BENCHMARK="VNINDEX"; API_SLEEP=1.2

def sma(a,p):
    r=np.full(len(a),np.nan)
    for i in range(p-1,len(a)): r[i]=np.mean(a[i-p+1:i+1])
    return r
def ema_c(a,p):
    r=np.full(len(a),np.nan); k=2.0/(p+1)
    for i in range(len(a)):
        if not np.isnan(a[i]):
            r[i]=a[i]
            for j in range(i+1,len(a)): r[j]=a[j]*k+r[j-1]*(1-k)
            break
    return r
def calc_rsi(a,p=14):
    n2=len(a); rsi=np.full(n2,np.nan); d=np.diff(a,prepend=a[0])
    g=np.where(d>0,d,0.0); lo=np.where(d<0,-d,0.0)
    ag=np.full(n2,np.nan); al=np.full(n2,np.nan)
    if p<n2:
        ag[p]=np.mean(g[1:p+1]); al[p]=np.mean(lo[1:p+1])
        for j in range(p+1,n2): ag[j]=(ag[j-1]*(p-1)+g[j])/p; al[j]=(al[j-1]*(p-1)+lo[j])/p
        for j in range(p,n2):
            if al[j]==0: rsi[j]=100.0
            elif not np.isnan(ag[j]): rsi[j]=100-100/(1+ag[j]/al[j])
    return rsi

# Fetch benchmark
print("Fetching benchmark...", flush=True)
a_s = datetime.strptime(ANALYSIS_START,"%Y-%m-%d").date()
ds = (a_s-timedelta(days=600)).strftime("%Y-%m-%d")
de = (datetime.strptime(ANALYSIS_END,"%Y-%m-%d").date()+timedelta(days=50)).strftime("%Y-%m-%d")
try:
    qb=Quote(source="vci",symbol=BENCHMARK,show_log=False)
    db=qb.history(start=ds,end=de,interval="1D"); db['date']=pd.to_datetime(db['time']).dt.date
    bc_arr=db['close'].values.astype(float)
    bm50=sma(bc_arr,50); bm150=sma(bc_arr,150)
    bc_map=dict(zip(db['date'],bc_arr)); bm50_map=dict(zip(db['date'],bm50)); bm150_map=dict(zip(db['date'],bm150))
    print(f"  VNINDEX: {len(db)} bars")
except: bc_map={}; bm50_map={}; bm150_map={}

def analyze(symbol):
    a_start=datetime.strptime(ANALYSIS_START,"%Y-%m-%d").date()
    a_end=datetime.strptime(ANALYSIS_END,"%Y-%m-%d").date()
    d_s=(a_start-timedelta(days=600)).strftime("%Y-%m-%d")
    d_e=(a_end+timedelta(days=120)).strftime("%Y-%m-%d")
    try:
        q=Quote(source="vci",symbol=symbol,show_log=False)
        df=q.history(start=d_s,end=d_e,interval="1D")
    except Exception as e: print(f"\n  {symbol}... ERROR: {e}"); return []
    df['date']=pd.to_datetime(df['time']).dt.date
    df=df.sort_values('date').reset_index(drop=True); n=len(df)
    print(f"\n  {symbol}... {n} bars [{df['date'].iloc[0]}->{df['date'].iloc[-1]}]")
    if n<260: print(f"    Skip {symbol}: {n}<260"); return []

    O=df['open'].values.astype(float); H=df['high'].values.astype(float)
    L=df['low'].values.astype(float); C=df['close'].values.astype(float)
    V=df['volume'].values.astype(float)

    ma20=sma(C,20); ma50=sma(C,50); ma150=sma(C,150); ma200=sma(C,200)
    ema12=ema_c(C,12); ema36=ema_c(C,36)
    vol_ma20=sma(V,20); vol_ma=sma(V,50)
    rsi_w=calc_rsi(C,70)

    # RS
    perf=np.full(n,np.nan); bp=np.full(n,np.nan)
    for i in range(BARS_52,n):
        if C[i-BARS_52]>0: perf[i]=(C[i]-C[i-BARS_52])/C[i-BARS_52]*100
        d=df['date'].iloc[i]; d0=df['date'].iloc[i-BARS_52]
        b1=bc_map.get(d,np.nan); b0=bc_map.get(d0,np.nan)
        if not np.isnan(b1) and not np.isnan(b0) and b0>0: bp[i]=(b1-b0)/b0*100
    rs_raw=perf-bp
    rs_norm=np.full(n,np.nan)
    for i in range(BARS_52,n):
        w=rs_raw[max(0,i-BARS_52+1):i+1]; v=w[~np.isnan(w)]
        if len(v)>0:
            rn=v.max()-v.min()
            rs_norm[i]=100*(rs_raw[i]-v.min())/rn if rn>0 else 50

    # 52w high
    hi52=np.full(n,np.nan)
    for i in range(1,n):
        lb=min(BARS_52,i); hi52[i]=np.max(H[i-lb:i])
    dist52h=np.where(hi52>0,(C-hi52)/hi52*100,np.nan)
    near_high=(~np.isnan(dist52h))&(dist52h>=-NEAR_HIGH_PCT)

    # Trend
    cp_above=np.array([not np.isnan(ma50[i]) and C[i]>ma50[i] and C[i]>ma150[i] and C[i]>ma200[i] for i in range(n)])
    cm_stack=np.array([not np.isnan(ma50[i]) and ma50[i]>ma150[i] and ma150[i]>ma200[i] for i in range(n)])
    cm_slope=np.array([i>=5 and not np.isnan(ma50[i]) and ma50[i]>ma50[i-5] and ma150[i]>=ma150[i-5] for i in range(n)])
    c_rs_up=np.array([i>=5 and not np.isnan(rs_norm[i]) and not np.isnan(rs_norm[i-5]) and rs_norm[i]>rs_norm[i-5] for i in range(n)])
    c_vol=np.array([not np.isnan(vol_ma[i]) and vol_ma[i]>0 and V[i]>vol_ma[i] for i in range(n)])

    ts=np.zeros(n,dtype=int)
    ts+=np.where(cp_above,2,0); ts+=np.where(cm_stack,2,0)
    ts+=np.where(cm_slope,2,0); ts+=np.where(near_high,2,0)
    ts+=np.where(c_rs_up,1,0); ts+=np.where(c_vol,1,0)
    is_s2=ts>=8; is_s2ok=(ts>=5)&(ts<8)

    rs_strong=np.array([not np.isnan(rs_norm[i]) and rs_norm[i]>=80 for i in range(n)])
    rs_vs=np.array([not np.isnan(rs_norm[i]) and rs_norm[i]>=90 for i in range(n)])
    rs_ok=np.array([not np.isnan(rs_norm[i]) and rs_norm[i]>=60 for i in range(n)])

    # ZONES
    is_atl=cp_above&cm_stack
    ma30w=ma150.copy(); ma30w_sl=np.full(n,0.0)
    for i in range(10,n):
        if not np.isnan(ma30w[i]) and not np.isnan(ma30w[i-10]): ma30w_sl[i]=ma30w[i]-ma30w[i-10]
    w_s4=np.array([not np.isnan(ma30w[i]) and C[i]<ma30w[i] and ma30w_sl[i]<0 for i in range(n)])
    w_s2e=np.array([not np.isnan(ma30w[i]) and C[i]>ma30w[i] and ma30w_sl[i]>0 and C[i]>ma30w[i]*1.02 for i in range(n)])
    w_s1bo=np.zeros(n,dtype=bool)
    for i in range(1,n):
        if not np.isnan(ma30w[i]) and not np.isnan(vol_ma[i]):
            w_s1bo[i]=C[i]>ma30w[i] and C[i-1]<=ma30w[i-1] and V[i]>vol_ma[i]*1.3 if not np.isnan(ma30w[i-1]) else False

    # Switch & bars since
    sw_atl=np.zeros(n,dtype=bool)
    for i in range(1,n): sw_atl[i]=is_atl[i] and not is_atl[i-1]
    bs_atl=np.full(n,999)
    last=-999
    for i in range(n):
        if sw_atl[i]: last=i
        if last>=0: bs_atl[i]=i-last

    # ETL detection
    is_etl=np.zeros(n,dtype=bool)
    for i in range(n):
        c1=(not is_atl[i]) and (w_s2e[i] or w_s1bo[i])
        c2=is_atl[i] and bs_atl[i]<=30 and not is_s2[i]
        c3=False
        if not np.isnan(ma200[i]) and not np.isnan(ma150[i]) and not np.isnan(ma50[i]):
            c3=(not is_atl[i]) and C[i]>ma200[i] and ma30w_sl[i]>0 and (ma50[i]-ma150[i])/ma150[i]*100>-3 if ma150[i]>0 else False
        is_etl[i]=c1 or c2 or c3

    zone=np.full(n,"BTL",dtype=object)
    for i in range(n):
        if is_atl[i] and not is_etl[i]: zone[i]="ATL"
        elif is_etl[i]: zone[i]="ETL"

    # Breakouts
    bh=np.full(n,np.nan)
    for i in range(BASE_LEN+1,n): bh[i]=np.max(H[i-BASE_LEN:i])
    pp=bh.copy()
    vs_pct=np.where(vol_ma20>0,V/vol_ma20*100,0)
    hvs=vs_pct>=VOL_SURGE_MIN; hv130=vs_pct>=130

    # Pivot BO (anti-repaint) + state tracking for pullback
    bo_t=False; bo_b=-1; bo_p=0.0; is_bo=np.zeros(n,dtype=bool)
    bo_act=np.zeros(n,dtype=bool); bo_piv=np.full(n,np.nan); bo_bar2=np.full(n,-1,dtype=int)
    for i in range(1,n):
        if not np.isnan(pp[i]):
            reg=C[i]>pp[i] and C[i-1]<=pp[i]
            gp=(O[i]-C[i-1])/C[i-1]*100 if C[i-1]>0 else 0
            gap=O[i]>pp[i] and C[i-1]<=pp[i] and gp>=2
            ab=reg or gap; nh=pp[i]>bo_p*1.005
            if (not bo_t and ab) or (bo_t and nh and ab): bo_t=True; bo_b=i; bo_p=pp[i]
            if C[i]<pp[i]*0.97: bo_t=False; bo_b=-1; bo_p=0
            is_bo[i]=(bo_b==i)
        bo_act[i]=bo_t; bo_piv[i]=bo_p if bo_t else np.nan; bo_bar2[i]=bo_b if bo_t else -1

    # Darvas
    DL=20; dh=np.full(n,np.nan); dl=np.full(n,np.nan)
    for i in range(DL+1,n): dh[i]=np.max(H[i-DL:i]); dl[i]=np.min(L[i-DL:i])
    d_bo=np.zeros(n,dtype=bool)
    for i in range(1,n):
        if not np.isnan(dh[i]): d_bo[i]=C[i]>dh[i] and C[i-1]<=dh[i]
    any_bo=is_bo|d_bo

    # Market
    mkt_bull=np.zeros(n,dtype=bool); mkt_ok=np.zeros(n,dtype=bool)
    for i in range(n):
        d=df['date'].iloc[i]; bc=bc_map.get(d,np.nan); b50=bm50_map.get(d,np.nan); b150=bm150_map.get(d,np.nan)
        if not np.isnan(bc) and not np.isnan(b50): mkt_bull[i]=bc>b50
        if not np.isnan(bc) and not np.isnan(b150): mkt_ok[i]=bc>b150*0.97

    # Stops
    sp=np.full(n,99.0)
    for i in range(VCP_SEG_LEN,n):
        if np.isnan(bh[i]) or bh[i]<=0: continue
        vt=np.min(L[max(0,i-VCP_SEG_LEN+1):i+1])*0.99; f7=bh[i]*0.93
        sp[i]=(bh[i]-max(vt,f7))/bh[i]*100
    sok_a=sp<=8.0; sok_b=sp<=10.0

    ema_ab=np.array([not np.isnan(ema12[i]) and not np.isnan(ema36[i]) and ema12[i]>ema36[i] for i in range(n)])
    ema10=ema_c(C,10); ema21=ema_c(C,21)  # v2: add EMA21 for deep pullback

    # Pattern score (simplified)
    ps=np.zeros(n,dtype=int); pn=np.full(n,"NO SETUP",dtype=object)
    vdu=np.array([not np.isnan(vol_ma20[i]) and vol_ma20[i]>0 and V[i]<vol_ma20[i]*0.7 for i in range(n)])
    tight=np.full(n,np.nan)
    for i in range(VCP_SEG_LEN,n):
        seg=C[max(0,i-VCP_SEG_LEN+1):i+1]
        if len(seg)>0 and np.max(seg)>0: tight[i]=(np.max(seg)-np.min(seg))/np.max(seg)*100
    is_tg=np.array([not np.isnan(tight[i]) and tight[i]<5 for i in range(n)])
    tc=np.zeros(n,dtype=int)
    for i in range(VCP_SEG_LEN*3,n):
        segs=[]
        for s in range(3):
            si=i-VCP_SEG_LEN*(s+1)+1; ei=i-VCP_SEG_LEN*s+1
            sh=np.max(H[max(0,si):ei]); sl2=np.min(L[max(0,si):ei])
            segs.append((sh-sl2)/sh*100 if sh>0 else 0)
        tc[i]=len(segs) if all(segs[j]<segs[j+1] for j in range(len(segs)-1)) else 0
    has_vcp=tc>=2
    vh=np.array([not np.isnan(vol_ma20[i]) and vol_ma20[i]>0 and V[i]>=vol_ma20[i]*0.5 for i in range(n)])

    for i in range(BASE_LEN+1,n):
        bd=bh[i]-np.min(L[i-BASE_LEN:i]) if not np.isnan(bh[i]) else 99
        bd_pct=bd/bh[i]*100 if not np.isnan(bh[i]) and bh[i]>0 else 99
        ppv=(C[i]-np.min(L[i-BASE_LEN:i]))/(bh[i]-np.min(L[i-BASE_LEN:i]))*100 if not np.isnan(bh[i]) and (bh[i]-np.min(L[i-BASE_LEN:i]))>0 else 0
        tr=tight[i] if not np.isnan(tight[i]) else 99
        rb=10 if rs_vs[i] else (5 if rs_strong[i] else 0)
        is_asc=False
        if i>=PIVOT_LOOK*3:
            p1=np.min(L[i-PIVOT_LOOK+1:i+1]); p2=np.min(L[i-PIVOT_LOOK*2+1:i-PIVOT_LOOK+1])
            p3=np.min(L[i-PIVOT_LOOK*3+1:i-PIVOT_LOOK*2+1])
            is_asc=p1>p2 and p2>p3 and bd_pct<=35 and ppv>=50
        if has_vcp[i] and bd_pct<=35 and ppv>=70 and is_tg[i] and vdu[i]:
            pn[i]="VCP"; ps[i]=85+rb
        elif bd_pct<=15 and ppv>=80 and vh[i]:
            pn[i]="FLAT"; ps[i]=70+rb
        elif is_asc:
            pn[i]="ASC"; ps[i]=72+rb
        elif has_vcp[i] and ppv>=50:
            pn[i]="FORMING"; ps[i]=40+rb
        else: ps[i]=0+rb

    # Qualification
    t12q=is_s2&(ps>=77)
    ss=rs_vs&is_s2ok&cp_above&(cm_stack|np.array([not np.isnan(rs_norm[i]) and rs_norm[i]>=95 for i in range(n)]))
    rsq=ss&(ps>=50)
    isq=t12q|rsq
    etlq=(ps>=50)|ema_ab

    # === ATL BREAKOUT BUY (Grade A+) ===
    atl_buy=(zone=="ATL")&is_bo&hvs&mkt_bull&sok_a&isq&rs_strong

    # === ATL PULLBACK BUY v2 (Expanded: deeper pullback + wider window) ===
    # v2: bsince 2-20, EMA21 deep support, pivot+5%, stop 7%
    pb_buy=np.zeros(n,dtype=bool); pb_sp=np.full(n,99.0); pb_deep=np.zeros(n,dtype=bool)
    for i in range(2,n):
        if not bo_act[i] or bo_bar2[i]<0: continue
        bsince=i-bo_bar2[i]
        if bsince<2 or bsince>20: continue  # v2: expanded from 10->20
        pv2=bo_piv[i]
        if np.isnan(pv2) or pv2<=0: continue
        is_deep=(bsince>10)  # v2: deep pullback classification
        if is_deep:
            sup=max(ema21[i] if not np.isnan(ema21[i]) else 0, pv2*0.93)  # v2: EMA21, pivot-7%
        else:
            sup=max(ema10[i] if not np.isnan(ema10[i]) else 0, pv2*0.97)  # Original: EMA10, pivot-3%
        pulled=C[i]<=pv2*1.05; above=C[i]>=sup  # v2: pivot+5% (was +3%)
        vd_prev=not np.isnan(vol_ma[i]) and vol_ma[i]>0 and V[i-1]<vol_ma[i]*0.7
        bounce=C[i]>O[i] and C[i]>C[i-1]
        if pulled and above and vd_prev and bounce and mkt_bull[i]:
            sw_len=8 if is_deep else 5  # v2: wider lookback for deep PB
            sw5=np.min(L[max(0,i-sw_len+1):i+1])
            pbs=max(sw5*0.99, pv2*0.95)  # v2: pivot-5% (was -3%)
            pbp=(C[i]-pbs)/C[i]*100
            pb_sp[i]=pbp
            if pbp<=7: pb_buy[i]=True; pb_deep[i]=is_deep  # v2: stop 7% (was 5%)
    atl_pb=(zone=="ATL")&pb_buy&isq&rs_strong

    # === ATL LOW-CHEAT PIVOT (Grade A-) ===
    # Buy at contraction low pre-breakout, VCP T>=2, tight, vol dry
    lc_buy=np.zeros(n,dtype=bool); lc_sp2=np.full(n,99.0)
    for i in range(VCP_SEG_LEN,n):
        if tc[i]<2 or not vdu[i] or not is_tg[i]: continue
        cl=np.min(L[max(0,i-VCP_SEG_LEN+1):i+1])
        ch=np.max(H[max(0,i-VCP_SEG_LEN+1):i+1])
        cr=(ch-cl)/ch*100 if ch>0 else 99
        if cr>8: continue
        if C[i]>cl*1.02: continue  # Must be at contraction low
        if np.isnan(bh[i]) or bh[i]<=0: continue
        bl2=np.min(L[max(0,i-BASE_LEN):i]) if i>=BASE_LEN else np.nan
        if np.isnan(bl2): continue
        ppv2=(C[i]-bl2)/(bh[i]-bl2)*100 if (bh[i]-bl2)>0 else 0
        if ppv2<50: continue
        lcs=cl*0.98; lcp=(C[i]-lcs)/C[i]*100
        lc_sp2[i]=lcp
        if lcp<=4 and mkt_bull[i] and not bo_act[i]: lc_buy[i]=True
    atl_lc=(zone=="ATL")&lc_buy&isq&rs_strong

    # === ETL BUY (refined - lower thresholds) ===
    hv120=vs_pct>=120
    rs_50=np.array([not np.isnan(rs_norm[i]) and rs_norm[i]>=50 for i in range(n)])
    etlq2=(ps>=30)|ema_ab
    etl_buy=(zone=="ETL")&(is_bo|d_bo)&hv120&mkt_ok&(sok_a|sok_b)&rs_50&etlq2&~w_s4

    # === BTL BUY ===
    was_os=np.zeros(n,dtype=bool)
    for i in range(n):
        lb=min(30,i+1)
        was_os[i]=any(not np.isnan(rsi_w[j]) and rsi_w[j]<40 for j in range(max(0,i-lb+1),i+1))
    btl_buy=(zone=="BTL")&d_bo&hv130&mkt_ok&sok_b&ema_ab&was_os&~w_s4

    # === ETL PULLBACK (relaxed thresholds vs ATL) ===
    etl_pb=np.zeros(n,dtype=bool); etl_pb_sp=np.full(n,99.0)
    for i in range(2,n):
        if not bo_act[i] or bo_bar2[i]<0: continue
        bsince=i-bo_bar2[i]
        if bsince<2 or bsince>20: continue
        pv2=bo_piv[i]
        if np.isnan(pv2) or pv2<=0: continue
        is_deep=(bsince>10)
        if is_deep:
            sup=max(ema21[i] if not np.isnan(ema21[i]) else 0, pv2*0.93)
        else:
            sup=max(ema10[i] if not np.isnan(ema10[i]) else 0, pv2*0.97)
        pulled=C[i]<=pv2*1.05; above=C[i]>=sup
        vd_prev=not np.isnan(vol_ma[i]) and vol_ma[i]>0 and V[i-1]<vol_ma[i]*0.7
        bounce=C[i]>O[i] and C[i]>C[i-1]
        if pulled and above and vd_prev and bounce and mkt_ok[i]:
            sw_len=8 if is_deep else 5
            sw5=np.min(L[max(0,i-sw_len+1):i+1])
            pbs=max(sw5*0.99, pv2*0.95)
            pbp=(C[i]-pbs)/C[i]*100
            etl_pb_sp[i]=pbp
            if pbp<=8: etl_pb[i]=True  # ETL: 8% stop (vs ATL 7%)
    etl_pb=(zone=="ETL")&etl_pb&rs_50

    # === BTL PULLBACK (after Darvas breakout) ===
    # Track Darvas breakout state for pullback
    dbo_t=False; dbo_b=-1; dbo_act=np.zeros(n,dtype=bool); dbo_bar=np.full(n,-1,dtype=int)
    for i in range(1,n):
        if d_bo[i]: dbo_t=True; dbo_b=i
        if not np.isnan(dh[i]) and C[i]<dh[i]*0.95: dbo_t=False; dbo_b=-1
        dbo_act[i]=dbo_t; dbo_bar[i]=dbo_b if dbo_t else -1

    btl_pb=np.zeros(n,dtype=bool); btl_pb_sp=np.full(n,99.0)
    for i in range(2,n):
        if not dbo_act[i] or dbo_bar[i]<0: continue
        bsince=i-dbo_bar[i]
        if bsince<2 or bsince>15: continue
        if np.isnan(dh[i]) or np.isnan(dl[i]): continue
        sup=max(ema10[i] if not np.isnan(ema10[i]) else 0, dl[i])
        pulled=C[i]<=dh[i]*1.03; above=C[i]>=sup
        vd_prev=not np.isnan(vol_ma[i]) and vol_ma[i]>0 and V[i-1]<vol_ma[i]*0.7
        bounce=C[i]>O[i] and C[i]>C[i-1]
        if pulled and above and vd_prev and bounce and mkt_ok[i]:
            sw5=np.min(L[max(0,i-4):i+1])
            pbs=max(sw5*0.99, dl[i]*0.98)
            pbp=(C[i]-pbs)/C[i]*100
            btl_pb_sp[i]=pbp
            if pbp>=2 and pbp<=10: btl_pb[i]=True
    btl_pb=(zone=="BTL")&btl_pb&~is_etl

    # === RE-ENTRY AFTER STOP-OUT v2 ===
    # Track breakout resets and generate re-entry when structure intact
    re_buy=np.zeros(n,dtype=bool)
    was_stopped=False; stop_bar=-1
    for i in range(1,n):
        # Detect breakout reset (proxy for stop-out)
        if not bo_act[i] and bo_act[i-1]:
            was_stopped=True; stop_bar=i
        if was_stopped:
            bars_since_stop=i-stop_bar
            if bars_since_stop>=3 and bars_since_stop<=30:
                struct_ok=not np.isnan(ma50[i]) and C[i]>ma50[i] and not w_s4[i]
                rs_re_ok=not np.isnan(rs_norm[i]) and rs_norm[i]>=70
                bounce_re=C[i]>O[i] and C[i]>C[i-1]
                vol_re_ok=not np.isnan(vol_ma20[i]) and vol_ma20[i]>0 and V[i]>vol_ma20[i]*0.8
                mkt_re=mkt_bull[i]
                if struct_ok and rs_re_ok and bounce_re and vol_re_ok and mkt_re:
                    sw5=np.min(L[max(0,i-4):i+1])
                    re_stop=sw5*0.98
                    re_sp=(C[i]-re_stop)/C[i]*100
                    if re_sp>=3 and re_sp<=8:
                        re_buy[i]=True
                        was_stopped=False  # Reset after re-entry
            if bars_since_stop>40:
                was_stopped=False  # Timeout
    atl_re=(zone=="ATL")&re_buy
    etl_re=(zone=="ETL")&re_buy  # ETL re-entry uses same logic (RS>=70 filter from re_buy)

    # === BTL RE-ENTRY (after Darvas stop-out) ===
    btl_re=np.zeros(n,dtype=bool)
    btl_was_stopped=False; btl_stop_bar=-1
    for i in range(1,n):
        # Detect Darvas breakout reset + stop hit
        if not dbo_act[i] and dbo_act[i-1]:
            if not np.isnan(dl[i]) and C[i]<dl[i]*0.98:  # Stop hit
                btl_was_stopped=True; btl_stop_bar=i
        if btl_was_stopped:
            bss=i-btl_stop_bar
            if bss>=3 and bss<=30:
                struct_ok=(not np.isnan(ma150[i]) and C[i]>ma150[i]) or (not np.isnan(dl[i]) and C[i]>dl[i])
                bounce_re=C[i]>O[i] and C[i]>C[i-1]
                vol_re_ok=not np.isnan(vol_ma20[i]) and vol_ma20[i]>0 and V[i]>vol_ma20[i]*0.8
                if struct_ok and bounce_re and vol_re_ok and mkt_ok[i] and ema_ab[i] and not w_s4[i]:
                    sw5=np.min(L[max(0,i-4):i+1])
                    re_stop=sw5*0.98
                    re_sp=(C[i]-re_stop)/C[i]*100
                    if re_sp>=3 and re_sp<=10:
                        btl_re[i]=True
                        btl_was_stopped=False
            if bss>40:
                btl_was_stopped=False
    btl_re=(zone=="BTL")&btl_re&~is_etl

    # === COMBINED ===
    any_buy=atl_buy|atl_pb|atl_lc|etl_buy|btl_buy|atl_re|etl_re|etl_pb|btl_pb|btl_re
    gap_bo=(is_bo|d_bo)&~any_buy

    # Buy type label
    buy_type=np.full(n,"",dtype=object)
    for i in range(n):
        if atl_buy[i]: buy_type[i]="ATL_BO"
        elif atl_pb[i]: buy_type[i]="ATL_PB" if not pb_deep[i] else "ATL_PB_DEEP"
        elif atl_lc[i]: buy_type[i]="ATL_LC"
        elif atl_re[i]: buy_type[i]="ATL_RE"
        elif etl_buy[i]: buy_type[i]="ETL"
        elif etl_pb[i]: buy_type[i]="ETL_PB"
        elif etl_re[i]: buy_type[i]="ETL_RE"
        elif btl_buy[i]: buy_type[i]="BTL"
        elif btl_pb[i]: buy_type[i]="BTL_PB"
        elif btl_re[i]: buy_type[i]="BTL_RE"

    # Collect
    mask=(df['date']>=a_start)&(df['date']<=a_end)
    signals=[]
    for i in df[mask].index.tolist():
        fwd={}; fh=[]; fl=[]; fc=[]
        for lb,bars in FWD_HORIZONS.items():
            fi=i+bars
            if fi<n:
                fwd[lb]=(C[fi]-C[i])/C[i]*100
                fwd[f"{lb}_dd"]=(np.min(L[i+1:fi+1])-C[i])/C[i]*100
            else: fwd[lb]=np.nan; fwd[f"{lb}_dd"]=np.nan
        for j in range(1,61):
            fi=i+j
            if fi<n: fh.append(float(H[fi])); fl.append(float(L[fi])); fc.append(float(C[fi]))
            else: fh.append(np.nan); fl.append(np.nan); fc.append(np.nan)

        signals.append({
            "symbol":symbol,"date":df['date'].iloc[i],"close":C[i],"volume":V[i],
            "zone":zone[i],"trend_score":int(ts[i]),
            "rs_norm":rs_norm[i] if not np.isnan(rs_norm[i]) else None,
            "rs_strong":bool(rs_strong[i]),"rs_ok":bool(rs_ok[i]),
            "pattern":pn[i],"pattern_score":int(ps[i]),
            "prior_pivot":pp[i] if not np.isnan(pp[i]) else None,
            "stop_pct":sp[i] if sp[i]<90 else None,
            "vol_surge":vs_pct[i],"has_vol_surge":bool(hvs[i]),"has_vol_130":bool(hv130[i]),
            "market_bullish":bool(mkt_bull[i]),"market_ok":bool(mkt_ok[i]),
            "ema_above":bool(ema_ab[i]),
            "is_breakout":bool(is_bo[i]),"darvas_bo":bool(d_bo[i]),"any_breakout":bool(any_bo[i]),
            "is_qualified":bool(isq[i]),"etl_qualified":bool(etlq[i]),
            "w_stage4":bool(w_s4[i]),"w_stage2_early":bool(w_s2e[i]),
            "atl_buy":bool(atl_buy[i]),"atl_pb":bool(atl_pb[i]),"atl_lc":bool(atl_lc[i]),
            "atl_re":bool(atl_re[i]),
            "etl_buy":bool(etl_buy[i]),"etl_pb":bool(etl_pb[i]),"etl_re":bool(etl_re[i]),
            "btl_buy":bool(btl_buy[i]),"btl_pb":bool(btl_pb[i]),"btl_re":bool(btl_re[i]),
            "any_buy":bool(any_buy[i]),"gap_bo":bool(gap_bo[i]),
            "buy_type":buy_type[i],
            "fwd_highs":fh,"fwd_lows":fl,"fwd_closes":fc,**fwd,
        })
    return signals

# === MAIN ===
print("="*130)
print("3-ZONE ANALYSIS: BTL / ETL / ATL")
print(f"Stocks: {len(STOCKS)} | Period: {ANALYSIS_START} -> {ANALYSIS_END}")
print("="*130)

all_sig=[]
for sym in STOCKS:
    if sym in SKIP: print(f"\n  Skip {sym}"); continue
    r=analyze(sym)
    if r: all_sig.extend(r)
    time.sleep(API_SLEEP)

df_all=pd.DataFrame(all_sig)
print(f"\nTotal: {len(df_all)} points, {df_all['symbol'].nunique()} stocks")

# === REPORTING (imported from separate module) ===
exec(open(os.path.join(os.path.dirname(__file__),"zone_report.py"),encoding="utf-8").read())
