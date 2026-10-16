# P1STAR-A-v1 資源運用追補 — 2026-10-17

本追補は、2026-10-17のユーザー指示「P1* Phase B科学用driverの実装・人工検証」により承認された**実用的な資源管理への移行**を記録する。元契約は直接変更しない。旧比較案 `R-TERMS-2` の全条項の採択を意味しない。

正本：[科学契約・commit 1771564d](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/1771564d919837e2440a9fcb175ac054284a729c/docs/research_exploration/p1star_symbolic_preflight_20261017/symbolic_verification_contract_draft.md)。資源比較は [commit a242f8e7](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/a242f8e7fffa8b3f51b06b89242f5cc16c6b839f/docs/research_exploration/p1star_resource_contract_options_20261017/resource_contract_options.md) の履歴として維持する。

## 維持する条件

- 自前の `TermLedger` による管理mapのlive entry総数の上限200,000。無効化・超過後の継続は行わない。
- 明示した一つの実行だけを扱う。協調lockと、一度失敗しても消費されるattempt markerを使う。自動retry、別ansatz、別sector、追加科学条件による救済はない。
- 計算workerは1個。workerを許可CPUの1個へ固定し、native solverはin-processで使う。controllerは監視とIOを担当する。parallel solverは無効化し、BLAS等のthread数は1に設定する。
- 全体wall timeout、worker RSS監視、virtual address space制限、異常終了の検出、bounded stdout/stderr、停止理由の記録を使う。管理出力の上限20 MiBを維持する。
- 数学的exact性、科学的入力と条件、固定hash、別途実行承認、mandatory STOPは維持する。

## 今後の必須保証から外す条件

- Z3 native内部・Python一時表現を含む全中間termsを200,000以下にする包括的instrumentationは要求しない。TermLedgerはnative AST、solver内部、多項式の非管理コピー、rank計算のlist、provenance・JSONの一時表現を数えない。
- 専用cgroupによるjob全体16 GiB RAM hard enforcementは実行準備の必須条件にしない。旧16 GiBを無条件なRAM保証として記載しない。
- これらの厳密保証だけを目的とした環境再調査・構築は再開しない。本作業ではcgroup作成・変更、権限昇格による資源設定、schedulerへの科学job投入を行っていない。

## 実用監視の意味と限界

`practical.py` はworkerの `/proc/<pid>/status` のRSSを約20 ms周期で読み、設定値超過またはwall超過で所有process groupをkillする。観測間の増加、scheduler遅延、停止処理の遅延、controllerのメモリはこのRSS閾値に含まれない。共有環境への負荷を減らす手段であり、job全体RAM hard capではない。workerは子processを起動しない実装だが、OSのjob全体process数保証は追加していない。

`RLIMIT_AS` はworkerのvirtual address spaceに適用する。RSS、RAM、swap、job全体メモリと同一視しない。[Python 3.11公式resource文書](https://docs.python.org/3.11/library/resource.html#resource.RLIMIT_AS) が示すaddress spaceの制限として用いる。実際に使用したCPythonは3.11.1であり、オンライン文書のpatch版と一致するという主張はしない。

stdout/stderrはworkerからcontrollerへの合算captureを制限する。最終JSON envelopeも制限する。controller自体への外部kill、電源断、OS障害では最終ログが残らない場合がある。attempt markerは残し、operatorは外部異常をINCONCLUSIVEとして記録する。別の入口・別lock directoryを意図的に使う利用者まで排他するsecurity sandboxではない。

## 停止と次回の固定事項

項数・trace上限、wall/RSS/output/AS不足、MemoryError、backend不一致、solver UNKNOWN、異常終了、witness再照合失敗は `INCONCLUSIVE`。どれも数学的UNSATへ読み替えない。UNSATはexact solverが指定した等式と閉box全体に対して返した場合だけ、solver依存の結論として記録する。

科学計算のwall、RSS閾値、AS上限、solver timeout、trace上限等は**未固定**。今回のtoy設定を科学設定に流用して承認済みとしない。次回の明示承認時に、これらの値、環境、code、入力、契約、追補のhash、共通lock/attempt directory、1回限りの実行と終了点を固定する。

4 modes、2因子、N=2の識別用途、full Fock主判定、共通oscillator、固定12 segment、実12変数box、4次形式展開、目標・位相・演算子順序は元契約のまま。D1/D2および既存研究のSTOP/PAUSEを変更しない。

**本追補は科学実行承認ではない。技術成果物の公開・照合後にmandatory STOP。**
