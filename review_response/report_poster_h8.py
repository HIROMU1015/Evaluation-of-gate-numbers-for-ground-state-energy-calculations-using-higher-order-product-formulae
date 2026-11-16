"""Publishable H8 extension: exact ratios, diagnostics, and poster figures."""
from __future__ import annotations
import copy
import hashlib
import json
import statistics
from collections import Counter
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator,FuncFormatter,NullFormatter
from poster_h8_accelerated import ROOT,OUT
from reproduce_poster_baseline import ALIASES,EPS,write_json
from trotterlib.config import BETA

LABELS=['8th(Morales)','10th(Morales)','4th(new_2)']
COLORS=['#8e44ad','#d97904','#1675ad']
NAMES=['Morales 8th (v2)','Morales 10th (v2)','New 4th (m=2)']
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':12,'pdf.fonttype':42,'ps.fonttype':42,'axes.grid':True,'grid.alpha':.2})


def merge():
    data=json.loads((OUT/'wide_time_cost_analysis.json').read_text())
    records={}
    for alias in ALIASES:
        p=OUT/'raw'/f'H8_{alias}.json'
        record=json.loads(p.read_text())
        records.update(record['results']['H8'])
    assert set(records)==set(LABELS)
    data['results']['H8']=records
    write_json(OUT/'wide_time_cost_analysis.json',data)
    prior=json.loads((ROOT/'artifacts/poster_finite_time_20261116/wide_time_cost_analysis.json').read_text())
    combined=dict(schema_version=1,cost_model=data['cost_model'],sources=dict(prior='../poster_finite_time_20261116/wide_time_cost_analysis.json',H8='wide_time_cost_analysis.json'),results={})
    for h in ('H2','H4','H6'):combined['results'][h]=prior['results'][h]
    combined['results']['H8']=records
    combined['results']['H5']=prior['results']['H5']
    combined['current_scope']=dict(primary=['H2','H4','H6'],poster_H8_validation=['H8'],reference=['H5'])
    write_json(OUT/'combined_wide_time_cost_analysis.json',combined)
    return data,combined


def validate(data):
    rows=[]
    for label,r in data['results']['H8'].items():
        points=r['direct_diagonalization']['points'];times=np.array(r['times']);e=np.array([p['direct_error_hartree'] for p in points]);cost=np.array([np.nan if x is None else x for x in r['direct_diagonalization']['curve']['costs']])
        assert np.all(np.diff(times)>0)
        valid=e<EPS
        actual=BETA*r['pauli_rotations_per_step']/(times[valid]*(EPS-e[valid]))
        assert np.allclose(actual,cost[valid],rtol=2e-15)
        assert np.all(np.isnan(cost[~valid]))
        m=r['direct_diagonalization']['curve']['minimum'];assert m['is_interior_of_sampled_time_range']
        assert m['index']==int(np.nanargmin(cost))
        assert max(p['eigenpair_residual_norm'] for p in points)<=1e-10
        assert max(p['unitarity_residual_frobenius_norm'] for p in points)<=1e-10
        assert all(abs(p['direct_error_hartree']-abs(p['signed_direct_error_hartree']))<1e-30 for p in points)
        a=r['at_analytic_time'];assert abs(a['time']/r['analytic_power_law_optimum']['time']-1)<1e-12
        q=a['same_time_direct_to_model_cost_ratio']
        if q is not None:
            c=BETA*r['pauli_rotations_per_step']/(a['time']*(EPS-a['direct_error_hartree']))
            assert abs(c/r['analytic_power_law_optimum']['value']/q-1)<1e-13
        rows.append(dict(label=label,point_count=len(points),methods=dict(Counter(p['eigensolver_method'] for p in points)),
                         selected_residual_max=max(p['eigenpair_residual_norm'] for p in points),
                         minimum=m,branch_quality_pass=r['direct_diagonalization']['diagnostic_gates']['optimum_branch_quality_pass'],
                         convergence=r['refinement_convergence']))
    write_json(OUT/'validation.json',dict(pass_=True,checks=rows,
        scope='Data integrity and selected-branch matrix residuals; all-time maximum-ground versus continuation disagreements remain explicit.'))


def tables(combined):
    header=['| 系 | 公式 | 解析的な総回転数比（8次v2＝1） | 直接最適化した総回転数比（8次v2＝1） | t_opt/t_ana | t_ana での r | t_ana/t_valid | 備考 |','|---|---|---:|---:|---:|---:|---:|---|']
    lines=[];ratios={}
    for group,systems in [('主対象：H₂・H₄・H₆',['H2','H4','H6']),('ポスター④の追加検証：H₈',['H8']),('参考：H₅',['H5'])]:
        lines.extend([f'**{group}**','']+header)
        for h in systems:
            rs=combined['results'][h];base=rs[LABELS[0]];ratios[h]={}
            for label in LABELS:
                r=rs[label];a=r['analytic_power_law_optimum'];d=r['direct_diagonalization'];m=d['curve']['minimum'];g=d['diagnostic_gates']
                ar=a['value']/base['analytic_power_law_optimum']['value'];dr=m['value']/base['direct_diagonalization']['curve']['minimum']['value']
                crossing=r['optimum_diagnostics']['signed_error_sign_change_in_near_optimal_interval']
                v=r['power_law_validity']['t_ana_over_t_valid'];vtext='—' if v is None else f'{v:.4f}'
                note=f"範囲内側；近傍符号反転{'あり' if crossing else 'なし'}；重なり最小 {d['minimum_selected_ground_state_overlap_probability']:.6g}"
                if not g['all_time_branch_agreement_pass']:note+='；上側の枝照合不一致あり'
                if not g['optimum_branch_quality_pass']:note+='；最小点の重なり/枝照合基準未達'
                if v is None:note+='；t_valid未確定'
                lines.append(f"| {h} | {label} | {ar:.4f} | {dr:.4f} | {r['direct_optimum_vs_analytic']['time_ratio']:.4f} | {r['at_analytic_time']['direct_to_model_ratio']:.4f} | {vtext} | {note} |")
                ratios[h][label]=dict(analytic_total_rotation_ratio=ar,direct_total_rotation_ratio=dr,
                    same_time_direct_to_model_cost_ratio=r['at_analytic_time']['same_time_direct_to_model_cost_ratio'],optimum_branch_quality_pass=g['optimum_branch_quality_pass'])
        lines.append('')
    lines.extend(['比は丸め前のコストから計算。最小値は計算した有限領域の格子上の値であり、連続時間の大域最小は主張しない。',
                  '近傍は連結した最小コスト+1%区間。重なり最小は短時間診断点から上側探索端までの全保存点での値。最小点の重なりはJSONに別途保存。',
                  '固定αとの短時間側からの連続10%適合域だけをt_validとして採用し、後の再適合を使用しない。数値床以下（5e-13 Ha）は未判定。',
                  'H₈は全群が厳密に保存する追加Z₂対称性で4900→2468次元に制限。群の小成分は全て保持し、係数・構造の追加切り捨ては0。',
                  '高速対角化の対象枝は実ユニタリで固有対残差を検査し、残差または参照重なりの基準を外れた点は複素Schur分解へ戻して再追跡。非対象枝の大きい残差は隠さず保存し、Schur残差と混同しない。'])
    (OUT/'summary.md').write_text('\n'.join(lines)+'\n')
    write_json(OUT/'comparison_ratios.json',ratios)
    h=ratios['H8'];new=h[LABELS[2]];ten=h[LABELS[1]]
    quality=all(x['optimum_branch_quality_pass'] for x in h.values())
    report=[f"H₈：新4次/8次は解析 {new['analytic_total_rotation_ratio']:.4f} → 直接最適化 {new['direct_total_rotation_ratio']:.4f}（新4次は{100*(1-new['direct_total_rotation_ratio']):.2f}%少ない）。",
            f"H₈：10次/8次は解析 {ten['analytic_total_rotation_ratio']:.4f} → 直接最適化 {ten['direct_total_rotation_ratio']:.4f}（10次は{100*(ten['direct_total_rotation_ratio']-1):.2f}%多い）。",
            f"全公式の最小点は探索範囲の内側。最小点近傍の枝診断は{'通過' if quality else '未達あり、比は参考値'}。短時間式の適合域・上側の枝切替は表と生データに併記。"]
    (OUT/'report.md').write_text('\n'.join(report)+'\n')


def figures(data):
    rs=data['results']['H8'];fig,ax=plt.subplots(figsize=(9.5,6.2));mins=[];atanas=[]
    for label,name,color in zip(LABELS,NAMES,COLORS):
        r=rs[label];a=r['analytic_power_law_optimum'];m=r['direct_diagonalization']['curve']['minimum'];times=np.array(r['times']);cost=np.array([np.nan if x is None else x for x in r['direct_diagonalization']['curve']['costs']]);model=np.array([np.nan if x is None else x for x in r['power_law_curve']['costs']])
        ax.plot(times,cost,color=color,lw=2,label=f'{name}: direct')
        ax.plot(times,model,'--',color=color,lw=1.5,label=f'{name}: power law')
        ax.plot(a['time'],a['value'],'o',mfc='white',mec=color,ms=8,mew=1.5)
        ax.plot(m['time'],m['value'],'*',color=color,ms=14)
        mins.extend([a['value'],m['value']]);atanas.append(a['time'])
    ax.plot([],[],'o',mfc='white',mec='black',label=r'Analytic optimum $t_{ana}$');ax.plot([],[],'*',ms=12,color='black',label='Refined direct minimum')
    ax.set(xscale='log',yscale='log',xlabel='Step time (atomic units)',ylabel='Total Pauli rotations (cost proxy)',title='H8 / STO-3G / 1.0 angstrom',xlim=(.3*min(atanas),2*max(atanas)),ylim=(.7*min(mins),5*max(mins)))
    ax.xaxis.set_major_locator(FixedLocator([.3,.5,1,2,3,4]));ax.xaxis.set_major_formatter(FuncFormatter(lambda x,pos:f'{x:g}'));ax.xaxis.set_minor_formatter(NullFormatter());ax.legend(ncol=2,fontsize=9,loc='upper left');fig.tight_layout()
    for ext in ('png','pdf'):fig.savefig(OUT/f'figure_H8_cost.{ext}',dpi=220,bbox_inches='tight')
    plt.close(fig)
    fig,ax=plt.subplots(figsize=(8.5,5.5))
    ax.axhspan(.9,1.1,color='#777777',alpha=.15,label='10% agreement band');ax.axhline(1,color='#555555',lw=1)
    for label,name,color in zip(LABELS,NAMES,COLORS):
        r=rs[label];points=r['direct_diagonalization']['points'];mask=[p['model_error_hartree']>5e-13 and p['direct_error_hartree']>5e-13 for p in points]
        x=[p['relative_time'] for p,valid in zip(points,mask) if valid];y=[p['direct_to_model_ratio'] for p,valid in zip(points,mask) if valid]
        ax.plot(x,y,color=color,lw=1.8,label=name)
        ax.plot(1,r['at_analytic_time']['direct_to_model_ratio'],'o',color=color)
    ax.axvline(1,color='black',ls='--',lw=1)
    upper=max(12.,max(p['direct_to_model_ratio'] for r in rs.values() for p in r['direct_diagonalization']['points'] if p['model_error_hartree']>5e-13 and p['direct_error_hartree']>5e-13)*1.2)
    ax.set(xscale='log',yscale='log',xlabel=r'Step time / $t_{ana}$',ylabel=r'$e_{direct}/(\alpha t^p)$',title='H8: finite-time validity of the leading power law',xlim=(.08,2),ylim=(.08,upper))
    ax.legend(fontsize=10);fig.tight_layout()
    for ext in ('png','pdf'):fig.savefig(OUT/f'figure_H8_error_ratio.{ext}',dpi=220,bbox_inches='tight')
    plt.close(fig)


def performance():
    rows=[]
    for alias in ALIASES:
        r=json.loads((OUT/'raw'/f'H8_{alias}.json').read_text())['results']['H8'][LABELS[ALIASES.index(alias)]]
        counts=Counter(p['eigensolver_method'] for p in r['direct_diagonalization']['points'])
        rows.append(dict(alias=alias,point_count=len(r['times']),formula_wall_seconds=r['wall_seconds'],methods=dict(counts)))
    write_json(OUT/'performance.json',dict(results=rows,note='Formula times overlap because workers and formula coordinators ran concurrently; do not add them as elapsed wall time.'))


def main():
    data,combined=merge();validate(data);tables(combined);figures(data);performance();print((OUT/'report.md').read_text())

if __name__=='__main__':main()
