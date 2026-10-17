# 複数jump／有限cycle：判断用handoff

2026-10-18 JST。**境界hoppingを保持した有限cycleは構成できた。ただし既知の部分空間resetへ還元され、独立した新構成候補は0件。一般のflag-breaking非可換Hへの新生成則は未構成・未判定。** 科学的採択/正式保留や一般NO-GOを記録するものではない。

Repository：Evaluation。branch `qc-collective-transition-multijump-cycle-20261018`、親 `b7ec04fb84cd01eb846b9e3cc6d545bdf833e657`。新規7資料だけを追加し、最終40文字SHAは公開後の完了報告で示す。

読む順序：本書 → [係数からcycleの構成](coefficient_to_cycle_construction.md) → [数学的導出・障害](cycle_paper_derivations.md) → [既知法・横断差分](prior_art_overlap_and_latest_sources.md) → [SOURCE registry](source_registry.json)・[静的監査](static_audit.json)・[provenance](provenance.json)。

## 1. 今回具体化できたもの

前回の5番目のmodeへの境界hoppingを残し、sourceを単一ketからoccupation部分空間 `P=span{12,23,25}` へ広げた。係数の支持と保存flagからPを選び、全sourceを同じrateで既知target34へ移す3-jump cycleを生成する。

\[
L_1=|34\rangle\langle12|,\quad
L_2=|34\rangle\langle23|,\quad
L_3=|34\rangle\langle25|.
\]

CAR符号を固定したfermionic式、ancilla unitary/reset、通常gateへ落とす規約を記載した。source ketはH固有stateでなく、block対角化・未知gap・固有一覧・全H oracleを入力しない。

`U>μ>0, ε5≥0, t>0, τ≠0, δ=2μ−t−|τ|>0` という明示classで、元の非可換H5に対し

\[
\Phi^*(H_5)-H_5\preceq-\sin^2\theta\,\delta P
\]

を紙上で示した。各substepは加熱し得るが全cycleで下降する。係数から決めるcutoff以下のspectral weightの増加下界も示した。scalar・N=2全空間・spin保存を追跡し、δを未知のexcitation gapとはしていない。

## 2. なぜ独立した新アルゴリズムとは判定しないか

合成チャネルは、Pのweak measurement後に成功branchだけ既知bへresetするinstrumentと**完全に一致**する。これは既知の部分空間振幅減衰/conditional replacementである。gateが同じという理由だけでなく、作用とcoherence・出力まで一致する還元を示した。

係数生成も、このclassでは保存された単純flagとtriangle norm証拠に尽きる。未知groundへ収束する新機構、一般にPを探す安価な規則、同accessの強いbaselineに対する費用差を得ていない。したがって**具体化したcycleはB（既知法への還元）**。一般の新規則が存在しないという判断ではない。

## 3. 数学的に新しく分かった限定的な点

- 同じrank-one jumpの細分化・phase変更・reset反復は同じ振幅減衰に戻り、前回の障害を避けない。
- sourceを係数から分かる不変部分空間へ広げれば、source個々の固有vectorを知らずにcycleの全状態下降を作れる。
- このreset文法の全状態単調性は、Pが元Hで不変かつ `PHP≥E_b P` であることと同値。rank-oneの固有state条件が部分空間不変性へ移る。

これらは今回の紙上設計診断であり、独立priority/新定理の正式認定ではない。

## 4. 残る非可換障害と限定inputの進捗

さらにdown-hopping `η(a4†a2+a2†a4)` を加えるとP/Q coherenceを生み、固定cycleの全状態単調性は破れる。closureを広げるだけではtargetもsourceに入り、この文法は止まる（C：限定障害）。別のcycle一般を否定しない。

一方、P/Q block-diagonal inputに限り、logical cycle列はそのclassを保つため、同じ元H_etaの期待energy下降は繰返しでも残る。coherenceを持つinputに対する条件付きdrift上界も示した。ただしH_etaの物理時間発展を途中で入れるとclass保存は一般に失われる。H_etaに必要なcoherenceを生成/制御する新しい係数則はD：未構成・未判定。

## 5. 絶対E0接続の到達点

低energy人口の増加は任意精度のE0推定やgroundへの収束ではない。Q内のdark成分が残り、既知bを直接準備する対照もある。H5では係数だけで `E_b−r≤E0≤E_b` が既に分かる。要求精度がこの区間だけで足りる場合は、古典区間の中点という対照を除外しない。

本cycleの後にenergy readoutを行うなら、準備後の低energy tail、精度・confidence、scalar復元、PF/synthesis/branch、reset/gate drift/sector leakage、古典生成費を別に保証する。D1を維持しblock-encoding/QSVT中心へ移行しない。D2では元の有限基底電子Hの絶対E0を保持するが、本模型は一般Coulomb分子の解法ではない。資源数値・改善率・benchmarkは作っていない。

## 6. 最新の他研究との重複確認

PRの旧20方向を再利用し、今回remote観測で追加のA2 EW2監査/実用preflight、H8再会計/H4-H8証拠整理を差分確認した。[詳細と固定commit](prior_art_overlap_and_latest_sources.md) §4を参照。

A2には追加の保証/実用条件の記録があるが未採択、certificate未完成。H8は既に6単価反映の再会計が公開されており、旧「削減率未更新」を現在の取得不足と扱わない。本研究はstate populationを変える別課題で、A2の式やH8費用を再計算していない。既存J1/Q1/R1-P/A1/A2と他系列の状態・SOURCE/grant/STOPを変更しない。

## 7. 次に判断すべきこと

**GPT／ユーザー**：この既知resetとしての限定成果を受け、さらに構成研究を続けるか、目的を修正するか、保留するかを判断する。

継続する場合の最小の数学的課題候補は、Pを保存しないH_etaについて、未知の固有projectorを使わず、H_etaが作るP/Q coherenceも含む入力classで進捗を持つ**具体的な**cycleを係数から生成できるか、である。単にjump数・名称・angleを変えるだけや、現在の部分空間resetを再提示することでは不足する。これは未承認の次作業案で、今回追加探索する指示ではない。

数値検証は今回実施せず、必要性も自動認定しない。将来実施するならHamiltonian/sector/初期state/cycle、係数/誤差/出力/判定/科学call/STOPを別契約と明示承認で固定する。既存の固定資源契約を変更しない。

## 8. 公開・保全・停止

18固定repository資料と6一次資料を取得し、repository sourceのGit blob・bytes・SHA-256・固定rawを照合した。科学的証明が機械でPASSしたという意味ではない。既存資料を重複copyせず新規7資料だけをstageして通常commit/non-force pushする。remote SHA・独立fetch・7 blob/bytes/SHA-256・固定rawを照合し、provenance自身も自己除外manifestとは別に確認する。

開始前Evaluation115件・PR184件の既存worktreeをHEAD/branch/status/staged/unstaged digestで比較する。ignored runtime・未追跡内容・全他jobの包括的監査ではない。PR本体には書き込まず、最新4branchは一時的な独立bareへ読むためだけにfetchした。

保全観測中、PRの `refs/remotes/origin/qc-a2-practical-preflight-20261017` だけが `370372e0160ce181f17a09ea552064e6e9f493bc` から `c62fe99d29e7edcaf0cb655d789d297890709a29` へ進んだ。本作業はPR refを書き換える操作を行っておらず、並行したremote-tracking更新として監査に記録する。参照済み固定snapshotはc62fe99dで、既存worktreeのHEAD/branch/作業差分は一致した。

新規科学数値計算、保存値再解析、科学用記号プログラム、solver、simulation、回路build/compile、benchmark、新grant、詳細科学レビュー、正式研究採択/保留変更は0件。

**Mandatory STOP：公開・照合後にCodexは停止し、GPT／ユーザーへ判断を戻す。**
