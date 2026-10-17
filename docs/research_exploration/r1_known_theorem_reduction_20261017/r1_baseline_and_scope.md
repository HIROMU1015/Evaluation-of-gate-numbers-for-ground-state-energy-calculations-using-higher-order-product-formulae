# R1-P：通常4次PFとの比較と研究範囲

## 1. 同じ情報を使う強い対照

R1-P正本と同じH_+、PSD局所項、locality、extensiveness J、layer、cutoffと指定sectorを与える。
(A+)とglobal local PSDの適用条件は [定理対応](r1_known_theorem_mapping.md) に従う。
比較対象は既知の通常4次PF \(S_4\) であり、新しい係数を作らない。

[L09 Corollary S4](https://arxiv.org/pdf/2504.20746v1) のp=4、単stepのnegligible budgetをζ/Rに取り、
main Eq.19／Supplement S60のtelescopingを使うと、有限Rで
\[
 \|(S_4(t/R)^R-e^{-itH_+})P_E\|
 \le K_4\frac{J^4E_4'|t|^5}{R^4}+\zeta,
 \qquad E_4'=E+O(J\log(nR/\zeta))
\]
を得る。step条件は同Corollaryの \(|t|/R\le c_4^*/J\)。
定数は選ぶ既知4次word・locality・layerに依存する。
この有限R表示は、時間や逆誤差をpoly(n)と置くasymptotic簡略化を必要としない。

R1-Pは同じ \(r^{-4}\) に加え \((E')^2|t|^6\) 項を持つ。
よって、R1-P成立だけで通常4次PFより強い誤差保証を得たことにはならない。
固定word定数・synthesis費は異なるので、上界の項の比較から実回路費の普遍的支配も主張しない。

## 2. 操作と価格の対応

| 項目 | 既知二点外挿X_r | 通常4次PF |
| --- | --- | --- |
| 操作対象 | 二つのunitary回路の信号を符号付き古典処理 | 一つのunitary wordを反復 |
| 誤差次数 | r^-2係数を相殺してr^-4 | 元からp=4 |
| finite-step保証 | 標準条件下で既知補題へ還元したR1-P | L09 Corollary S4 p=4 |
| cutoff依存 | E'の一次と二次の両方 | 既知上界ではE_4'の一次 |
| simulation呼出し | shotごとにU_rまたはU_2r。X_rそのものをunitaryとしてcallしない | 目的protocolに必要なS_4反復 |
| signed weight | S=4/3+1/3=5/3。bounded signalの十分shotsにS^2が現れる | この外挿由来のweight増幅なし |
| control | Hadamard信号にはcontrolled PF等の価格が必要 | 同じ測定protocolならcontrol価格を含める |
| state・eta・tail | 反復準備、overlapとlow-energy tail証拠を払う | 同じ情報を与え、同じ費用会計をする |
| scalar | 各回路の総時刻tでcontrol枝のe^-ictを保持 | 同じscalar phaseを保持 |

samplingは確率 \(|b_j|/S\) でbranchを選び、測定値を \(S\operatorname{sgn}(b_j)\) で重み付ける既知法。
X_rがunitaryであるとの認定や、qubitization／block-encoding実装への転換はない。

## 3. 絶対E0への射程

既知のcを除いたnorm評価は
\[
 X_r^{orig}=e^{-ict}X_r,
 \quad\|(X_r^{orig}-e^{-itH_{orig}})P_E\|
 =\|(X_r-e^{-itH_+})P_E\|
\]
として戻せる。ただしcontrolled phaseは実装で残し、合成誤差を別計上する。
一体項・二体項・残余・係数誤差・元のsectorは省略しない。

このnorm上界だけではE0推定のpreparation、eta証拠、CDF／phase protocol、branch、全confidence、gate価格は閉じない。
総費用はT0の \(G_{setup}+\sum_jN_j(P_j+C_j+\cdots)\) のまま。
R1-Pの保守的な定数が巨大になり得ることも、実用改善を意味しない理由である。
今回は新しい数値ランキング・期待費用の再集計・benchmarkを一切行っていない。

## 4. 研究価値と次段階

標準の(A+)解釈では、相殺とlow-energy性の同時成立は既知補題から導ける固定次数の帰結。
通常4次PFも同じ情報で同次数の低energy保証を持つ。
このため「同時保証が未確認だったこと」だけを根拠に独立研究として続ける価値は、今回の確認後には支持されない。
ただし、既存の外挿法一般の実用性や任意の定数改善を否定する判断ではない。

**第一推奨：4軌道・2電子検証へ進まず、R1-Pを独立課題として不保持にするかGPT／ユーザーが判断する。**
任意fragmentの意味が意図されていた場合は、(A+)との差分・Jの会計を先に明確にする。
今回、正式不保持・PAUSE・採択を記録する状態ファイルは作らない。

J1／Q1と他研究のSOURCE・結果・grant・承認・科学契約・STOPは不変。
新一般定理の本格的証明探索、別外挿法、4軌道例、科学計算・実装へ自動進行しない。
