# Coherence保持部分空間：今回の課題と入力

2026-10-18 JST。ユーザーが添付した[作業指示原本](inputs/user_instruction.txt)と、明示指定した[GPT再レビュー原本](inputs/gpt_rereview_20261018.md)に基づく限定紙上構成。**正式研究ID・新規性認定・研究方向の正式採択ではない。**

## 1. 今回閉じる作業単位

係数と実行可能なseedから、有限のpredicate候補、coherent basis、取得すべき測定記録、更新規則までを記述する。射影QSEの基本式を再提示するだけでは終了しない。具体化した手順をVQNHE・shadow QSE等へ対応させ、差が残る場所を限定する。

成果の技術分類は[handoff](research_decision_handoff.md)。実施したのは一次文献取得・本文読解、固定SOURCE照合、紙上の生成規則・導出、文書とGit/hashの管理検査である。新規科学計算・保存値再解析・科学用symbolic checker・solver・simulation・回路build/compile・benchmark・新grantは各0件。記載した擬似コード・測定計画を実行していない。

## 2. 元問題とaccess

有限個のn spin orbitalsで、指定sectorの元Hamiltonianを

\[
H=cI+\sum_{pq}h_{pq}a_p^\dagger a_q+
\sum_{pqrs}v_{pqrs}a_p^\dagger a_q^\dagger a_s a_r
=cI+J
\]

とする。vの係数規約を入力に含め、重複・CAR符号・Hermiticity・mode順・scalar・sectorを固定する。二体係数の慣用の1/2や1/4はvへ吸収する。入力モデルの近似やDF切捨てを無費用で行わない。目標は指定sectorでの**絶対E0**であり、今回直接得られるものは部分空間Ritz energyとその統計幅までである。

| 入力／access | 必要な内容と費用 |
| --- | --- |
| 古典係数 | L個の有限bit係数と支持、sector情報。読取・整列・JW等への写像・算術精度を払う |
| seed | 純粋状態ψ=A\|0〉の独立な再準備。回路記述と1 copyの費用C_Aを持つ。ground、overlap、全振幅表は入力しない |
| 測定access | 通常のancilla、controlled Pauli、X/Y/Z測定。controlled-A、A†、time-evolution oracle、QPE、固有projectorは不要 |
| 古典記録 | term ID、測定軸、ancilla符号、occupation bitstringとseedの人口標本。理論上の記録形式だけを設計し、今回は標本を生成しない |
| 設計パラメータ | K_max、shot数m_H/m_S、Ritz精度ε_RR、失敗率α_H/α_S、古典費用重み。全て記号のまま。実入力・値・科学契約は未採択 |

seedは正しいsectorにあると仮定する。predicateはoccupationに対角なのでNとN_up/N_downを保存できる。ただし一般のS²とは可換しない。spin純粋sectorが必須なら、可換性を満たすpredicateへの制限・別構成が必要であり、本書をそのままspin純粋保証に用いない。個々のPauli測定操作は中間的にN sectorを出てもよい。元HのRitz評価はseedと対角basisのsector内で行う。

実装誤差・混合seed・読み出しnoiseを今回認証していない。数学は明示した純粋seed・理想測定のモデルについて述べる。将来は別の系統誤差幅を統計誤差と合わせて会計する。

## 3. 最初に具体化する電子family

一般二体Hへの測定恒等式は書けるが、生成則の検討対象を次へ絞る。

\[
H_{\mathrm{dd}}=cI+\sum_p\epsilon_p n_p+
\sum_{p<q}(t_{pq}a_p^\dagger a_q+t_{pq}^*a_q^\dagger a_p)
+\sum_{p<q}U_{pq}n_pn_q.
\]

非零hopping graphが連結、degreeが定数で有界、相互作用支持数がO(n)のdensity-interacting電子模型を紙上の主対象とする。tとUの非可換性を残す。spinful Hubbardの適切なsector等を含められるが、一般分子Coulomb積分のfamilyとの同一視はしない。

このfamilyで、係数から有限predicateを生成する手順は得た。一方、少数cellでgroundを近似できること、十分な人口、強対照への総費用差を保証する係数条件は得ていない。familyを「正しい振幅比が既知の系」と定義して穴を埋めない。

## 4. 既存研究との分担と保全

| 固定系列 | 今回の境界 |
| --- | --- |
| J1・Q1 | PAUSE維持。pulse探索・全固有basis・pairing level挿入を再開しない |
| R1-P | 独立候補不保持を維持。PF Richardson保証の再検討をしない |
| 集団遷移生成 | b58d5750…のPAUSED維持。reset/jump/coolingを変更しない。今回は元Hを変分制限する別作業 |
| 第一・第二研究、PR Track A/B・M1-S | 固有枝・PF/RTE law・native価格・保存値再会計を行わない |
| SOS-PF A2 | 7af83266…の接続設計とNOT_ADOPTEDを維持。certificate・lower boundを今回の近似誤差の穴埋めとして開発しない |
| PRのencoding／downfolding／測定関連 | 共通の数学語だけで無重複としない。元HのRitz basis・predicate生成という課題単位で比較し、既存grantや保証を移送しない |

全chat・未保存の同時研究の網羅監査はしていない。固定公開資料に記録された課題との対応を確認した範囲である。別chatのjob・共有設定・他worktreeへ書き込まない。

## 5. SOURCEの実際の読取り範囲

[source_registry.json](source_registry.json)の13資料について全bytesのGit blob/bytes/SHA-256・固定rawを照合する。意味の読取りはE01の20行・境界、E02の状態表、E03全文、E04/E06の構成全文、E05結論と境界、E07のreset恒等式と限定障害、E08全文、P01の系列概要・正式状態・STOP、P02の20方向と課題境界、P03全文である。E09/P04は来歴・参照確認。全transitive SOURCE、PR側長大資料の全数値表や全証明を再監査したわけではない。

前回GPT原本は取得済みで、公開用copyはbytesを変えていない。原本の「未公開」「未承認」は作成時点の記録として保持し、本作業の承認・公開状態とは分ける。P03はorigin/result commitが8031f29e…、verified snapshotが指定された7af83266…であり、同じ欄へ統合しない。

## 6. 作業領域とSTOP

branch `qc-coherent-adaptive-subspace-paper-20261018`、base `b58d5750b2d9d1917d3f34d25dd49bdcaf6b5c66`。独立worktreeのAGENTS.mdも読んだ。base版にない2026-10-17の性能・次段階記載規約は、今回の直接ユーザー提供規約として適用する。D1のblock-encoding/qubitization中心への無断移行禁止、D2の元H・scalar・sector保持を維持する。

本directoryのみを明示stage・通常commit/non-force pushし、独立fetch・固定raw照合後に停止する。K/shot/候補数の有限指定は科学作業量の定義であり、CPU/GPU/RAM/workerへの人工上限を設けるものではない。将来の計算は別の承認と性能準備が必要で、本書は実行契約・grantではない。
