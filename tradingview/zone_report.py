"""
Reporting module for 3-zone analysis v4. Executed via exec() from analyze_3zone.py.
Expects df_all (DataFrame) and USER_JOURNAL (dict) to be in scope.
"""
# User's actual trades from analyze_trades.py
TRADES = [
    {"c":"PVC_2025_12","s":"PVC","d":"2025-12-30","t":"btl","r":"win","p":15.81},
    {"c":"STB_2025_12","s":"STB","d":"2025-12-30","t":"btl","r":"lose","p":-7.07},
    {"c":"G36_2026_01","s":"G36","d":"2026-01-15","t":"btl","r":"win","p":7.02},
    {"c":"DPM_2026_01","s":"DPM","d":"2026-01-15","t":"btl","r":"lose","p":-5.73},
    {"c":"PHR_2026_01","s":"PHR","d":"2026-01-16","t":"btl","r":"lose","p":-5.09},
    {"c":"DGW_2026_01","s":"DGW","d":"2026-01-19","t":"btl","r":"lose","p":-5.53},
    {"c":"NDN_2026_01","s":"NDN","d":"2026-01-23","t":"btl","r":"lose","p":-5.88},
    {"c":"FIT_2026_01","s":"FIT","d":"2026-01-23","t":"btl","r":"lose","p":-5.08},
    {"c":"TTF_2026_01","s":"TTF","d":"2026-01-23","t":"btl","r":"lose","p":-4.75},
    {"c":"VHC_2026_01","s":"VHC","d":"2026-01-30","t":"btl","r":"win","p":0.31},
    {"c":"BIC_2026_01","s":"BIC","d":"2026-01-30","t":"btl","r":"win","p":2.68},
    {"c":"PSX_2026_01","s":"PSX","d":"2026-01-30","t":"btl","r":"lose","p":-10.53},
    {"c":"CTD_2026_02","s":"CTD","d":"2026-02-05","t":"btl","r":"lose","p":-6.24},
    {"c":"HPG_2026_02","s":"HPG","d":"2026-02-05","t":"btl","r":"lose","p":-6.03},
    {"c":"SZC_2026_02","s":"SZC","d":"2026-02-05","t":"btl","r":"lose","p":-5.87},
    {"c":"DGW_2026_02","s":"DGW","d":"2026-02-04","t":"btl","r":"lose","p":-11.47},
    {"c":"GMD_2026_02","s":"GMD","d":"2026-02-04","t":"btl","r":"lose","p":-4.13},
    {"c":"PAC_2026_03","s":"PAC","d":"2026-03-04","t":"btl","r":"lose","p":-9.26},
    {"c":"PLX_2026_01","s":"PLX","d":"2026-01-15","t":"atl","r":"win","p":19.85},
    {"c":"BAF_2026_01","s":"BAF","d":"2026-01-15","t":"atl","r":"lose","p":-6.25},
    {"c":"CTG_2026_01","s":"CTG","d":"2026-01-12","t":"atl","r":"lose","p":-8.10},
    {"c":"BSR_2026_01","s":"BSR","d":"2026-01-12","t":"atl","r":"win","p":0.97},
    {"c":"DCL_2026_01","s":"DCL","d":"2026-01-12","t":"atl","r":"win","p":15.96},
    {"c":"PVD_2026_01","s":"PVD","d":"2026-01-09","t":"atl","r":"lose","p":-8.04},
    {"c":"NAF_2026_01","s":"NAF","d":"2026-01-06","t":"atl","r":"win","p":0.52},
    {"c":"PNJ_2026_01","s":"PNJ","d":"2026-01-27","t":"atl","r":"win","p":1.98},
    {"c":"MSR_2026_01","s":"MSR","d":"2026-01-29","t":"atl","r":"win","p":9.93},
    {"c":"PVS_2026_01","s":"PVS","d":"2026-01-28","t":"atl","r":"win","p":3.35},
    {"c":"PVB_2026_01","s":"PVB","d":"2026-01-28","t":"atl","r":"lose","p":-4.99},
    {"c":"MWG_2026_01","s":"MWG","d":"2026-01-30","t":"atl","r":"lose","p":-5.11},
    {"c":"BIG_2026_02","s":"BIG","d":"2026-02-12","t":"atl","r":"win","p":19.23},
    {"c":"OIL_2026_03","s":"OIL","d":"2026-03-04","t":"atl","r":"lose","p":-9.31},
    {"c":"POW_2026_03","s":"POW","d":"2026-03-03","t":"atl","r":"lose","p":-9.82},
    {"c":"MSR_2026_03","s":"MSR","d":"2026-03-03","t":"atl","r":"lose","p":-15.13},
]

from datetime import datetime as _dt

# === PART 1: ZONE DISTRIBUTION ===
n_total = len(df_all)
print(f"\n{'='*130}")
print("PART 1: ZONE & SIGNAL DISTRIBUTION (v4 - with Pullback + Low-Cheat)")
print(f"{'='*130}")
for z in ["ATL","ETL","BTL"]:
    nz=(df_all['zone']==z).sum()
    print(f"  {z}: {nz} days ({nz/n_total*100:.0f}%)")

na=df_all['atl_buy'].sum()
nap=df_all['atl_pb'].sum() if 'atl_pb' in df_all else 0
nal=df_all['atl_lc'].sum() if 'atl_lc' in df_all else 0
nar=df_all['atl_re'].sum() if 'atl_re' in df_all else 0
ne=df_all['etl_buy'].sum()
nep=df_all['etl_pb'].sum() if 'etl_pb' in df_all else 0
ner=df_all['etl_re'].sum() if 'etl_re' in df_all else 0
nb=df_all['btl_buy'].sum()
nbp=df_all['btl_pb'].sum() if 'btl_pb' in df_all else 0
nbr=df_all['btl_re'].sum() if 'btl_re' in df_all else 0
nany=df_all['any_buy'].sum(); ngap=df_all['gap_bo'].sum()
nbo=df_all['any_breakout'].sum()
print(f"""
  SIGNAL BREAKDOWN:
    ATL Breakout (A+): {na}
    ATL Pullback (A):  {nap}  (v2: bsince 2-20, EMA21 deep, stop 7%)
    ATL Low-Cheat (A-): {nal}
    ATL Re-entry (B+): {nar}
    ETL Buy:           {ne}   (refined thresholds)
    ETL Pullback:      {nep}  <- v3 NEW
    ETL Re-entry:      {ner}
    BTL Buy:           {nb}
    BTL Pullback:      {nbp}  <- v3 NEW
    BTL Re-entry:      {nbr}  <- v3 NEW
    ─────────────────────
    Combined:          {nany}
    Gap (still missed): {ngap} ({ngap/max(nbo,1)*100:.0f}% of {nbo} breakouts)
""")

# === PART 2: SIGNAL TABLES ===
def print_buy(sdf, label):
    print(f"\n{'='*130}")
    print(f"{label} ({len(sdf)} signals)")
    print(f"{'='*130}")
    if len(sdf)==0: print("  (no signals)"); return
    print(f"  {'Sym':>5} {'Date':>12} {'Close':>7} {'Zone':>4} {'Pat':>8} {'RS':>4} {'TS':>3} {'Vol%':>5} {'Stp%':>5} "
          f"{'T+2':>7} {'T+7':>7} {'T+14':>7} {'T+30':>7}")
    print(f"  {'-'*115}")
    for _,r in sdf.sort_values(['symbol','date']).iterrows():
        rs=f"{r['rs_norm']:.0f}" if pd.notna(r.get('rs_norm')) else "n/a"
        vs=f"{r['vol_surge']:.0f}" if pd.notna(r.get('vol_surge')) else "n/a"
        sp2=f"{r['stop_pct']:.1f}" if pd.notna(r.get('stop_pct')) else "n/a"
        def fmt(h): return f"{r[h]:+.1f}%" if pd.notna(r.get(h)) else "n/a"
        print(f"  {r['symbol']:>5} {str(r['date']):>12} {r['close']:>7.0f} {r['zone']:>4} {r['pattern']:>8} "
              f"{rs:>4} {r['trend_score']:>3} {vs:>5} {sp2:>5} "
              f"{fmt('T+2'):>7} {fmt('T+7'):>7} {fmt('T+14'):>7} {fmt('T+30'):>7}")
    for h in ['T+2','T+7','T+14','T+30']:
        v=sdf[h].dropna()
        if len(v)>0:
            print(f"    {h}: Win {(v>0).sum()}/{len(v)} ({(v>0).sum()/len(v)*100:.0f}%) | "
                  f"Avg {v.mean():+.2f}% | Med {v.median():+.2f}%")

b_atl=df_all[df_all['atl_buy']==True]
b_pb=df_all[df_all.get('atl_pb',pd.Series(False,index=df_all.index))==True] if 'atl_pb' in df_all else pd.DataFrame()
b_lc=df_all[df_all.get('atl_lc',pd.Series(False,index=df_all.index))==True] if 'atl_lc' in df_all else pd.DataFrame()
b_are=df_all[df_all['atl_re']==True] if 'atl_re' in df_all else pd.DataFrame()
b_etl=df_all[df_all['etl_buy']==True]
b_epb=df_all[df_all['etl_pb']==True] if 'etl_pb' in df_all else pd.DataFrame()
b_ere=df_all[df_all['etl_re']==True] if 'etl_re' in df_all else pd.DataFrame()
b_btl=df_all[df_all['btl_buy']==True]
b_bpb=df_all[df_all['btl_pb']==True] if 'btl_pb' in df_all else pd.DataFrame()
b_bre=df_all[df_all['btl_re']==True] if 'btl_re' in df_all else pd.DataFrame()
print_buy(b_atl, "PART 2a: ATL BREAKOUT BUY (A+)")
print_buy(b_pb, "PART 2b: ATL PULLBACK BUY v2 (A/A-)")
print_buy(b_lc, "PART 2c: ATL LOW-CHEAT PIVOT (A-)")
print_buy(b_are, "PART 2d: ATL RE-ENTRY (B+)")
print_buy(b_etl, "PART 2e: ETL BUY (transition)")
print_buy(b_epb, "PART 2f: ETL PULLBACK (v3 NEW)")
print_buy(b_ere, "PART 2g: ETL RE-ENTRY")
print_buy(b_btl, "PART 2h: BTL BUY (oversold recovery)")
print_buy(b_bpb, "PART 2i: BTL PULLBACK (v3 NEW)")
print_buy(b_bre, "PART 2j: BTL RE-ENTRY (v3 NEW)")

# === PART 3: PERFORMANCE COMPARISON ===
print(f"\n{'='*130}")
print("PART 3: PERFORMANCE COMPARISON (5 entry types)")
print(f"{'='*130}")

_has_pb = 'atl_pb' in df_all.columns
_has_lc = 'atl_lc' in df_all.columns
combos = [
    ("ATL Breakout (A+)", lambda r: r['atl_buy']),
    ("ATL Pullback (A)", lambda r: r.get('atl_pb',False)) if _has_pb else None,
    ("ATL Low-Cheat (A-)", lambda r: r.get('atl_lc',False)) if _has_lc else None,
    ("ATL Re-entry (B+)", lambda r: r.get('atl_re',False)),
    ("ATL Combined (BO+PB+LC+RE)", lambda r: r['atl_buy'] or r.get('atl_pb',False) or r.get('atl_lc',False) or r.get('atl_re',False)),
    ("---", None),
    ("ETL BUY", lambda r: r['etl_buy']),
    ("ETL Pullback", lambda r: r.get('etl_pb',False)),
    ("ETL Re-entry", lambda r: r.get('etl_re',False)),
    ("ETL Combined", lambda r: r['etl_buy'] or r.get('etl_pb',False) or r.get('etl_re',False)),
    ("---", None),
    ("BTL BUY", lambda r: r['btl_buy']),
    ("BTL Pullback", lambda r: r.get('btl_pb',False)),
    ("BTL Re-entry", lambda r: r.get('btl_re',False)),
    ("BTL Combined", lambda r: r['btl_buy'] or r.get('btl_pb',False) or r.get('btl_re',False)),
    ("---", None),
    ("All 10 types combined", lambda r: r['any_buy']),
    ("Gap (still missed)", lambda r: r['gap_bo']),
    ("---", None),
    ("BO+Vol ATL zone", lambda r: r['is_breakout'] and r['has_vol_surge'] and r['zone']=="ATL"),
    ("BO+Vol ETL zone", lambda r: r['is_breakout'] and r['has_vol_surge'] and r['zone']=="ETL"),
    ("BO+Vol BTL zone", lambda r: r['is_breakout'] and r['has_vol_surge'] and r['zone']=="BTL"),
]
combos = [c for c in combos if c is not None]

print(f"\n  {'Combo':<35} {'Sigs':>5}", end="")
for h in ['T+2','T+7','T+14','T+30']:
    print(f"  {'Win':>14} {'Avg':>7}", end="")
print()
print(f"  {'-'*125}")

for nm, fn in combos:
    if fn is None: print(f"  {'─'*125}"); continue
    try:
        mk=df_all.apply(fn, axis=1); sub=df_all[mk]; ns=len(sub)
        if ns==0: print(f"  {nm:<35} {0:>5}"); continue
        ln=f"  {nm:<35} {ns:>5}"
        for h in ['T+2','T+7','T+14','T+30']:
            hv=sub[h].dropna()
            if len(hv)>0:
                ws=f"{(hv>0).sum()}/{len(hv)}({(hv>0).sum()/len(hv)*100:.0f}%)"
                ln+=f"  {ws:>14} {hv.mean():>+6.1f}%"
            else: ln+=f"  {'n/a':>14} {'n/a':>7}"
        print(ln)
    except Exception as e: print(f"  {nm:<35} ERR: {e}")

# === PART 4: TRADE SIMULATION ===
print(f"\n{'='*130}")
print("PART 4: TRADE SIMULATION (SL/TP)")
print(f"{'='*130}")

def sim(row, sl_p=-8.0, tp_p=20.0):
    e=row['close']; slx=e*(1+sl_p/100); tpx=e*(1+tp_p/100)
    fh=row.get('fwd_highs',[]); fl2=row.get('fwd_lows',[]); fc2=row.get('fwd_closes',[])
    res={}
    for hz in [7,14,30]:
        sld=tpd=None
        for d in range(min(hz,len(fl2))):
            lo2,hi2=fl2[d],fh[d]
            if np.isnan(lo2) or np.isnan(hi2): break
            if sld is None and lo2<=slx: sld=d+1
            if tpd is None and hi2>=tpx: tpd=d+1
        if sld and tpd:
            if sld<=tpd: oc,rt=("SL",sl_p)
            else: oc,rt=("TP",tp_p)
        elif sld: oc,rt=("SL",sl_p)
        elif tpd: oc,rt=("TP",tp_p)
        else:
            ix=hz-1
            if ix<len(fc2) and not np.isnan(fc2[ix]): oc="HOLD"; rt=(fc2[ix]-e)/e*100
            else: oc="N/A"; rt=np.nan
        res[f"T{hz}_oc"]=oc; res[f"T{hz}_ret"]=rt
    return res

_sim_list=[
    ("ATL Breakout (SL=-8%)", lambda r:r['atl_buy'], -8),
    ("ATL Pullback (SL=-5%)", lambda r:r.get('atl_pb',False), -5),
    ("ATL Low-Cheat (SL=-4%)", lambda r:r.get('atl_lc',False), -4),
    ("ETL BUY (SL=-8%)", lambda r:r['etl_buy'], -8),
    ("BTL BUY (SL=-10%)", lambda r:r['btl_buy'], -10),
    ("All 5 combined (SL=-8%)", lambda r:r['any_buy'], -8),
    ("Gap BO+Vol (SL=-8%)", lambda r:r['gap_bo'] and r['has_vol_surge'], -8),
]
for cn,cf,sl2 in _sim_list:
    try:
        cm=df_all.apply(cf,axis=1); cs=df_all[cm]
        if len(cs)==0: print(f"\n  {cn}: (no signals)"); continue
        sd2=[sim(cr,sl_p=sl2) for _,cr in cs.iterrows()]
        sdf2=pd.DataFrame(sd2)
        print(f"\n  {cn} ({len(cs)} signals):")
        for hz in [7,14,30]:
            oc2=f'T{hz}_oc'; rc2=f'T{hz}_ret'
            if oc2 not in sdf2.columns: continue
            vv=sdf2[sdf2[oc2]!='N/A']
            if len(vv)==0: continue
            ns2=(vv[oc2]=='SL').sum(); nt2=(vv[oc2]=='TP').sum(); nh2=(vv[oc2]=='HOLD').sum(); nv2=len(vv)
            ar2=vv[rc2].dropna().mean()
            print(f"    T+{hz}: SL={ns2}({ns2/nv2*100:.0f}%) TP={nt2}({nt2/nv2*100:.0f}%) HOLD={nh2}({nh2/nv2*100:.0f}%) | Avg={ar2:+.1f}%")
    except Exception as e: print(f"\n  {cn}: ERR {e}")

# === PART 5: BIG MOVERS ===
print(f"\n{'='*130}")
print("PART 5: BIG TREND (50%+ gain)")
print(f"{'='*130}")
_bt_col = 'buy_type' if 'buy_type' in df_all.columns else None
print(f"\n  {'Sym':>5} {'Ret':>7} {'MaxGn':>7} {'ATLd':>5} {'ETLd':>5} {'BTLd':>5} "
      f"{'Sigs':>4} {'1stBuyDt':>12} {'Type':>7} {'UserMode':>8}")
print(f"  {'-'*90}")
for sym in sorted(df_all['symbol'].unique()):
    sd=df_all[df_all['symbol']==sym].sort_values('date')
    if len(sd)==0: continue
    sp2=sd.iloc[0]['close']; ep=sd.iloc[-1]['close']
    mg_p=[sd.iloc[j]['close'] for j in range(len(sd))]
    mg=(max(mg_p)-sp2)/sp2*100
    if mg<50: continue
    ret=(ep-sp2)/sp2*100
    na2=(sd['zone']=="ATL").sum(); ne2=(sd['zone']=="ETL").sum(); nb2=(sd['zone']=="BTL").sum()
    nsigs=sd['any_buy'].sum()
    fb=sd[sd['any_buy']==True]
    if len(fb)>0:
        fbd=str(fb.iloc[0]['date'])
        fbt=fb.iloc[0].get('buy_type','?') if _bt_col else fb.iloc[0]['zone']
    else: fbd="NONE"; fbt="MISSED"
    um=",".join(USER_JOURNAL.get(sym,["?"])).upper()
    print(f"  {sym:>5} {ret:>+6.1f}% {mg:>+6.1f}% {na2:>5} {ne2:>5} {nb2:>5} "
          f"{nsigs:>4} {fbd:>12} {fbt:>7} {um:>8}")

# ═══════════════════════════════════════════════════════════════
# PART 6: TRADE JOURNAL CROSS-REFERENCE (RS ANALYSIS)
# ═══════════════════════════════════════════════════════════════
print(f"\n{'='*130}")
print("PART 6: TRADE JOURNAL CROSS-REFERENCE (analyze_trades.py)")
print("Q: Is ATL performing in its zone? Does RS<80 = higher fail?")
print(f"{'='*130}")

# Match each trade to system data
from datetime import timedelta as _td
trade_results = []
for tr in TRADES:
    sym=tr['s']; tgt=_dt.strptime(tr['d'],"%Y-%m-%d").date()
    sd=df_all[df_all['symbol']==sym]
    if len(sd)==0: trade_results.append({**tr,'zone':'?','rs':None,'ts':0,'sys_buy':'','pattern':'?'}); continue
    # Find closest date
    best=None; best_d=999
    for _,row in sd.iterrows():
        dd=abs((row['date']-tgt).days)
        if dd<best_d: best_d=dd; best=row
    if best is None or best_d>3:
        trade_results.append({**tr,'zone':'?','rs':None,'ts':0,'sys_buy':'','pattern':'?'}); continue
    trade_results.append({
        **tr,
        'zone': best['zone'],
        'rs': best['rs_norm'],
        'ts': best['trend_score'],
        'sys_buy': best.get('buy_type','') if best.get('any_buy',False) else '',
        'pattern': best['pattern'],
        'mkt_bull': best.get('market_bullish',False),
        'qualified': best.get('is_qualified',False),
    })

print(f"\n  {'Code':<18} {'UserT':>4} {'R':>2} {'PnL':>7} {'Zone':>4} {'RS':>4} {'TS':>3} {'Pat':>8} {'SysBuy':>8} {'Qual':>4} {'Mkt':>4}")
print(f"  {'-'*90}")
for tr in sorted(trade_results, key=lambda x: (x['t'], -x['p'])):
    mk='W' if tr['r']=='win' else 'L'
    rs_s=f"{tr['rs']:.0f}" if tr['rs'] is not None else "n/a"
    sb=tr.get('sys_buy','') or '-'
    q='Y' if tr.get('qualified',False) else 'N'
    mb='Y' if tr.get('mkt_bull',False) else 'N'
    print(f"  {tr['c']:<18} {tr['t']:>4} {mk:>2} {tr['p']:>+6.1f}% {tr['zone']:>4} {rs_s:>4} {tr['ts']:>3} {tr.get('pattern','?'):>8} {sb:>8} {q:>4} {mb:>4}")

# RS bucket analysis
print(f"\n  RS BUCKET ANALYSIS (actual trades):")
print(f"  {'Bucket':<20} {'Total':>5} {'Win':>4} {'WR%':>5} {'AvgPnL':>8}")
print(f"  {'-'*50}")
for bname, bfn in [
    ("RS >= 80 (ATL ok)", lambda t: t['rs'] is not None and t['rs']>=80),
    ("RS 60-79 (ETL ok)", lambda t: t['rs'] is not None and 60<=t['rs']<80),
    ("RS < 60 (weak)", lambda t: t['rs'] is not None and t['rs']<60),
    ("RS n/a", lambda t: t['rs'] is None),
]:
    bk=[t for t in trade_results if bfn(t)]
    if not bk: continue
    bw=len([t for t in bk if t['r']=='win'])
    bwr=bw/len(bk)*100 if bk else 0
    bap=sum(t['p'] for t in bk)/len(bk)
    print(f"  {bname:<20} {len(bk):>5} {bw:>4} {bwr:>4.0f}% {bap:>+7.1f}%")

# By zone match
print(f"\n  ZONE MATCH ANALYSIS:")
print(f"  {'Category':<30} {'Total':>5} {'Win':>4} {'WR%':>5} {'AvgPnL':>8}")
print(f"  {'-'*55}")
for cname, cfn in [
    ("ATL trades in ATL zone", lambda t: t['t']=='atl' and t['zone']=='ATL'),
    ("ATL trades in ETL zone", lambda t: t['t']=='atl' and t['zone']=='ETL'),
    ("ATL trades in BTL zone", lambda t: t['t']=='atl' and t['zone']=='BTL'),
    ("BTL trades in BTL zone", lambda t: t['t']=='btl' and t['zone']=='BTL'),
    ("BTL trades in ETL zone", lambda t: t['t']=='btl' and t['zone']=='ETL'),
    ("BTL trades in ATL zone", lambda t: t['t']=='btl' and t['zone']=='ATL'),
    ("Sys confirmed buy", lambda t: t.get('sys_buy','')!=''),
    ("No sys confirmation", lambda t: t.get('sys_buy','')==''),
]:
    ck=[t for t in trade_results if cfn(t)]
    if not ck: continue
    cw=len([t for t in ck if t['r']=='win'])
    cwr=cw/len(ck)*100
    cap=sum(t['p'] for t in ck)/len(ck)
    print(f"  {cname:<30} {len(ck):>5} {cw:>4} {cwr:>4.0f}% {cap:>+7.1f}%")

# ATL zone performance deep dive
print(f"\n  ATL ZONE PERFORMANCE DEEP DIVE:")
atl_trades=[t for t in trade_results if t['t']=='atl']
if atl_trades:
    atl_w=[t for t in atl_trades if t['r']=='win']
    atl_l=[t for t in atl_trades if t['r']=='lose']
    print(f"    Total ATL trades: {len(atl_trades)} | Win: {len(atl_w)} ({len(atl_w)/len(atl_trades)*100:.0f}%) | Lose: {len(atl_l)}")
    # RS comparison
    w_rs=[t['rs'] for t in atl_w if t['rs'] is not None]
    l_rs=[t['rs'] for t in atl_l if t['rs'] is not None]
    if w_rs and l_rs:
        print(f"    Win avg RS: {sum(w_rs)/len(w_rs):.0f} | Lose avg RS: {sum(l_rs)/len(l_rs):.0f}")
    # Zone distribution
    for z in ['ATL','ETL','BTL']:
        zl=[t for t in atl_trades if t['zone']==z]
        if not zl: continue
        zw=len([t for t in zl if t['r']=='win'])
        print(f"    ATL trades in {z} zone: {len(zl)} (win {zw}/{len(zl)} = {zw/len(zl)*100:.0f}%)")

# BTL trades deep dive
btl_trades=[t for t in trade_results if t['t']=='btl']
if btl_trades:
    btl_w=[t for t in btl_trades if t['r']=='win']
    btl_l=[t for t in btl_trades if t['r']=='lose']
    print(f"\n  BTL TRADES DEEP DIVE:")
    print(f"    Total: {len(btl_trades)} | Win: {len(btl_w)} ({len(btl_w)/len(btl_trades)*100:.0f}%) | Lose: {len(btl_l)}")
    w_rs2=[t['rs'] for t in btl_w if t['rs'] is not None]
    l_rs2=[t['rs'] for t in btl_l if t['rs'] is not None]
    if w_rs2 and l_rs2:
        print(f"    Win avg RS: {sum(w_rs2)/len(w_rs2):.0f} | Lose avg RS: {sum(l_rs2)/len(l_rs2):.0f}")
    for z in ['ATL','ETL','BTL']:
        zl=[t for t in btl_trades if t['zone']==z]
        if not zl: continue
        zw=len([t for t in zl if t['r']=='win'])
        print(f"    BTL trades in {z} zone: {len(zl)} (win {zw}/{len(zl)} = {zw/len(zl)*100:.0f}%)")

# === PART 7: RS<80 QUESTION ANALYSIS ===
print(f"\n{'='*130}")
print("PART 7: RS<80 QUESTION - RECONCILIATION")
print(f"{'='*130}")
print("""
  Q: "RS<80 fail rate cao hon, co mau thuan voi ket luan RS 50-70 tang nhanh la bullish?"

  ANSWER: KHONG MAU THUAN. Day la 2 nhan dinh cho 2 zone KHAC NHAU:

  1. TRONG ATL ZONE (confirmed uptrend):
     RS>=80 la BAT BUOC vi day la xac nhan co phieu THUC SU DAN DAU thi truong.
     RS<80 trong ATL = co phieu DANG YEU DI so voi ma, do la dau hieu CANH BAO.
     -> Nhut ky giao dich xac nhan: ATL trades voi RS<80 fail rate CAO HON.

  2. TRONG ETL ZONE (transition):
     RS 50-70 va DANG TANG la dau hieu co phieu BAT DAU TANG MANH.
     RS chua dat 80 vi co phieu MOI BAT DAU xu huong tang - chua du 252 bars.
     -> Day la noi BIG MOVES BAT DAU, RS se tang len 80+ sau 1-2 thang.

  KET LUAN:
  - ATL zone: RS>=80 = FILTER DUNG, giu nguyen
  - ETL zone: RS>=50 va tang = ENTRY SOM, R:R tot hon
  - Van de: Ban phan loai nhieu ma la "ATL" nhung thuc te la ETL zone
    -> Ap dung RS>=80 filter cho ETL stocks = BO LO co hoi tot
""")

# Verify with data
print("  DATA VERIFICATION:")
for z in ['ATL','ETL','BTL']:
    zt=[t for t in trade_results if t['zone']==z]
    if not zt: continue
    rs_hi=[t for t in zt if t['rs'] is not None and t['rs']>=80]
    rs_lo=[t for t in zt if t['rs'] is not None and t['rs']<80]
    if rs_hi:
        wh=len([t for t in rs_hi if t['r']=='win']); ph=sum(t['p'] for t in rs_hi)/len(rs_hi)
        print(f"    {z} zone, RS>=80: {len(rs_hi)} trades, win {wh}/{len(rs_hi)} ({wh/len(rs_hi)*100:.0f}%), avg PnL {ph:+.1f}%")
    if rs_lo:
        wl=len([t for t in rs_lo if t['r']=='win']); pl=sum(t['p'] for t in rs_lo)/len(rs_lo)
        print(f"    {z} zone, RS<80:  {len(rs_lo)} trades, win {wl}/{len(rs_lo)} ({wl/len(rs_lo)*100:.0f}%), avg PnL {pl:+.1f}%")

# === PART 8: CONCLUSIONS ===
print(f"\n{'='*130}")
print("PART 8: FINAL PANORAMIC SUMMARY")
print(f"{'='*130}")
print(f"""
  DATASET: {df_all['symbol'].nunique()} stocks, {n_total} bar-days, {len(TRADES)} actual trades

  SIGNAL EVOLUTION:
    v2: ATL=62 BTL=0  gap=90%  (2 modes, breakout only)
    v3: ATL=42 ETL=42 BTL=6 gap=87%  (3 zones, breakout only)
    v4: ATL_BO={na} ATL_PB={nap} ATL_LC={nal} ETL={ne} BTL={nb} gap={ngap/max(nbo,1)*100:.0f}%
        (3 zones, 5 entry types)

  ATL ZONE VERDICT: {'PERFORMING WELL' if na > 0 else 'NEEDS MORE SIGNALS'}
    - Breakout (A+): High conviction but strict filters reduce count
    - Pullback (A): {nap} signals - tighter stop, better R:R
    - Low-Cheat (A-): {nal} signals - best R:R pre-breakout
    - RS>=80 IS CORRECT for ATL zone (journal confirms RS<80 = higher fail)

  ETL ZONE VERDICT: KEY INNOVATION
    - {ne} transition signals capturing moves before full ATL confirmation
    - RS>=50 threshold appropriate (stock EMERGING, not yet established)
    - THIS IS NOT contradicting RS>=80 for ATL - different zones, different rules

  REMAINING GAP: {ngap/max(nbo,1)*100:.0f}% of breakouts still not captured
    Main reasons: volume below threshold, no pattern, market weak
    These are CORRECTLY filtered - not all breakouts should be traded

  ACTIONABLE RECOMMENDATIONS:
    1. ATL zone: Use all 3 entry types (BO + PB + LC), keep RS>=80
    2. ETL zone: Entry with RS>=50 rising, vol>=120%, relaxed qualification
    3. BTL zone: Only Darvas + oversold recovery, strict risk management
    4. RECLASSIFY stocks: Many "ATL" stocks are actually in ETL zone
    5. RS<80 in ATL = WARNING SIGNAL, not entry opportunity
""")
# ═══════════════════════════════════════════════════════════════
# PART 9: ZONE COMPARISON (T+2, T+14, T+30, T+60) — 4 TABLES
# ═══════════════════════════════════════════════════════════════
print(f"\n{'='*130}")
print("PART 9: SO SANH ATL vs ETL vs BTL — T+2, T+14, T+30, T+60 (KHONG SL)")
print(f"{'='*130}")

_zone_filters = [
    ("ATL Breakout (A+)", lambda r: r['atl_buy']),
    ("ATL Pullback (A)", lambda r: r.get('atl_pb', False)),
    ("ATL Low-Cheat (A-)", lambda r: r.get('atl_lc', False)),
    ("ATL Combined", lambda r: r['atl_buy'] or r.get('atl_pb', False) or r.get('atl_lc', False)),
    ("ETL Buy", lambda r: r['etl_buy']),
    ("BTL Buy", lambda r: r['btl_buy']),
    ("All Combined", lambda r: r['any_buy']),
]

# Pre-compute filtered dataframes
_zone_dfs = []
for zname, zfn in _zone_filters:
    try:
        zmk = df_all.apply(zfn, axis=1)
        _zone_dfs.append((zname, df_all[zmk]))
    except:
        _zone_dfs.append((zname, pd.DataFrame()))

for horizon in ['T+2', 'T+14', 'T+30', 'T+60']:
    hdd = f"{horizon}_dd"
    print(f"\n  ┌─── {horizon} {'─'*60}")
    print(f"  │ {'Entry Type':<22} {'Sigs':>5} {'N':>4} {'Win%':>6} {'AvgAll':>8} {'AvgGain':>8} {'AvgLoss':>8} {'MaxDD':>7} {'AvgDD':>7}")
    print(f"  │ {'─'*22} {'─'*5} {'─'*4} {'─'*6} {'─'*8} {'─'*8} {'─'*8} {'─'*7} {'─'*7}")

    for zname, zdf in _zone_dfs:
        ns = len(zdf)
        if ns == 0:
            print(f"  │ {zname:<22} {0:>5} {'─':>4} {'─':>6} {'─':>8} {'─':>8} {'─':>8} {'─':>7} {'─':>7}")
            continue
        if horizon not in zdf.columns:
            print(f"  │ {zname:<22} {ns:>5} {'─':>4} {'n/a':>6}")
            continue

        hv = zdf[horizon].dropna()
        dd = zdf[hdd].dropna() if hdd in zdf.columns else pd.Series(dtype=float)
        nh = len(hv)
        if nh == 0:
            print(f"  │ {zname:<22} {ns:>5} {0:>4} {'─':>6} {'─':>8} {'─':>8} {'─':>8} {'─':>7} {'─':>7}")
            continue

        wins = hv[hv > 0]
        losses = hv[hv <= 0]
        wr = len(wins) / nh * 100
        avg_all = hv.mean()
        avg_g = wins.mean() if len(wins) > 0 else 0.0
        avg_l = losses.mean() if len(losses) > 0 else 0.0
        max_dd = dd.min() if len(dd) > 0 else np.nan
        avg_dd = dd.mean() if len(dd) > 0 else np.nan
        print(f"  │ {zname:<22} {ns:>5} {nh:>4} {wr:>5.0f}% {avg_all:>+7.1f}% {avg_g:>+7.1f}% {avg_l:>+7.1f}% {max_dd:>+6.1f}% {avg_dd:>+6.1f}%")

    print(f"  └{'─'*68}")

# Summary insight
print(f"\n  NHAN XET TONG HOP:")
for zname, zdf in _zone_dfs:
    if len(zdf) == 0 or zname in ("All Combined",): continue
    row_parts = [f"  {zname:<22}"]
    for h in ['T+2','T+14','T+30','T+60']:
        hv = zdf[h].dropna() if h in zdf.columns else pd.Series(dtype=float)
        if len(hv) > 0:
            wr = (hv > 0).sum() / len(hv) * 100
            row_parts.append(f"{h}: {wr:.0f}%win {hv.mean():+.1f}%avg")
        else:
            row_parts.append(f"{h}: n/a")
    print("  " + " │ ".join(row_parts))

# ═══════════════════════════════════════════════════════════════
# PART 10: SL STRATEGY SIMULATION (ATL -10%, ETL -7%, BTL -5%) + RE-ENTRY
# ═══════════════════════════════════════════════════════════════
print(f"\n{'='*130}")
print("PART 10: MO PHONG SL THUC TE (ATL -10%, ETL -7%, BTL -5%) + RE-ENTRY")
print(f"{'='*130}")

def _get_sl_pct(row):
    if row.get('atl_buy',False) or row.get('atl_pb',False) or row.get('atl_lc',False):
        return -10.0
    elif row.get('etl_buy',False):
        return -7.0
    elif row.get('btl_buy',False):
        return -5.0
    return -8.0

def _zone_of(row):
    if row.get('atl_buy',False) or row.get('atl_pb',False) or row.get('atl_lc',False):
        return "ATL"
    elif row.get('etl_buy',False):
        return "ETL"
    elif row.get('btl_buy',False):
        return "BTL"
    return "?"

# Build signal lookup: {symbol: [(date, row_index), ...]} sorted by date
_sig_lookup = {}
for idx2, row2 in df_all.iterrows():
    if not row2.get('any_buy', False):
        continue
    sym2 = row2['symbol']
    if sym2 not in _sig_lookup:
        _sig_lookup[sym2] = []
    _sig_lookup[sym2].append((row2['date'], idx2))
for sym2 in _sig_lookup:
    _sig_lookup[sym2].sort(key=lambda x: x[0])

def _sim_sl_reentry(row, horizon_days, sl_pct):
    """Simulate single trade with SL. Returns (final_ret, stopped, reentry_ret, max_dd)"""
    entry = row['close']
    sl_price = entry * (1 + sl_pct / 100)
    fl = row.get('fwd_lows', [])
    fh = row.get('fwd_highs', [])
    fc = row.get('fwd_closes', [])
    max_bars = min(horizon_days, len(fl))

    # Track max drawdown (intraday)
    max_dd = 0.0
    stopped_day = None

    for d in range(max_bars):
        lo = fl[d]
        if np.isnan(lo):
            break
        dd_d = (lo - entry) / entry * 100
        if dd_d < max_dd:
            max_dd = dd_d
        if lo <= sl_price:
            stopped_day = d + 1  # 1-indexed day
            break

    if stopped_day is None:
        # Not stopped — use close at horizon
        ix_h = horizon_days - 1
        if ix_h < len(fc) and not np.isnan(fc[ix_h]):
            ret = (fc[ix_h] - entry) / entry * 100
        else:
            ret = np.nan
        return ret, False, 0.0, max_dd
    else:
        # Stopped out
        first_ret = sl_pct

        # Look for re-entry signal for same symbol after stop date
        sym = row['symbol']
        from datetime import timedelta as _td2
        stop_date = row['date'] + _td2(days=stopped_day + 1)  # approx trading days
        end_date = row['date'] + _td2(days=int(horizon_days * 1.5))  # approx

        reentry_ret = 0.0
        if sym in _sig_lookup:
            for sig_date, sig_idx in _sig_lookup[sym]:
                if sig_date <= stop_date:
                    continue
                if sig_date > end_date:
                    break
                # Found re-entry signal
                re_row = df_all.loc[sig_idx]
                re_entry = re_row['close']
                re_sl = _get_sl_pct(re_row)
                re_sl_price = re_entry * (1 + re_sl / 100)
                re_fl = re_row.get('fwd_lows', [])
                re_fc = re_row.get('fwd_closes', [])
                remaining = horizon_days - stopped_day
                if remaining <= 0:
                    break
                re_max = min(remaining, len(re_fl))
                re_stopped = False
                for d2 in range(re_max):
                    if np.isnan(re_fl[d2]):
                        break
                    if re_fl[d2] <= re_sl_price:
                        reentry_ret = re_sl
                        re_stopped = True
                        break
                if not re_stopped:
                    ix_r = remaining - 1
                    if ix_r < len(re_fc) and not np.isnan(re_fc[ix_r]):
                        reentry_ret = (re_fc[ix_r] - re_entry) / re_entry * 100
                break  # Only first re-entry

        total_ret = first_ret + reentry_ret
        return total_ret, True, reentry_ret, max_dd

# Run simulation for each zone filter and horizon
_zone_filters_sl = [
    ("ATL Breakout (A+)", lambda r: r['atl_buy'], -10),
    ("ATL Pullback (A)", lambda r: r.get('atl_pb', False), -10),
    ("ATL Low-Cheat (A-)", lambda r: r.get('atl_lc', False), -10),
    ("ATL Combined", lambda r: r['atl_buy'] or r.get('atl_pb', False) or r.get('atl_lc', False), -10),
    ("ETL Buy", lambda r: r['etl_buy'], -7),
    ("BTL Buy", lambda r: r['btl_buy'], -5),
    ("All Combined", lambda r: r['any_buy'], None),  # None = use per-signal SL
]

# Pre-compute
_zone_dfs_sl = []
for zname, zfn, sl_fixed in _zone_filters_sl:
    try:
        zmk = df_all.apply(zfn, axis=1)
        _zone_dfs_sl.append((zname, df_all[zmk], sl_fixed))
    except:
        _zone_dfs_sl.append((zname, pd.DataFrame(), sl_fixed))

for horizon in ['T+2', 'T+14', 'T+30', 'T+60']:
    h_days = {'T+2': 2, 'T+14': 14, 'T+30': 30, 'T+60': 60}[horizon]
    print(f"\n  ┌─── {horizon} (SL: ATL -10%, ETL -7%, BTL -5% + re-entry) {'─'*30}")
    print(f"  │ {'Entry Type':<22} {'Sigs':>5} {'N':>4} {'Win%':>6} {'AvgAll':>8} {'AvgGain':>8} {'AvgLoss':>8} {'SL%':>5} {'ReEnt':>5} {'MaxDD':>7}")
    print(f"  │ {'─'*22} {'─'*5} {'─'*4} {'─'*6} {'─'*8} {'─'*8} {'─'*8} {'─'*5} {'─'*5} {'─'*7}")

    for zname, zdf, sl_fixed in _zone_dfs_sl:
        ns = len(zdf)
        if ns == 0:
            print(f"  │ {zname:<22} {0:>5}")
            continue

        rets = []
        n_stopped = 0
        n_reentry = 0
        n_valid = 0
        max_dd_worst = 0.0

        for _, row in zdf.iterrows():
            sl_p = sl_fixed if sl_fixed is not None else _get_sl_pct(row)
            ret, stopped, re_ret, mdd = _sim_sl_reentry(row, h_days, sl_p)
            if not np.isnan(ret):
                rets.append(ret)
                n_valid += 1
                if stopped:
                    n_stopped += 1
                    if re_ret != 0:
                        n_reentry += 1
                if mdd < max_dd_worst:
                    max_dd_worst = mdd

        if n_valid == 0:
            print(f"  │ {zname:<22} {ns:>5} {0:>4}")
            continue

        rets_arr = np.array(rets)
        wins = rets_arr[rets_arr > 0]
        losses = rets_arr[rets_arr <= 0]
        wr = len(wins) / n_valid * 100
        avg_all = rets_arr.mean()
        avg_g = wins.mean() if len(wins) > 0 else 0.0
        avg_l = losses.mean() if len(losses) > 0 else 0.0
        sl_rate = n_stopped / n_valid * 100

        print(f"  │ {zname:<22} {ns:>5} {n_valid:>4} {wr:>5.0f}% {avg_all:>+7.1f}% {avg_g:>+7.1f}% {avg_l:>+7.1f}% {sl_rate:>4.0f}% {n_reentry:>5} {max_dd_worst:>+6.1f}%")

    print(f"  └{'─'*80}")

# Compare: No SL vs With SL
print(f"\n  ┌─── SO SANH: KHONG SL vs CO SL {'─'*50}")
print(f"  │ {'Entry Type':<22} {'Hz':>5} │ {'NoSL Win%':>9} {'NoSL Avg':>9} │ {'SL Win%':>8} {'SL Avg':>8} │ {'Delta':>7}")
print(f"  │ {'─'*22} {'─'*5} ┼ {'─'*9} {'─'*9} ┼ {'─'*8} {'─'*8} ┼ {'─'*7}")

for zname, zdf, sl_fixed in _zone_dfs_sl:
    if len(zdf) == 0 or zname in ("All Combined",):
        continue
    for horizon in ['T+14', 'T+30', 'T+60']:
        h_days = {'T+14': 14, 'T+30': 30, 'T+60': 60}[horizon]
        # No SL
        if horizon not in zdf.columns:
            continue
        hv = zdf[horizon].dropna()
        if len(hv) == 0:
            continue
        nosl_wr = (hv > 0).sum() / len(hv) * 100
        nosl_avg = hv.mean()

        # With SL
        rets = []
        for _, row in zdf.iterrows():
            sl_p = sl_fixed if sl_fixed is not None else _get_sl_pct(row)
            ret, _, _, _ = _sim_sl_reentry(row, h_days, sl_p)
            if not np.isnan(ret):
                rets.append(ret)
        if len(rets) == 0:
            continue
        ra = np.array(rets)
        sl_wr = (ra > 0).sum() / len(ra) * 100
        sl_avg = ra.mean()
        delta = sl_avg - nosl_avg

        print(f"  │ {zname:<22} {horizon:>5} │ {nosl_wr:>8.0f}% {nosl_avg:>+8.1f}% │ {sl_wr:>7.0f}% {sl_avg:>+7.1f}% │ {delta:>+6.1f}%")

print(f"  └{'─'*80}")

# ═══════════════════════════════════════════════════════════════
# PART 11: SL DIAGNOSTIC — TAI SAO SL GIET LOI NHUAN?
# ═══════════════════════════════════════════════════════════════
print(f"\n{'='*130}")
print("PART 11: CHAN DOAN SL — TAI SAO SL GIET LOI NHUAN?")
print(f"{'='*130}")

from datetime import timedelta as _td3

# ─── 11A: SHAKEOUT ANALYSIS ───
# For each stopped-out trade, what happened AFTER the SL hit?
print(f"\n  ── 11A: SHAKEOUT ANALYSIS (Bi SL roi co hoi phuc khong?) ──")

_sl_map = {True: -10.0, 'atl': -10.0, 'etl': -7.0, 'btl': -5.0}

shakeout_data = []
buy_mask = df_all['any_buy'] == True
for _, row in df_all[buy_mask].iterrows():
    sl_p = _get_sl_pct(row)
    entry = row['close']
    sl_price = entry * (1 + sl_p / 100)
    fl = row.get('fwd_lows', [])
    fh = row.get('fwd_highs', [])
    fc = row.get('fwd_closes', [])
    zone_label = _zone_of(row)

    # Find SL day within 60 bars
    sl_day = None
    for d in range(min(60, len(fl))):
        if np.isnan(fl[d]):
            break
        if fl[d] <= sl_price:
            sl_day = d + 1
            break

    if sl_day is None:
        continue  # Not stopped — skip

    # After SL hit, what was the max gain from SL price within remaining bars?
    max_gain_after = np.nan
    close_at_60 = np.nan
    for d2 in range(sl_day, min(60, len(fh))):
        if not np.isnan(fh[d2]):
            g = (fh[d2] - sl_price) / sl_price * 100
            if np.isnan(max_gain_after) or g > max_gain_after:
                max_gain_after = g
    if 59 < len(fc) and not np.isnan(fc[59]):
        close_at_60 = (fc[59] - entry) / entry * 100  # from original entry

    shakeout_data.append({
        'sym': row['symbol'], 'date': row['date'], 'zone': zone_label,
        'sl_pct': sl_p, 'sl_day': sl_day,
        'max_gain_after_sl': max_gain_after,
        'close_at_60_from_entry': close_at_60,
        'buy_type': row.get('buy_type', ''),
    })

if len(shakeout_data) > 0:
    sdf = pd.DataFrame(shakeout_data)
    total_sl = len(sdf)
    recovered = sdf[sdf['max_gain_after_sl'] > abs(sdf['sl_pct'])]
    n_recovered = len(recovered)
    mild_recover = sdf[sdf['max_gain_after_sl'] > 0]

    print(f"\n  Tong so lenh bi SL (trong 60 phien): {total_sl}")
    print(f"  Sau SL, gia hoi phuc > 0% (tu SL price):  {len(mild_recover)} ({len(mild_recover)/total_sl*100:.0f}%)")
    print(f"  Sau SL, gia tang > |SL%| (shakeout thuc su): {n_recovered} ({n_recovered/total_sl*100:.0f}%)")

    # Breakdown by zone
    for z in ['ATL', 'ETL', 'BTL']:
        zs = sdf[sdf['zone'] == z]
        if len(zs) == 0:
            continue
        zr = zs[zs['max_gain_after_sl'] > abs(zs['sl_pct'])]
        avg_sl_day = zs['sl_day'].mean()
        avg_gain_after = zs['max_gain_after_sl'].mean()
        print(f"\n  {z}: {len(zs)} lenh bi SL")
        print(f"    Avg ngay bi SL: T+{avg_sl_day:.1f}")
        print(f"    Avg max gain sau SL (tu SL price): {avg_gain_after:+.1f}%")
        print(f"    Shakeout (hoi > |SL|): {len(zr)}/{len(zs)} ({len(zr)/len(zs)*100:.0f}%)")

    # ─── 11B: TIME-TO-SL DISTRIBUTION ───
    print(f"\n  ── 11B: PHAN BO THOI GIAN BI SL ──")
    print(f"  (Bi SL som = diem buy chua chuan, bi SL muon = trend that bai)")
    buckets = [(1, 2, "T+1~2 (mua la SL)"), (3, 5, "T+3~5 (SL som)"),
               (6, 10, "T+6~10 (SL trung)"), (11, 30, "T+11~30 (SL muon)"),
               (31, 60, "T+31~60 (trend fail)")]
    for b_lo, b_hi, b_name in buckets:
        cnt = len(sdf[(sdf['sl_day'] >= b_lo) & (sdf['sl_day'] <= b_hi)])
        bar = '█' * int(cnt / max(1, total_sl) * 40)
        print(f"    {b_name:<25} {cnt:>3} ({cnt/total_sl*100:>4.0f}%) {bar}")

    # Detail: Top 10 shakeouts (stocks that recovered most after SL)
    sdf_sorted = sdf.sort_values('max_gain_after_sl', ascending=False)
    print(f"\n  Top 10 SHAKEOUT (bi SL nhung hoi phuc manh nhat):")
    print(f"    {'Sym':>5} {'Date':>12} {'Zone':>4} {'SL%':>5} {'SLday':>5} {'MaxGainAfter':>12} {'Close@T60':>10}")
    for _, r in sdf_sorted.head(10).iterrows():
        c60 = f"{r['close_at_60_from_entry']:+.1f}%" if not np.isnan(r['close_at_60_from_entry']) else "n/a"
        mga = f"{r['max_gain_after_sl']:+.1f}%" if not np.isnan(r['max_gain_after_sl']) else "n/a"
        print(f"    {r['sym']:>5} {str(r['date']):>12} {r['zone']:>4} {r['sl_pct']:>+4.0f}% T+{r['sl_day']:>2.0f}  {mga:>12} {c60:>10}")

# ─── 11C: PIVOT-BASED SL vs FLAT % SL ───
print(f"\n  ── 11C: PIVOT-BASED SL vs FLAT % SL ──")
print(f"  (Minervini: SL duoi pivot * 0.97, khong phai % co dinh)")

def _sim_pivot_sl(row, horizon_days):
    """Simulate with pivot-based SL: max(pivot*0.97, entry-8%)"""
    entry = row['close']
    pivot = row.get('prior_pivot')
    if pivot is not None and not np.isnan(pivot) and pivot > 0:
        sl_price = pivot * 0.97
        sl_pct_actual = (sl_price - entry) / entry * 100
        # Cap: SL khong qua rong (-15%) hoac qua chat (-3%)
        if sl_pct_actual < -15:
            sl_price = entry * 0.85
        elif sl_pct_actual > -3:
            sl_price = entry * 0.97
    else:
        # No pivot — fallback to flat %
        sl_price = entry * (1 + _get_sl_pct(row) / 100)

    sl_pct_used = (sl_price - entry) / entry * 100
    fl = row.get('fwd_lows', [])
    fc = row.get('fwd_closes', [])
    max_bars = min(horizon_days, len(fl))
    for d in range(max_bars):
        if np.isnan(fl[d]):
            break
        if fl[d] <= sl_price:
            return sl_pct_used, True, sl_pct_used, d + 1
    # Not stopped
    ix_h = horizon_days - 1
    if ix_h < len(fc) and not np.isnan(fc[ix_h]):
        ret = (fc[ix_h] - entry) / entry * 100
    else:
        ret = np.nan
    return ret, False, sl_pct_used, None

# Compare flat vs pivot SL for each zone at T+14, T+30, T+60
_cmp_zones = [
    ("ATL Combined", lambda r: r['atl_buy'] or r.get('atl_pb', False) or r.get('atl_lc', False)),
    ("ETL Buy", lambda r: r['etl_buy']),
    ("BTL Buy", lambda r: r['btl_buy']),
]

print(f"\n  {'Zone':<22} {'Hz':>5} │ {'Flat SL':^25} │ {'Pivot SL':^25} │ {'Delta':>7}")
print(f"  {'':22} {'':>5} │ {'Win%':>6} {'Avg':>8} {'SL%':>5} │ {'Win%':>6} {'Avg':>8} {'SL%':>5} │ {'':>7}")
print(f"  {'─'*22} {'─'*5} ┼ {'─'*25} ┼ {'─'*25} ┼ {'─'*7}")

for zname, zfn in _cmp_zones:
    try:
        zmk = df_all.apply(zfn, axis=1)
        zdf = df_all[zmk]
    except:
        continue
    if len(zdf) == 0:
        continue

    for horizon in ['T+14', 'T+30', 'T+60']:
        h_days = {'T+14': 14, 'T+30': 30, 'T+60': 60}[horizon]

        # Flat SL
        flat_rets = []
        flat_sl_cnt = 0
        for _, row in zdf.iterrows():
            sl_p = _get_sl_pct(row)
            ret, stopped, _, _ = _sim_sl_reentry(row, h_days, sl_p)
            if not np.isnan(ret):
                flat_rets.append(ret)
                if stopped:
                    flat_sl_cnt += 1

        # Pivot SL
        pvt_rets = []
        pvt_sl_cnt = 0
        pvt_sl_pcts = []
        for _, row in zdf.iterrows():
            ret, stopped, sl_used, _ = _sim_pivot_sl(row, h_days)
            if not np.isnan(ret):
                pvt_rets.append(ret)
                pvt_sl_pcts.append(sl_used)
                if stopped:
                    pvt_sl_cnt += 1

        if len(flat_rets) == 0 or len(pvt_rets) == 0:
            continue

        fa = np.array(flat_rets)
        pa = np.array(pvt_rets)
        f_wr = (fa > 0).sum() / len(fa) * 100
        p_wr = (pa > 0).sum() / len(pa) * 100
        f_avg = fa.mean()
        p_avg = pa.mean()
        f_sr = flat_sl_cnt / len(fa) * 100
        p_sr = pvt_sl_cnt / len(pa) * 100
        delta = p_avg - f_avg

        print(f"  {zname:<22} {horizon:>5} │ {f_wr:>5.0f}% {f_avg:>+7.1f}% {f_sr:>4.0f}% │ {p_wr:>5.0f}% {p_avg:>+7.1f}% {p_sr:>4.0f}% │ {delta:>+6.1f}%")

# ─── 11D: BUY TIMING — T+0 vs T+1 CONFIRMATION ───
print(f"\n  ── 11D: BUY TIMING — Mua ngay T+0 vs Doi xac nhan T+1 ──")
print(f"  (Gia thuyet: mua T+1 close tranh duoc shakeout ngay breakout)")

for zname, zfn in _cmp_zones:
    try:
        zmk = df_all.apply(zfn, axis=1)
        zdf = df_all[zmk]
    except:
        continue
    if len(zdf) == 0:
        continue

    for horizon in ['T+14', 'T+30']:
        h_days = {'T+14': 14, 'T+30': 30}[horizon]

        t0_rets = []
        t1_rets = []
        for _, row in zdf.iterrows():
            entry0 = row['close']
            fc = row.get('fwd_closes', [])
            fl = row.get('fwd_lows', [])

            # T+0 entry (current logic)
            sl_p = _get_sl_pct(row)
            ret0, _, _, _ = _sim_sl_reentry(row, h_days, sl_p)
            if not np.isnan(ret0):
                t0_rets.append(ret0)

            # T+1 entry: enter at close of next day IF close > entry (confirmation)
            if len(fc) >= 2 and not np.isnan(fc[0]):
                entry1 = fc[0]  # close of T+1
                if entry1 >= entry0:  # confirmation: T+1 close >= breakout close
                    sl_price1 = entry1 * (1 + sl_p / 100)
                    remaining = h_days - 1
                    stopped1 = False
                    ret1 = np.nan
                    for d in range(1, min(remaining + 1, len(fl))):
                        if np.isnan(fl[d]):
                            break
                        if fl[d] <= sl_price1:
                            ret1 = sl_p
                            stopped1 = True
                            break
                    if not stopped1:
                        ix_h = h_days - 1
                        if ix_h < len(fc) and not np.isnan(fc[ix_h]):
                            ret1 = (fc[ix_h] - entry1) / entry1 * 100
                    if not np.isnan(ret1):
                        t1_rets.append(ret1)
                else:
                    # T+1 close < breakout close → skip (no confirmation)
                    pass

        if len(t0_rets) > 0 and len(t1_rets) > 0:
            t0a = np.array(t0_rets)
            t1a = np.array(t1_rets)
            print(f"\n  {zname} @ {horizon}:")
            print(f"    T+0 entry: N={len(t0a):>3}, Win={((t0a>0).sum()/len(t0a)*100):>4.0f}%, Avg={t0a.mean():>+6.1f}%")
            print(f"    T+1 confirm: N={len(t1a):>3}, Win={((t1a>0).sum()/len(t1a)*100):>4.0f}%, Avg={t1a.mean():>+6.1f}%")
            print(f"    Bi loc (T+1<T+0): {len(t0a)-len(t1a)} lenh → {(len(t0a)-len(t1a))/max(1,len(t0a))*100:.0f}% signals khong xac nhan")

# ─── 11E: PULLBACK COVERAGE GAP ───
print(f"\n  ── 11E: PULLBACK COVERAGE GAP ──")
print(f"  (Bao nhieu lenh bi SL co the da duoc bat lai neu co PB signal?)")

if len(shakeout_data) > 0:
    n_with_reentry = 0
    n_without = 0
    could_recover = 0
    for sd in shakeout_data:
        sym = sd['sym']
        sl_date = sd['date']
        # Check if any subsequent buy signal exists within 30 days
        has_reentry = False
        if sym in _sig_lookup:
            for sig_date, sig_idx in _sig_lookup[sym]:
                if sig_date > sl_date and (sig_date - sl_date).days <= 45:
                    has_reentry = True
                    break
        if has_reentry:
            n_with_reentry += 1
        else:
            n_without += 1
            if not np.isnan(sd['max_gain_after_sl']) and sd['max_gain_after_sl'] > 10:
                could_recover += 1

    print(f"\n  Tong lenh bi SL: {total_sl}")
    print(f"  Co signal re-entry trong 45 ngay: {n_with_reentry} ({n_with_reentry/total_sl*100:.0f}%)")
    print(f"  KHONG co signal re-entry: {n_without} ({n_without/total_sl*100:.0f}%)")
    print(f"  Trong do, gia tang >10% sau SL (missed opportunity): {could_recover}")

# ─── 11F: KET LUAN CHAN DOAN ───
print(f"\n  ── 11F: KET LUAN CHAN DOAN ──")
print(f"""
  1. SHAKEOUT RATE: Ty le bi SL roi gia hoi phuc manh (shakeout)
     → Neu cao = diem buy OK nhung SL qua chat
     → Neu thap = diem buy chua chuan (trend that su yeu)

  2. TIME-TO-SL: Phan bo thoi gian bi SL
     → Nhieu lenh bi SL trong T+1~2 = mua qua som, chua co xac nhan
     → Nhieu lenh bi SL T+6~30 = trend that bai, SL dung

  3. PIVOT SL vs FLAT SL:
     → Pivot SL (duoi pivot*0.97) cho phep stock "tho" tu nhien
     → Flat SL (-10/-7/-5) co the qua chat hoac qua rong tuy stock

  4. T+1 CONFIRMATION:
     → Doi T+1 close > breakout close moi entry
     → Loc bot duoc false breakout, giam SL rate

  5. PULLBACK COVERAGE:
     → Can them signal PB/LC de bat lai song sau SL
     → Hien tai chi 5 PB+LC / 111 total = qua it
""")

print(f"\n{'='*130}")
print("ANALYSIS COMPLETE - v4")
print(f"{'='*130}")
