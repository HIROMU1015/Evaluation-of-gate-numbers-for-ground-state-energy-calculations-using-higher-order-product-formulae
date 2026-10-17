# T0：条件付きの強いbaseline

同じ入力・sector・精度・成功率・gate価格に揃った数値資料はないため、普遍的な最強法は認定しない。
以下は競合を落とさないためのbaseline cardsであり、保存値の再順位付けではない。
SOURCE IDの固定commit、path、bytes・hash、実際の読取り範囲は [registry](source_registry.json) を参照。

## 1. 比較の入口

| card | 最も直接の出力／強み | 全taskへの不足 |
| --- | --- | --- |
| B0 | 標準PF＋gap-free CDF。単純で保証の入口が明確 | preparationとoverlapの正当化、PF・controlの価格 |
| B1 | 本repoの既存PFとcheap-first固定校正。保存taskでの実績 | 連続rotation proxyから全E0保証への飛躍は不可 |
| B2 | QPE固有energy誤差／compact BCHによる強い評価 | gap・漸近・state情報の取得条件 |
| B3 | 部分乱択RTEを位相推定へ組み込む既知構成 | overlap、RMS対confidence、誤差定数・native価格 |
| B4-A/B | Track Aは信号回路価格、M1-Sは適用域付き理論 | 元Hの絶対E0・総費用の勝者ではない |
| B5 | SPRINTの化学simulation資源推定 | 実証taskはXAS、E0との直接比較不可 |
| B6 | 外挿PF＋CDFのgate/sample/preprocessing定理 | 低energy外挿保証、準備・overlap取得費 |
| B7 | QET-Uのoverlap改善・認証 | D1外部対照、gap等の情報差・block-encoding価格 |

### B0：標準Strang／既知高次PF＋Lin–Tong CDF

根拠：[L01](https://arxiv.org/pdf/1912.08854v3)、[L02](https://arxiv.org/html/2102.11340v2)。
入力は既知分割の係数、各fragmentの合成、準備 \(\rho\)、ground-space overlap下限 \(\eta\)、安全なenergy window。
CDF方式は小overlapを許しgapを要求しないが、\(\eta\) の保証は必要。
単一ancillaのHadamard testからCDFを古典処理し、最左の有意な立上りを探す。

L02のCorollary 3では、controlled-evolution accessで最大時刻は概ね
\(\widetilde O(\epsilon_E^{-1})\)、総evolution timeは
\(\widetilde O(\epsilon_E^{-1}\eta^{-2})\)。overlapは確率であり振幅と混同しない。
このtimeはgate数ではない。PFを使う場合の追加精度・呼出し費は同論文Appendix Dですでに扱われる。
Appendix Eのcontrol削減も、容易に準備できる既知energyの参照状態等の条件付きである。
元Hのvacuum energyにscalarがあればそれも保持する。

強みは一般的な安全対照を既知の操作だけで書けること。古典CDF生成・postprocessing、shotごとの準備、
PF誤差・synthesisを加算して初めてtask全体になる。高confidenceでない裸のQPE出力を反復して最小値だけ採る方法は、
小overlap時の偽低energy tailを処理せず、この保証の代用にならない。

### B1：本repoの現行PF・第一／第二研究

根拠：E09–E13。実装にはStrang、Yoshida 4次、current m3系、Moralesの公開高次・processed系がある。
実装の存在を、その全候補の科学的採択や優位としない。processorは両端一回の実装を静的に確認した。
費用は主に \(\beta n_{\exp}/[t(\epsilon_E-e(t))]\) 型の連続rotation proxyで、条件は費用分解に示す。

第一研究の固定開発条件ではcurrent m3とYoshida4を比較し、固定gammaの安全性は保存範囲の経験的結果。
最終状態は `complete_mechanism_study_no_method_benefit` であり、新手法の総資源優位へ読み替えない。
第二研究のDirection Cはcheap-first固定gammaをbaseline、spectral方式を条件付き比較とし、承認済みclosureを保持する。
保存結果のbudget advantage不成立を、全分子・全stateに対する不可能性へ拡張しない。

入力誤差曲線・state・branch・truthの取得費が重要。保存exact stateやgapを運用入力に移すとS1違反になる。
理論的な有限step認証・離散回路・準備費を含む全E0保証は、この保存proxyだけでは成立しない。
今回はgamma、時刻、rank、PFを再選定していない。

### B2：QPE-aware PFと実用BCH評価

根拠：[L03](https://arxiv.org/html/2412.16811v1)、[L05](https://arxiv.org/html/2606.30738v1)。
L03は固有energyの摂動展開を一般次数PFに与え、energy目的に合う既知PFを構成する。
対象固有値の隔離はstep 0から対象stepまで必要で、branch対応・overlap変化も払う。
全入力のunitary誤差とenergy shiftを同一視しない。

L05は漸近的なBCH対角成分による評価と、BCH生成・samplingの古典費用削減を与える。
係数生成がcompactでも、対角期待値を得るstateや古典近似の品質は別問題。
漸近statementと掲載数値は、有限stepの全sector上界や未知ground-state期待値の無料取得を意味しない。
このため「PF誤差を全norm以外で評価すること」「BCHをcompactに書くこと」は新gapとして残さない。

### B3：部分乱択RTEによる位相推定

根拠：[L04](https://arxiv.org/pdf/2503.05647v2)、Theorems IV.1／V.1、Appendix B。
\(H=\sum_{l=1}^{L_D}H_l+H_R\)、tail Pauli weight \(\lambda_R\)、p次deterministic分割を用いる。
主な費用は、掲載定理の記法で

\[
 O(L_D C_{gs}^{1/p}\epsilon_E^{-1-1/p})\quad\text{fragment evolutions},
 \qquad O(\lambda_R^2\epsilon_E^{-2})\quad\text{tail rotations}.
\]

\(C_{gs}\) は分割依存。数値推定ではfully deterministicの経験係数を流用するheuristicと、rigorousな上界を区別している。
各fragment evolutionをnative gate単価で払う。normalizerによる信号減衰とshotsも含む既知構成であり、
乱択simulationからenergy推定への接続自体を新規課題とはしない。

RPEの掲載結果は大きいoverlap下限 \(\eta>4-2\sqrt3\) 等を仮定し、RMS精度を扱う。
小overlapのB0やhigh-confidence taskとの比較には、その条件と変換費を揃える。
最適partitionは費用尺度と \(C_{gs}\) に依存するため、largest-weight ruleを普遍的最適法としない。

### B4-A：PR Track Aのnative wrapper費用

根拠：PRA。固定DF Hamiltonianで \(z(T)=\langle\psi|e^{-iH_{DF}T}|\psi\rangle\) を推定する保存task。
compiled Hadamard wrapperの一shot価格と、bias/headroom/normalizerを入れた十分shotsを組み合わせる。
主要proxyは \(G_{RZ}=\sum_aN_a\bar C_{RZ,a}\)、P=0が既定の比較。CX・depthは別指標。

H4固定範囲ではB0+IとB2の両方にpoint winnerがあり、保存報告は普遍的winnerを示していない。
H6のfresh confirmationは探索データとpoolしない。H4/H6/H8はidentity・scopeが異なり、今回scaling fitを作らない。
希少eventの経験的費用推定は全eventを覆うrigorous upper boundと区別される。

準備費・DFモデル誤差・絶対E0・ground overlap認証はこのP=0有限信号taskの外。
compiled RZ節約だけをT/Toffoli節約や全E0優位としない。

### B4-B：Track B／M1-Sの理論と価格の境界

根拠：PRB、PRM、PRS、PRG、PRC。
Track Bの新アルゴリズム探索・実験主線は正式休止。M1-Sの保存成果は別の限定理論・検証記録として保持する。
正負branchで同位置labelを共有するjoint law、有限モデル・共鳴／gap条件・時刻スケーリングを固定した保証がある。
部分乱択の理論ではexact deterministic内部発展、全Hの孤立対象state等の条件が残り、
その内部PF実装、一般DF event、実用係数取得、多round RPEの総費用までは保証しない。

保存H4診断は数値sector-ground oracle等を使う条件付き証拠。visibility増加とphase bias改善は別で、
shot削減、native単価、準備、全round成功までの接続は未確立。
M1-Sの概念label数や方向制御回路を、L04のTaylor event・normalizer付きRTEと同一視しない。
SOS-PF現系列CLOSEDと、A2有限step保証 `NOT_ADOPTED` は区別する。
未確立の接続をT0の新規課題として再採択しない。

### B5：SPRINT／GRADE

根拠：[L06](https://arxiv.org/html/2606.30741v1)、特に§IV–VとAppendix B。
化学factorization、near-integrable PF、processing、randomization、QROMを組み合わせた強い既知構成。
公表XAS例では以前の同taskよりToffoli費用が約4.5倍減る一方、qubitizationより約2.5倍多いToffoli、約5.5倍少ないlogical qubitsという推定である。
E0推定全体のwinnerという値ではない。

factorization・残余・leakage、state準備、Trotter誤差評価、rotation synthesisとQROMを払う。
GRADEの低いper-step価格だけでは不十分で、Trotter／leakage誤差が競争力を損なう例も報告される。
未知stateの期待値や最適factorizationを無料にせず、同じ精度・Hamiltonianで比較する必要がある。

### B6：commutator-scaling外挿PF＋CDFと、通常PFの低energy保証

根拠：[L08](https://arxiv.org/html/2608.13862v1)、Theorem 48。
既知even-order PFをclassical signed samplingで外挿しCDFへ組み込む。
記法 \(\Gamma\) はfragment数、\(\Upsilon\) はPF stage係数、\(a_{\max}\) は最大係数、
\(\lambda_{comm}\) は同論文定義の高次commutator量。
最大gate depthの上界は概ね
\(\widetilde O[\Gamma\Upsilon(a_{\max}\Upsilon\lambda_{comm}/\epsilon_E)^{1+1/p}
\log^{2+1/p}(1/\eta)]\)、samplesは
\(\widetilde O[\eta^{-2}\log^2(\widehat K/\epsilon_E)\log(1/\alpha)]\)、
preprocessingは \(\widetilde O[(\widehat K/\epsilon_E)\log^2(1/\eta)]\)。
これはgap-freeな条件付きE0構成で、本文のprimitive access・norm上界・overlapを要する。
raw RZやFT単価と同じ尺度ではない。準備・\(\eta\) の取得も外から加算する。

もう一つの強い対照は [L09](https://arxiv.org/pdf/2504.20746v1) の通常PF低energy定理。
positive local terms、local extensiveness、低energy supportの条件下で、誤差は全energy scaleより低いcutoffに依存し得る。
この通常PFの成果は解決済み。termごとのpositive shiftは可能でもcutoffをextensiveに増やし得るため、
任意の分子で利得が出るとはしない。R1では、この通常4次PFも同じ情報を与える強い対照に含める。

### B7：QET-U推定・認証――D1の外部対照

根拠：[L07](https://arxiv.org/pdf/2304.09827v2)、Theorems 2.3／5.1、§6。
既知gap下限 \(\Delta\) とoverlap \(\eta\) を使う推定は、概ね
\(\widetilde O(\eta^{-1}\Delta^2\epsilon_E^{-2})\) circuits、最大evolution timeは概ね \(\widetilde O(\Delta^{-1})\)。
認証はgap下限なしでincorrect acceptanceを抑えるが、correct estimateでも浅すぎれば棄却し得る。
Theorem 5.1の \(\widetilde O(\eta^{-3}\epsilon_E^{-4}\log(1/\alpha))\) はGaussian関数のblock-encoding呼出しの期待数で、PF gate総数ではない。
初期energy bracket等のpromiseも必要。

overlap依存改善はすでに既知。認証費用・depth/runtimeの下界には同論文の明示した未解決方向がある。
しかし、既知構成の中心はQET-Uでの関数block-encodingである。
それを採用せず同じ改善を得る新規則は今回作っておらず、D1の中心候補に移さない。

## 2. 「最強」の限定回答

小overlap・gap未認証の測定型E0にはB0を安全な単純対照とし、B6の強い既知保証も必ず比較する。
大overlap・long-tail分割ではB3が有力で、B1の保存proxyやB4-Aの固定信号価格では各既存baselineを保持する。
低energy supportを利用するならB6の通常PF対照を先に含める。

B5のXAS、B4の有限信号、B1の連続rotation、B7のoracle／block-encoding費用を横断した順位はない。
同一の実instanceと全費用が未取得なので、「全E0でこの一法が最安」という結論は本調査では未確立である。
