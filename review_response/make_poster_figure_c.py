"""Poster VI error curves from saved PF eigenphases; no diagonalization here.

Run with the common scientific interpreter. Additional points, if absent, are
computed separately by add_poster_figure_c_points.py. Existing inputs are read-only.
"""
from __future__ import annotations
import hashlib, json, math, pickle, subprocess
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import LogLocator, FuncFormatter, NullFormatter
from trotterlib.config import BETA, DECOMPO_NUM
from trotterlib.cost_validation import analytic_minimum_cost

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/poster_finite_time_20261116'
EPS=1.59360010199040e-4
FLOOR=5e-13
PUBLISHED='8th(Morales-Y8m10b)'
REJECTION='artifacts/server_cost_validity/integrated_boundary_recheck_20260902/pf_cost_rejection_tests.json'
H6_SOURCE='artifacts/poster_finite_time_20261116/references/4672f3f/artifacts/hchain_direct_optimal_time_scaling_v1_1_20260927_ce7b961/raw/H6_y8.json'
COLORS={'8th_v2':'#BF00BF','8th_published':'#7A1FA2','4th_new':'#0000FF'}
NAMES={'8th_v2':'8th v2','8th_published':'8th published','4th_new':'New 4th (reference)'}
EXPECTED={'H2':{'8th_v2':(.874,1.23),'8th_published':(.024,3.73),'4th_new':(.960,.72)},
          'H4':{'8th_v2':(.982,.58),'8th_published':(1.265,3.15),'4th_new':(.941,.80)},
          'H6':{'8th_v2':(.994,.99),'8th_published':(3.355,2.11),'4th_new':(.921,.90)}}
INPUTS={}

def read(name):
    p=ROOT/name;INPUTS[name]=hashlib.sha256(p.read_bytes()).hexdigest()
    return json.loads(p.read_text())

def save(name,data,compact=False):
    text=json.dumps(data,ensure_ascii=False,allow_nan=False,**({'separators':(',',':')} if compact else {'indent':2}))+'\n'
    (OUT/name).write_text(text)

def point(t,e,overlap,agreement=True,source='existing',basis=None):
    return dict(t=float(t),e_signed=float(e),overlap=float(overlap),used=bool(agreement and abs(e)>FLOOR),source=source,
                branch_agreement=bool(agreement),branch_agreement_basis=basis)

def first_valid(points,alpha,p):
    reliable=[q for q in points if abs(q['e_signed'])>FLOOR and alpha*q['t']**p>FLOOR]
    if not reliable:return None,dict(status='no_resolved_points')
    start=reliable[0]
    if not start['branch_agreement'] or abs(abs(start['e_signed'])/(alpha*start['t']**p)-1)>.1:
        return None,dict(status='first_resolved_point_fails',first_time=start['t'])
    last=start
    for q in points[points.index(start)+1:]:
        if not q['branch_agreement'] or abs(q['e_signed'])<=FLOOR or abs(abs(q['e_signed'])/(alpha*q['t']**p)-1)>.1:
            return last['t'],dict(status='first_interval_bracketed',bracket=[last['t'],q['t']],start=start['t'])
        last=q
    return last['t'],dict(status='right_censored',start=start['t'])

def crossings(points):
    pairs=[]
    for a,b in zip(points,points[1:]):
        if a['used'] and b['used'] and a['e_signed']*b['e_signed']<0:
            fraction=abs(a['e_signed'])/(abs(a['e_signed'])+abs(b['e_signed']))
            pairs.append(dict(t=math.exp(math.log(a['t'])+fraction*math.log(b['t']/a['t'])),bracket=[a['t'],b['t']]))
    return pairs

def thin(points,tana,tvalid,bracket,changes,limit=28):
    """Keep anchors, two neighbors on each side, sign/quality transitions, log grid."""
    keep={0,len(points)-1}
    anchors=[tana]+([tvalid] if tvalid else [])+list(bracket or [])
    for t in anchors:
        i=int(np.searchsorted([q['t'] for q in points],t))
        keep.update(j for j in range(i-2,i+3) if 0<=j<len(points))
    for c in changes:
        keep.update(i for i,q in enumerate(points) if q['t'] in c['bracket'])
    # Keep the endpoints of every used/un-used segment so figures cannot bridge it.
    for i in range(1,len(points)):
        if points[i]['used']!=points[i-1]['used']:keep.update((i-1,i))
    assert len(keep)<=40,('too many mandatory points',len(keep))
    limit=max(limit,len(keep))
    lt=np.log([q['t'] for q in points])
    for target in np.linspace(lt[0],lt[-1],limit):
        if len(keep)>=limit:break
        keep.add(int(np.argmin(abs(lt-target))))
    while len(keep)<min(limit,len(points)):
        remaining=[i for i in range(len(points)) if i not in keep]
        keep.add(max(remaining,key=lambda i:min(abs(lt[i]-lt[j]) for j in keep)))
    return [points[i] for i in sorted(keep)]

def curve(h,key,rejection,extra):
    name=f'H{h}';record=next(r for r in rejection['current_target_records'] if r['h_chain']==h and r['label']==PUBLISHED)
    inherited=None
    if key!='8th_published':
        alias='w8' if key=='8th_v2' else 'wmy4'
        source=f'artifacts/poster_finite_time_20261116/raw/{name}_{alias}.json'
        r=next(iter(read(source)['results'][name].values()))
        alpha=r['initial_fit']['alpha'];p=r['formal_order'];tana=r['analytic_power_law_optimum']['time']
        alpha_source=r['initial_fit']['source'];INPUTS[alpha_source]=hashlib.sha256((ROOT/alpha_source).read_bytes()).hexdigest()
        pts=[point(q['time'],q['signed_direct_error_hartree'],q['selected_ground_state_overlap_probability'],
                   q['branch_shift_disagreement_hartree']<=1e-10,basis='tracked shift agrees with maximum-ground-overlap shift within 1e-10 Ha')
             for q in r['direct_diagonalization']['points']]
        inherited=r['power_law_validity']['t_valid'];label=r['label'];nrot=r['pauli_rotations_per_step']
        alpha_rule='original fixed formal-order coefficient, unchanged'
    elif h==6:
        d=read(H6_SOURCE);r=d['results']['H6']['results'][PUBLISHED]
        alpha=r['fixed_order_alpha'];p=r['formal_order'];tana=r['analytic_optimal_time']
        alpha_source=H6_SOURCE+'#/results/H6/results/'+PUBLISHED+'/fixed_order_alpha'
        alpha_rule='frozen 2026-09-27 fixed-order alpha; not refitted here; old rejection alpha differs by 7.43 ppm'
        source=H6_SOURCE;label=PUBLISHED;nrot=DECOMPO_NUM[name][label]
        pts=[]
        for q in r['points']:
            a=q['continuously_tracked_branch'];b=q['maximum_ground_overlap_branch']
            agrees=a['schur_index']==b['schur_index'] and abs(a['unwrapped_energy_shift_hartree']-b['energy_shift_hartree'])<=1e-10
            pts.append(point(q['time'],a['unwrapped_energy_shift_hartree'],a['ground_overlap_probability'],agrees,
                             basis='continuation and maximum-ground-overlap Schur index and energy shift agree'))
        inherited=record['t_valid']
    else:
        source=f'artifacts/server_cost_validity/{name}_wide_direct_validation.json'
        d=read(source);r=d['results'][PUBLISHED];p=8;tana=record['t_ana'];alpha=EPS/((p+1)*tana**p)
        alpha_source=REJECTION+f'#/current_target_records(h_chain={h},label={PUBLISHED})/t_ana'
        alpha_rule='frozen rejection-test coefficient recovered algebraically as epsilon_E/(9*t_ana^8); wide analysis uses a different rolling fit'
        nrot=DECOMPO_NUM[name][PUBLISHED];label=PUBLISHED;energy=d['system']['ground_energy_without_constant_hartree']
        pts=[]
        for t,q in zip(r['times'],r['points']):
            overlap=q['selected_ground_state_overlap_probability']
            # A > 1/2 projection in the (normal unitary) eigensystem is uniquely
            # maximal. These legacy points save the tracked vector's overlap,
            # but not the index of the maximum-ground cross-check. Do not invent it.
            pts.append(point(t,q['selected_effective_energy_hartree']-energy,overlap,overlap>.5,
                basis='legacy continuation; >1/2 exact-ground weight proves unique dominant ground component (index not saved)'))
        q=next(r['point'] for r in extra['results'] if r['system']==name)
        pts.append(point(q['time'],q['signed_direct_error_hartree'],q['selected_ground_state_overlap_probability'],q['branch_agreement'],'new',q['branch_agreement_basis']))
        inherited=record['t_valid']
    pts=sorted(pts,key=lambda q:q['t'])
    # Validity is evaluated on the full saved grid, before display trimming.
    valid,detail=first_valid(pts,alpha,p)
    total_points=len(pts)
    requested_upper=max(1.2*tana,1.05*valid if valid else 0.)
    upper=next((q['t'] for q in pts if q['t']>=requested_upper),pts[-1]['t'])
    pts=[q for q in pts if q['t']<=upper]
    changes=crossings(pts)
    nearest=min(pts,key=lambda q:abs(q['t']-tana))
    assert abs(nearest['t']/tana-1)<1e-12
    result=dict(p=p,alpha=alpha,alpha_source=alpha_source,alpha_rule=alpha_rule,n_rot=nrot,t_ana=tana,t_valid=valid,
        t_valid_diagnostics=detail,t_valid_reference=inherited,t_valid_reference_source=REJECTION if key=='8th_published' else source+'#/power_law_validity',
        point_data_source=source,sign_changes=[c['t'] for c in changes],sign_change_brackets=[c['bracket'] for c in changes],
        r_at_t_ana=abs(nearest['e_signed'])/(alpha*tana**p),overlap_at_t_ana=nearest['overlap'],branch_agreement_at_t_ana=nearest['branch_agreement'],
        original_point_count=total_points,display_domain_point_count=len(pts),points=[])
    if key=='8th_published' and h==6:
        lows=[q for q in pts if q['overlap']<.99];first=lows[0]
        previous=pts[pts.index(first)-1]
        result['first_overlap_below_0p99']=dict(time=first['t'],relative_time=first['t']/tana,overlap=first['overlap'],bracket_relative=[previous['t']/tana,first['t']/tana])
    for q in thin(pts,tana,valid,detail.get('bracket'),changes):
        result['points'].append({k:v for k,v in q.items() if k not in ('branch_agreement_basis',)})
    return result,pts

def plot_curves(data):
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':17,'axes.labelsize':19,'legend.fontsize':12.5,'pdf.fonttype':42})
    for h in ('H6','H2','H4'):
        curves=data[h]
        fig,axes=plt.subplots(1,2,figsize=(13,5.4),sharey=True)
        for ax,key in zip(axes,('8th_v2','8th_published')):
            r=curves[key];color=COLORS[key];q=r['points'];t=np.array([x['t'] for x in q]);y=np.array([abs(x['e_signed']) if x['used'] else np.nan for x in q]);good=np.array([x['used'] for x in q]);low=np.array([x['overlap']<.99 for x in q])
            ax.loglog(t,y,'-',color=color,lw=2,label=NAMES[key]+': direct')
            for mask,face in [(good&~low,color),(good&low,'white')]:
                ax.scatter(t[mask],y[mask],s=29,edgecolors=color,facecolors=face,zorder=4)
            grid=np.geomspace(min(t),max(t),400);ax.loglog(grid,r['alpha']*grid**r['p'],'--',color='0.25',lw=1.7,label=r'$\alpha t^p$')
            ax.axvline(r['t_ana'],color=color,ls='-.',lw=1.8,label=r'$t_{\rm ana}$')
            if r['t_valid']:ax.axvline(r['t_valid'],color=color,ls=':',lw=2,label=r'$t_{\rm valid}$')
            ax.axhline(EPS,color='0.35',ls='--',lw=1.1,label=r'$\epsilon_E$')
            for change in r['sign_changes']:ax.plot(change,.045,marker='x',color='#CE6600',ms=8,mew=1.8,transform=ax.get_xaxis_transform(),clip_on=False)
            ax.set_xlabel(r'Step time $t$ (a.u.)');ax.grid(True,which='major',alpha=.18);ax.legend(loc='upper left',ncol=2,columnspacing=.8,handlelength=1.8)
            ax.set_ylim(FLOOR/1.5,max(EPS*3,np.nanmax(y)*2));ax.set_xlim(min(t)*.93,max(t)*1.07)
            ax.xaxis.set_major_locator(LogLocator(base=10,subs=(1,2,5),numticks=6))
            ax.xaxis.set_major_formatter(FuncFormatter(lambda value,position:f'{value:g}'))
            ax.xaxis.set_minor_formatter(NullFormatter())
        axes[0].set_ylabel(r'$|\delta E|$ (Ha)')
        # Identical legend convention in both C1 and C2: open points are retained.
        axes[1].plot([],[],'o',mfc='white',mec='0.3',label='Overlap < 0.99');axes[1].plot([],[],'x',color='#CE6600',label='Sign change (bracketed)')
        axes[1].legend(loc='upper left',ncol=2,columnspacing=.8,handlelength=1.5,fontsize=11.3)
        fig.tight_layout()
        for ext in ('png','pdf'):fig.savefig(OUT/f'figure_C1_{h}.{ext}',dpi=300,bbox_inches='tight')
        plt.close(fig)
        fig,ax=plt.subplots(figsize=(8.8,5.8));largest=3.5
        ax.axhspan(.9,1.1,color='0.88',zorder=0,label='10% agreement');ax.axvline(1,color='0.3',ls='--',lw=1.3,label=r'$t/t_{\rm ana}=1$')
        for key,r in curves.items():
            color=COLORS[key];q=r['points'];x=np.array([p['t']/r['t_ana'] for p in q]);y=np.array([abs(p['e_signed'])/(r['alpha']*p['t']**r['p']) if p['used'] else np.nan for p in q]);good=np.array([p['used'] for p in q]);low=np.array([p['overlap']<.99 for p in q]);largest=max(largest,float(np.nanmax(y)))
            ax.semilogx(x,y,'-' if key!='4th_new' else '--',color=color,lw=2,label=NAMES[key])
            for mask,face in [(good&~low,color),(good&low,'white')]:ax.scatter(x[mask],y[mask],s=31,facecolors=face,edgecolors=color,zorder=4)
            if r['t_valid']:
                xv=r['t_valid']/r['t_ana'];ax.plot(xv,.015,'v',color=color,ms=10,transform=ax.get_xaxis_transform(),clip_on=False)
            for change in r['sign_changes']:ax.plot(change/r['t_ana'],.96,'x',color=color,ms=8,mew=2,transform=ax.get_xaxis_transform())
        ax.plot([],[],'o',mfc='white',mec='0.3',label='Overlap < 0.99');ax.plot([],[],'v',color='0.3',label=r'$t_{\rm valid}/t_{\rm ana}$');ax.plot([],[],'x',color='0.3',label='Sign change (bracketed)')
        right=max(1.3,max(r['t_valid']/r['t_ana']*1.08 for r in curves.values() if r['t_valid']))
        ax.set(xlabel=r'$t/t_{\rm ana}$',ylabel=r'$|\delta E|/(\alpha t^p)$',ylim=(-.12,largest*1.13),xlim=(.025,right));ax.grid(True,which='major',alpha=.18)
        ax.legend(loc='upper left',ncol=2,fontsize=10.8,columnspacing=.8);fig.tight_layout()
        for ext in ('png','pdf'):fig.savefig(OUT/f'figure_C2_{h}.{ext}',dpi=300,bbox_inches='tight')
        plt.close(fig)

def historical_audit():
    rows=[]
    for h in (2,4,6,8):
        row=dict(system=f'H{h}',snapshots={})
        for rev in ('ad2037d','0d9db33^','0d9db33'):
            vals={};files={}
            for alias,label in [('w8','8th(Morales)'),('wmy4','4th(new_2)')]:
                folder='trotter_expo_coeff_gr' if rev=='ad2037d' else 'trotter_expo_coeff_gr_original'
                filename=label if rev=='ad2037d' else alias
                path=f'artifacts/{folder}/H{h}_sto-3g_singlet_distance_100_charge_0_grouping_Operator_{filename}_ave'
                blob=subprocess.check_output(['git','show',rev+':'+path],cwd=ROOT)
                vals[alias]=float(pickle.loads(blob));files[alias]=dict(path=path,sha256=hashlib.sha256(blob).hexdigest())
            costs={a:analytic_minimum_cost(BETA,DECOMPO_NUM[f'H{h}'][lab],vals[a],p,EPS) for a,lab,p in [('w8','8th(Morales)',8),('wmy4','4th(new_2)',4)]}
            row['snapshots'][rev]=dict(alpha=vals,files=files,new4_over_v2=costs['wmy4']/costs['w8'])
        rows.append(row)
    return dict(rows=rows,paper_pdf_commit='ad2037d (2026-03-17)',notebook_figure3_call="tl.exp_extrapolation_diff(Hchain, n_w_list, use_original=False)",
        coefficient_revisions=[dict(commit='788bf3f',date='2026-05-28',scope='regular folder current-label H2-H7 new4 coefficients',message='prescribed-time alpha values had not been saved'),
                               dict(commit='0d9db33',date='2026-05-28',scope='original folder legacy wmy4 H2-H7 coefficients',message='alpha had not been calculated at prescribed times; corrected')],
        fit='p fixed to 4 or 8; alpha=10**mean(log10(abs(error))-p*log10(t)); plots_timeevo_error.trotter_error_plt_qc_gr; analysis_utils.loglog_average_coeff',
        prescribed_windows={'H2_new4':[.73,.74,.002],'H4_new4':[.37,.38,.002],'H6_new4':[.25,.26,.002]},
        evidence_limit='The notebook call and same-commit coefficients reproduce the quoted Figure 3 points. No separate figure-generation manifest links the PDF to an execution; this is numerical provenance evidence, not a recovered execution log.')

def report(data,audit,extra):
    checks=[];table=['| 系 | 公式 | r（今回） | r（既存） | 差 | t_ana/t_valid（今回） | 既存 | 差 |','|---|---|---:|---:|---:|---:|---:|---:|']
    for h in ('H2','H4','H6'):
        for key,r in data[h].items():
            er,et=EXPECTED[h][key];rv=r['r_at_t_ana'];tv=r['t_ana']/r['t_valid'] if r['t_valid'] else None;rd=rv/er-1;td=tv/et-1 if tv else None
            table.append(f"| {h} | {NAMES[key]} | {rv:.6f} | {er:.3f} | {rd:+.2%} | {tv:.6f} | {et:.2f} | {td:+.2%} |")
            checks.append(dict(system=h,formula=key,r=rv,r_reference_rounded=er,r_relative_difference=rd,r_reference_unrounded=(.02350493484706352 if h=='H2' and key=='8th_published' else 1.2652062001161106 if h=='H4' and key=='8th_published' else None),r_relative_difference_from_unrounded=(rv/.02350493484706352-1 if h=='H2' and key=='8th_published' else rv/1.2652062001161106-1 if h=='H4' and key=='8th_published' else None),t_ana_over_t_valid=tv,t_ratio_reference_rounded=et,t_ratio_relative_difference=td,over_one_percent=abs(rd)>.01 or abs(td or 0)>.01))
    costrows=[]
    for h in ('H2','H4','H6'):
        a=data[h]['8th_published'];b=data[h]['8th_v2'];ca=analytic_minimum_cost(BETA,a['n_rot'],a['alpha'],8,EPS);cb=analytic_minimum_cost(BETA,b['n_rot'],b['alpha'],8,EPS)
        costrows.append(dict(system=h,n_rot_published=a['n_rot'],n_rot_v2=b['n_rot'],published_over_v2=ca/cb))
    save('figure_C_checks.json',dict(checks=checks,published_cost_ratios=costrows,new_diagonalization_points=extra['new_diagonalization_points'],additional_calculation_seconds=extra['total_seconds']))
    oldsummary=(OUT/'summary.md').read_text();marker='\n<!-- poster-figure-C-validation -->\n'
    appendix=marker+'\n**図Cの検算（符号付き固有値誤差を保存、rは絶対値比）**\n\n'+'\n'.join(table)+'\n\nH6出版版は9月27日の保存済みH6_y8.jsonを採用。r=3.332860は旧3.355に対し−0.66%。同じ10%判定をこの0.05 t_ana格子で行うとt_valid=0.45 t_ana、比2.222222となり旧2.11との差は+5.32%。旧境界t_valid=1.8104843850973964はJSONに参照値として残すが、元の密な境界ファイルは未収録のため再検証していない。係数やデータを差に合わせて変更しない。\nH2出版版のt_validは1.8814263695985207で旧1.6315022863829147と異なる（比3.235559対3.73、−13.26%）。旧t_validはwide解析の別α=9.764532835733884e-12に対する境界で、旧t_anaから復元した固定α=9.38954983833999e-12とは混用できない。差を解消するための再fitや再計算はしない。\nH2出版版の旧r=0.024は3桁丸めの影響が大きい。小数第6位までの今回値と旧JSONの非丸め値もfigure_C_checks.jsonに記録する。\n'
    (OUT/'summary.md').write_text(oldsummary.split(marker)[0]+appendix)
    h6=data['H6']['8th_published'];low=h6['first_overlap_below_0p99'];hist=['| 系 | 論文コミットの通常係数からの比 | original修正前 | original修正後（今回） |','|---|---:|---:|---:|']
    for row in audit['rows']:
        s=row['snapshots'];hist.append(f"| {row['system']} | {s['ad2037d']['new4_over_v2']:.6f} | {s['0d9db33^']['new4_over_v2']:.6f} | {s['0d9db33']['new4_over_v2']:.6f} |")
    costs=['| 系 | 出版版1回の回転数 | 8次v2 | 固定αによる出版版/v2総回転数 |','|---|---:|---:|---:|']+[f"| {r['system']} | {r['n_rot_published']} | {r['n_rot_v2']} | {r['published_over_v2']:.6f} |" for r in costrows]
    signs=[]
    for h in ('H2','H4','H6'):
        sign=[]
        for key,r in data[h].items():
            q=next(q for q in r['points'] if q['used']);sign.append(NAMES[key]+('：正' if q['e_signed']>0 else '：負'))
        signs.append(h+' '+', '.join(sign))
    text='''# ポスター⑥：PF固有値誤差と短時間モデル

主成果物は figure_C_data.json（各曲線40点以下、50 KB以下）。C1/C2は同じJSONから描画し、PNGは300 dpi、PDFも保存。新4次は参考としてC2とJSONに含めた。
JSONのe_signedは符号付き。図C2・検算のrは|e_signed|/(alpha*t^p)。白抜きは重なり0.99未満で、採用からは除外しない。used=falseは枝照合の不一致または|誤差|≤5e-13 Ha。
符号反転の印は解像された採用点間の符号反転区間内を、log(t)上で線形補間した位置。厳密なゼロ点を新たに解いた値ではない。隣接する両端点を間引かず、sign_change_bracketsも保存する。雑音床以下の符号反転は数えない。
間引きは対数格子を基本とし、t_ana、t_valid、境界、符号反転、採否の切替の隣接点を保護する。元の全点は既存生データに残る。

## 検算

'''+ '\n'.join(table)+'''

H2/H4出版版の固定αは、pf_cost_rejection_tests.jsonのt_anaからepsilon_E/(9*t_ana^8)で復元した（再フィットではない）。wide_time_cost_analysis.jsonのinitial_fitは異なるrolling fitなので混用しない。
H6出版版はユーザー指定により9月27日保存データの固定αとt_anaを使う。旧αとの差は7.43 ppm。rの差は−0.66%で1%以内だが、t_validの差は+5.32%。これは旧0.475 t_anaの密な境界点が現在の0.05刻み格子にないため。新しい格子上では最初の連続合格区間は0.45まで、0.50が失敗。後の再適合は採用しない。
元の境界ファイル2件はリポジトリ未収録とユーザー確認済み。旧t_validを新データで再検証したとは扱わず、図は今回の格子上の値を表示する。
H2出版版のt_validは1.8814263695985207で、旧1.6315022863829147との差は旧t_validがwide解析の別α=9.764532835733884e-12で求められていたため。旧t_anaから復元した固定α=9.38954983833999e-12を使った連続10%境界を今回の図に使い、旧境界も参照として残す。比3.235559対3.73（−13.26%）を直すために係数や点を変更しない。\nH2出版版のrの1%超差は旧表示0.024への丸めが主因である。旧JSONの未丸めr=0.02350493484706352とも比較する。

## H6出版版の枝と重なり

'''+f"重なりが0.99を下回る最初の保存点はt/t_ana={low['relative_time']:.2f}、直前点との区間は{low['bracket_relative']}。t_anaでの重なり={h6['overlap_at_t_ana']:.9f}、r={h6['r_at_t_ana']:.9f}。\n"+'''
この点では前刻みの固有ベクトルとの最大重なりで追跡した枝と、その刻みの最大基底状態重なりの枝が同じSchur index（283）で、エネルギーシフトも一致する。短時間基底状態から追跡した固有位相という意味では照合が一致する。ただし刻み間隔0.05 t_anaの保存点に基づく確認であり、その間の回避交差を完全に解像した証明ではない。0.881という混合も白抜きで明示する。
旧3.355は9月2日の集約報告、今回3.333は9月27日の計算で後者が新しい。今回の主格子は0.05 t_ana刻み。旧rを生んだ元ファイルがないため、t_ana付近でどちらが細かいかは断定できない。旧境界は0.475/0.5 t_anaを区別しており、t_valid付近は今回より細かい。
出どころ：'''+H6_SOURCE+'''

## B1 回転数と固定αでの予測比

'''+ '\n'.join(costs)+'''

回転数の値はsrc/trotterlib/config.pyのDECOMPO_NUM。H6出版版は42876=2038*21+78で一致。総回転数は固定αと形式次数8、同じepsilon_E・BETAで解析最小値を求め、丸め前に割った。

## B2 新4次係数の由来

'''+ '\n'.join(hist)+'''

論文PDFを追加したad2037d（2026-03-17）のabe_trotter_project.ipynbのFig.3セルはuse_original=Falseで、artifacts/trotter_expo_coeff_gr/*_Operator_4th(new_2)_aveと同フォルダの8th(Morales)_aveを読む。同時点の係数を使うと1.0247/0.8688/0.7816となり、図から読んだ1.02/0.87/0.78を再現する。各値とファイルのGit履歴・SHA256はfigure_C_coefficient_audit.json。
5月28日に788bf3fで通常フォルダの現行ラベル、0d9db33でoriginalフォルダのwmy4ラベルのH2〜H7係数が修正された。コミット説明は「規定の時間で取った値が保存されていなかった」「規定のtで計算されていなかった」。H8のoriginalはこの修正で変わらない。
フィットは形式次数pを固定し、alpha=10**mean(log10(error)-p*log10(t))。元は基底状態の重なりから求める摂動代理誤差のfitで、今回の直接固有位相データを再フィットしたものではない。規定窓はノートブックで新4次H2:0.73〜0.74、H4:0.37〜0.38、H6:0.25〜0.26、刻み0.002。実際の保存αファイルにはfit時刻が埋め込まれておらず、過去の実行ログまでは復元していない。
論文PDFの付録HのTable VIの新4次αには約3倍異なる別の値もあるため、表・図・現在のoriginalを同一データとみなさない。ノートブックと同時点係数による数値一致は確認したが、独立した論文図の生成manifestはない。

## B3 t_validの手順

v2も出版版も基準自体は同じ10%で、短時間側の最初の連続適合域の最後の合格点を使い、後の再適合へ飛ばさない。v2のposter_finite_time.Sweep.validityはモデル値と直接誤差がともに雑音床を上回る最初の点から開始し、境界を追加細分化した。出版版旧報告は別α・別格子で、H6は密な境界overrideを使っていた。したがって閾値・連続性の考え方は同じだが、全く同じ点列・境界解像度の手順ではない。今回のt_validは間引き前の全候補点から同じルールで再集計した。

## 追加計算と限界

'''+f"追加対角化はH2とH4の出版版t_ana各1点、計2点。合計{extra['total_seconds']:.3f}秒（準備・診断を含む）。H6の新規対角化は0点。その他は既存データの抽出・作図のみ。\n"+'''
追加点はfigure_C_additional_points.jsonに診断値と時間を保存し、図用JSONではsource=new。H2/H4の既存点はcontinuation結果の重なり>0.5により最大基底重なり枝との一意な一致を判定する（元のcrosscheck indexは保存されていない）。H6/v2は直接保存された2つの枝の照合を使う。
既存のsummary本文・raw・係数・既存図は保存し、summaryにはこの検算だけを追記した。新規生成ファイルのSHA256、全入力ハッシュ、検算はfigure_C_validation.jsonに保存。
短時間側の符号：'''+ ' / '.join(signs)+'。\n'
    (OUT/'figure_C_report.md').write_text(text)
    return checks

def main():
    rejection=read(REJECTION);extra=read('artifacts/poster_finite_time_20261116/figure_C_additional_points.json')
    data=dict(epsilon_E=EPS,noise_floor=FLOOR,ratio_definition='abs(e_signed)/(alpha*t**p)',sign_change_definition='log-time linear interpolation between adjacent used opposite-sign points; see brackets',
              used_rule='branch agreement and abs(e_signed)>5e-13 Ha; overlap<0.99 is retained with open markers',max_points_per_curve=40)
    full={}
    for h in (6,2,4):
        name=f'H{h}';data[name]={}
        for key in ('8th_v2','8th_published','4th_new'):
            data[name][key],full[(name,key)]=curve(h,key,rejection,extra)
    save('figure_C_data.json',data,compact=True)
    assert (OUT/'figure_C_data.json').stat().st_size<=50000
    audit=historical_audit();save('figure_C_coefficient_audit.json',audit)
    checks=report(data,audit,extra);plot_curves(data)
    assert abs(data['H2']['8th_published']['r_at_t_ana']/.02350493484706352-1)<1e-6
    assert data['H6']['8th_published']['n_rot']==42876
    for h in ('H2','H4','H6'):
        for key,r in data[h].items():
            kept={q['t'] for q in r['points']}
            assert r['t_valid'] in kept
            assert all(t in kept for pair in r['sign_change_brackets'] for t in pair)
    original_summary=subprocess.check_output(['git','show','17b30aa:artifacts/poster_finite_time_20261116/summary.md'],cwd=ROOT)
    assert (OUT/'summary.md').read_bytes().startswith(original_summary)
    input_ok=all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==sha for p,sha in INPUTS.items())
    for h in ('H2','H4','H6'):
        for key,r in data[h].items():
            assert 0<len(r['points'])<=40
            assert all(a['t']<b['t'] for a,b in zip(r['points'],r['points'][1:]))
            assert all(q['used']==(q['branch_agreement'] and abs(q['e_signed'])>FLOOR) for q in r['points'])
            assert abs(r['t_ana']-(EPS/((r['p']+1)*r['alpha']))**(1/r['p']))<1e-12
            assert any(abs(q['t']/r['t_ana']-1)<1e-12 for q in r['points'])
    generated=sorted(p for p in OUT.glob('figure_C*') if p.is_file() and p.name not in ('figure_C_validation.json','figure_C_generation.log'))
    scripts={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'review_response/make_poster_figure_c.py',ROOT/'review_response/add_poster_figure_c_points.py')}
    validation=dict(pass_=bool(input_ok),scripts_sha256=scripts,data_bytes=(OUT/'figure_C_data.json').stat().st_size,inputs_sha256=INPUTS,
        generated_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in generated},checks=checks,
        point_counts={h:{k:len(r['points']) for k,r in data[h].items()} for h in ('H6','H2','H4')},
        extra_points=2,extra_h6_points=0,extra_seconds=extra['total_seconds'])
    save('figure_C_validation.json',validation);assert validation['pass_']
    print(json.dumps(dict(data_bytes=validation['data_bytes'],checks=checks,extra_seconds=extra['total_seconds']),indent=2))
if __name__=='__main__':main()
