# Q1最小紙上検証：既知法への対応と独立性の限界

2026-10-17 JST。必要箇所の一次文献・固定資料の静的比較であり、新規性の網羅的査読ではない。
独立した新操作、Q1一般の不可能性、資源優位を認定していない。

## 1. 今回得た表現は何に還元されるか

親一対の \(\mathsf d-gJ\) に対するsecular式とCauchy型成分は、既知のdiagonal＋rank-one固有問題そのもの。
一対のRichardson式としても説明できる。親二対は、この特定の三準位でのhole／準位反転とscalarの移動で対応する。
したがって[導出(8)–(13)](parent_form_factor_derivation.md)を新しいBethe basis compilerとは呼ばない。
secular座標を係数から内部で求めることはSOURCEでも禁止されていないが、取得費を消すことは禁止されている。

| 対照 | 確認した入力→操作→出力 | 今回への意味と不足 |
|---|---|---|
| RG eigenvector／Slavnov・Gaudin式 [P01] | 準位・結合とrapiditiesを使うstate、norm、overlap、form factorの式 | 親一対表現は既知。点ごとの式から共通の子Bは従わない |
| Algebraic Bethe Circuits [P02] | Betheパラメータを持つABAをQRでunitary state準備へ変換 | 一状態からの準備と、係数だけから全labelを扱う挿入は別の契約 |
| F-basisによるABCs [P03] | 既知XXZのMPS／補助空間基底から解析的unitary準備を導く | 閉形式unitaryが既にあることを尊重する。RGの本挿入則へ移送した証明は今回ない |
| integrable adiabatic準備 [P04] | stateに対応するchargeとparent条件を使い指定stateを準備 | charge取得・gap条件を無料化して今回のBと置き換えられない |
| collective spin／CG | Tのsingular channelは既知spinの昇降構造でも理解できる | 異なるdを含むenergyと両立するchannelは(17)で不成立。一般CG不存在の主張ではない |

[P01]: https://arxiv.org/html/2012.10477v1
[P02]: https://arxiv.org/html/2202.04673v4
[P03]: https://arxiv.org/html/2411.02519v3
[P04]: https://arxiv.org/html/2503.21741v3

## 2. form factor文献との添字・規約対応

[P01の§II、§III.1–III.2](https://arxiv.org/html/2012.10477v1)では、pair演算子、Richardson式、
rapidities指定のoverlapとnorm、pair creationのform factorを定義する。
同論文のHamiltonianは \(\tfrac12\sum_i\varepsilon_i^{lit}\hat n_i-\tfrac{g_{lit}}2\sum_{ij}S_i^+S_j^-\)。
今回の規約へは \(\varepsilon_i^{lit}=2\epsilon_i=d_i\)、\(g_{lit}=2g\)、\(S_i^+=P_i^\dagger\) と対応させる。
一対Richardson式は \(1/g+\sum_i(\lambda-d_i)^{-1}=0\) となり、導出(9)に一致する。
文献の1/2をそのまま使ってself項を半分にしない。

同粒子数TDMと、今回の \(\langle E_I^{(2)}|\sum_iP_i^\dagger|E_I^{(1)}\rangle\) は異なる作用対象。
文献の式(45),(48)はcreation form factorをoverlapのresidueとして扱う手掛かりを与えるが、
必要なon-shell／off-shell rapidity情報と正規化は依然必要である。
今回はその一般行列式を数値評価・全状態へ展開せず、固定parentの直接的な(13)で足りる範囲だけを確認した。

## 3. 公開実装の静的確認

[Algebraic-Bethe-Circuits](https://github.com/AlejandroSopena/Algebraic-Bethe-Circuits/tree/7f33e688e4ac15cb3a7a1c57a5de4a3a66d0cdee)
release 1.0の固定snapshotについて、既存取得byteをhashで照合し、README、bethe_circuit.py、Pk_gates.pyを静的に再読した。
`aba(roots)`、`_unitary_gates(roots)`、`full_pink(nspins, roots, delta)` がrootを入力し、
Kronecker積とQRで指定stateの準備用作用を作ることを確認した。
XXZの実装をRGの任意入力変換と扱わず、import・実行・backend設定・test・compileをしていない。
元repositoryを変更、commit、pushしていない。取得同一性とorigin/snapshotの別fieldは[source registry](source_registry.json)。

## 4. 元の研究条件と結論の境界

このtaskの出発点はSOURCEの[research_problem.md](../open_problem_research_design_20261017/research_problem.md) (Q1)–(Q7)であり、
今回確認したのはL=4,m=2の(Q5),(Q6)と特定文法の障害である。
過去の二電子collisionのCG/Paldus還元を変更したり、新名称で再提案したりしていない。
J1の `PAUSED_PENDING_NEW_MECHANISM`、他のSOURCE・結果・grant・承認・STOPは保全する。

D1に従いblock-encoding／qubitization中心へ移行しない。
D2としてc、一体項、self-pair項、元Hの絶対energy originを保持する。
R=0は今回指定された厳密模型の条件であり、一般Coulomb Hの残余を零とした主張ではない。
seniority-zeroの最低値を全4電子sectorの絶対E0と同一視しない。
全電子問題にはblocked sector、必要ならR、state準備・overlap・phase window・energy誤差の対応が別途必要で、今回検証していない。

一般Lへのpoly費用やfast-forwarding、全branchの安価なroot生成、Bのunitarity／coherence／clean workは未確立。
Gが失敗したことから別の生成規則を全面排除しない。
また形式的なHermitian対角化の存在や既知の汎用対角化を、Q1の具体的な挿入則と数えない。
必要な文献箇所に限った比較であり、未発見を不存在・新規性の証拠にしない。
