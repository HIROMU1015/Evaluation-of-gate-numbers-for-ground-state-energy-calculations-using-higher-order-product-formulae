"""Tables, scientific figures, numerical audit, and approval-stage estimates."""
from __future__ import annotations
import hashlib
import copy
import json
import math
import statistics
import subprocess
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator, FuncFormatter, NullFormatter
from poster_finite_time import ROOT, EPS, BETA, Sweep
from trotterlib.config import DECOMPO_NUM
from reproduce_poster_baseline import ALIASES, analytic, write_json

OUT=ROOT/'artifacts/poster_finite_time_20261116'
LABELS=[analytic(8,a)['label'] for a in ALIASES]
COLORS=['#8e44ad','#d97904','#1675ad']
DISPLAY=['Morales 8th (v2)','Morales 10th (v2)','New 4th (m=2)']
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':12,'pdf.fonttype':42,'ps.fonttype':42,'axes.grid':True,'grid.alpha':.23})

def fmt(x):
    return '—' if x is None else f'{x:.4f}'

def plotting_curve(ax,times,costs,color,label,style='-'):
    y=np.asarray([np.nan if c is None else c for c in costs],float)
    ax.plot(times,y,style,color=color,lw=2 if style=='-' else 1.5,label=label)

def figures(data):
    h='H4'
    fig,ax=plt.subplots(figsize=(9.5,6.3))
    minima=[]
    for label,color,name in zip(LABELS,COLORS,DISPLAY):
        r=data['results'][h][label];a=r['analytic_power_law_optimum'];d=r['direct_diagonalization']['curve']['minimum']
        plotting_curve(ax,r['times'],r['direct_diagonalization']['curve']['costs'],color,f'{name}: direct')
        plotting_curve(ax,r['times'],r['power_law_curve']['costs'],color,f'{name}: power law','--')
        ax.plot(a['time'],a['value'],'o',ms=8,mfc='white',mec=color,mew=1.8)
        ax.plot(d['time'],d['value'],'*',ms=14,color=color)
        minima.extend((a['value'],d['value']))
    ax.plot([],[],'o',mfc='white',mec='black',label=r'Analytic optimum $t_{ana}$')
    ax.plot([],[],'*',ms=12,color='black',label='Refined direct grid minimum')
    ax.set(xscale='log',yscale='log',xlabel='Step time (atomic units)',ylabel='Total Pauli rotations (cost proxy)',title='H4 / STO-3G / 1.0 angstrom',ylim=(.75*min(minima),6*max(minima)))
    atimes=[data['results'][h][l]['analytic_power_law_optimum']['time'] for l in LABELS]
    ax.set_xlim(.3*min(atimes),2*max(atimes))
    ax.xaxis.set_major_locator(FixedLocator([.3,.5,1,2,3,5]))
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x,pos:f'{x:g}'))
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.legend(fontsize=9,ncol=2,loc='upper left')
    fig.tight_layout()
    for ext in ('png','pdf'):fig.savefig(OUT/f'figure_A.{ext}',dpi=220,bbox_inches='tight')
    plt.close(fig)
    old=json.loads((ROOT/'artifacts/server_cost_validity/wide_time_cost_analysis.json').read_text())
    fig,axes=plt.subplots(1,3,figsize=(15,4.7))
    figure_b_data={}
    for h,ax in zip(('H2','H4','H6'),axes):
        if h=='H6':
            path=OUT/'references/4672f3f/artifacts/hchain_direct_optimal_time_scaling_v1_1_20260927_ce7b961/raw/H6_y8.json'
            saved=json.loads(path.read_text())['results']['H6']['results']['8th(Morales-Y8m10b)']
            n=DECOMPO_NUM[h]['8th(Morales-Y8m10b)'];alpha=saved['fixed_order_alpha'];tana=saved['analytic_optimal_time']
            times=[x['time'] for x in saved['points']];costs=[x['continuously_tracked_branch']['cost'] for x in saved['points']]
            index=min((i for i,c in enumerate(costs) if c is not None),key=lambda i:costs[i])
            a=dict(time=tana,cost=BETA*n/(tana*(EPS-alpha*tana**8)))
            d=dict(index=index,time=times[index],value=costs[index])
            r=dict(times=times,initial_fit=dict(alpha=alpha),formal_order=8,pauli_rotations_per_step=n,analytic_power_law_optimum=a,direct_diagonalization=dict(curve=dict(minimum=d,costs=costs)))
            source='4672f3f:'+str(path.relative_to(OUT/'references/4672f3f'))
        else:
            r=old['results'][h]['8th(Morales-Y8m10b)'];a=r['analytic_power_law_optimum'];d=r['direct_diagonalization']['curve']['minimum']
            source='20d64c2:artifacts/server_cost_validity/wide_time_cost_analysis.json'
        times=r['times'];alpha=r['initial_fit']['alpha'];p=r['formal_order'];n=r['pauli_rotations_per_step']
        t=np.geomspace(min(times),max(times),1000);error=alpha*t**p
        cost=np.where(error<EPS,BETA*n/(t*(EPS-error)),np.nan)
        plotting_curve(ax,times,r['direct_diagonalization']['curve']['costs'],COLORS[0],'Stored direct curve')
        ax.plot(t,cost,'--',color='#333333',lw=1.5,label='Power-law model')
        ax.plot(a['time'],a['cost'],'o',mfc='white',mec='black',ms=8,label=r'$t_{ana}$')
        ax.plot(d['time'],d['value'],'*',color=COLORS[0],ms=14,label='Stored direct grid minimum')
        ax.set(xscale='log',yscale='log',title=h,xlabel='Step time (atomic units)',ylim=(.75*min(a['cost'],d['value']),8*max(a['cost'],d['value'])))
        ticks=[x for x in (1,2,4,8) if min(times)<=x<=max(times)]
        ax.xaxis.set_major_locator(FixedLocator(ticks))
        ax.xaxis.set_major_formatter(FuncFormatter(lambda x,pos:f'{x:g}'))
        ax.xaxis.set_minor_formatter(NullFormatter())
        figure_b_data[h]=dict(analytic=a,direct_minimum=d,source=source)
    axes[0].set_ylabel('Total Pauli rotations (cost proxy)')
    axes[0].legend(fontsize=9)
    fig.suptitle('Published Morales 8th (Y8m10b): existing data only',y=1.02)
    fig.tight_layout()
    for ext in ('png','pdf'):fig.savefig(OUT/f'figure_B.{ext}',dpi=220,bbox_inches='tight')
    plt.close(fig)
    write_json(OUT/'figure_B_sources.json',figure_b_data)


def estimates(data):
    h6=data['systems']['H6'];source=data['results']['H6'];rows=[]
    for h,dimension,groups in ((8,4900,136),):
        scale=(dimension/400)**3;group_scale=groups/h6['num_groups']
        for alias,label in zip(ALIASES,LABELS):
            pts=source[label]['direct_diagonalization']['points']
            serial_reference=json.loads((OUT/'serial_H6_timing_reference.json').read_text())[label]
            build=serial_reference['median_build_seconds']
            other=serial_reference['median_other_seconds']
            perpoint=scale*(build*group_scale+other)
            # 160-point planning budget. Actual resonances can require more.
            serial=perpoint*160*1.5
            stages={'w8':9,'w1016':17,'wmy4':3}[alias]
            matrix=16*dimension**2
            resident=matrix*(groups+stages+8)+536870912
            streamed=matrix*(stages+8)+536870912
            rows.append(dict(system=f'H{h}',alias=alias,label=label,dimension=dimension,group_count_reference=groups,
                planned_points=160,safety_factor=1.5,estimated_point_seconds=perpoint,
                estimated_one_gpu_seconds=serial,ideal_three_gpu_lower_bound_seconds=serial/3,
                resident_device_bytes_with_20percent_margin=math.ceil(1.2*resident),
                streamed_device_bytes_with_20percent_margin=math.ceil(1.2*streamed),
                host_group_spectra_bytes=groups*matrix,
                requires_user_approval=True,status='not_executed',
                caveat='Cubic extrapolation from current busy shared A100/H6; not a measured H8 benchmark. Three-GPU value is an ideal lower bound; H8 speedup has not been verified. H8 requires streamed spectra.'))
    payload=dict(method='H6 median build and other time; n^3 and group-count scaling; 160 points and 1.5 safety factor',
                 numerical_validation_of_three_gpu_path='parallel_validation.json',rows=rows,
                 H8_existing_streamed_reference='0af2a8d:artifacts/server_hchain_direct_optimal_time_h8_phase_a_v1_3_20260927_33040c6/resource_feasibility.json',
                 H8_resident_spectra_ineligible_on_40GB_A100=True,
                 preparation_time_and_additional_adaptive_points='extra; estimates are formula sweep budgets, not guaranteed wall-time caps')
    write_json(OUT/'resource_estimates.json',payload)
    text=['| 系 | 公式 | 1 GPU の概算 | 3 GPU の理想下限 | GPUメモリ概算 |','|---|---|---:|---:|---:|']
    for r in rows:
        unit=60 if r['system']=='H7' else 3600;name='分' if unit==60 else '時間'
        memory=r['resident_device_bytes_with_20percent_margin'] if r['system']=='H7' else r['streamed_device_bytes_with_20percent_margin']
        text.append(f"| {r['system']} | {r['label']} | {r['estimated_one_gpu_seconds']/unit:.1f} {name} | {r['ideal_three_gpu_lower_bound_seconds']/unit:.1f} {name} | {memory/2**30:.1f} GiB/GPU |")
    text.extend(['','H₈は未実行。160点/公式、安全係数1.5の外挿であり、系の準備と追加の枝追跡点は別途必要。GPUの空きと負荷は実行前に再確認する。',
                 'H₄の3GPU経路は逐次と数値一致したが、小行列では逐次より遅かった。大きい系でも並列化の効果は実測で確認する。3GPU欄は速度向上の保証ではない。',
                 'H₈の群スペクトルだけで約48.7 GiBあり、40 GB GPUに全常駐できない。後続0af2a8dのホスト常駐・群ごとの転送方式が必要。表のH₈メモリはその方式を仮定し、今回のrunnerによるH₈実行は無効のまま。',
                 '1時間を超える可能性のあるH₈は、公式別の実行予算と停止条件の承認後に進める。'])
    (OUT/'resource_estimates.md').write_text('\n'.join(text)+'\n')


def tables(data):
    lines=['| 系 | 公式 | 解析的な総回転数比（8次v2＝1） | 直接最適化した総回転数比（8次v2＝1） | t_opt/t_ana | t_ana での r | t_ana/t_valid | 備考 |',
           '|---|---|---:|---:|---:|---:|---:|---|']
    header=lines.copy()
    lines=['**主対象：H₂・H₄・H₆**','']+lines
    comparisons={}
    for h in ('H2','H4','H6','H5'):
        if h=='H5':lines.extend(['','**参考：H₅**','']+header)
        rs=data['results'][h];base=rs[LABELS[0]];comparisons[h]={}
        for label in LABELS:
            r=rs[label];di=r['direct_diagonalization'];m=di['curve']['minimum'];g=di['diagnostic_gates']
            ar=r['analytic_power_law_optimum']['value']/base['analytic_power_law_optimum']['value']
            dr=m['value']/base['direct_diagonalization']['curve']['minimum']['value']
            notes=f"範囲内側；近傍符号反転なし；重なり最小 {di['minimum_selected_ground_state_overlap_probability']:.6g}"
            if not g['all_time_branch_agreement_pass']:notes+='；上側の枝照合不一致あり'
            if not base['direct_diagonalization']['diagnostic_gates']['optimum_branch_quality_pass']:notes+='；基準8次の最小点重なり基準未達'
            validity=r['power_law_validity']
            if validity['t_valid'] is None:notes+='；短時間側の連続10%適合域未確定'
            lines.append(f"| {h} | {label} | {ar:.4f} | {dr:.4f} | {r['direct_optimum_vs_analytic']['time_ratio']:.4f} | {r['at_analytic_time']['direct_to_model_ratio']:.4f} | {fmt(validity['t_ana_over_t_valid'])} | {notes} |")
            comparisons[h][label]=dict(analytic_total_cost_ratio=ar,direct_optimized_total_cost_ratio=dr,
                optimum_local_branch_quality_pass=g['optimum_branch_quality_pass'],all_time_branch_agreement_pass=g['all_time_branch_agreement_pass'],
                ratios_reference_has_optimum_quality_pass=base['direct_diagonalization']['diagnostic_gates']['optimum_branch_quality_pass'],
                same_time_direct_to_model_cost_ratio=r['at_analytic_time']['same_time_direct_to_model_cost_ratio'])
    data['results'].pop('H3',None)
    lines.extend(['','比は丸め前の値から計算。最小値は探索した有限領域の離散格子上の値であり、全正時刻での大域最小を証明しない。',
                 '「近傍」は連結した最小コスト+1%の区間。重なり最小は、下側の診断点から上側探索端までの全保存点での値。H₄/H₅/H₆の8次は上側で基底重なりを失うが、最小点近傍では枝照合が一致し、重なりは0.999以上。',
                 'H₆・8次は追加細分化で狭い共鳴を解像し、最小点を再選択。最終最小点の重なりは0.9999995、最終2回のコスト変化は3.64e-7および2.04e-9。初回の未収束データはattempts/に保管し、主表には使わない。',
                 't_validは固定αに対する短時間側からの連続10%適合域の最後の合格点。先行する雑音床以下（5e-13 Ha）は未判定。H₄/H₆の10次は最初の解像された点が10%基準を外れ、後から再適合してもt_validに採用していない。',
                 'H₃の診断は優先順位変更前に完了した記録として別途保管し、今回の表・報告から除外。H₇は新規計算なし。'])
    (OUT/'summary.md').write_text('\n'.join(lines)+'\n')
    data['comparisons_vs_w8']=comparisons
    data['diagnostic_only_systems']={}
    data['current_scope']=dict(primary=['H2','H4','H6'],reference=['H5'],awaiting_estimate_approval=['H8'],excluded=['H3','H7'])
    data['earlier_scope_diagnostics']=dict(H3=dict(source='H3_diagnostic.json',status='completed_before_scope_change_excluded_from_current_comparison'))
    write_json(OUT/'wide_time_cost_analysis.json',data)
    c=comparisons
    report=[
        '主対象の新4次/8次（解析→直接）：'+ '、'.join(f"{h} {c[h][LABELS[2]]['analytic_total_cost_ratio']:.4f}→{c[h][LABELS[2]]['direct_optimized_total_cost_ratio']:.4f}" for h in ('H2','H4','H6'))+'。H₄・H₆で新4次の優位、H₂で劣位を維持。',
        '主対象の10次/8次（直接）：'+ '、'.join(f"{h} {c[h][LABELS[1]]['direct_optimized_total_cost_ratio']:.4f}" for h in ('H2','H4','H6'))+'。3系とも10次が多い。H₈の約13%差は未検証。',
        f"参考H5：新4次/8次 {c['H5'][LABELS[2]]['direct_optimized_total_cost_ratio']:.4f}、10次/8次 {c['H5'][LABELS[1]]['direct_optimized_total_cost_ratio']:.4f}。H₈は見積もり後の確認待ち、H₃・H₇は今回の集計対象外。"
    ]
    (OUT/'report.md').write_text('\n'.join(report)+'\n')


def audit(data):
    checks=[]
    for h,rs in data['results'].items():
        for label,r in rs.items():
            times=np.array(r['times']);p=r['direct_diagonalization']['points'];e=np.array([x['direct_error_hartree'] for x in p]);cost=np.array([np.nan if x is None else x for x in r['direct_diagonalization']['curve']['costs']])
            valid=e<EPS;expected=BETA*r['pauli_rotations_per_step']/(times[valid]*(EPS-e[valid]))
            assert np.all(np.diff(times)>0)
            assert np.allclose(cost[valid],expected,rtol=2e-15)
            assert np.all(np.isnan(cost[~valid]))
            m=r['direct_diagonalization']['curve']['minimum']
            if m is None:
                assert h=='H3' and r['status']=='no_interior_minimum_through_16_tana'
                checks.append(dict(system=h,label=label,points=len(p),cost_recomputed=True,minimum_interior=False,comparison_eligible=False))
                continue
            assert m['is_interior_of_sampled_time_range']
            assert m['index']==int(np.nanargmin(cost))
            assert all(abs(x['direct_error_hartree']-abs(x['signed_direct_error_hartree']))<1e-30 for x in p)
            r_at=r['at_analytic_time'];assert abs(r_at['time']/r['analytic_power_law_optimum']['time']-1)<1e-12
            q=r_at['same_time_direct_to_model_cost_ratio'];order=r['formal_order']
            if q is not None:
                direct=BETA*r['pauli_rotations_per_step']/(r_at['time']*(EPS-r_at['direct_error_hartree']))
                assert abs(direct/r['analytic_power_law_optimum']['value']/q-1)<1e-13
            checks.append(dict(system=h,label=label,points=len(p),cost_recomputed=True,minimum_interior=True,signed_error_consistency=True))
    write_json(OUT/'validation.json',dict(pass_=True,checks=checks,scope='Cost algebra, point ordering, exact t_ana, signed/absolute errors, sampled minima. Scientific diagnostic failures remain visible and are not relabeled as pass.'))


def main():
    data=json.loads((OUT/'wide_time_cost_analysis.json').read_text())
    tables(data);figures(data);estimates(data);audit(data)
    print((OUT/'report.md').read_text())
    print((OUT/'resource_estimates.md').read_text())

if __name__=='__main__':main()
