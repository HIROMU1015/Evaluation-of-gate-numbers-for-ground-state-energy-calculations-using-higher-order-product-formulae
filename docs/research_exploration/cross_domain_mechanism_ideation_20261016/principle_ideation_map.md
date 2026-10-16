# 分野横断の原理発想：未検証の構成仮説

承認日：2026-10-16 JST。対象は量子化学のHamiltonian simulationと、元の有限基底電子Hamiltonianの絶対基底エネルギー。**発想8件を記録し、照合後はBを1件保持する。Aは0件、Cは4件、Dは3件。いずれも発明・正式研究候補・科学的GOではない。**

今回の正式変更は「既存法の組合せから選ぶ探索」から「新しい構成規則を仮説として作る探索」への移行である。資源不足を理由とする探索終了、論文化可能性による選別、保証未証明だけによる棄却は行わない。以下のPhase Aと、[既知法照合](prior_art_and_novelty_boundaries.md)、[分類・判断handoff](research_hypothesis_handoff.md)を分離する。

## Phase Aの固定と前提

最初に指定されたEvaluationの3資料とPRの3資料を固定commitから読んだ。その後、追加文献検索の前にP1〜P8の機構・問い・未解決核心をローカル記録へ固定した。そのSHA-256はprovenanceのphase_a_recordにある。本書はその8件を入力・出力まで展開したもの。後から生じた狭い残余仮説P1*と照合結果は明示して追記する。発想が既存知識から完全に独立して生じた、という主張ではない。

固定資料は重複確認用であり、O1〜O5、X1/X2を発想の全空間とはしない。前回の「独立候補0件」は当時の限定結論として保存する。[E1] [E2] [E3] [R1] [R2] [R3]

共通の入力は、係数・定数項・粒子数／spin等の対象sector、要求される精度・成功確率の概念仕様である。E0、exact vector、RDM、数値gap、正しいphase branchは無料入力にしない。copies、coherent preparationとinverseも区別する。今回は具体的な分子、時刻、rank、PF、角度、shots、閾値、実行予算を新設していない。

| 発想元 | 化学へ移す構成上の問い | 仮説 |
| --- | --- | --- |
| 量子制御・幾何学的位相・補助振動子 | 非可換な電子密度に対する演算子値の閉路を、CARの関係で閉じられるか | P1 |
| 疎行列・局所グラフ分解・フェルミオン励起 | 軌道の重なりを許し、配置ごとに小さな励起閉路をcoherentに束ねられるか | P2 |
| 幾何学的積分・等スペクトル変形 | 近似誤差を固有位相を動かさない方向へ送れるか | P3 |
| 統計力学・経路積分的な状態量の復元 | 基準からenergy微分を積分することが別の取得原理になるか | P4 |
| 行列関数・受動散乱・有理近似 | Cayley変換のresolventを許可された操作で作れるか | P5 |
| 統計推定・制御変量・定常性 | 固有状態の零期待値関係を、測定生成規則へ変えられるか | P6 |
| 誤り訂正・Hamiltonian engineering | 有限step誤差だけをsyndromeへ出し、目的位相をlogicalに残せるか | P7 |
| 自律制御・周波数同期 | 絶対energyを読むclockに、既存と異なる情報転送操作を定義できるか | P8 |

## P1：非可換な電子密度を使う共通振動子の閉路

1. **問題**：異なる軌道frameの密度平方を別々に指数化する代わりに、電子相互作用を共通の補助系との閉路から生成できるか。
2. **異なる発想**：各平方の実装後に補助系を閉じる単位を、複数の非可換な密度にまたがる演算子値の閉路へ変える。電子の反交換関係（CAR）で同じ作用になる項をまとめ、必要な二体作用と不要なbus結合を選別する。
3. **入力→処理→出力**：元Hの一体・二体係数から、Hermitian一体密度の平方表示と既知の一体／scalar補正を指定する。密度と振動子quadratureの線形結合、符号反転、位相回転を組み合わせる設計条件を作る。もし満たせれば、元相互作用に対応する電子発展と、振動子が所定状態へ戻る制御仕様を出力する。満たせなければ、その制御族内の未達条件を出力する。
4. **未確認仮定**：非可換な密度を同じbusへ結合する物理操作、必要な符号・quadrature制御、CARに基づく共同閉路の存在、有限時間でのcoherentな帰還とphase追跡。一般化学での効率性は仮定しない。
5. **成立時の変化**：相互作用の生成単位が「既存の各密度平方ゲート」から変わる可能性がある。回路・制御設計の新しいクラスや、適用可能な電子代数の条件が分かり得る。総資源改善は別問題である。
6. **失敗可能性**：一次の平均変位が0でも非可換性によるsqueezingや残留entanglementが残る。既知の単独閉路／decouplingへ還元される、又は必要な電子―bus結合の生成費用が大きい可能性がある。

**照合後**：単独密度の閉路、単なるDF＋幾何学ゲート、非可換force一般は既知。これらを新規とはしない。CARの商関係を使う共同閉路の構成問題だけをP1*としてBに残す。詳細は後述。

## P2：配置依存の励起閉路による可解cell

1. **問題**：軌道supportが重なる励起を、Pauli項又は単一の励起edgeごとに切ることが本質的か。
2. **異なる発想**：決定基底の頂点を電子配置、辺をsingle／double励起とし、配置に応じて小さな閉路cellを選ぶ。固定軌道clusterと異なる分割を狙う。
3. **入力→処理→出力**：係数と占有bit列から短い励起閉路を列挙し、全頂点で同じcanonical labelとなる閉路だけを候補にする。共有頂点を持つ候補はlabelの全順序で競合を解消する。選ばれたcellのHermitian作用と、残る全edge・対角項のresidualを合わせた分解仕様を出す。edgeを捨てない。
4. **未確認仮定**：cell所属判定の可逆性、局所情報からの一致、残余の完全被覆、指数的な配置表なしでの小cell発展。小さな行列を知ることと安い量子操作を区別する。
5. **成立時の変化**：複数の励起をexactに扱う単位や、その構成費用の理解が変わり得る。
6. **失敗可能性**：競合解消・Slater符号・可逆label計算が支配する。cellがedgeへ退化する。既知の疎行列分解と局所最適化の範囲に留まる。

**照合後：C。** CI行列のone-sparse分解、局所oracleからのgraph分解、多edgeの可解成分は既知。[L06] [L07] 短いcycleを選ぶ最適化目標は説明できるが、既報を越えるCAR固有のlabel生成・対角化規則を今回提示できない。完全なcycle版同値定理を証明したのではない。未証明だからCなのではなく、具体化した生成の骨格が既知で、独立する追加規則がないためである。

## P3：誤差を等スペクトル方向へ送る積分

1. **問題**：状態全体の近似と、energyを読む固有位相の誤差は同じ目的でなくてもよいか。
2. **異なる発想**：有限stepのdefectを共役変形やHとの交換子方向へ移し、固有位相を保つ方向を設計に用いる。
3. **入力→処理→出力**：既知の分割と形式的defectを受け、processor／kernel補正とフェルミオン恒等式を使って設計条件を作り、積分仕様と残余を出す。
4. **未確認仮定**：補正の指数化費用、有限stepでの対象branch、情報取得。共役だけで固有値が改善すると仮定しない。
5. **成立時の変化**：元Hのenergy biasが減る可能性がある。
6. **失敗可能性**：既知corrected／processed PF又は固有状態commutator条件へ帰着し、独立生成規則が残らない。

**照合後：C。** 既存H1監査がこの中核と既報の対応を既に記録している。[R4] processorとkernelの違いも既知。H1・H-E1・SOS-PFを新しい名称で再開しない。

## P4：基準energyからの微分積分

1. **問題**：長時間のcoherent位相取得を、基準からの状態量復元へ変えられるか。
2. **異なる発想**：既知基準のH(0)からH(1)=元Hへ至る経路で、基底energyの微分を積分する。
3. **入力→処理→出力**：基準energy、Hamiltonian経路、各点の対応状態へのaccessを受け、導関数期待値を取得して積分し、offsetを含むE0を出すという概念手順。
4. **未確認仮定**：経路上の同じ基底branch、交差・縮退の扱い、状態準備、積分・測定誤差。基準energyも無料追加しない。
5. **成立時の変化**：coherent時間と測定・状態準備の配分が変わり得る。
6. **失敗可能性**：既知のHellmann–Feynman関係と経路積分の組合せに留まり、経路途中の状態取得が難しい。

**照合後：C。** 微分を使う核は既知。[L11] 新しい経路・状態取得・積分規則を今回定義していない。文献は関係の出典であり、今回の全energy算法の費用保証ではない。

## P5：補助散乱による有理propagator

1. **問題**：多くの指数を掛けず、Cayley／Padé型のunitary近似を直接作れるか。
2. **異なる発想**：位相を保持する散乱のtransfer functionを行列関数の有理近似へ対応させる。
3. **入力→処理→出力**：H係数からrational近似の仕様を作るまでは言えるが、必要なresolventを許可されたprimitiveから供給する操作が未定義。出力回路まで到達していない。
4. **未確認仮定**：安いresolvent、成功確率・normalization・control位相の保持。
5. **成立時の変化**：直接的な非PF生成原理になり得る。
6. **失敗可能性**：既知block embedding／walk中心の実現が必要となりD1に抵触する、又は全Hの発展を入力に仮定して循環する。

**照合後：D。** 近似関数を名付けることと、許可された生成操作は別。保証がないためではなく、resolventを得る中核操作が定まらない。既存D1外技法への移行を承認しない。

## P6：定常性からのenergy測定制御変量

1. **問題**：exact eigenstateでH全体の分散が0という構造を、実際の測定費用へ移せるか。
2. **異なる発想**：固有状態で零期待値となるi[H,A]をenergy observableに加え、推定値を保って測定分解を変える。
3. **入力→処理→出力**：Hと明示的な低体数Aの候補、target copiesを受け、既知の零期待値制約を追加したobservableと、その分解・重みを出す。共分散を使うなら取得費を戻す。
4. **未確認仮定**：状態の定常性、Aを選ぶ規則、追加項の測定費用、近似stateでのbias管理。
5. **成立時の変化**：同じ絶対energy期待値の取得分散が変わり得る。
6. **失敗可能性**：既存の零期待値制約によるobservable再表現と配分最適化に留まる。追加高体項や状態検証が高価になる。

**照合後：C。** 零期待値制約を足して測定を変える枠組みは既報。[L08] 固有状態commutatorの全基底が同論文のmarginal制約と一致する、とまでは主張しない。今回は独立したA選択・測定生成規則がなく、この枠組みを越えない。

## P7：有限step誤差だけをsyndromeへ送るlift

1. **問題**：アルゴリズム近似誤差を、目的のlogical発展を保つ可訂正誤差へ変換できるか。
2. **異なる発想**：各電子generatorを補助codeへliftし、誤差成分だけを検出可能なsyndromeにする。
3. **入力→処理→出力**：元のterm列とcodeを受け、liftとdeterministic recoveryを設計したい。しかし具体的lift・recovery・正常branchのphase規則がなく、出力操作は未定義。
4. **未確認仮定**：回復後に電子stateと環境の相関が残らないこと、同じ絶対位相、block embeddingを中核にしない実現。
5. **成立時の変化**：有限step近似と誤り訂正の境界に新しい構成問題が生じ得る。
6. **失敗可能性**：codeを保つgeneratorのlogical交換子もlogicalに残る既知の障害を回避できない。射影によるH実装へ置き換えるとD1の問題になる。

**照合後：D。** 具体的liftがないことが理由である。高リスクや未証明そのものをDの理由にしない。新しい不能性証明は作っていない。

## P8：自律的なenergy clock

1. **問題**：元Hの絶対energyを、長いcontrolled evolutionと異なるclock読出しで取得できるか。
2. **異なる発想**：補助clockの同期周波数に電子energyを移す。
3. **入力→処理→出力**：Hとclockを指定するだけでは、結合・基準・符号取得が定まらない。入力から読出しへの具体的な規則は未定義。
4. **未確認仮定**：原点を保つ基準、追加oracleなしの結合生成、signed energyと周波数の識別。
5. **成立時の変化**：energy情報の取得形式が変わり得る。
6. **失敗可能性**：既知の位相参照／spectroscopyを言い換えるか、元energyを供給するoracleを仮定する。

**照合後：D。** 自律性という名称から独立操作を認定しない。停止中H4の再開にはしない。

## P1*：照合後に保持する狭い構成仮説

**科学的な問い**：複数の非可換な一体電子密度と共通busの線形結合から、CARで同値な項を利用する位相cycleを構成し、必要な二体作用を残しつつbus依存作用を同時に除去できるか。単独密度の閉路を並べる既知構成とは異なる規則が残るか。

ここで扱う仕様を

\[
H_{\rm orig}=cI+T+\sum_{\ell=1}^{r}\lambda_\ell L_\ell^2+R,\qquad
L_\ell=\sum_{pq}(\ell_\ell)_{pq}a_p^\dagger a_q=L_\ell^\dagger
\]

と書く。これは既知の密度平方表示を入力契約として使う記号であり、新しい分解定理ではない。[L01] 一体・normal-order・核反発等はc,Tへ、未表現／近似残差はRへ明示する。今回は分解・rank選択・truncationを実行していない。一般複素係数への対応は未確認。

想定する制御は、例えば

\[
H_{\rm ctl}(s)=\sum_\ell L_\ell\otimes
 \{u_\ell(s)X_b+v_\ell(s)P_b\}+H_{\rm known}(s)
\]

という形の線形電子―bus相互作用と、既知のbus回転・電子一体制御。H_knownを任意の二体Hを供給するoracleにはしない。物理時間sと、模擬する電子時間τを区別する。単一quadratureしか使えない装置はこの契約を自動では満たさない。

**提案する構成の文法**は次の通り。係数、pulse、回路、正しさの証明を今回生成したものではない。

1. 入力された密度factorのlabelを使い、零平均の有限Fourier modeを持つu,vと、その符号・quadrature位相cycleからなる有限制御族を記述する。mode数・振幅・時間は将来別途固定する設計変数であり、今回数値を選ばない。
2. 既知のMagnus／Lie-word表示を使う設計で、電子operator wordをCARと明示したsector関係で整理することを提案する。**個々の非可換cross項を全て独立に0と置く代わりに、同じ電子作用になる項を共同で扱う**ことが仮説の核心である。
3. busを含まない必要な二体作用を目標相互作用に合わせ、一体・scalarは記録して補償可能性を別会計にする。bus依存作用と、元Hへ戻せない高体項は除去対象にする。平均変位だけの閉鎖条件にはしない。
4. 条件に解があれば制御仕様、なければ当該ansatzで未達な条件を返す。一般optimal-control solverへの目的関数の投入だけなら新原理にはならない。CARの関係から制御cycleを生成する追加規則が必要であり、その存在が未解決である。
5. 有限次数の形式条件が満たせた後も、有限時間のcoherent return、busの占有tail、準備・control・readout、T/Rとの接続は別に確認する。外側に既知PFを使うだけの部分は新規と数えない。

目標は、busを初期状態へ埋め込むisometry Vに対し

\[
\|U_{\rm joint}V-Ve^{-i\tau\sum_\ell\lambda_\ell L_\ell^2}\|
\leq \epsilon_{\rm joint}
\]

のような**位相を保つ作用の近似**を説明できること。これは達成した保証ではなく、将来満たしたい契約の定義である。部分traceしたchannelの近さだけではcontrolled energy読出しに足りない。unbounded oscillatorの全空間operator normを無条件に使わず、初期bus state、占有／tail、対象電子sectorを明示する必要がある。

D1上は、補助busをdeterministicに戻す相互作用生成を考える。Hのblock-encoding、PREP/SELECT＋postselection、qubitizationを中核にしない。将来そのような実現が必要と判明すれば、今回の制約内の仮説から外す。D2上は元Hへの誤差とscalarを全て戻し、bus付加系の基底energyを元E0と読み替えない。

**未確立の核心**は、上の条件が非可換な化学factor族で両立し、しかも既知の独立閉路・一般decoupling・汎用pulse最適化へ完全還元されない生成規則が得られるかである。具体的な操作族と検証可能な構成上の問いがあるためBとして保持する。未証明であり、成立を前提にはしない。既報の一部が関連することだけを棄却理由にもしない。

## 今回実施した範囲

静的資料読取り、一次文献・公開実装の必要箇所の照合、上記の概念仕様、文書・Git・hash監査のみ。数式は既知表現又は仮説の目標条件であり、新しい正しさの導出・定理・反例証明ではない。新規科学計算、simulation、保存値再解析／fit、回路生成／compile、pulse数値最適化、科学実装、benchmarkは0件。

**資料公開と照合後にMandatory STOP。** P1*の係数方程式の生成・求解、実装、実験、証明、正式採択へ自動進行しない。

[E1]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/60bf810df6559cc41686f3fcff90fd5108435b1a/docs/research_exploration/obstacle_driven_algorithm_principles_20261016/research_decision_handoff.md
[E2]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/60bf810df6559cc41686f3fcff90fd5108435b1a/docs/research_exploration/obstacle_driven_algorithm_principles_20261016/problem_and_failure_map.md
[E3]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/60bf810df6559cc41686f3fcff90fd5108435b1a/docs/research_exploration/obstacle_driven_algorithm_principles_20261016/constructive_principle_candidates.md
[R1]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/56f1cc55c59ab7bc42c6b24e0953675de9b29b1d/docs/research/qc_new_algorithm_research_scope_20261016/research_coverage_map.md
[R2]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/56f1cc55c59ab7bc42c6b24e0953675de9b29b1d/docs/research/qc_new_algorithm_research_scope_20261016/open_problem_landscape.md
[R3]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/56f1cc55c59ab7bc42c6b24e0953675de9b29b1d/docs/research/qc_new_algorithm_research_scope_20261016/research_state_transition.md
[R4]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/0d460c54f3bf54ea46d4d8129f6702703c4bb217/docs/research/qc_new_algorithm_static_screen_k0_20261016/technical_report.md
[L01]: https://arxiv.org/abs/1808.02625v2
[L06]: https://arxiv.org/abs/1312.2579v2
[L07]: https://arxiv.org/abs/1003.3683v2
[L08]: https://arxiv.org/abs/1801.03524v2
[L11]: https://journals.aps.org/pr/abstract/10.1103/PhysRev.56.340
