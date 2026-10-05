# Prospective CPU preflight result — 2026-10-05

Status: `prospective_budget_safety_preflight_complete_review_required`.
科学計算開始の許可ではない。Direction C、承認済みRQ・claim scope、既存formal resultを維持する。

Publication status: `pending_user_push`。
Read-only調査とprotocol案、local commitは完了したが、GitHub handoffは未公開・未完了。
ユーザーが「プッシュはこちらで行うのでコマンドだけ」と指定したため、公開担当をユーザーへ引き渡す。
Codexはこれ以上push/API書込みを試行せず、local commitとpushコマンドを残して停止する。
通常HTTPS pushは `could not read Username` で失敗した。
既存credential helper、GitHub token環境変数、SSH鍵は確認できず、設定を追加していない。
接続済みGitHub連携は本人認証とrepository metadataを読めたが、Git tree作成は
`403 Resource not accessible by integration`。書込み権限の迂回や権限/共有設定変更はしない。
remote branch先端・remote fetch・成果blobの取得確認はできていない。
既存push認証経路の問い合わせに対し、ユーザーがpushを担当すると回答した。
公開待ちを科学計算の開始理由にしない。

ユーザー指定handoff `c04d95a9fa8b9653b58bea59169ce6e7352a9da0` の
AGENTS.md、指示書、必読資料を全文確認し、そのcommitから独立worktreeを作成した。
指定branch `pf-study2-prospective-server-preflight-20261005` のremote先端も同SHAだった。
公開成果snapshot `e895870f16878ee4181b0e0dfe3159826a791563` がhandoffの祖先であることを確認した。
成果origin `1883d8a75d5dfe83052c52da24c079ddfde2aa2f` と公開snapshotは別fieldで保持する。
今回の作業branchは `gpu-pf-study2-prospective-preflight-20261005`。

共有環境、package、Python/CUDA/driver、scheduler設定、他ユーザーprocessに変更を加えていない。
既存rootの未コミット変更・indexは保持し、変更先を新規review資料に限定した。
sandbox起動時の `bwrap: Failed RTM_NEWADDR` のため自動審査済みの実行経路を使用したが、
system/network/sandbox設定自体は変更していない。

## 確認結果と限界

| 項目 | 確認できたこと | 今回確立していないこと |
|---|---|---|
| CPU | EPYC 7742、2 sockets × 64 cores、128 logical CPUs、affinity 0–127 | 承認されたCPU割当。proc statusの0–255表記は128-visible CPUと一致せず、256を利用枠にしない |
| RAM | host総量・available、own cgroupと祖先のlimitをread-onlyで記録 | RAM予約・他ジョブ予約・自分の利用枠。`max` は利用許可ではない |
| disk | `/home` 空き約5.39 GiB、`/tmp` のfilesystem空き約547 GiB | 個人quota、予約、将来のruntime/cache出力先・I/O上限 |
| allocation | scheduler job ID/CPU/RAM割当metadataなし | `allocation_unverified`。worker数は未確定 |
| Python | `/home/AbeHiromu/venvs/trotter-common/bin/python` は実在、Python 3.12.3 | 数値importの互換性、実際のBLAS thread数、execution readiness |
| package | NumPy 1.26.4、SciPy 1.14.1、PySCF 2.7.0、OpenFermion 1.6.1等のmetadata | importや計算は実施していない。threadpoolctl metadataは検出せず、導入しない |
| history | heads/remotes/tags 128 refs、95 distinct tipsのtracked path調査。remote 88 headsはすべてlocal tip集合に存在 | 中間commit全内容、checkpoint refs、untracked結果、archive payload、他の履歴は網羅しない |
| candidates | 5 families × 4 geometryの20件案、別open-shell案4件、既使用identity 5件、実装除外例2件 | 確定test setは0。condition_unseen/family_unseen認定はともに0 |
| resources | STO-3G shell数・electron populationからdimensionとdense storageを整数算術で見積り | 新分子のRSS・速度・wall上限・並列効率の保証 |

計測日時とbyte値は [hardware_and_allocation.json](hardware_and_allocation.json) を原本とする。
瞬間的な機械全体のavailableと、自分の承認された利用枠を区別する。

LiH、LiF、BeH2は使用済みfamilyである。異なるgeometryをnew-family holdoutと呼ばない。
CH2/HCNには調査したref先端の分子名付きpathが見つからなかったが、内容まで網羅した独立性監査ではないため
`unverified` のままにする。20件のgeometryは事前設計の案であり、平衡値・実測相関・spectral有利性を主張しない。
CH2 singletもstate recipeの提案であり、ground multiplicityを仮定した採用ではない。
triplet案は別stratumとして承認前に追加しない。

## 実装上の不足

Active fileの `src/trotterlib/chemistry_hamiltonian.py` はH-chainの入力であり、一般分子のCISD/sector契約を提供しない。
既存 `_prepare_system` はRHF/CAS integral抽出後にfull-sector `eigh` とground state取得を実行するため、
prospective prediction前の入力生成へそのまま流用できない。
H8のstreamed input実装はground取得を分離しているが、H8・population(4,4)・dimension4900を固定している。
一般分子用のtruth-free wrapper、state/sector/order/energy originのseal、focused testsの別承認が必要。
今回はsourceを変更せず、どの関数もimport・実行していない。

## 完了した範囲と次の判断

Read-only hardware/allocation・環境metadata・使用履歴範囲の記録、candidate inventory、組合せ・storage算術、
parallel/resource案とprotocol案を作成した。確認できない項目を `unresolved_requires_review` と記録したので、
preflight調査は完了するが `execution_ready` ではない。
最終検証はJSON/CSV、ローカルリンク、manifest hash、local source/blob、禁止操作0、dirty保存に限定した。
公開commitの照合は認証不足で未完了であり、passedと記載しない。
数値test・legacy suite・数値pilotは実行していない。

新規SCF/Hamiltonian/CISD、PF/H action、reference/cheap、Arnoldi/M1、eigensolve、exact ground、
full PF、direct truth、gap、scoring、数値benchmark、GPU query/allocation/kernel、CuPy import、nvidia-smiは全て0。
初期metadata検索で旧文書の数値的な説明が一部表示されたが、候補・strata選択や旧truthの分析には使用していない。
詳細は [access_and_operation_audit.json](access_and_operation_audit.json)。

GPT側とユーザーには、最終条件/strataとnovelty要件、basis/active space/state recipe、一般分子reference、
3候補とT0/B0、fixed B1 selection、M1範囲/rank/width/adoption、truth/branch/gap/gates、
承認されたCPU/RAM/disk/wall枠とretry/failure/分母契約の判断を依頼する。
[protocol_draft.md](protocol_draft.md) の未確定10項目を解決してprotocolをcommitした後も、
次段階は別実行承認を要する。今回のcommit/pushを計算許可として解釈しない。

## Review資料

読む順序と公開SHAの取得法は [handoff.md](handoff.md)。
[candidate_inventory.csv](candidate_inventory.csv)、[usage_history_scope.json](usage_history_scope.json)、
[parallel_resource_plan.md](parallel_resource_plan.md)、[resource_planning_arithmetic.json](resource_planning_arithmetic.json)、
[source_registry.json](source_registry.json)、[bundle_manifest.json](bundle_manifest.json)、
[validation.json](validation.json) を同じ公開commitで確認する。
既存sourceや凍結science artifactの再生成・重複commitは行わない。
