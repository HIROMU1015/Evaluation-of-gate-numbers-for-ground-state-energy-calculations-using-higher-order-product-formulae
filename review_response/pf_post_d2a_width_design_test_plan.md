# Post-D2A width design：C1 test plan draft

状態：test仕様のみ。実行、実装、threshold調整は未承認。

## 1. 境界

C1を承認する場合も、最初に既存D2-A predictionをbyte-identicalに固定し、width predictorが
truth artifactを開かないことを検査する。prediction/width/claim class/branch/budgetをcommitした後だけ、
別processのscorerが既存truthまたはoracle diagnosticを開く。

operational armとoracle armを別artifactにし、oracle gapやtarget IDをoperational出力へ戻さない。
C1結果を見てbound、gap定義、threshold、claim classを変更しない。

## 2. 数理positive controls

1. **二準位Hermitian**：`H=diag(E0,E0+Delta)`と混合stateについて、Rayleigh errorが
   `p Delta`、residualが`Delta sqrt(p(1-p))`になり、小`p`で二次型になることを検査。
2. **normal unitary**：既知2位相とlifted vectorで、B1 chord bound、B2 phase変換、
   direct phase errorの包含を検査。
3. **gauge covariance**：全固有位相と`rho`を同じglobal phaseで回転してもchord boundと
   principal phase幅が不変であることを検査。

## 3. 必須negative controls

1. **gap不足**：`g_rho_others<=r`ならcertificateを返さず`indeterminate`。
2. **near collision**：近接枝でphase幅がalias分離を越えた場合はliftを拒否。
3. **degenerate cluster**：単一固有値boundへ分解せず、cluster/set扱い未実装なら棄却。
4. **wrong-ground residual zero**：励起固有vectorの残差が0でもground certificateを発行しない。
5. **projected gap leakage**：Ritz gapをfull-space gap下界として使用したらfail。
6. **nonnormal projected matrix**：`T_m`がnonnormalでもnormal theoremを`T_m`へ直接適用しない。
7. **projection false shift**：`U=exp(iHt)`でもprojectionによる見かけのshiftをcertificateにしない。
8. **prefix-only width**：prefix一致だけでは上界を発行しない。
9. **true-gap leakage**：D1 true gapをoperational armが読むとfail。
10. **integer-coordinate mismatch**：absolute unwrap整数とground除去後整数を直接比較するとfail。

## 4. 幾何・数値境界test

- `rho=0`は`indeterminate`。
- `d<|1-|rho||`はidentity/bound不整合。
- `d>=1+|rho|`はphase幅`pi`のtrivial resultで、physical liftは未認定。
- arccos引数が丸め許容内だけ`[-1,1]`へclampされる。
- 丸め許容外はfailし、clampで救済しない。
- `g_chord=2 sin(g_phase/2)`は両固有値がunit circle上かつ`g_phase in [0,pi]`だけ。
- energy幅への変換は`t>0`かつalias-free liftが必要。
- roundoff、basis非直交、inexact PF/H actionの各budgetを別fieldとして加算する。

## 5. Resource-value test

- `e_direct=abs(delta_direct)`を強制し、signed値をbudget分母へ入れない。
- `epsilon_E-e_use<=0`ならbudgetを返さない。
- `w_win(t;0)`をbaseline同等境界、strict improvementを`w<w_win`として区別。
- `w_win<=0`を「改善不能」と「数値欠損」に分ける。
- `C_req`、`S_max_same_time`を保存6座標でC0 CSVと再現する。
- CPU秒、Pauli rotation、memoryを単一scalarへ無断換算しない。
- guarantee classまたはcoverageが異なるbudgetを単純winner判定しない。

## 6. Identity・アクセスtest

- 固定入力9件とD2-A prediction/result commitのSHA-256/blob identity。
- predictor allowlist外のD1/R1/Phase-B truth pathを開けないこと。
- scorer開始時にprediction commitとartifact hashを再確認。
- scorerがprediction、width、branch、claim class、budgetを変更できないこと。
- output manifestがfile set、bytes、SHA-256を全件照合すること。
- C1失敗時に別output、別threshold、追加座標で救済しないこと。

## 7. C1を承認する場合の上限案

以下はdraftであり、C0では実行しない。

- molecular development coordinates：既存HCl 6点だけ。
- new molecular coordinate / LiF / new PF：0。
- Arnoldi、PF vector action、H matvecの再実行：0（保存scalarを優先）。
- operational width arm：最大1方式。
- oracle sensitivity arm：最大1方式、freeze後のscorer専用。
- empirical/heuristic baseline：既存D2-A widthだけ。
- synthetic control：最大8 case、各dimension最大4、CPU単一process、BLAS thread 1。
- synthetic full spectrum：最大8、molecular full spectrum：0。
- GPU query/allocation/kernel：0。
- 新しいthreshold fit：0。

保存scalarだけでは必要な量を得られない場合、C1を暗黙に拡張せず、新計算の種類・上限・情報漏洩境界を
別authorizationで固定する。

## 8. C1 success / no-go draft

### Prototype candidate

- boundの仮定がtestで成立。
- operationalに取得可能なfull-space separation/reference経路がある。
- action/roundoffを含むwidthが少なくとも一部座標で`w_win`へ到達可能。
- 情報費用が記録され、元問題を実質的に解いていない。

### Information-cost / limit result

- oracle armでは鋭いがoperational gapを取得できない、または取得費用がmarginより不利。
- access modelを明示した反例または必要精度・費用関係が得られる。

### Route close

- 標準boundをtrue gapへ代入する確認に留まり、運用経路も有用な定量的限界も得られない。

いずれもC2、D2-B、LiF、holdoutを自動承認しない。
