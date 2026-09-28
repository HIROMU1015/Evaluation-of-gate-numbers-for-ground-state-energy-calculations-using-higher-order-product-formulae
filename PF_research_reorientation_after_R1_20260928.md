# PF研究方針の再設計：R1後の中心課題・実行計画

**作成日：2026-09-28**
**基準commit：`a134ba3950a521225a14c46943d0dbe469425e00`**
**基準branch：`research-direction-review-after-d2r-r1-20260928`**
**文書の状態：研究方針と次pilotの提案。計算実行の許可ではない。**

**identity分離：** 上記基準commitは科学的evidenceの正本である。D0で作るprotocol・runner・testは別のplanning bundle commitに固定し、そのcommitが存在すること自体はD1/P-SPEC-6の実行許可を意味しない。D1はD0成果を独立確認した後の明示的な別指示を必要とする。

## 0. 今回決めること

次の中心課題を、**「有限時間PFの固有値誤差を資源配分へ用いる際、どの校正情報が必要で、その情報取得と保守的な量子予算のどちらに費用を払うべきか」**とする。

ただし、この上位目的を直ちに汎用selector／多分岐validatorの開発へ置き換えない。最初の本研究上の焦点は、**単一のecho観測が目的PF固有位相と一致しない機構と、必要なスペクトル情報の量**に置く。実用法は、その情報を安く取得でき、単純な校正＋余裕付き予算より有利な場合にだけ開発する。

前計画からの主な変更は次の通り。

- `current_m3`、候補点確認、truth遮断は初期の比較条件として維持するが、普遍的な研究制約とはしない。
- 一度にmodel・state・proxyを全部直すadaptive selectorは、最初の成果にしない。
- 旧評価の`gamma=1.01`を、新方式にも必須の成功条件として引き継がない。
- HClを「一般的な近似状態校正の成功／失敗例」として扱わず、ほぼexactな状態からでもproxyがずれる機構対照として使う。
- 新PF探索は、校正上の困難だけで自動的に開始しない。

第一研究の論文化は継続し、新規計算を第一研究の完成条件へ差し戻さない。第二研究v1の`complete_no_benefit`は変更しない。R0/R1と今後のpilotはpost-hoc developmentであり、旧独立評価の成功への読み替えはしない。[R1-decision][D2-completion]

## 1. 監査の範囲と証拠の強さ

今回の検討では、基準branchのHEAD、R1座標CSV、16行の分解CSV、decision、resource audit、protocol、資料索引、第二研究の保存direct点を確認した。R1の10座標・16strategy行・new direct coordinate 0・R2未許可は一致している。詳細なR1数値は保存CSVに基づく。

ただし、GPUサーバーの非公開runtime cacheのbyte identityや全テストをこのレビュー環境で独立に再実行したわけではない。資料索引の11ハッシュ一致は保存・報告された監査として扱い、今回その全てを独立再計算したとは主張しない。以下の派生数値は保存値の算術計算であり、新しいHamiltonian計算・PF計算・係数探索ではない。[Review-index][R1-resource]

## 2. 何が確定し、何が未確定か

| 区分 | 内容 |
|---|---|
| 確定事実 | R1はmodel 6、state 4、proxy 2、mixed 4の分類を保存した。16行は4条件内のstrategy行で、独立標本16件ではない。 |
| 確定事実 | LiF平衡ではlocal CISD proxyに置換しても4strategy行は未達。exact-localでは達成する。 |
| 確定事実 | HCl伸長のequal-information選択点ではexact-localでも未達。単なるmodel fit改善や状態exact化では、この点の1%予算条件を満たさない。 |
| 合理的推論 | 現在の二種類の情報不足を、同じwindow整合性または状態品質スカラーで一括解決する方針は根拠が弱い。 |
| 合理的推論 | 候補点観測は重要な基準法だが、それだけを完成した方法論の主張にはできない。 |
| 未検証仮説 | HClのproxy差を、少数の非対象固有位相と重みの情報だけで資源判断に必要な精度まで説明・圧縮できる。 |
| 未検証仮説 | その情報をexact state/direct truthなしに安く取得できる。 |
| 未検証仮説 | スペクトル情報を使う方法が、単純な余裕増額より古典費用込みで有利である。 |

根拠：[R1-coordinate][R1-decomposition][R1-protocol]

### 2.1 条件別の解釈

| 条件 | 観測 | 研究上の意味 | 言ってはいけないこと |
|---|---|---|---|
| LiF平衡 | モデルの相殺点付近で大きな過小評価。局所CISDにも残差がある。 | modelとstateの二段階を分ける。局所点評価だけでは十分でない。 | modelだけが唯一の原因。 |
| LiF伸長 | state成分が大きいが元の予算はsafe。 | signed誤差の大きさと危険な過小評価は違う。 | state成分を減らすほど量子費用が必ず下がる。 |
| HCl平衡 | currentの小不足はmixed。0.65のMWRはsafe。0.8ではproxyとdirectの符号が逆でも絶対値予算はsafe。 | 符号一致やsigned残差だけを採否に使わない。 | 符号反転は直ちにunsafe、またはbranch取り違え。 |
| HCl伸長 | 0.65のequal-informationではproxy差が主要因。0.8の別選択はsafe。 | 目的枝と非対象スペクトルの寄与を調べる価値がある。 | 全時刻域がunsafe、またはcap撤廃が常に有効。 |

## 3. 前計画に追加すべき三つの視点

### 3.1 1%余裕は物理的な必須条件ではない

旧評価は固定して保持する。一方、将来方式の費用は、校正精度と安全余裕を共同で考えるべきである。

局所proxyの絶対値を`e_hat`、真の絶対誤差を`e`とし、両方が`epsilon`未満なら、同一時刻で必要な倍率は

\[
\gamma_{\rm req}=\frac{\epsilon-\widehat e}{\epsilon-e}.
\]

運用上`gamma >= 1`を要求するなら`max(1,gamma_req)`である。これはtruthを使う事後診断であり、selector入力ではない。

R1保存値からの算術では、local CISD予算に必要な最大倍率は約`1.098139`、HCl伸長0.65では約`1.016655`である。従って、同じ10座標に限ればlocal CISD＋`gamma=1.10`は誤差条件を満たす。**ただし、この1.10は結果を見た後の値で、独立に検証された安全係数ではない。採用方式や新しい成功結果にしてはいけない。**

この計算の意味は、将来の高度な推定器に「10%前後の単純な予算増額より何がよいのか」という比較義務があることだけである。新方式の閾値は別developmentで固定し、将来の未使用条件で評価する。[R1-coordinate]

### 3.2 HCl/STO-3Gは特殊な状態対照である

保存protocolではHClは18電子・10空間軌道、固定`N_alpha=N_beta=9`である。そのdeterminant空間は

\[
\binom{10}{9}^2=100
\]

次元で、保存結果も100次元である。各スピンに空軌道が一つしかないので、同じ粒子数セクターのdeterminantはRHF配置から高々2電子励起で到達できる。従って、対応するスピン対称性の空間ではCISDの励起次数切断は実質的に消える。RCISDのスピン制約、収束誤差、別スピン状態の可能性は別問題であり、無条件の全スピン基底状態保証とはしない。

この構造は、HClのCISD/exact overlapがほぼ1だったことと整合する。HClは「一般的な近似状態でも高精度だった」ことを示す例ではなく、**状態近似をほぼ外した状態でproxyの問題を切り分ける対照**として価値がある。[D2-protocol][R1-resource]

CISDの定義とスピン制約の参考：[PySCF CI documentation](https://pyscf.org/user/ci.html)。上の100次元と励起空間に関する結論は、保存された電子・軌道数からの推論である。

### 3.3 Imをargへ変えるだけでは、今回の差は消えない

R1に保存されたcomplex echoから`arg(z)/t - Im(z)/t`を算術的に比較すると、10座標で最大絶対差は約`1.63e-11 Ha`である。HCl伸長0.65では約`5.81e-13 Ha`であり、観測されたsigned proxy差`7.42e-6 Ha`よりはるかに小さい。

したがって、今回の既存座標について、Imをargへ変えるだけの方式を次の主研究にする根拠はない。この限定は他の時刻やモデル一般の同値性を意味しない。[R1-coordinate]

## 4. 方針の比較と採否

| 案 | 長所 | 問題 | 採否 |
|---|---|---|---|
| 汎用candidate validatorを即開発 | 目的は実用的。既存pipelineを使える。 | state、proxy、branch、budgetの複数課題が未解決。同じ4条件専用の多分岐系を作りやすい。 | 最初の主軸にはしない。 |
| local recalibration＋余裕付き予算 | 軽量で、model外挿の主因を除ける。 | state/proxy biasは残る。 | 必ず含める強い基準法。 |
| より高精度な状態計算 | LiFの問題へ直接働く。 | HClには効かず、古典固有値計算を解き直す危険がある。 | 補助候補。 |
| 有限時間スペクトル情報と必要校正精度 | HClで他の誤差をほぼ除いた対象を持てる。必要情報・コストを問える。 | 恒等式確認だけでは新規性にならない。近似スペクトル取得の費用と枝識別が難しい。 | 次の中心。 |
| 固有値誤差の補正・ゼロ刻み外挿へ転換 | 校正保証に依存しない別のQPE設計になり得る。 | 複数QPEの総費用・推定誤差増幅・枝対応が新課題。先行研究がある。 | 中長期の別案。今回のpilotと混ぜない。 |
| 新PF係数探索 | 量子回路費用を直接変えられる。 | 現段階の証拠は主に推定情報の不足。既存PF集合の限界をまだ示していない。 | 条件付き保留。 |

## 5. 採用する中心問題と仮説

**中心問題：有限時間の小さなPF固有値誤差を、どの観測・情報精度なら量子資源の配分に利用できるか。その情報を取得するより保守的な予算を払う方が安いのはどの領域か。**

### 主仮説 H-SPEC

ほぼexactな初期状態でも、非対象PF固有状態の小さな重みが有限時間echoに入り、目的固有位相の微小shiftを推定するにはmaterialになり得る。この影響は、単なるPF誤差ノルムや全重なりではなく、重みと相対位相の組で定量化できる。

支持材料はHClのnear-exact CISD、非常に高い対象PF overlap、なお残るsigned/absolute proxy差である。これはまだ「少数モードから安く推定可能」を意味しない。

### 方法仮説 H-COMPRESS

資源予算を判断するのに必要なスペクトル寄与は、full spectrumより大幅に少ない情報で近似／上界化できる可能性がある。

反証条件：多数の微小成分が必要、総漏れ上界が緩すぎる、対象枝識別にexact truthが不可欠、必要な計算がfull classical solveへ近づく、または単純なmargin増額より利益がない。

### 補助仮説 H-BUDGET

一律に1%級の推定を要求するより、許容過小評価量・余剰量子予算・古典情報費用を同時に管理する方がよい。H-SPECの詳細な推定が不要な条件もある。

### 補助仮説 H-STATE

LiF型では、候補点観測でmodel誤差を除いても状態由来biasが残る。これを安く評価できなければ、H-SPEC側の成功を一般的な近似状態校正法へ拡張しない。

### 採用しない前提

- 相殺があるPFは悪い。
- signed proxyの符号一致が安全性の必要条件である。
- high overlapなら微小固有値shiftも正確である。
- exact stateへ変えれば有限時間echoはdirect eigenvalueになる。
- `gamma=1.01`で全条件を通すことが新研究の必須目標である。
- scalar proxyを改善し続ければ必ず安価なselectorが完成する。

## 6. 必要な理論：最初に示すべき式

### 6.1 スペクトル混合の厳密な分解

リポジトリの符号規約に合わせ、

\[
U_P(t)|u_j(t)\rangle=e^{it\widetilde E_j(t)}|u_j(t)\rangle,
\quad H|0\rangle=E_0|0\rangle,
\quad p_j(t)=|\langle u_j(t)|0\rangle|^2
\]

とする。`j=0`は保存された対象枝であり、「主値の位相が最小の枝」ではない。全ての枝に連続したenergyを定義する必要はなく、非対象枝には円周上のphaseを使えばよい。

\[
z_0(t)=\langle0|e^{-iHt}U_P(t)|0\rangle
=\sum_jp_j(t)e^{it(\widetilde E_j(t)-E_0)}.
\]

目的shiftを`delta_0=tilde E_0-E_0`とすると、

\[
g_0(t)-\delta_0(t)
=\frac{\sin(t\delta_0)}t-\delta_0
+\frac1t\sum_{j\ne0}p_j
\left[\sin\{t(\widetilde E_j-E_0)\}-\sin(t\delta_0)\right].
\]

第1項は単一phaseの非線形性、第2項は非対象スペクトルの混入である。これはスペクトル分解からの恒等式であり、新定理とは主張しない。

`q=1-p_0`とすると、例として

\[
|g_0-\delta_0|
\le \frac{2q}{t}+\frac{|\delta_0|^3t^2}{6}
\]

が得られる。`q`や`delta_0`をtruthから入れる限りこれは診断用であって運用証明ではない。`q/t`をtightに推定できるか、位相情報で保守性をどこまで減らせるかが研究課題になる。

### 6.2 signedの分解と資源上の危険を分ける

資源配分で直接重要なのは

\[
|\delta_0|-\widehat e
\]

の正の部分であり、`|g_0-delta_0|`そのものではない。sign reversalがあっても`|g_0|`が安全側なら予算は足りる。R1のdominance分類は診断規則として保持し、新方式の安全性定義へそのまま移さない。

### 6.3 予算への接続

\[
B=\frac{\gamma\beta K}{t(\epsilon-\widehat e)}
\]

では、

\[
|\delta_0|-\widehat e
\le (1-1/\gamma)(\epsilon-\widehat e)
\]

が採用しているcontinuous proxy内の条件となる。

区間`delta_0 in [ell,u]`を正しく構成できた場合は、`U=max(|ell|,|u|)`を予算へ入れる。区間の包含が経験的なのか、明示した仮定の下で厳密なのかを分ける。仮定の検証にexact gapやexact overlapが必要な場合、その取得費用とoracle依存を隠さない。

### 6.4 状態置換の補助評価

`A=(W-W†)/(2it)`、`W=exp(-iHt)U_P(t)`とし、状態不忠実度を`eta`とする。任意の実数`c`について

\[
|g_\psi-g_0|\le2\|A-cI\|\sqrt{\eta}
\]

が使えるが、`eta`や作用ノルムを安く得られるとは限らない。この式の存在だけでLiF型を解決したことにしない。

### 6.5 相似変換を機構対照に使う

新しいPF係数探索と別に、数学的な対照として

\[
U_{P,\lambda}(t)=V_\lambda(t)U_P(t)V_\lambda(t)^\dagger,
\quad V_\lambda(t)=e^{i\lambda t^4S}
\]

を考える。固有位相は全て不変だが、固定した`|0>`から見た`p_j`とechoは変わる。4次PFなら、`V=I+O(t^4)`なので、同じHに対する形式4次も維持する局所構成になり得る。

これは「真の固有値誤差を変えずに、校正量だけを動かす」対照であり、Hや複数誤差係数を同時に変える比較より原因を切り分けやすい。`S`をexact eigenbasisから作る場合はoracle-assisted controlと明示する。物理実装ではprocessor費用が増えるため、量子費用が不変とは言わない。今回提案する6点pilotではまだ実行せず、次の理論・構成例の候補とする。

### 6.6 情報限界を過大主張しない

一つのcomplex echoはスペクトル分布の一つのmomentであり、一般には分布を一意に決めない。ただし、selectorが全Hamiltonianも入力として持つなら、「同じechoだから全アルゴリズムに不可能」とは言えない。no-goを主張するには、許す状態・演算子作用回数・観測moment・計算予算を明示する。単なるscalar-momentの反例と、PFとして実現できる反例、計算複雑性の下界を区別する。

## 7. 最小protocol-design pilot：P-SPEC-6

### 7.1 目的

HClでR1が残したproxy差が、どの非対象スペクトル寄与で生じ、資源判断に必要な精度でどの程度圧縮可能かを調べる。重なりやbranch identityを記録するだけで終わらせない。

### 7.2 範囲

- PF：保存`current_m3`のみ。係数変更なし。
- 分子：既存HCl平衡・伸長のみ。
- 座標：R1のHCl既存6座標だけ。新時刻、new molecule、new basisなし。
- 状態：同じHの保存／再取得したexact stateを診断用に使用。新しい状態近似方式は導入しない。
- 新しく取得する情報型：**PFのground-state spectral measure `{phase_j,p_j}`**。全固有ベクトルを研究用runtimeへ保存してよいが、公開結果はweights/phasesとhashを中心とする。
- LiF：今回新しい計算なし。R1の保存値を対照として使う。

| 条件 | t/t_ana | t (Ha^-1) |
|---|---:|---:|
| HCl equilibrium | 0.5 | 0.12118203522285972 |
| HCl equilibrium | 0.65 | 0.15753664578971766 |
| HCl equilibrium | 0.8 | 0.19389125635657556 |
| HCl stretch150 | 0.5 | 0.1551067153525844 |
| HCl stretch150 | 0.65 | 0.20163872995835974 |
| HCl stretch150 | 0.8 | 0.24817074456413507 |

正確な座標identityはR1 protocolの`time_hex`を正本にする。[R1-protocol]

### 7.3 計算上限と会計

既存cacheにfull spectral decompositionが残っていれば優先再利用する。残っていなければ、**既存座標での再構築・再対角化**をpilotで明示的に許可した場合に限る。

- new direct coordinate：0。
- existing-coordinate full PF unitary rebuild：最大6。
- existing-coordinate PF eigendecomposition：最大6。
- same-H exact-ground regeneration：最大2。
- new Hamiltonian/state-approximation method：0。
- new threshold/selector tuning：0。
- backend：CPUのみ、単一process、BLAS thread各1。GPU query/allocation/kernelは0。
- peak memory：4 GiB以下。総wall time：1800秒以下。

「座標が既存」でも再対角化は新しい計算であり、`new PF eigenpair computation=0`と記録してはいけない。復元したHがoriginal Phase Aと一致しなければ停止する。過去のlocal reconstruction bridge失敗は削除せず、hash不一致を近似一致へ読み替えない。

### 7.4 保存項目

1. unitary/source/state/coordinate identity。
2. 全phase、`p_j`、対象枝、spectral projectorの扱い。
3. `sum(p_j)`、eigenpair residual、unitarity residual、対象branch整合。
4. 再構成complex echoの実部・虚部とR1値の差。
5. 単一phase非線形項、非対象weighted-sine項、signed gap、absolute-error gap。
6. 総漏れ上界`2q/t`と、実際のsigned寄与の相殺。
7. 非対象項を`K=1,2,4,8,all`だけ保持した場合の診断誤差と未保持重み上界。
8. 予算に必要な不確実性幅・余裕費用。truth補正後の費用はdiagnosticと表示。
9. wall time、peak memory、cache reuse、全新規作用／対角化回数。

寄与上位Kをtruthで選ぶ比較は**oracle compression diagnostic**であり、安いK-mode estimatorの実装・性能ではない。

### 7.5 数値gate案

- 保存研究と同等のeigenpair／unitarity gateを継承する。
- echo再構成とR1 proxyの差は`1e-10 Ha`以下を基本案とし、sourceの誤差床を検討して実行前に確定する。
- target branchは保存shiftに対応する位相とoverlapで照合。固有ベクトル番号だけで照合しない。
- 縮退・準縮退部分は個々のベクトルの重みでなくprojector weightを用いる。cluster規則は結果を見る前に固定する。
- gate不合格は科学仮説の反証と混同せず、数値未確定として停止する。

### 7.6 科学gateと終了条件

**再構成が一致しただけでは、研究仮説の新規な実証として不十分。** それは定義・identityの確認である。

pilot後の選択肢は次の三つだけにする。

1. **方法prototypeへ進む**：資源上materialな寄与が低次元に圧縮可能で、その情報をtruthなしに近似取得する具体的な計算経路と上限を設計できる。
2. **限界研究へ絞る**：広いスペクトル／枝識別／精度要求が本質的に高価で、低コスト校正に明確な制約がある。次は定量関係や実現可能な構成例をまとめる。
3. **この主題を閉じる**：標準恒等式の数値確認以上の知見が出ず、方法の見込みもない。新しい分子や閾値を増やして救済しない。

「少数Kで再構成できる」だけでは1への十分条件にしない。安く観測可能か、単純な予算増額を上回る価値があるかが必要である。

### 7.5 D0で固定する定義・計算gate

D1を許可する場合にも、以下を結果を見て変更しない。

- phase clusterは円周距離 `<=1e-8 rad`。対象clusterは保存対象枝を含むprojectorで定義し、個別固有ベクトル番号には依存しない。
- non-target寄与は `c_j=p_j[sin(phi_rel,j)-sin(t*delta_0)]/t` とする。
- top-Kは二種類を併記する。(a) `weight_ranked`: `p_j`降順、(b) `oracle_contribution_ranked`: `|c_j|`降順。後者はoracle診断専用であり運用法ではない。
- tie-breakは重み降順、wrapped phase昇順、cluster index昇順。Kは `1,2,4,8,all`。
- 座標allowanceは、同じcondition/time_hexを選択した元strategyの `original_allowed_underestimation_hartree` の最小値。
- 実際のomitted signed residualと、保守的上界 `2*q_omit/t` を別々に報告する。
- 「低次元に圧縮可能」は、6点すべてでK<=4によりactual omitted residualがallowanceの25%以下、かつ保守的上界がallowance以下であること。oracle-contribution、weight-ranked、certifiable omissionを混同しない。
- prototype候補には、weight-ranked K<=4の上記成立に加え、truth-free route（subspace dimension<=8、PF作用<=8/座標、H作用<=8/座標、full dense eigensolve/direct truth入力なし、peak memory<=4 GiB）を具体化できることを要求する。
- D1はCPU単一process、BLAS thread各1、peak memory<=4 GiB、総wall time<=1800秒。GPU query/allocation/kernelは0。
- 数値gateはweight normalization、eigenpair residual、unitarity residual、exact-ground residual、complex echo residual、energy reconstruction、保存direct shift、保存target overlapを各`<=1e-10`、phase gap `>1e-8 rad`、branch disagreement 0とする。

D1の終了statusは `d1_complete_prototype_candidate_stop`、`d1_complete_information_cost_limit_stop`、`d1_complete_close_spectral_route_stop` のいずれかで、すべてD2未許可のまま停止する。

## 8. pilot後の方法開発を始める場合

最初の候補は、固定PFに対する小部分空間／少数momentによる**paired spectral estimation**とする。HとPFのenergyを無関係に高精度化して差を取るだけの方法は、校正が本問題と同程度に難しくなる可能性があるため避ける。

少数momentを使う場合、固定した候補時刻`t`における`U_P(t)^k`のmomentと、異なるstep sizeの`U_P(k*t)`を混同しない。一般に両者は同じユニタリではなく、後者のスペクトル自体が変わる。追加PF作用回数とreference evolutionの費用も数える。

対象枝への対応、近似参照エネルギーの誤差、subspace truncation、数値誤差を全て会計する。残差が小さいだけでは、目的と違うexact eigenvectorでも合格してしまう。wrong-branch negative controlは必須。

この段階で初めて、部分空間サイズ、H-vector/PF-vector action数、候補時刻数、メモリの上限を固定する。全次元まで増やして成功させることを禁止する。目的量をabsolute energyからerror differenceへ変えただけで指数計算量がなくなったとは主張しない。

LiFへの状態誤差対応は、方法が対象として主張する範囲に応じて別に評価する。HClでの成功をLiFに対する成功と代用しない。必要なら適用範囲をnear-eigenstate calibrationへ限定し、その条件を運用時にどう確認するかも記す。

## 9. 比較対象と成功基準

### 9.1 基準法

- 旧current fallback：歴史的参照。独立条件で常に安全とは呼ばない。
- local CISD proxy＋固定予算余裕：単純で強い基準法。
- equal-information pooled/local calibration：提案法と同じ情報取得費用。
- conservative operator bound：計算できる範囲の安全側参照。tightnessを別途報告。
- direct PF eigensolve／基底状態計算：小系の古典費用参照。selector入力ではない。

未来のmargin-gridはdevelopmentで定め、独立評価前に固定する。今回の派生最大値から`1.10`を採用して、その同じ集合で成功を主張しない。

### 9.2 主指標

1. unsafe件数、coverage、abstention/fallback内訳。
2. 条件ごとの凍結量子予算。unsafe行の安い予算を効率改善に数えない。
3. 共通前処理を含む総古典費用と追加古典費用。
4. 採用している離散候補集合上の基準費用との差。連続大域oracleとは呼ばない。
5. 単純基準法との差。familyを等重みで集計する値と、絶対予算合計を併記する。

success-rateだけ上げる棄却や、難条件を除外する後付け操作はしない。失敗確率・noninferiorityを統計的に主張するなら、family数と目標効果量を事前に設計する。4条件や16strategy行から一般安全確率を保証しない。

### 9.3 効果量

旧研究の1%、前提案の10%削減・20%triggerなどを自動継承しない。必要な効果量は、測定誤差、追加古典費用、研究の対象用途を踏まえてpre-registration前に固定する。まず必要なのは「同等安全性・coverage・古典予算で基準法に支配されないこと」である。

## 10. データ分割と独立性

H-chain、LiH、BeH2、H2O、NH3、CH4、N2、CO、HF、LiF、HClの既知結果は方法開発側として扱う。旧評価時点の独立性を遡って取り消す必要はないが、その結果を見て作る新方式に対しては独立ではない。

最終方式と用途が決まる前に新しいfamilyを消費しない。将来holdoutを決める際は、分子名だけでなく電子・軌道数、真にCISD切断が存在するか、対象スピン、sector、geometry、basis、精度、候補時刻生成規則、計算上限を固定する。

HCl型の少hole完全CISD対照だけで「近似状態一般性」を主張しない。機構の構成例ではfamily holdoutは必須ではなく、一般的方法性能を主張する段階で初めて必要になる。

運用Phase Aではfull truth、oracle branch labels、exact-state overlap、direct-grid optimaを遮断する。Phase Bで採点する。順次取得規則がある場合は、観測した情報だけで次点を決め、全truth曲線を見て次点を選ばない。

## 11. 第3方針へ進む条件

### 条件A：利用可能性がPF構造で制限される

固定validatorと古典予算の下で、既存PFには大きなcalibration penaltyが残り、単純margin増額や既存PF変更では要求を満たせない。しかもその困難がPFの高次寄与・固有基底変化・状態感度と対応している。

### 条件B：校正は十分だが、既存PF自体が高コスト

`B_validated`が各PFの真の候補集合最良費用へ近いにもかかわらず、既存PF集合で求める量子費用を満たさない。この場合は同じPF内のoracle headroomが小さくても新PFに意味がある。

いずれも、current_m3だけの失敗や元2PFのselection loss=0では判定しない。validatorを固定し、代表的なYoshida型・Morales型・既存最適化PFを同一の資源指標・情報予算で比べる。この比較は方法が固まった後のstageであり、今開始しない。

新PF探索は最初に校正法を固定して行い、量子予算・古典費用・unsafe/coverageの少数軸を主目的にする。`a4`、相殺比、state sensitivity等はdescriptorまたは根拠のあるregularizerに下げる。PF＋校正法のjoint optimizationは単独の改善が確認された後だけ。

相似変換processorで固有位相を保ちつつproxyを改善できても、それだけを「新PFの固有値誤差が改善した」と呼ばない。

## 12. 実行ロードマップと停止点

| 段階 | 作業 | Codexの担当 | 停止点 |
|---|---|---|---|
| D0 | 本方針とP-SPEC-6の文書化 | source確認、算術派生表、protocol/authorization文書 | 計算を実行せず提出 |
| D1 | P-SPEC-6 | 許可後に同一H/既存6点のspectral measureを取得・分解 | 方法prototype／限界整理／閉鎖の3分岐 |
| D2 | 選んだ一方式か定量理論に集中 | truth-free最小prototype、または相似変換等の構成的control | 数理・計算費用・新規性の成立を判断 |
| D3 | developmentで強い基準法と比較 | action数・メモリ上限付き比較、safe/coverage/費用 | 支配される方式は停止 |
| D4 | 方法の主張がある場合だけ独立評価 | Phase A/B、hash固定、一回のlockbox | 成否をそのまま固定 |
| D5 | 原稿・再現資料 | 図表、claims、limitations、再現runbook | 成果の範囲を確定 |

第一論文の完成はこのロードマップと並行して進める。D1の結果を得るたびに全研究目的を一から再設定するのではなく、今回は上位目的を固定し、次に残す成果の型だけを3分岐で選ぶ。

## 13. 論文としての着地点

### 中核成果

仮題：**有限時間積公式の固有値誤差校正に必要なスペクトル情報と量子資源費用**。

必要な成果は、スペクトル恒等式そのものではなく、(a)量子予算に対する必要なweight/phase精度、(b)scalar情報とspectral情報の使い分け条件、(c)その情報を取得する費用と保守的な量子予算の比較、の少なくとも一つを定量的・再現可能に示すことである。

### 方法論として強くする条件

小部分空間等の情報で誤差区間または実用上十分な校正を行い、同一安全性・coverageの単純基準法より古典費用込みで有利であることを示す。一般的方法の主張には独立評価が必要。

### 限界研究として成立させる条件

許された情報では目的phaseを識別できない実現可能な構成例、必要情報の下界／十分条件、あるいは明確な計算費用上のtrade-offが必要。「またno-benefitだった」だけでは独立論文の成立を前提にしない。

## 14. 先行研究との差分

- Martínez-Martínez, Kamath & Izmaylov, *Estimating Trotter Approximation Errors to Optimize Hamiltonian Partitioning for Lower Eigenvalue Errors*, arXiv:2312.13282v3. 近似状態と摂動的固有値誤差、上界化と時刻選択という課題は先行する。今回の焦点は有限時間echo・微小shift・情報費用の接続。
- Yi & Crosson, *Spectral Analysis of Product Formulas for Quantum Simulation*, arXiv:2102.12655. eigenvalue/eigenvectorを分ける発想は新規ではない。
- Morales et al., *Selection and improvement of product formulae for best performance of quantum simulation*, arXiv:2210.15817v3. 有限時刻評価、固有値誤差最適化、processingは既に扱われる。表題が以前の版と異なる点に注意。
- Hejazi et al., *Better product formulas for quantum phase estimation*, arXiv:2412.16811. task-specific errorと高次PF・低エネルギー解析は先行する。
- Maxwell et al., *Practical Estimation of Trotter Error for Hamiltonian Simulation*, arXiv:2606.30738. compact BCHと実用規模の誤差評価が既にある。小さいdense例だけで「実用的な安価な推定法」と主張しない。
- Epperly, Lin & Nakatsukasa, *A Theory of Quantum Subspace Diagonalization*, SIAM J. Matrix Anal. Appl. 43, 1263–1290 (2022), arXiv:2110.07492. subspace推定のconditioningやtruncationは既存の重要論点。一般的な投影法を実装しただけでは新規性にならない。
- Rendon, Watkins & Wiebe, *Improved Accuracy for Trotter Simulations Using Chebyshev Interpolation*, arXiv:2212.14144. 固有値のゼロ刻み外挿は既存の別方向であり、単なる目的変更では新規性を得られない。

これらを確認した範囲で、新規性は「未踏で確定」とは評価しない。定量的な情報要件または同一予算での方法改善を示して初めて差分を確定する。

参考URL：
- https://arxiv.org/html/2312.13282v3
- https://arxiv.org/abs/2102.12655
- https://arxiv.org/html/2210.15817v3
- https://arxiv.org/abs/2412.16811
- https://arxiv.org/html/2606.30738v1
- https://arxiv.org/abs/2110.07492
- https://epubs.siam.org/doi/10.1137/21M145954X
- https://arxiv.org/abs/2212.14144

## 15. 次の人間の判断は三つに絞る

1. 最初の主軸を汎用selectorではなく、スペクトル情報と資源費用の研究に置くか。
2. P-SPEC-6の上限・数値gateを確定して、既存座標の再対角化を別途許可するか。
3. pilot後の方法prototype／限界研究／閉鎖の3分岐を受け入れるか。

この文書だけでR2や新しい科学計算が自動許可されたとは扱わない。

---
## 固定sourceリンク

- [R1-coordinate][R1-coordinate] — `artifacts/server_pf_candidate_validation_r1_20260928_fba3383/coordinate_proxy_results.csv`
- [R1-decomposition][R1-decomposition] — `artifacts/server_pf_candidate_validation_r1_20260928_fba3383/strategy_cause_decomposition.csv`
- [R1-decision][R1-decision] — `artifacts/server_pf_candidate_validation_r1_20260928_fba3383/decision.json`
- [R1-resource][R1-resource] — `artifacts/server_pf_candidate_validation_r1_20260928_fba3383/resource_audit.json`
- [R1-protocol][R1-protocol] — `review_response/pf_candidate_validation_r1_protocol.json`
- [Review-index][Review-index] — `review_response/pf_research_direction_review_materials_20260928.json`
- [D2-protocol][D2-protocol] — `review_response/second_study_safe_time_domain_protocol.json`
- [D2-truth][D2-truth] — `artifacts/server_second_study_safe_time_domain_phase_b_20260928_d4dd42f/direct_points.csv`
- [D2-score][D2-score] — `artifacts/server_second_study_safe_time_domain_phase_b_20260928_d4dd42f/strategy_scoring.csv`
- [D2-completion][D2-completion] — `review_response/second_study_safe_time_domain_completion_report.md`
- [R0-ledger][R0-ledger] — `artifacts/pf_candidate_validation_r0_20260928_05649f1/failure_ledger.csv`

[R1-coordinate]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/a134ba3950a521225a14c46943d0dbe469425e00/artifacts/server_pf_candidate_validation_r1_20260928_fba3383/coordinate_proxy_results.csv
[R1-decomposition]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/a134ba3950a521225a14c46943d0dbe469425e00/artifacts/server_pf_candidate_validation_r1_20260928_fba3383/strategy_cause_decomposition.csv
[R1-decision]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/a134ba3950a521225a14c46943d0dbe469425e00/artifacts/server_pf_candidate_validation_r1_20260928_fba3383/decision.json
[R1-resource]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/a134ba3950a521225a14c46943d0dbe469425e00/artifacts/server_pf_candidate_validation_r1_20260928_fba3383/resource_audit.json
[R1-protocol]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/a134ba3950a521225a14c46943d0dbe469425e00/review_response/pf_candidate_validation_r1_protocol.json
[Review-index]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/a134ba3950a521225a14c46943d0dbe469425e00/review_response/pf_research_direction_review_materials_20260928.json
[D2-protocol]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/a134ba3950a521225a14c46943d0dbe469425e00/review_response/second_study_safe_time_domain_protocol.json
[D2-truth]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/a134ba3950a521225a14c46943d0dbe469425e00/artifacts/server_second_study_safe_time_domain_phase_b_20260928_d4dd42f/direct_points.csv
[D2-score]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/a134ba3950a521225a14c46943d0dbe469425e00/artifacts/server_second_study_safe_time_domain_phase_b_20260928_d4dd42f/strategy_scoring.csv
[D2-completion]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/a134ba3950a521225a14c46943d0dbe469425e00/review_response/second_study_safe_time_domain_completion_report.md
[R0-ledger]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/a134ba3950a521225a14c46943d0dbe469425e00/artifacts/pf_candidate_validation_r0_20260928_05649f1/failure_ledger.csv
