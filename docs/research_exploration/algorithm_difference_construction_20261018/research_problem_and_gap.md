# 差分仮説：占有条件付き測定はenergy取得費を変えるか

2026-10-18 JST。ユーザーの今回の指示とGPT戦略レビュー原本（[読取identity](source_registry.json)、原本非公開）に基づく限定紙上構成研究。**一つの仮説について、生成・識別例・強対照の照合まで実施した。結果は既知手順への還元であり、独立候補の成立・正式採択を認定しない。** 新規科学数値計算・保存科学値再解析・symbolic checker・solver・回路build/compileは行っていない。

## 1. どの差を仮説としたか

絶対E0推定の一部分として、再準備できるstate ρの元Hamiltonian期待値を取得するtaskを考える。互いに非可換なhoppingとdensity項を別poolで測ると、各項に分散が残る。**同じcopy内の占有情報から測定軸を変えれば、係数の干渉を一標本に残し、固定基底で別々に測る場合の分散を減らせるのではないか**、という仮説を置いた。

仮説の核心Rは「結果の後処理だけを変える」ことではなく、spectator occupationを測り、その値からactive軌道の回転角を係数で生成してから測る操作である。狙う差は量子測定law・準備copy数・測定操作費。古典共分散縮約を速くしたことによるshot削減を仮定しない。

この疑問から[familyと識別例](discriminating_examples.md)、[有限操作の生成](generation_rule_construction.md)を構成した。固定一軸に対する差と分散差は紙上で得られたが、**その核心は公表済みの条件付き軌道回転測定に具体的に一致する**。[三種の対照](claim_and_baseline_comparison.md)を区別した上で還元する。framework包含やB_plus_core一致だけを棄却理由にしていない。

## 2. Hamiltonian・sector・scalar

一般入力は元の有限基底電子Hで、係数は有限bit、CARとHermiticityを固定する。本packetでは二体係数を重複のないpair順規約

\[
H=cI+\sum_{pq}h_{pq}a_p^\dagger a_q+
\sum_{p<q,\ r<s}V_{pq;rs}a_p^\dagger a_q^\dagger a_s a_r,
\quad h=h^\dagger,\quad V=V^\dagger
\tag{P1}
\]

へ集める。1/2、1/4等を暗黙に追加しない。元の全添字vからの符号付き集計は入力処理費である。

具体的に構成するfamilyは、同じspin種の四mode、順序1<2<3<4、全粒子数N=2に限定する。X_pq=a_p†a_q+a_q†a_p、Z=n1−n2、S=n3−n4として

\[
\begin{split}
H&=cI+F+R,\\
F&=\nu S+dZ+tX_{12}+uSZ,\\
R&=\eta(X_{23}+X_{34}).
\end{split}\tag{P2}
\]

c,ν,d,t,u,ηは実の有限bit係数、構造的な識別ではtuη≠0とする。hopping graphは1–2–3–4と連結で、Rは一般にFと非可換。Fのn3,n4対称性を**全Hの対称性へ移さない**。

P1ではh11=d、h22=−d、h33=ν、h44=−ν、h12=h21=t、h23=h32=h34=h43=η。二体対角要素はV13;13=u、V14;14=−u、V23;23=−u、V24;24=u、他は0である。これで一体・相互作用・scalarを落とさずP2へ戻る。これは電子CARを満たす制限familyで、一般分子のCoulomb積分が必ずこの構造を持つ／全係数が実分子として実現できる、とは主張しない。

## 3. accessとE0への未完接続

ρはN=2 sectorの任意のstateで、Aによる独立再準備費C_Aを持つ。全振幅表・ground・gap・固有projector・最適varianceを無料入力にしない。occupation読出しと、隣接1,2のnumber-conserving Givens回転、測定結果の古典feedforwardを許す。同じ装置accessをB_fairへ与える。A†、controlled-A、time-evolution oracleは要求しない。D1に従いblock-encoding/QSVT/qubitizationを用いない。

今回得るのはE_ρ=Tr(ρH)の測定仕様である。E_ρ≥E0(H)であっても、E_ρ−E0の有用な上界は未構成。ε_measだけを小さくして絶対E0精度εを達成したとはしない。D2の元H・sector・scalarを保持し、\(\widehat E=c+\widehat F+\widehat R\)とする。state品質・準備費、Rの測定、系統誤差が別途残る。

## 4. 既存研究との境界

固定SOURCE E01–E08/P01–P04は[source registry](source_registry.json)に記録する。20方向のうちPRM11（測定）・PRM19（basis）と課題上の接点があるが、PF分割係数探索・exact encoding・旧G dictionary更新・旧共分散kernel縮約の再発注ではない。今回はseedから変分部分空間を増やさず、既存shadow標本の後処理だけで新shot改善を作らず、Fの測定basisを明記して比較する。

現G CLOSED／NOT RETAINED、集団遷移生成PAUSED、J1/Q1 PAUSE、R1-P不保持、A2 NOT_ADOPTEDと現経路追加投資見送り、PR共分散縮約REDUCES_TO_KNOWN_METHOD、第一・第二研究・PR Track A/Bその他の状態・契約・STOPは変更しない。本探索の還元判定も、新しい正式CLOSED判断ではない。

今回はこの一件を識別可能なところまで閉じる。還元後に係数・順序・別heuristicを変更して独立性を救済する探索は続けない。
