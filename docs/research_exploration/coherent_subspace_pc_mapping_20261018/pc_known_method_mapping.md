# Gの生成・更新規則と既知手順の具体的な対応

2026-10-18 JST。固定Gを[scope](scope_and_protocol.md)の条件で照合する。結論は**既知手順の組合せによる再現が可能**。無変更のVQNHE実装やSSE原論文の全procedureがGと同一、という主張ではない。測定まで含む対応は[情報・費用比較](pc_information_and_cost_comparison.md)に示す。

## 1. 係数dictionaryの生成

term支持をhyperedgeと見ると、w_pqは各hyperedgeがp,qへ与えるabs(b_μ)を集計した重み付きclique projectionである。これを重み降順に並べて成分をunionするのはKruskalの最大重みforest構成そのもの。edgeの重みを順序反転したd_pqへ写せば通常の最小木の手順になる。欠けたedgeは同じ規約で欠けたままにする。

重みの閾値λまでedgeを処理したとき、得られる成分は元graphのw≥λのedgeによる連結成分に一致する。理由は、異なる成分を結ぶ処理済みedgeをKruskalはunionし、同成分内で棄却したedgeは連結性を変えないからである。同率内のbinary refinementはGの固定edge順になる。従ってunion直後のcluster列は、similarity版single linkageのhierarchyとその固定binary refinementである。MSTとsingle linkageの関係は[Gower–Rossの一次publisher summary](https://academic.oup.com/jrsssc/article/18/1/54/6882518)にも明示されるが、この段落の対応は上の手順から紙上で確認した。PDF全文の定理を輸入したのではない。

残りは、singleton／term支持との集合union、構文重複除去、各集合について整数feature N_C(x)=Σ_{p∈C}x_pの全thresholdを作る処理である。未知stateを使わない標準的な特徴生成で、operator-poolへそのまま出力できる。clusterの選び方を学習したり、groundとの関係を証明したりする別の生成操作はGにない。

| 生成・選択の部位 | 対照での具体化 | 同じ条件で残る差 |
| --- | --- | --- |
| 係数→w | 同じcanonical listから同じ支持別加算を行う | なし。入力長・bit算術費も同じ |
| forest→C | 同じedge順のKruskal／single-linkage hierarchyを作り、同じ中間clusterを保存 | なし。これは最終treeだけの比較ではなく全union列の一致 |
| C→D | 同じoccupation-count featureと全thresholdを生成 | なし。quantum operator名を付けることは新しい計算操作でない |
| Dを予め渡す場合 | D構造と係数の両方を同じに渡す | G固有の取得は残らない。生成費を比較から落とすなら双方同様。end-to-endなら双方へ生成費を戻す |

同じDが掲載された量子化学論文を特定した、というpriority認定はしていない。**新しい生成上の保証や操作が、この具体化された既知graph処理以外に残るか**という今回の問いへの答えが「残らない」である。特定のDが実用的に有用かはP-dであり、今回調べない。

## 2. cell splitをVQNHE／QSEの関数更新へ写す

各leaf indicatorをd_a(x)=1[f(x)=a]とし、

\[
F_{f,z}(x)=\sum_a z_a d_a(x),\qquad
|\phi_{f,z}\rangle=F_{f,z}|\psi\rangle.
\tag{K1}
\]

と置く。VQNHEの一般diagonal関数の表現[本文式(1)–(2)、complex supplement](https://arxiv.org/html/2106.05105v1)へこの有限関数classを与え、seedの量子parameterは固定する。自由変数zに関する最小化は

\[
\min_{z\ne0}\left(c+\frac{z^\dagger J^f z}{z^\dagger S^f z}\right)
=c+\lambda_{\min}(J^f,S^f).
\tag{K2}
\]

従ってgenericなneural optimizerを走らせず、既知QSEの線形係数solveを使えばGと同じenergyと係数spaceになる。これはVQNHE原論文の特定RBM訓練をそのまま実行することとは異なる。zeroや複素値を持つK1に、正のoutput rangeを仮定するVQNHEの効率定理は適用していない。

leaf aをqで二分する更新は

\[
d_a\longmapsto d_{a0}=d_a(1-q),\quad d_{a1}=d_aq,
\quad d_a=d_{a0}+d_{a1}.
\tag{K3}
\]

というpredicate treeの特徴置換である。QSEならoperator O_aをΠ_aとした同じ置換になる。旧親は子の和として残り、他leafは変えない。全Dの全leaf splitを同じ順に生成すれば、候補operator／部分空間の集合はGと一致する。Gram対角性も同じ。

## 3. confidence・gain・費用をどう再現するか

Gのconfidenceは固定された有限Fについてのbounded-sample concentrationとunion bound、そのmatrix norm評価、quotient perturbation評価である。P-aの幅を既知法にもそのまま与えるという今回の比較では、同じmatrix記録から同じphat_minとu_fを計算できる。新しい情報取得や固有projectorを必要としない。

interval I_f=[Ehat_f−u_f,Ehat_f+u_f]を作ると

\[
g_L=\inf I_f-\sup I_{f'}
\tag{K4}
\]

であり、二つの同時confidence intervalの端点差そのもの。g_L>0で受理する規則も同じ比較で再現できる。相関のあるmatrix entriesを独立と仮定する必要はなく、有限Fの同時eventを使う。原Gの式以上に鋭い統計保証を新しく開発していない。

C_addも、前回の具体式へ同じrecordと候補treeを代入するだけである。

\[
\begin{split}
C(f,f')={}&\sum_{r\in R_H}[W_{f'}(x_r)+W_{f'}(x_r\oplus d_{l_r})]
+\sum_{x\in R_S}W_{f'}(x)\\
&+a_s(K+1)^3+a_a(m_H+m_S+(K+1)^2)
+a_m((K+1)^2-K^2).
\end{split}
\tag{K5}
\]

ここでW_f(x)=Σ_{q∈path_f(x)}(2サイズ(C(q))+1)。K5は原GがC_addと呼ぶ費用proxyであり、旧treeからの厳密な限界実費を新しく証明したものではない。rewardをg_L、costを正のK5としたratio greedy selectionへ代入すると、Gのargmaxになる。benefit/cost比を使うgreedy primitive自体は[Golovin–Krause §4.1](https://arxiv.org/html/1003.3967v5)等に明示される。ただしGのg_Lは同論文のconditional expected marginal benefitではなく、costもstate依存のproxyである。submodularityや近似率定理をGへ移していない。ここで対応付けたのは**選択の計算操作**である。

## 4. 全更新列の同値性

以下は既知部品を接続する**仕様上のadapter**で、実装・実行はしていない。入力に新しい候補や情報を足さない。

```text
Give both procedures the same I and the same acquired records.
Generate the same D by coefficient aggregation / ordered Kruskal / thresholds.
Represent each leaf by its indicator operator or piecewise diagonal feature.
For each existing leaf and each q in D:
    Substitute the two child indicators from K3.
    Aggregate the same Jhat and population Gram from shared records.
    Apply the same finite-class confidence and validity checks.
    Solve the same QSE linear-coefficient problem K2.
    Compute interval gap K4 and the explicit classical-cost proxy K5.
Choose argmax of interval gap / cost; use the same structural tie-break.
Apply the same no-candidate / uncertainty / K_max termination.
```

帰納法で確認できる。初期treeは同じ。step tでtreeが同じなら候補list、各matrix、幅、cost、scoreが同じなので、固定tieで選ぶ次treeとSTOPも同じである。従って**全ての合法な同一recordについて、全更新列と終了理由まで一致**する。新たな量子query、shot、state準備、ground情報は0追加である。

これは「任意のalgorithmをbaselineへ丸ごとコピーすればよい」という比較ではない。追加した各操作を、Kruskalとcount-threshold生成、既知diagonal/QSE solve、bounded finite-class confidence、interval差、加算型operation count、ratio greedyへ分解した。Gの中にそれら以外の生成・取得・保証mechanismを特定できなかった、という範囲の還元である。これらを組み合わせた全く同じ擬似コードの先行掲載を証明したものではない。

## 5. SSEとadaptive measurement QSEは何が違うか

| 対象 | 原論文のprocedure | Gとの正確な関係 |
| --- | --- | --- |
| SSE [§III.1–3](https://arxiv.org/html/2406.11533v1) | local Pauli poolの{I,G_i}による2次元filter、上位poolのsolve、Gram固有値のtruncation | literalな選択結果はGと同じとは限らない。Gは現tree全体の一leaf splitを評価し、interval/costを用い、弱いpopulationを棄却する。原SSEのPauli反交換を使う安いfilter式は一般のΠ_aにそのまま適用不可 |
| 同じD・recordを許すQSE＋既知greedy wrapper | K1–K5をoperator class／confidence／scoreとして用いる | 上の帰納法によりGを再現。SSE原実装を無変更で再現したとはしない |
| adaptive measurement QSE [§II](https://arxiv.org/html/2311.07893v2) | Ritz係数からdressed observableを作り、次の測定basis配分を変更 | 測定配分更新とGの固定recordによるtree更新は異なる。ただし同じoperator class・固定record・wrapperを使えば上の同値性を妨げない |
| selected CI [HCI方法](https://arxiv.org/html/1606.07453v1) | 配置接続とCI係数によるselection | literalにGではない。Gのcoherent cellはdeterminant listではない。selected CIだけへ無理に完全還元したことにしない |

これら原法とのliteralな差は保持する。一方、今回許された強対照へ同じD・record・confidence・費用を与えたときには、Gだけに残る操作差の証拠にはならない。
