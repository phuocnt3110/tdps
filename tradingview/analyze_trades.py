#!/usr/bin/env python3
"""
analyze_trades.py - Phân tích tín hiệu giao dịch ATL & BTL
Sử dụng vnstock (VCI) để lấy dữ liệu OHLCV +/-7 ngày quanh ngày mua.
Chạy: python analyze_trades.py
"""
import sys, os, time, warnings
warnings.filterwarnings('ignore')
_vp = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'vnstock')
if os.path.exists(_vp): sys.path.insert(0, _vp)
import pandas as pd, numpy as np
from datetime import datetime, timedelta
try:
    from vnstock import Quote
except ImportError:
    print("ERROR: pip install vnstock"); sys.exit(1)

DAYS_B, DAYS_A, BUF, SLEEP = 7, 7, 14, 0.5

TRADES = [
    # BTL
    {"c":"PVC_2025_12","s":"PVC","d":"2025-12-30","t":"btl","e":11700,"r":"win","p":15.81},
    {"c":"STB_2025_12","s":"STB","d":"2025-12-30","t":"btl","e":60150,"r":"lose","p":-7.07},
    {"c":"G36_2026_01","s":"G36","d":"2026-01-15","t":"btl","e":12100,"r":"win","p":7.02},
    {"c":"DPM_2026_01","s":"DPM","d":"2026-01-15","t":"btl","e":25000,"r":"lose","p":-5.73},
    {"c":"PHR_2026_01","s":"PHR","d":"2026-01-16","t":"btl","e":67750,"r":"lose","p":-5.09},
    {"c":"DGW_2026_01","s":"DGW","d":"2026-01-19","t":"btl","e":45833,"r":"lose","p":-5.53},
    {"c":"NDN_2026_01","s":"NDN","d":"2026-01-23","t":"btl","e":11900,"r":"lose","p":-5.88},
    {"c":"FIT_2026_01","s":"FIT","d":"2026-01-23","t":"btl","e":5036,"r":"lose","p":-5.08},
    {"c":"TTF_2026_01","s":"TTF","d":"2026-01-23","t":"btl","e":3160,"r":"lose","p":-4.75},
    {"c":"VHC_2026_01","s":"VHC","d":"2026-01-30","t":"btl","e":64900,"r":"win","p":0.31},
    {"c":"BIC_2026_01","s":"BIC","d":"2026-01-30","t":"btl","e":26100,"r":"win","p":2.68},
    {"c":"PSX_2026_01","s":"PSX","d":"2026-01-30","t":"btl","e":3800,"r":"lose","p":-10.53},
    {"c":"CTD_2026_02","s":"CTD","d":"2026-02-05","t":"btl","e":85000,"r":"lose","p":-6.24},
    {"c":"HPG_2026_02","s":"HPG","d":"2026-02-05","t":"btl","e":28200,"r":"lose","p":-6.03},
    {"c":"SZC_2026_02","s":"SZC","d":"2026-02-05","t":"btl","e":36650,"r":"lose","p":-5.87},
    {"c":"DGW_2026_02","s":"DGW","d":"2026-02-04","t":"btl","e":55800,"r":"lose","p":-11.47},
    {"c":"GMD_2026_02","s":"GMD","d":"2026-02-04","t":"btl","e":72700,"r":"lose","p":-4.13},
    {"c":"PAC_2026_03","s":"PAC","d":"2026-03-04","t":"btl","e":26450,"r":"lose","p":-9.26},
    # ATL
    {"c":"PLX_2026_01","s":"PLX","d":"2026-01-15","t":"atl","e":48100,"r":"win","p":19.85},
    {"c":"BAF_2026_01","s":"BAF","d":"2026-01-15","t":"atl","e":38400,"r":"lose","p":-6.25},
    {"c":"CTG_2026_01","s":"CTG","d":"2026-01-12","t":"atl","e":43200,"r":"lose","p":-8.10},
    {"c":"BSR_2026_01","s":"BSR","d":"2026-01-12","t":"atl","e":20700,"r":"win","p":0.97},
    {"c":"DCL_2026_01","s":"DCL","d":"2026-01-12","t":"atl","e":46000,"r":"win","p":15.96},
    {"c":"PVD_2026_01","s":"PVD","d":"2026-01-09","t":"atl","e":30286,"r":"lose","p":-8.04},
    {"c":"NAF_2026_01","s":"NAF","d":"2026-01-06","t":"atl","e":38150,"r":"win","p":0.52},
    {"c":"PNJ_2026_01","s":"PNJ","d":"2026-01-27","t":"atl","e":116000,"r":"win","p":1.98},
    {"c":"MSR_2026_01","s":"MSR","d":"2026-01-29","t":"atl","e":34600,"r":"win","p":9.93},
    {"c":"PVS_2026_01","s":"PVS","d":"2026-01-28","t":"atl","e":44800,"r":"win","p":3.35},
    {"c":"PVB_2026_01","s":"PVB","d":"2026-01-28","t":"atl","e":40100,"r":"lose","p":-4.99},
    {"c":"MWG_2026_01","s":"MWG","d":"2026-01-30","t":"atl","e":90100,"r":"lose","p":-5.11},
    {"c":"BIG_2026_02","s":"BIG","d":"2026-02-12","t":"atl","e":7800,"r":"win","p":19.23},
    {"c":"OIL_2026_03","s":"OIL","d":"2026-03-04","t":"atl","e":24700,"r":"lose","p":-9.31},
    {"c":"POW_2026_03","s":"POW","d":"2026-03-03","t":"atl","e":16300,"r":"lose","p":-9.82},
    {"c":"MSR_2026_03","s":"MSR","d":"2026-03-03","t":"atl","e":52000,"r":"lose","p":-15.13},
]

def to_dt(v):
    if isinstance(v,(datetime,pd.Timestamp)): return v.date() if hasattr(v,'date') else v
    if isinstance(v,str): return datetime.strptime(v[:10],"%Y-%m-%d").date()
    return v

def fetch(sym, dstr):
    bd = datetime.strptime(dstr,"%Y-%m-%d")
    s = (bd - timedelta(days=BUF+DAYS_B)).strftime("%Y-%m-%d")
    e = (bd + timedelta(days=BUF+DAYS_A)).strftime("%Y-%m-%d")
    try:
        q = Quote(source="vci", symbol=sym, show_log=False)
        df = q.history(start=s, end=e, interval="1D")
        if df is None or df.empty: return None,-1
        df['_d'] = df['time'].apply(to_dt)
        df = df.sort_values('_d').reset_index(drop=True)
        tgt = bd.date()
        for i,row in df.iterrows():
            if row['_d'] >= tgt: return df, i
        return df, -1
    except Exception as ex:
        print(f"  ERR {sym}: {ex}"); return None,-1

def scale(df, evnd):
    med = df['close'].median()
    return 1000.0 if evnd/med > 500 else 1.0

def analyze(t, df, bi, sc):
    if df is None or bi < 0: return None
    ps = max(0, bi-DAYS_B); pre = df.iloc[ps:bi]
    buy = df.iloc[bi]
    pe = min(len(df), bi+DAYS_A+1); post = df.iloc[bi+1:pe]
    m = {'code':t['c'],'symbol':t['s'],'type':t['t'],'result':t['r'],'pnl':t['p'],'buy_date':t['d']}

    if len(pre)>=3:
        m['pre_avg_vol'] = pre['volume'].mean()
        m['pre_vol_dry'] = pre['volume'].iloc[-3:].mean()/max(pre['volume'].mean(),1)
        m['pre_chg'] = (pre['close'].iloc[-1]-pre['close'].iloc[0])/pre['close'].iloc[0]*100
        hl = pre['high']-pre['low']; hl=hl.replace(0,np.nan)
        m['pre_bp'] = ((pre['close']-pre['low'])/hl).mean()
        m['pre_green'] = (pre['close']>pre['open']).mean()
    else:
        m.update({k:np.nan for k in ['pre_avg_vol','pre_vol_dry','pre_chg','pre_bp','pre_green']})

    m['buy_vol'] = buy['volume']
    if bi>0:
        pc = df.iloc[bi-1]['close']
        m['gap'] = (buy['open']-pc)/pc*100
        m['ato_prem'] = (t['e']/sc - pc)/pc*100
    else: m['gap']=m['ato_prem']=np.nan
    pv = m.get('pre_avg_vol',0)
    m['vol_rat'] = buy['volume']/max(pv,1) if pv>0 else np.nan
    m['buy_clr'] = 'G' if buy['close']>buy['open'] else 'R'

    if len(post)>=1:
        m['mx_gain'] = (post['high'].max()-buy['close'])/buy['close']*100
        m['mx_dd'] = (post['low'].min()-buy['close'])/buy['close']*100
        m['d_gain'] = int(post['high'].idxmax()-bi)
        m['d_dd'] = int(post['low'].idxmin()-bi)
        n3 = min(3,len(post))
        m['p3vol'] = post.iloc[:n3]['volume'].mean()
        m['vol_sus'] = m['p3vol']/max(pv,1) if pv>0 else np.nan
        m['ret7'] = (post['close'].iloc[-1]-buy['close'])/buy['close']*100
        t1 = post.iloc[0]
        m['t1'] = 'G' if t1['close']>t1['open'] else 'R'
        m['t1_ret'] = (t1['close']-buy['close'])/buy['close']*100
    else:
        m.update({k:np.nan for k in ['mx_gain','mx_dd','d_gain','d_dd','p3vol','vol_sus','ret7','t1','t1_ret']})
    return m

def fetch_vni(dates):
    dts = [datetime.strptime(d,"%Y-%m-%d") for d in dates]
    s = (min(dts)-timedelta(days=40)).strftime("%Y-%m-%d")
    e = (max(dts)+timedelta(days=20)).strftime("%Y-%m-%d")
    try:
        q = Quote(source="vci",symbol="VNINDEX",show_log=False)
        df = q.history(start=s,end=e,interval="1D")
        df['_d'] = df['time'].apply(to_dt)
        return df.sort_values('_d').reset_index(drop=True)
    except: return None

def vni_ctx(vni, dstr):
    if vni is None: return {}
    tgt = datetime.strptime(dstr,"%Y-%m-%d").date()
    idx=-1
    for i,r in vni.iterrows():
        if r['_d']>=tgt: idx=i; break
    if idx<10: return {}
    p7=vni.iloc[idx-7:idx]; q7=vni.iloc[idx:min(len(vni),idx+8)]
    p25=vni.iloc[max(0,idx-25):idx]; va=p25['volume'].mean()
    dd=int(((p25['close']<p25['open'])&(p25['volume']>va)).sum())
    return {
        'vni_pre7':(p7['close'].iloc[-1]-p7['close'].iloc[0])/p7['close'].iloc[0]*100,
        'vni_post7':(q7['close'].iloc[-1]-q7['close'].iloc[0])/q7['close'].iloc[0]*100 if len(q7)>1 else np.nan,
        'vni_dist25':dd,
    }

def fv(v,f='.1f',s=''):
    if v is None or (isinstance(v,float) and np.isnan(v)): return ' N/A'
    return f"{v:{f}}{s}"

def report(df):
    S='═'*80
    print(f"\n{S}\n  TRADING SIGNAL ANALYSIS REPORT\n{S}")
    print(f"  Trades: {len(df)} | {df['buy_date'].min()} → {df['buy_date'].max()}\n")
    for tt in ['btl','atl']:
        td=df[df['type']==tt];
        if td.empty: continue
        w=td[td['result']=='win']; l=td[td['result']=='lose']
        wr=len(w)/len(td)*100
        print(f"{S}\n  {tt.upper()} | Total:{len(td)} Win:{len(w)}({wr:.0f}%) Lose:{len(l)}")
        print(f"  AvgPnL:{td['pnl'].mean():.2f}% WinAvg:{w['pnl'].mean():.2f}% LoseAvg:{l['pnl'].mean():.2f}%\n{S}")
        cols=[('gap','Gap%','.1f','%'),('ato_prem','ATO premium','.1f','%'),('vol_rat','VolRatio','.1f','x'),
              ('pre_vol_dry','PreVolDry','.2f',''),('pre_chg','PreChg%','.1f','%'),('pre_bp','BuyPress','.2f',''),
              ('mx_gain','MaxGain%','.1f','%'),('mx_dd','MaxDD%','.1f','%'),('vol_sus','VolSustain','.1f','x'),
              ('ret7','7dRet%','.1f','%'),('t1_ret','T+1 Ret%','.1f','%')]
        print(f"  {'METRIC':<20}{'WIN':>10} {'LOSE':>10} {'SIG':>4}")
        print(f"  {'-'*48}")
        findings=[]
        for c,lb,fm,sf in cols:
            if c not in td.columns: continue
            wv=w[c].mean() if len(w) else np.nan; lv=l[c].mean() if len(l) else np.nan
            sig=''
            if not np.isnan(wv) and not np.isnan(lv) and lv!=0:
                if abs(wv-lv)/max(abs(lv),0.01)*100>30: sig='★★'; findings.append((lb,wv,lv))
                elif abs(wv-lv)/max(abs(lv),0.01)*100>15: sig='★'
            print(f"  {lb:<20}{fv(wv,fm,sf):>10} {fv(lv,fm,sf):>10} {sig:>4}")
        print(f"\n  {'CODE':<15}{'R':>2}{'PnL':>7}{'Gap':>6}{'VR':>5}{'MxG':>6}{'MxDD':>7}{'7d':>6}{'T1':>4}")
        print(f"  {'-'*55}")
        for _,r in td.sort_values('pnl',ascending=False).iterrows():
            mk='✓' if r['result']=='win' else '✗'
            print(f"  {r['code']:<15}{mk:>2}{r['pnl']:>6.1f}%"
                  f"{fv(r.get('gap'),'.1f','%'):>6}{fv(r.get('vol_rat'),'.1f','x'):>5}"
                  f"{fv(r.get('mx_gain'),'.1f','%'):>6}{fv(r.get('mx_dd'),'.1f','%'):>7}"
                  f"{fv(r.get('ret7'),'.1f','%'):>6}{str(r.get('t1','?'))[:1]:>4}")
        if findings:
            print(f"\n  ★ KEY DIFFERENCES:")
            for lb,wv,lv in findings: print(f"    {lb}: Win={wv:.2f} Lose={lv:.2f}")

    if 'vni_dist25' in df.columns:
        print(f"\n{'='*80}\n  VNINDEX CONTEXT\n{'='*80}")
        for tt in ['btl','atl']:
            td=df[df['type']==tt]; w=td[td['result']=='win']; l=td[td['result']=='lose']
            if td.empty: continue
            print(f"  {tt.upper()}:")
            for c,lb in [('vni_pre7','Pre-7d'),('vni_post7','Post-7d'),('vni_dist25','DistDays/25')]:
                wv=w[c].mean() if len(w) and c in w else np.nan
                lv=l[c].mean() if len(l) and c in l else np.nan
                print(f"    {lb:<15} Win:{fv(wv):>8} Lose:{fv(lv):>8}")

    print(f"\n{'='*80}\n  KHUYẾN NGHỊ\n{'='*80}")
    for tt in ['btl','atl']:
        td=df[df['type']==tt];
        if td.empty: continue
        w=td[td['result']=='win']; l=td[td['result']=='lose']
        print(f"\n  {tt.upper()}:")
        for c,lb,act in [
            ('gap','Gap%','KHÔNG MUA nếu ATO gap > 3%'),
            ('vol_rat','VolRatio','Yêu cầu vol ratio >= 1.5x'),
            ('pre_vol_dry','PreVolDry','Volume phải dry-up trước breakout (<0.8)'),
            ('mx_dd','MaxDD','Cắt lỗ sớm nếu DD > 5% trong 3 ngày'),
            ('vni_dist25','DistDays','KHÔNG MUA khi dist days >= 5'),
        ]:
            if c not in td.columns: continue
            wv=w[c].mean() if len(w) else np.nan; lv=l[c].mean() if len(l) else np.nan
            if not np.isnan(wv) and not np.isnan(lv):
                better = abs(wv)<abs(lv) if c in ['gap','mx_dd','vni_dist25'] else wv>lv
                icon = '✓' if better else '⚠'
                print(f"    {icon} {lb}: Win={fv(wv)} Lose={fv(lv)} → {act if not better else 'OK'}")

def main():
    print(f"{'='*80}\n  TRADE ANALYSIS - vnstock VCI\n{'='*80}")
    print(f"  {len(TRADES)} trades, +/-{DAYS_B} days\n")
    vni = fetch_vni(list(set(t['d'] for t in TRADES)))
    print(f"  VNINDEX: {'OK' if vni is not None else 'FAIL'}\n")
    results=[]; sc=None
    for i,t in enumerate(TRADES):
        print(f"[{i+1}/{len(TRADES)}] {t['c']} ({t['s']}) {t['t'].upper()} {t['r']}...",end=' ')
        df,bi = fetch(t['s'],t['d'])
        if df is None or bi<0: print("SKIP"); results.append({'code':t['c'],'symbol':t['s'],'type':t['t'],'result':t['r'],'pnl':t['p'],'buy_date':t['d']}); time.sleep(SLEEP); continue
        if sc is None: sc=scale(df,t['e']); print(f"scale={sc}x",end=' ')
        m = analyze(t,df,bi,sc)
        if m:
            m.update(vni_ctx(vni,t['d']))
            results.append(m)
            print(f"gap={fv(m.get('gap'),'.1f','%')} vol={fv(m.get('vol_rat'),'.1f','x')} 7d={fv(m.get('ret7'),'.1f','%')}")
        else: print("FAIL")
        time.sleep(SLEEP)
    rdf = pd.DataFrame(results)
    report(rdf)
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)),'trade_analysis_results.csv')
    rdf.to_csv(out,index=False)
    print(f"\nSaved: {out}")
    return rdf

if __name__=="__main__": main()
