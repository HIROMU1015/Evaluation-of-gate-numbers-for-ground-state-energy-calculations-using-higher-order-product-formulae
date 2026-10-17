# T0：未採択の数学的研究課題――保持1件

**R1のみを、次の紙上検証の選択肢として条件付き保持する。** 新しい操作原理・新アルゴリズム・総資源優位を認定した結果ではない。
既知の外挿PFの保証問題であり、成果型の一括採用、科学GO、Q1/J1等の再開は含まない。
根拠となる未解決性は [L08 §1.7](https://arxiv.org/html/2608.13862v1) の明示した低energy外挿の問題に限定する。
通常PFの低energy改善自体は [L09](https://arxiv.org/pdf/2504.20746v1) ですでに解決されている。

## R1：低energy射影の下で外挿の相殺次数を保てるか

### 1. 対象クラスと入力

\(n\) fermion modesのnumber-conservingな有限基底Hamiltonianのうち、指定sector \(\mathcal S\) 上で、
既知scalarを保持したまま \(H_{orig}=cI+H_+\) と書ける制限クラスを対象とする。
\(H_+=\sum_Xh_X\)、\(h_X\succeq0\)、locality \(k=O(1)\)、
\(\max_i\sum_{X\ni i}\|h_X\|\le J\)、commuting layer数 \(\Gamma=O(1)\) とする。
qubit符号化でもこの局所性・価格を保つことを条件とし、一般の分子Coulombに自動適用しない。

最初の候補クラスは、1次元近接hoppingとdensity interactionを持つ電子模型。
例えばPSDなbond hopping Laplacian、非負onsite、非負近接密度相互作用という係数記述から検討できる。
この例で有利なfamilyが存在する、または元のE0が未知で非自明なまま有利になるとは、まだ確認していない。
負の項をshiftしてPSDにした場合は \(c\) と低energy cutoffの増加を両方記録する。

入力は各局所係数、sector、layer、\(J\) の合法な上界、時刻 \(t\)、整数 \(r\)、cutoff \(E\)、許容漏れ \(\zeta\in(0,1)\)。
\(P_E=1_{[0,E]}(H_+)|_{\mathcal S}\) は**定理の記述用**であり、実装する射影oracleではない。
固有state、未知gap、Bethe roots、固有phase一覧は入力しない。

### 2. 既知操作を固定した、反証可能な目標

既知の対称2次PFを \(S_2\)、\(U_r(t)=S_2(t/r)^r\) とし、標準的な一段Richardson combination

\[
 X_r(t)=\tfrac43 U_{2r}(t)-\tfrac13 U_r(t)
\]

を対象にする。これは**既知の数式・既知sampling対象**で、新しい挿入則を構成していない。
\(X_r\) はunitaryではない。二つのHadamard信号を符号付き古典処理し、weight和 \(5/3\) の統計価格を払う。
\((X_r)^s\) を物理unitaryとして反復することは許さない。

**目標命題R1-P（未証明・未検証）**：上記クラスに対し、系サイズ・粒子数に依存しない定数 \(C,C_0\) を
locality・固定PFから明示し、

\[
 E'=E+C_0J\log(nr/\zeta),\quad
 r\ge C_0\max\{1,(J+E')|t|\}
\]

のような明示した適用域で、

\[
 \|(X_r(t)-e^{-itH_+})P_E\|
 \le {C\over r^4}\left\{J^4E'|t|^5+J^4(E')^2|t|^6\right\}+\zeta
 \tag{R1-P}
\]

を示せるか。定数・対数・step条件の正確な形は証明または反例で判定する対象であり、成立済みの公式ではない。
単なる \(O(r^{-4})\) の形式展開でなく、有限r、全対象state、一様な剰余・leakage boundまで求める。
二つの誤差の積を無視してcutoffへの線形依存だけを要求しないため、二次項も目標に残す。
この形が不成立なら、その具体的反例と正しい必要依存を結果として保存する。

### 3. 既知法だけでは未確認な点

L08は外挿の全空間commutator保証とsectorの利用を与え、L09は通常PFの低energy保証を与える。
しかし、各通常2次PFの既知低energy誤差を絶対値で足すだけでは、外挿の \(r^{-2}\) 項の相殺を使えない。
一方、全空間外挿の係数に \(\|H\|\to E\) と代入するだけでは、個々のfragmentや中間wordがcutoff外へ出ることを扱わない。
必要なのは、相殺を保つrestrictedな高次係数・積・剰余を、同じenergy cutoffと漏れ会計で抑える補題である。

これはL08のopen questionの具体化であり、「この問題を初めて発見した」とは主張しない。
既存lowenergy／MPFの定理を条件通り組み合わせればR1-Pが直ちに従う場合、独立した数学的貢献の候補から外す。
全既知証明への還元を今回完了したわけではないため、数学的新規性・priorityは未確認。

### 4. E0 taskへ移す際のS1・S5

| gate | 必要な確認 | 今回の判定 |
| --- | --- | --- |
| S1・state | 明示準備 \(A\)、\(p_0\ge\eta\)、\(\operatorname{Tr}[(I-P_E)\rho]\le\tau\) の根拠・取得費 | 未取得。operator定理だけでは運用可能にしない |
| S1・tail | trace信号への移行で一般には \(O(\sqrt\tau)\) の項も残す。CDFの必要信号精度と整合させる | 必要条件の特定のみ。tailをゼロと置いていない |
| S5・sector | 同じ係数・particle sectorで得る \(\lVert H_{\mathcal S}\rVert\) 上界を全対照へ与える | 必須。固定少数粒子ならsector上界だけで系サイズ利得が消える可能性 |
| S5・通常PF | L09の通常4次／高次PF、control・synthesis・preparationも同価格 | 必須。R1の成立だけではこれらより安いとしない |
| S5・外挿 | L08の全空間／sector保証、同じweight・samples・古典費 | 比較可能な数学的対照。finite constant優位は未確認 |
| D2 | \(c\)、全局所項、残余、shift、sector、全confidence | 全て保持。lowenergyのEは未知E0との差を無料入力した値ではない |

最初のinstance条件は、cutoffが全空間上界だけでなく**最良の合法なsector上界よりも十分小さいこと**。
\(E'=\Theta(nJ)\) なら期待する低energy利得はなく、このtask向けの推薦理由が弱くなる。
frustration-freeでE0が既知のzeroであるだけのfamilyは、未知絶対E0を推定する改善例に数えない。

### 5. 最初の紙上検証案――今回は未実施

担当候補はCodex、開始範囲の判断はGPT／ユーザー。

1. 文献の条件照合：L08のMPF error series／sector定理と、L09のrestricted commutator／leakage証明から、R1-Pが既知の系として出ないか確認する。出るなら新課題から外す。
2. 4 modes・2 electronsのnumber sector、非可換な隣接hopping layersとdensity interactionで、同じscalarを保持し、\(r^{-2}\) 相殺と \(r^{-4}\) の必要項を紙上で確認する。係数値・matrix・solverを新しく生成しない契約を別途固定する。
3. 複数の独立小blockを並べるfamilyで、cutoffの二次項・系サイズ因子・中間leakageが目標と矛盾しないか紙上の反例を探す。小例PASSは一様定理の証明ではない。
4. 同じ入力に通常4次PFと最良sector上界を与え、保証から導く価格の比較項を記号で並べる。準備・tail証拠・\(\eta\) の費用を含めても余地が残るか判定する。

これは一つの限定した検証計画の提案で、今回の実行権限ではない。
大量ansatz探索、系サイズ拡張、科学用記号プログラム、数値実験へ移らない。

### 6. 成功・失敗・保留

**数学的成功**は、既知定理の単なる適用ではない有限rの相殺＋低energy剰余補題、またはR1-Pを否定する具体的反例・必要条件を得ること。
**資源上の成功**はさらに、非自明な未知E0のクラス、合法な準備・情報取得、最良sector／通常高次PF対照を含む総費用差を示すこと。
前者だけでは後者を認定しない。

既知定理への直接還元、PSD shiftやpreparation取得費による改善消失、通常PFの同保証・同価格による支配なら、
新アルゴリズム研究の候補としては棄却または保留する。目標上界の不成立は全外挿法の不可能性ではない。

現時点では、**文献に根拠のある保証gapと、最初の反証可能な命題を定義した段階**。
R1-P、資源優位、独立性、新primitiveは未証明。第二候補は保持しない。
