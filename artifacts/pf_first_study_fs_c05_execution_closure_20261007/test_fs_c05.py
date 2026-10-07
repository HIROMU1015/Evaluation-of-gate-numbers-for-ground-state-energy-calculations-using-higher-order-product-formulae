"""Contract, negative boundary, scalar reproduction and native toy tests."""
import ast
import copy
import importlib.util
import json
from pathlib import Path
import sys
from unittest.mock import Mock

import numpy as np
import pytest
from scipy.linalg import expm
from scipy.sparse import csr_matrix

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import closure_adapter as a

def load(name):
    return json.loads((HERE/name).read_text())

def boundary():
    p=a.ROOT/'artifacts/pf_first_study_fs_c0_20261007/serialization_boundary.py'
    spec=importlib.util.spec_from_file_location('fs_c05_recovery',p)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def identity():
    return dict(hamiltonian_sha256='H',cisd_sha256='C',restricted_basis_sha256='B',
        ordered_group_sha256=['g0','g1'],ordered_component_sha256=[['c0','c1'],['c2']],
        sector_metadata_sha256='sector',step_order_sha256='step',source_kind='matching_historical_pickle')

# Baseline requirements 1–5.
def test_01_historical_3point_authority():
    p=load('fs_c1_protocol_v2.json')
    assert a.baseline_gate(p)
    historical=json.loads((a.ROOT/'artifacts/server_practical_calibration_minimal_20260923_79035cc/protocol.json').read_text())
    assert p['historical_baseline_model']==historical['selector']['proxy_model']['name']=='echo_imag_3point'
    assert p['historical_training_relative']==[0.1,0.2,0.3]

def test_02_sentinel_not_fit():
    p=load('fs_c1_protocol_v2.json')
    p['sentinel_in_fit']=True
    with pytest.raises(ValueError,match='sentinel'):
        a.baseline_gate(p)

def test_03_no_fourth_coordinate():
    p=load('fs_c1_protocol_v2.json')
    p['historical_training_relative'].append(0.4)
    with pytest.raises(ValueError,match='three'):
        a.baseline_gate(p)

def test_04_exact_absolute_coordinates():
    p=load('fs_c1_protocol_v2.json')
    old=json.loads((a.ROOT/'artifacts/pf_first_study_fs_c0_20261007/fs_c1_protocol.json').read_text())
    for new,saved in zip(p['systems'],old['systems']):
        assert new['M10_training_absolute']==new['historical_training_absolute']==saved['historical_training_times']
    p['systems'][0]['M10_training_absolute'][0]=np.nextafter(p['systems'][0]['M10_training_absolute'][0],np.inf)
    with pytest.raises(ValueError,match='coordinates'):
        a.baseline_gate(p)

def test_05_H01_five_point_cannot_replace():
    p=load('fs_c1_protocol_v2.json')
    p['historical_baseline_model']='echo_imag_5point'
    with pytest.raises(ValueError,match='replacement'):
        a.baseline_gate(p)

# Source requirements 6–11.
def test_06_wrong_whole_SHA_no_decode(tmp_path):
    p=tmp_path/'N2.pkl'; p.write_bytes(b'not-the-original')
    decoder=Mock(side_effect=AssertionError('must not decode'))
    result=a.check_pickle(p,'0'*64,decoder)
    assert result['status']=='NO_GO_SOURCE_IDENTITY' and not result['decoded']
    decoder.assert_not_called()

def test_07_missing_source_NO_GO(tmp_path):
    decoder=Mock()
    assert a.check_pickle(tmp_path/'missing.pkl','0'*64,decoder)['status']=='NO_GO_SOURCE_MISSING'
    assert load('GO_NO_GO_FOR_FS_C1.json')['status']=='NO_GO_SOURCE_MISSING'
    decoder.assert_not_called()

def test_08_wrong_H_rejected():
    actual=identity(); actual['hamiltonian_sha256']='other H'
    with pytest.raises(ValueError,match='hamiltonian'):
        a.validate_member_identities(actual,identity())

def test_09_wrong_CISD_rejected():
    actual=identity(); actual['cisd_sha256']='other state'
    with pytest.raises(ValueError,match='cisd'):
        a.validate_member_identities(actual,identity())

def test_10_ordered_groups_rejected():
    actual=identity(); actual['ordered_group_sha256'].reverse()
    with pytest.raises(ValueError,match='ordered_group'):
        a.validate_member_identities(actual,identity())

def test_11_regeneration_rejected(tmp_path):
    with pytest.raises(ValueError,match='regenerated'):
        a.check_pickle(tmp_path/'p.pkl','0'*64,regenerated=True)
    actual=identity(); actual['source_kind']='pyscf_regenerated'
    with pytest.raises(ValueError,match='historical'):
        a.validate_member_identities(actual,identity())

# Native backend requirements 12–17: actual old function bodies on toy arrays.
def test_12_arbitrary_state_native_left_product():
    backend,state=a.fixture()
    Z=np.diag([1.,-1.]); X=np.array([[0.,1.],[1.,0.]])
    # Independently expand the full unmerged S2 sequence.
    expected=state.copy()
    for w in backend.sequence:
        for H,weight in ((Z,w/2),(X,w),(Z,w/2)):
            expected=expm(1j*0.2*weight*H) @ expected
    actual=backend.forward(state,0.2)
    np.testing.assert_allclose(actual,expected,rtol=0,atol=2e-14)
    other=np.array([0.,1.],dtype=complex)
    assert not np.allclose(backend.forward(other,0.2),actual)
    assert actual.dtype==np.complex128

def test_13_echo_sign_time_state_origin():
    backend,state=a.fixture()
    evolved=backend.forward(state,0.2)
    direct=np.vdot(state,expm(-1j*0.2*backend.H.toarray()) @ evolved)
    result=backend.proxy(state,0.2)
    assert result['proxy']==pytest.approx(direct.imag/0.2,abs=4e-15)
    assert result['proxy'] > 0
    wrong=np.vdot(state,expm(1j*0.2*backend.H.toarray()) @ evolved)
    assert abs(wrong.imag/0.2-result['proxy']) > 1e-2

@pytest.mark.parametrize('state',[np.array([1.,0.]),np.array([0.,1.]),np.array([1.,1j])/np.sqrt(2)])
def test_14_PF_norm(state):
    backend,_=a.fixture()
    assert abs(np.linalg.norm(backend.forward(state,0.3))-1) < 2e-14
    with pytest.raises(ValueError,match='normalized'):
        backend.forward(2*state,0.3)

@pytest.mark.parametrize('index',[0,1])
def test_15_saved_scalar_numerical_convention(index):
    saved=load('saved_scalar_fixture.json')['systems'][index]
    result=a.historical_scalar_fit(saved['times'],saved['saved_proxy_values'],saved['t_ref'],saved['t0'])
    # Arithmetic check only, portable binary64 roundoff tolerance; never a backend certificate.
    np.testing.assert_allclose(result['coefficient_values'],saved['saved_coefficients'],rtol=2e-14,atol=0)
    assert result['signed_prediction_at_t0']==pytest.approx(saved['saved_signed_prediction'],rel=2e-14,abs=0)
    for t,imag,proxy in zip(saved['times'],saved['saved_echo_imaginary'],saved['saved_proxy_values']):
        assert imag/t == proxy

def test_16_complete_cold_fixture():
    initial,s0=a.fixture(); cold,s1=a.fixture()
    assert initial.H is not cold.H and initial.spectra is not cold.spectra
    assert initial.ledger is not cold.ledger and not np.shares_memory(s0,s1)
    for a0,b0 in zip(initial.spectra,cold.spectra):
        assert not np.shares_memory(a0.batches[0].eigenvectors,b0.batches[0].eigenvectors)
    def toy_refinement(backend,state):
        # Tiny two-dimensional one-residual Ritz fixture, built independently.
        hstate=backend.H @ state
        backend.ledger.explicit_Ritz_H_matvec += 1
        residual=hstate-np.vdot(state,hstate)*state
        q=residual/np.linalg.norm(residual)
        hq=backend.H @ q
        backend.ledger.explicit_Ritz_H_matvec += 1
        V=np.column_stack((state,q)); HV=np.column_stack((hstate,hq))
        _,vectors=np.linalg.eigh(V.conj().T @ HV)
        backend.ledger.small_Ritz_solve += 1
        return V @ vectors[:,0]
    r0=toy_refinement(initial,s0); r1=toy_refinement(cold,s1)
    assert not np.shares_memory(r0,r1)
    times=[0.1,0.2,0.3]
    y0=[initial.proxy(r0,t)['proxy'] for t in times]
    y1=[cold.proxy(r1,t)['proxy'] for t in times]
    f0=a.historical_scalar_fit(times,y0,1.,0.4,ledger=initial.ledger)
    f1=a.historical_scalar_fit(times,y1,1.,0.4,ledger=cold.ledger)
    assert f0==f1
    assert initial.ledger.scalar_fit==cold.ledger.scalar_fit==1
    assert initial.ledger.PF_forward==cold.ledger.PF_forward==3
    assert initial.ledger.explicit_Ritz_H_matvec==cold.ledger.explicit_Ritz_H_matvec==2
    assert initial.ledger.small_Ritz_solve==cold.ledger.small_Ritz_solve==1

def test_17_unknown_internal_work_null():
    backend,state=a.fixture(); backend.proxy(state,0.2)
    snap=json.loads(json.dumps(backend.ledger.snapshot()))
    assert snap['internal_count_status']=='unknown'
    assert all(x is None for x in snap['expm_internal'].values())

# Cost requirements 18–20.
def test_18_no_mixed_unit_scalar():
    cost=load('cost_contract.json')
    assert cost['single_weighted_sum'] is None
    assert len(set(cost['units'].values()))==3
    snap=a.Ledger().snapshot()
    assert set(snap['classical'])=={'wall_seconds','peak_RSS_bytes'}
    assert snap['predicted_QPE']['unit']=='PF rotations'

def test_19_logical_echo_counts_separate_from_internal_H():
    backend,state=a.fixture()
    backend.proxy(state,0.1); backend.proxy(state,0.2)
    assert backend.ledger.logical_exact_H_echo==backend.ledger.PF_forward==2
    assert backend.ledger.explicit_Ritz_H_matvec==0
    assert backend.ledger.expm_internal['matvec'] is None
    assert backend.ledger.group_application==30

@pytest.mark.parametrize('rank',[0,1,3,8])
def test_20_rank_stop_actual_work(rank):
    plan=a.action_plan(rank)
    assert plan['explicit_Ritz_H_matvec']==4*(1+rank)
    assert plan['PF_forward']==plan['logical_exact_H_echo']==32
    assert plan['total_fit_calls']==8
    assert plan['M10_initial_operational_fits']==2
    with pytest.raises(ValueError):
        a.action_plan(9)

# Truth requirements 21–23.
def test_21_truth_reader_never_invoked():
    reader=Mock(side_effect=AssertionError('truth must not open'))
    with pytest.raises(PermissionError,match='truth barrier'):
        a.open_c1_truth(reader)
    reader.assert_not_called()

def test_22_direct_truth_not_tolerance_input():
    with pytest.raises(ValueError,match='authorized'):
        a.reproduction_tolerance({'direct_truth':1e-8})
    result=a.reproduction_tolerance(dict(historical_backend_bound=None,cold_variability_bound=None,floating_backend_bound=None))
    assert result['tolerance_hartree'] is None
    assert result['status']=='M00_REPRODUCTION_TOLERANCE_UNCLOSED'

def test_23_exact_ground_not_source_construction():
    ns=a.native_namespace()
    assert 'prepare_condition' not in ns and 'diagonalize_components' not in ns
    assert 'fixed_population_basis' not in ns and 'find_balanced_z2_symmetry' not in ns
    actual=identity(); actual['exact_ground_overlap']=Mock(side_effect=AssertionError())
    assert a.validate_member_identities(actual,identity())
    actual['source_kind']='constructed_from_exact_ground'
    with pytest.raises(ValueError):
        a.validate_member_identities(actual,identity())

# Recovery requirements 24–25.
def test_24_private_recovery_before_public(tmp_path):
    b=boundary(); private=tmp_path/'private.json'; public=tmp_path/'public.json'
    def validator(payload):
        assert private.exists() and not public.exists()
        assert b.recover(private)==payload
    result=b.checkpoint_then_publish({'rows':({'proxy':np.float64(0.1)},),'ledger':{'PF':1}},private,public,validator)
    assert result['recovery_saved_before_schema']
    assert private.read_bytes()==public.read_bytes()

def test_25_failure_does_not_authorize_rerun(tmp_path):
    b=boundary(); private=tmp_path/'private.json'; public=tmp_path/'public.json'
    science=Mock(return_value={'proxy':0.1,'ledger':{'PF':1}})
    payload=science()
    reject=Mock(side_effect=ValueError('schema failed'))
    with pytest.raises(ValueError,match='schema failed'):
        b.checkpoint_then_publish(payload,private,public,reject)
    assert b.recover(private)==payload and not public.exists()
    with pytest.raises(FileExistsError):
        b.checkpoint_then_publish(payload,private,public,reject)
    science.assert_called_once()

# Additional high-impact boundary/provenance checks.
def test_matching_bytes_decode_only_after_hash(tmp_path):
    p=tmp_path/'source.pkl'; p.write_bytes(b'identity fixture')
    decoder=Mock(return_value={'identity_hash':'fixture'})
    result=a.check_pickle(p,a.digest(p.read_bytes()),decoder)
    assert result['decoded']; decoder.assert_called_once_with(p.read_bytes())

def test_component_reorder_rejected():
    actual=identity(); actual['ordered_component_sha256'][0].reverse()
    with pytest.raises(ValueError,match='component'):
        a.validate_member_identities(actual,identity())

def test_step_order_rejected():
    actual=identity(); actual['step_order_sha256']='reversed'
    with pytest.raises(ValueError,match='step_order'):
        a.validate_member_identities(actual,identity())

def test_production_scope_and_size_blocked():
    backend,_=a.fixture()
    with pytest.raises(PermissionError):
        a.NativeFixtureAdapter(backend.H,backend.spectra,backend.sequence,scope='production')
    with pytest.raises(PermissionError):
        a.NativeFixtureAdapter(csr_matrix((1568,1568)),backend.spectra,backend.sequence)

def test_coefficients_cannot_drift():
    backend,_=a.fixture()
    seq=list(backend.sequence); seq[0]=np.nextafter(seq[0],np.inf)
    with pytest.raises(ValueError,match='coefficients'):
        a.NativeFixtureAdapter(backend.H,backend.spectra,seq)

def test_native_hash_tampering_rejected(tmp_path):
    pins=load('native_source_pins.json')
    p=tmp_path/pins['sources'][0]['path']; p.parent.mkdir(parents=True); p.write_text('tampered')
    with pytest.raises(ValueError,match='hash mismatch'):
        a.native_namespace(tmp_path)

def test_identity_report_never_certifies_missing_arrays():
    canonical=load('canonical_source_identity.json')
    assert canonical['closed'] is False
    for s in canonical['systems']:
        assert s['cisd_sha256'] is None and s['source_path'] is None
        assert s['expected_whole_pickle_sha256'] and s['recovered_whole_pickle_sha256'] is None

def test_saved_primary_never_replaced():
    v2=load('fs_c1_protocol_v2.json')
    old=json.loads((a.ROOT/'artifacts/pf_first_study_fs_c0_20261007/fs_c1_protocol.json').read_text())
    for s0,s1 in zip(old['systems'],v2['systems']):
        for field in ('B0','historical_signed_prediction','historical_coefficients','t0','t_ref','identity'):
            assert s0[field]==s1[field]
    for s in v2['systems']:
        c=abs(s['historical_signed_prediction']); cfg=v2['constants']
        B=cfg['gamma']*cfg['beta']*s['K']/(s['t0']*(cfg['epsilon_E']-c))
        assert B==pytest.approx(s['B0'],rel=3e-15,abs=0)

def test_no_science_driver_imports_in_builder_adapter():
    for filename in ('build_closure.py','closure_adapter.py'):
        tree=ast.parse((HERE/filename).read_text())
        imports=[n.module or '' for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)]
        assert all('pyscf' not in n and 'run_h01' not in n and 'openfermion' not in n for n in imports)
        calls=[n.func.id for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name)]
        assert not set(calls)&{'prepare_condition','eig','eigh','schur','open_c1_truth'}
