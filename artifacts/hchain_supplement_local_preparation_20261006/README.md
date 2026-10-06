# H chain ローカル補助検証の準備

H6 geometry sweepとH6/H7/H8 rank convergenceを、このPCで実施するための準備です。
承認済みのDirection Cと添付の科学仕様は維持しています。
入力のbyte照合と補助コードのtestsは通過しましたが、科学実行枠とrank別continuationは未確定です。
新規科学計算は開始していません。

## 読む順序

1. [承認済み指示原文](../../docs/second_study_v2/hchain_supplement_local_20261006/approved_request.txt)
2. [Preregistration](../../docs/second_study_v2/hchain_supplement_local_20261006/preregistration.json)
3. [入力とsourceの監査](inventory.json)
4. [Focused tests](test_gate_summary.json)
5. [監査実装](../../review_response/hchain_supplement_preflight.py)と[prefix補助実装](../../review_response/hchain_cached_prefix.py)

Preregistration commitは `de91a39` で、実装と監査より先に固定しています。
起点は `971dc7a9b1b138fbbbb95fc684aa52af657e81b1` です。
source registryは原本のorigin/result commitと、今回照合したsnapshot commitを分離しています。
candidate CSVの公開commitと、科学predictionのfreeze commitも区別しています。

## 確認できた入力

H6/H7/H8の121 runtimeファイル、計11,211,647 bytesを保存manifestと照合しました。
9候補のbinary64時刻とhex、27 source blobも一致しています。
runtimeの移送、再構築、変更は行っていません。
runtimeは旧worktreeに残し、Gitには追加していません。

| System | 保存済み物理contract | Sector | CISD | K |
|---|---|---:|---:|---:|
| H6 | neutral singlet、alpha 3 beta 3 | 400 | 118 | 14344 |
| H7 | charge +1 triplet、alpha 4 beta 2 | 735 | 171 | 27552 |
| H8 | neutral singlet、alpha 4 beta 4 | 4900 | 361 | 47932 |

H7を中性doubletへ変更してはいけません。今回のrank検証は保存済みH7を使います。

監査はファイルhashとNPZのZIP member一覧だけを読み、arrayをdeserializeしていません。
保存truth、ground archive、進行中prospective truthのruntimeや途中出力は開いていません。
今回のbyte照合は、今後のarray identity・energy-origin・physical-branch検証を省略する理由にはなりません。
特にTrack GのR1 anchorを最終的にreuse可能とするには、そのclosureが必要です。

## 準備した補助コード

監査コードはsource、runtime、candidate時刻の不一致を停止理由として扱います。
保存値の書き換えや科学計算を行う機能はありません。
shared chainのprefix補助コードは、各prefixのorthogonalityとPF norm残差を
そのprefixだけから求め、rank32の最大残差をrank8へ流用しません。
実rank不足はmissingのまま返し、低rankをaccepted primaryへ昇格させません。

新規focused testsは監査前後とも33 passed、fail/skip 0です。
toy chainのrank8 prefixと単独rank8のcached arraysは完全一致しました。
これはmolecular rank8 reproductionの実証ではありません。
toy fixtureでは40 PFと40 H作用を使いましたが、分子作用・分子生成・ground・truth・gap取得はすべて0です。
分子science runner、予測freeze、scorer、最終図の実装と検証はまだ完了していません。

## 実行前に必要な承認

### ローカル独立実行枠

提案はCPU 1、worker 1、BLAS 1、RAM合計12 GiB、全体12時間、2 trackの累積新規保存量2 GiBです。
保存上限の128 MiB手前で停止し、GとRは逐次実行します。
既存runtimeはreadonly reuseし、複製しません。新たなruntime、ログ、checkpoint、成果物は累積保存量に含めます。

出力先候補はこのrepositoryの `.worktrees/pf-study2-hchain-h6-geometry-sweep-20261006/artifacts/hchain_h6_geometry_sweep_20261006`
と `.worktrees/pf-study2-hchain-m1-rank-convergence-20261006/artifacts/hchain_m1_rank_convergence_20261006` です。
これらは提案であり、ユーザーの数値承認・開始時刻に結び付いたallocation記録が必要です。
ホストの空きRAMや古いGPU allocationを承認の代わりにはしません。

### Rank別continuation

旧 `analyze_coordinate` は、前時刻で選んだprimary rank8 vectorを全prefixへ渡しています。
新しいrank比較で各prefixが自分の前時刻vectorを使うと、rank8の下位prefix差分widthが
旧計算と一致する保証はありません。rank32のvectorを全rankへ渡す案も、旧rank8との比較条件を変えます。

未承認の候補は「各rankは自身の前時刻vectorで独立に継続し、旧rank8 ruleの再現controlを
同じcached UQ/HQから別途保存する」です。
主診断widthは承認原文の `abs(delta_M(m)-delta_M(m/2))` を維持し、
旧rank8 controlのwidthを主診断widthへ置換しません。追加PF/H actionは不要です。
この選択はまだ実装・採用していません。ユーザーまたはGPTによる解析仕様の確認が必要です。

この2点が確定しても、source/input/time freeze、science runnerのfocused tests、
prediction commit/byte gate、truth boundaryを通過してから各科学段階を開始します。
Gの新truthはprediction freeze後だけ、Rの保存truthの読み出しも新prediction freeze後だけです。
旧rank8のformal結果、budget、width、abstentionは変更しません。

## 停止状態

現在は `local_inputs_byte_verified_science_gated` です。
Track G/Rの完了statusや `execution_ready` ではありません。
進行中のgeneral-molecule prospective validationとは独立し、その結果を使って仕様を変更していません。
研究方針の変更や追加条件の承認は、この準備からは発生しません。
