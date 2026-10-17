# R1-P：既知定理の条件・記号対応

2026-10-17 JST。固定SOURCEはT0 commit `f0da24896b346e59ce225d1c264dd04420e1276c`。
正本は同commitの `t0_research_problem_candidates.md`（registry T02）。
正本の定数・適用域を変更せず、定理が適用できる条件を区別する。

## 1. 一次資料と証明箇所

| ID・固定版 | 使用する箇所 | 確認した証明の役割 |
| --- | --- | --- |
| [L08：2608.13862v1](https://arxiv.org/pdf/2608.13862v1) | §3.1 Lemmas 11–13、§3.2 Lemma 14、§5 Lemmas 29–31、§6.1 Theorem 32、Appendix A Eqs.258–268、§1.7 | 共通inverse-step展開、外挿相殺、global剰余、sector条件、打切り |
| [L09：2504.20746v1](https://arxiv.org/pdf/2504.20746v1) | Theorem 1、Supplement S2 Theorem S1／Corollary S2、S3 Theorem S3／Corollary S4、Eqs.S5–S59、S4 Eqs.S60–S66 | PSD、restricted commutator、局所励起抑制、finite-step剰余、反復 |
| [M26：2507.06557v4](https://arxiv.org/pdf/2507.06557v4) | §3.1 Theorem 3、Eqs.42–59と証明、§3.2 Theorem 4、Eqs.61–67 | L08 Lemma 29の原典。打切りの明示的step条件 |
| [AKL：1406.3898v3](https://arxiv.org/pdf/1406.3898v3) | §2.1、Theorem 2.1 Eq.8、§3の証明／Lemma 3.1 | L09 Eq.S41の基礎となる局所energy tail |

PDF identityと読取り範囲は [SOURCE registry](source_registry.json)。
L08の全application、M26 Appendix Bの全証明、L09数値実験を独立再検証したものではない。

## 2. 記号対応と正本

| R1-P正本 | L08 | L09 | 今回の規約 |
| --- | --- | --- | --- |
| modes／qubits n | n | N | 符号化後も固定localityを保つ対象 |
| H_+ | H | H | scalarを除いたPSD局所和。未知E0を引かない |
| local extensiveness J | g（§5） | g | 各siteに接する局所項norm総和 |
| E | low-energy cutは主定理の入力ではない | Δ | absolute cutoff |
| P_E | Π_iとは異なる | Π_≤Δ | 指定sector内の入力射影 |
| r、t/r | 1/s、sT | r、t/r | 総時刻t、microstep h=t/r |
| 対称2次S_2 | p=2、σ=2 | p=2 | 同じ固定wordと分割 |
| ζ | truncation／statistical εとは別 | negligible ϵとも別 | norm誤差の加算予算 |
| E'=E+C_0 J log(nr/ζ) | refined factorとは別 | Δ'=Δ+O(g log(N/ϵ)) | 固定wordからC_0を選べる存在命題 |

正本は
\[
 X_r=\tfrac43 S_2(t/(2r))^{2r}-\tfrac13 S_2(t/r)^r,
\]
\[
 r\ge C_0\max\{1,(J+E')|t|\},\quad
 \|(X_r-e^{-itH_+})P_E\|
 \le {C\over r^4}\{J^4E'|t|^5+J^4(E')^2|t|^6\}+\zeta.
 \tag{T0-R1-P}
\]
過去に未証明だったことと今回の条件付き還元判定を混同しない。

## 3. PSDは分割にも必要

L09 Eq.2は \(h_X\succeq0\)、Eq.3は \(\sum_{X\ni i}\|h_X\|\le J\)。
Eq.5／Theorem S3は \(H_\gamma=\sum_Xh_X^\gamma\)、\(h_X^\gamma\succeq0\)、
\(\sum_\gamma h_X^\gamma=h_X\) という分割を使う。layer数は \(\Gamma=O(1)\)。
原子局所項をlayersへ振り分けるgroupingなら同じJの会計も保たれる。
より一般のrefinementを用いるときは、L09 S40を同じJで使うため
\(\sum_{X\ni i,\gamma}\|h_X^\gamma\|\le J\) も確認した範囲に限る。
以下この適用範囲を **positive refinement条件(A+)** と略記する。

正本T0はPSD局所和とcommuting layersを記すが、任意のfragmentに対して(A+)を別式で宣言してはいない。
**元の正の局所項をlayersへ分ける通常の解釈なら満たす。任意の相殺再分解まで含める解釈では自動ではない。**
和のPSDだけから \(0\preceq H_\gamma\preceq H_+\) を推論しない。
今回は(A+)を正本へ追記せず、任意分割への保証も認定しない。
局所性・PSDは符号化した空間で必要であり、sector圧縮した項だけのPSDから自動では従わない。

## 4. L09が与えるもの

Theorem S1 Eq.S5は、各PSD局所Hamiltonianについて \(P H_jP\preceq bP\) なら
\[
 \|P[H_q,[\cdots,[H_1,H_0]]]P\|\le q!(2kJ)^q b. \tag{K1}
\]
これは**両側射影**。証明S7–S21はHermitian／anti-Hermitian性、PSD平方根、Cauchy–Schwarz、
重なるsupportの数え上げを使う。Corollary S2の同一stateでの絶対期待値の和を、各normの和へ無断で替えない。

Eq.S41はlocal O_Xについて
\[
 \|P_{>b}O_XP_{\le a}\|\le\|O_X\|e^{-(b-a-3J|X|)/(4kJ)}. \tag{K2}
\]
AKL Theorem 2.1／§3は、imaginary-time共役とnested commutatorからこの型のtailを導く。
spectral gap下限や射影oracleの実装は要しない。

L09 S3はdefect generatorを有限次数まで展開し、global Taylor remainder、cutoff外のlocal tail、
両側restricted部分に分ける（S28–S38）。S44–S51／S55–S59が有限hで三つを加算する。
PF word全体のlow-energy保存は仮定しない。
Γ固定のCorollary S4は、固定PFの定数で
\[
 \|(T_p(h)-e^{-ihH_+})P_E\|\le K_p(J|h|)^p b|h|+\varepsilon,
 \quad b=E+O(J\log(n/\varepsilon)),\quad |h|\le c_p^*/J. \tag{K3}
\]
反復には \([e^{-itH_+},P_E]=0\) とunitarityを使う（main Eq.19、S60）。
簡略なasymptotic step scaling（Proposition S5）にはpoly(n)の時間・逆誤差条件がある。
今回はK3を直接反復し、その追加仮定をR1-Pへ持ち込まない。

## 5. L08とfinite-step打切り

L08 Lemmas 11–13はeffective-Hの収束条件下で共通inverse-step展開を与え、Lemma 14が外挿の相殺とglobal剰余を扱う。
これだけでlow-energy上界にはならない。局所系の高次commutatorのfactorial増大があるため、
無限級数の収束域とR1-Pのstep域を同一視しない。

§5のLemma 29は原典M26 Theorem 3の条件も戻して使う：
\[
 q_0=\lceil\log(3n/\varepsilon)\rceil,\qquad |h|\le[8e^3c_*q_0kJ]^{-1},
\]
\[
 \left\|S_2(h)-\exp\left[-ih\left(H_++
 \sum_{\substack{2\le j\le q_0-1\\j\ \mathrm{even}}}h^jD_{j+1}\right)\right]\right\|
 \le\varepsilon. \tag{K4}
\]
DはHermitianな既知BCH Lie係数、\(c_*\) は固定wordの係数・stageから得る定数。
原典証明はsubsystem因子分解、local Taylor係数上界、有限打切りの幾何級数を使う。
L08 Eqs.126–130はこのtruncation誤差を繰返し・外挿へ配分する。
**打切り次数とstep条件を落とした使用は不可。**

## 6. sectorとlow-energyは異なる

L08 Theorem 32は各fragmentの \([H_\gamma,S]=0\) を要求し、PF、BCH係数、係数積もsector射影と可換になる（148–152）。
\([H_+,P_E]=0\) だけではこの証明をP_Eへ転用できない。
\[
 A B P_E=A P_E B P_E+A(I-P_E)B P_E
\]
の第二項を落とすのは誤り。\(\|P_E(X-U)P_E\|\) だけでもcutoff外出力は管理できない。

後述の(A+)下の還元はTheorem 32をlow-energy定理として使わず、全空間でK1/K2/K4を使い、
最後に入力を指定sectorへ制限する。このnorm不等式自体にはfragmentのsector保存を追加仮定しない。
sector専用の価格・実装を使う比較には、その実装の保存条件が別途必要である。
