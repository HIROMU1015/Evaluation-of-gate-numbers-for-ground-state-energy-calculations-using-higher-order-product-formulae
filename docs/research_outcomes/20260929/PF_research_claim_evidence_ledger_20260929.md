# PF研究：主張・証拠・限定条件の台帳

**整理日：2026年9月29日｜v0.1｜内容整理稿・Codex証拠監査前**

この台帳は、本体レポートと短縮版に書ける内容の境界を管理する。CLは主張ID、Sは固定source IDである。各主張は「記録値」「条件付きの数理設計」「総合的解釈」「将来判断」を分けて記載する。原資料の報告値を読んだことは、全raw行の再計算やmanifestの独立再hashを行ったこととは異なる。

**共通snapshot：`fe55a0cb1dfe303eb2e878d6c098b6a7a556c5e3`。** 一部sourceは、この会話で直接確認した前段commitへ固定している。commitが異なるsource同士を同一blobと見なす場合は、Codexで実際にhashを照合する。

## 1．主張索引

| ID | 内容 | 証拠区分 | source |
|---|---|---|---|
| [CL01](#CL01) | 公開H-chain研究の性能比較 | 公開プレプリントの報告 | [S01](#S01) |
| [CL02](#CL02) | 初期の分子間比較はoracle-assisted | 当時の固定比較・使用履歴 | [S16](#S16) |
| [CL03](#CL03) | 校正誤差の三分解 | 定義・解析恒等式 | [S04](#S04) [S07](#S07) |
| [CL04](#CL04) | 固定128 caseの状態置換支配 | 固定機構実験 | [S04](#S04) |
| [CL05](#CL05) | H4でも安全性と費用は異なる | 固定development資源評価 | [S04](#S04) |
| [CL06](#CL06) | S0の1%余裕はdevelopment 6/6達成 | 凍結predictionのdevelopment採点 | [S03](#S03) [S04](#S04) |
| [CL07](#CL07) | 資源因子とPF選択損失 | 保存結果再解析 | [S02](#S02) [S03](#S03) |
| [CL08](#CL08) | HFのcap制約の下界 | 解析上下界＋保存scalar | [S03](#S03) |
| [CL09](#CL09) | biasの資源感度は残余予算で決まる | 費用式の恒等的整理 | [S02](#S02) |
| [CL10](#CL10) | S4の追加診断は資源改善なし | 固定比較のnegative result | [S02](#S02) [S03](#S03) |
| [CL11](#CL11) | S4のbeta統一監査 | 費用定義の手続き監査 | [S03](#S03) |
| [CL12](#CL12) | 第二研究は固定benefit条件を満たさない | 独立4条件の事前固定negative evaluation | [S05](#S05) |
| [CL13](#CL13) | 通常経路と拡張経路を分ける | 保存選択点と事後解釈 | [S06](#S06) [S18](#S18) |
| [CL14](#CL14) | R1は4条件・10座標・16行の診断 | post-hoc development diagnosis | [S06](#S06) [S18](#S18) |
| [CL15](#CL15) | R1では単一の誤差構造ではない | 固定診断規則による事後分類 | [S06](#S06) [S07](#S07) |
| [CL16](#CL16) | local置換のcounterfactual | post-hoc counterfactual | [S06](#S06) [S07](#S07) |
| [CL17](#CL17) | 単純な予算余裕との比較材料 | 保存scalarのpost-hoc算術 | [S19](#S19) |
| [CL18](#CL18) | HClは状態誤差を小さくした機構対照 | 限定条件の数値観測 | [S06](#S06) [S07](#S07) |
| [CL19](#CL19) | D1は少数の非対象clusterへ圧縮 | post-hoc exact-ground spectral diagnostic | [S08](#S08) [S09](#S09) |
| [CL20](#CL20) | 圧縮診断は取得法ではない | 定義とaccessの限定 | [S08](#S08) [S09](#S09) |
| [CL21](#CL21) | D2-Aの有限作用predictor | development prototype | [S10](#S10) [S17](#S17) |
| [CL22](#CL22) | unwrap座標系監査 | post-hoc procedural definition audit | [S12](#S12) |
| [CL23](#CL23) | HCl6点での高精度shift一致 | truth採点による限定的回収結果 | [S12](#S12) [S11](#S11) |
| [CL24](#CL24) | 回収精度は資源優位へ直結しなかった | 凍結budget結果と事後分解 | [S11](#S11) [S12](#S12) [S14](#S14) |
| [CL25](#CL25) | D2-Aの古典費用は小系cache条件の記録 | saved resource measurement | [S17](#S17) |
| [CL26](#CL26) | C0は条件付きboundと変換を仕様化 | 数理設計・未実証の候補 | [S15](#S15) |
| [CL27](#CL27) | C0でoperational認証は未確立 | design status | [S13](#S13) [S14](#S14) [S15](#S15) |
| [CL28](#CL28) | 固定時刻での校正改善には小さい利益上限 | post-hoc development arithmetic | [S14](#S14) [S15](#S15) |
| [CL29](#CL29) | 圧縮・取得・幅・資源価値は別の問い | 限定evidenceからの総合的解釈 | [S08](#S08) [S12](#S12) [S13](#S13) |
| [CL30](#CL30) | 現在の作業は成果整理であり新実験ではない | governance_scope | [S13](#S13)・同梱Codex指示書 |

## 2．主張ごとの境界

<a id="CL01"></a>
### CL01｜公開H-chain研究の性能比較

**本文に使う主張：** H₂〜H₁₅を用い、摂動的固有値誤差推定から総ゲート数とRZ-layer depthを比較した。形式次数の増大が単調な費用削減にならないという報告を出発点とする。

**証拠：** [S01](#S01)。参照箇所：Abstract。区分：公開プレプリントの報告。

**必須の限定：** 対象・近似・PF集合に限定。公開原稿の新4次式とcurrent_m3の係数同一性、査読出版状況は今回未照合。

**書かない表現：** 「全分子で8次／新4次が最良」「査読出版済み」「コードIDとの同一性確認済み」

**配置：** 背景・研究の出発点。**照合状態：** 内容をsourceと対応付け済み。Codexの原row・hash照合は未実施。

<a id="CL02"></a>
### CL02｜初期の分子間比較はoracle-assisted

**本文に使う主張：** N₂/CO active-space 4条件で複数のPF・モデル組が合格し、current_m3が合格PF中で最小費用と報告された。各対象でdirect固有値点を使う校正である。

**証拠：** [S16](#S16)。参照箇所：2026-09-21固定ホールドアウトの結果。区分：当時の固定比較・使用履歴。

**必須の限定：** 当時の固定問いに対する転用性。後続の方法設計に使用した時点からdevelopment。

**書かない表現：** 「高価な対象別校正なしで未知分子を予測した」

**配置：** 性能比較から校正研究への接続。**照合状態：** 内容をsourceと対応付け済み。Codexの原row・hash照合は未実施。

<a id="CL03"></a>
### CL03｜校正誤差の三分解

**本文に使う主張：** f−δ=(f−gψ)+(gψ−g0)+(g0−δ)によりmodel、state substitution、proxy–eigenvalueを分離した。

**証拠：** [S04](#S04)、[S07](#S07)。参照箇所：第一研究§1–4／R1 decomposition。区分：定義・解析恒等式。

**必須の限定：** 同じH・P・t・proxy規約での比較。guard premiumは中央予測と別に扱う。

**書かない表現：** 「恒等式のclosureだけで全実装・物理機構が証明された」

**配置：** 方法・共通記号。**照合状態：** 内容をsourceと対応付け済み。Codexの原row・hash照合は未実施。

<a id="CL04"></a>
### CL04｜固定128 caseの状態置換支配

**本文に使う主張：** H4 56 case＋人工二準位72 caseの計128 caseでstate支配79、mixed49。第一研究の判定はresolved点の過半数・他成分の3倍という固定規則による。

**証拠：** [S04](#S04)。参照箇所：§4 Experiment B/Cの機構判定。区分：固定機構実験。

**必須の限定：** 128分子ではない。R1の2倍dominanceと異なる。状態支配は普遍則ではない。

**書かない表現：** 「128分子でstate誤差が支配」「全てのPFでstateだけが問題」

**配置：** 主要結果・機構。**照合状態：** 内容をsourceと対応付け済み。Codexの原row・hash照合は未実施。

<a id="CL05"></a>
### CL05｜H4でも安全性と費用は異なる

**本文に使う主張：** H4のm5_best選択はγ=1.01でsafeだが、joint regret約64.51%、凍結budgetはdirect grid基準より約98.35%大きかった。

**証拠：** [S04](#S04)。参照箇所：§5 H4の凍結資源判定。区分：固定development資源評価。

**必須の限定：** S0のN₂/CO/HF 6条件とは別のselector・case。費用指標二つを混同しない。

**書かない表現：** 「全実験でcurrent_m3を選択」「64.51%と98.35%は同一regret」

**配置：** 安全性と効率の対照例。**照合状態：** 内容をsourceと対応付け済み。Codexの原row・hash照合は未実施。

<a id="CL06"></a>
### CL06｜S0の1%余裕はdevelopment 6/6達成

**本文に使う主張：** N₂/CO主4条件、HF stress2条件の全6条件でγ=1.01が目標を満たす。γ=1.0では5/6。

**証拠：** [S03](#S03)、[S04](#S04)。参照箇所：Safetyとefficiency／第一研究§6。区分：凍結predictionのdevelopment採点。

**必須の限定：** continuous cost proxy、既使用条件、実際の選択時刻での採点。

**書かない表現：** 「1%が未知分子でも安全を保証」「QPE実機全成功率を保証」

**配置：** 主要結果・安全性。**照合状態：** 内容をsourceと対応付け済み。Codexの原row・hash照合は未実施。

<a id="CL07"></a>
### CL07｜資源因子とPF選択損失

**本文に使う主張：** 元2 PF・保存grid上でFP=1が6/6。HFのFtotalは2.150313／2.102857。主4条件はN₂伸長がtime、他3条件がcalibration/budget支配。

**証拠：** [S02](#S02)、[S03](#S03)。参照箇所：条件別の費用会計／主張C4–C7。区分：保存結果再解析。

**必須の限定：** 保存gridと候補集合に限定。FtotalとFt、比と百分率を区別。

**書かない表現：** 「既存PF全体に改善余地なし」「連続時間大域oracle」

**配置：** 主要結果・資源因子。**照合状態：** 内容をsourceと対応付け済み。Codexの原row・hash照合は未実施。

<a id="CL08"></a>
### CL08｜HFのcap制約の下界

**本文に使う主張：** HF平衡/伸長でFdomain≥2.114659／2.069664。cap内最大削減は1.254948%／0.322572%。

**証拠：** [S03](#S03)。参照箇所：HF cap境界。区分：解析上下界＋保存scalar。

**必須の限定：** feasibleなcap点と保存gridによる境界。cap外の安全性は未確認。

**書かない表現：** 「cap外の最適時刻を認証」「同じ値をHClへ適用」

**配置：** time-domain研究の動機。**照合状態：** 内容をsourceと対応付け済み。Codexの原row・hash照合は未実施。

<a id="CL09"></a>
### CL09｜biasの資源感度は残余予算で決まる

**本文に使う主張：** e_hat=e+bならFmodel=1/[1−b/(epsilon−e)]。誤差の相対精度だけでなく残余予算への比が重要。

**証拠：** [S02](#S02)。参照箇所：§5 費用分解と用語。区分：費用式の恒等的整理。

**必須の限定：** 正の分母と同一時刻の費用式。新推定器の成功ではない。

**書かない表現：** 「この式だけで最適selectorを得た」

**配置：** 数理的整理・解釈。**照合状態：** 内容をsourceと対応付け済み。Codexの原row・hash照合は未実施。

<a id="CL10"></a>
### CL10｜S4の追加診断は資源改善なし

**本文に使う主張：** operator-sensitive二状態診断のtargeted fallbackはbaselineより資源費用を改善しなかった。no_benefitを保持。

**証拠：** [S02](#S02)、[S03](#S03)。参照箇所：主張C9／結論・停止判断。区分：固定比較のnegative result。

**必須の限定：** 固定診断と同じcapを含む比較。第一研究の他の成果と分ける。

**書かない表現：** 「state診断一般は無意味」「第一研究全体が成果なし」

**配置：** negative result。**照合状態：** 内容をsourceと対応付け済み。Codexの原row・hash照合は未実施。

<a id="CL11"></a>
### CL11｜S4のbeta統一監査

**本文に使う主張：** 保存scoring β=0.105をpractical/S0の1.2へ整合させても42/42 safe、成否変更0、no_benefit不変。

**証拠：** [S03](#S03)。参照箇所：S4費用定義監査。区分：費用定義の手続き監査。

**必須の限定：** 元artifact不変。旧絶対phase-error/energy-marginは再監査値を優先。

**書かない表現：** 「βの違いはなかった」「新しい独立selector評価」

**配置：** 再現性・引用規則。**照合状態：** 内容をsourceと対応付け済み。Codexの原row・hash照合は未実施。

<a id="CL12"></a>
### CL12｜第二研究は固定benefit条件を満たさない

**本文に使う主張：** multiple-windowは3/4 safe。aggregate budgetはcurrent比0.8933806671、equal-information比1.2526414181。正式complete_no_benefit。

**証拠：** [S05](#S05)。参照箇所：主結果／停止。区分：独立4条件の事前固定negative evaluation。

**必須の限定：** 単一固定規則。当時の独立性を保持。unsafeを含む費用和で勝者を決めない。

**書かない表現：** 「時間域拡張一般は不可能」「3/4で普遍的に安全」

**配置：** 主要negative result。**照合状態：** 内容をsourceと対応付け済み。Codexの原row・hash照合は未実施。

<a id="CL13"></a>
### CL13｜通常経路と拡張経路を分ける

**本文に使う主張：** LiF平衡のMWRはcurrent選択と同一座標。HCl平衡MWRは0.65へ拡張しsafe、HCl伸長では0.5へ戻りsafe、equal-informationの0.65はunsafe。

**証拠：** [S06](#S06)、[S18](#S18)。参照箇所：condition＋strategies＋selected_relative_to_t_anaとR1 Safe列。区分：保存選択点と事後解釈。

**必須の限定：** パスと観測の関係。元判定を覆さず、一般的な因果効果を推定しない。

**書かない表現：** 「唯一の失敗は時間を拡張したせい」

**配置：** 失敗の解釈・問いの変化。**照合状態：** 内容をsourceと対応付け済み。Codexの原row・hash照合は未実施。

<a id="CL14"></a>
### CL14｜R1は4条件・10座標・16行の診断

**本文に使う主張：** 重複除去後10座標、16strategy行。saved CISD再利用5、新CISD5、新exact proxy10、新direct truth0。

**証拠：** [S06](#S06)、[S18](#S18)。参照箇所：Fixed calculation counts／10座標CSV。区分：post-hoc development diagnosis。

**必須の限定：** 16独立標本ではない。結果を見た後の診断。

**書かない表現：** 「16件の独立検証」「独立な新手法評価」

**配置：** 方法・証拠階層。**照合状態：** 内容をsourceと対応付け済み。Codexの原row・hash照合は未実施。

<a id="CL15"></a>
### CL15｜R1では単一の誤差構造ではない

**本文に使う主張：** model6、state4、proxy2、mixed/none4。LiF平衡はmodel、LiF伸長はstate、HCl伸長0.65の失敗はproxyが主。

**証拠：** [S06](#S06)、[S07](#S07)。参照箇所：Strategy-level decomposition／fixed_attribution_rule。区分：固定診断規則による事後分類。

**必須の限定：** materialityと2倍dominanceに依存。LiF伸長は元予算がsafe。

**書かない表現：** 「state成分が大きい＝失敗原因」「件数比が分子一般の頻度」

**配置：** 条件別機構。**照合状態：** 内容をsourceと対応付け済み。Codexの原row・hash照合は未実施。

<a id="CL16"></a>
### CL16｜local置換のcounterfactual

**本文に使う主張：** 元の時刻でCISD-local予算なら11/16、exact-localなら15/16がsafe。exactでもHCl伸長equal-informationの1行が未達。

**証拠：** [S06](#S06)、[S07](#S07)。参照箇所：CISD-local safe／exact-local safe／counterfactual_diagnostics。区分：post-hoc counterfactual。

**必須の限定：** 元の時刻とgammaを固定した理想化比較。

**書かない表現：** 「local法が独立評価11/16に成功」

**配置：** 情報不足の切り分け。**照合状態：** 内容をsourceと対応付け済み。Codexの原row・hash照合は未実施。

<a id="CL17"></a>
### CL17｜単純な予算余裕との比較材料

**本文に使う主張：** local CISDの必要倍率最大は既存10座標で1.0981387383。HCl伸長0.65は1.0166546542。

**証拠：** [S19](#S19)。参照箇所：local_cisd_gamma_required。区分：保存scalarのpost-hoc算術。

**必須の限定：** truthから得た必要倍率であり、将来の保証値ではない。

**書かない表現：** 「1.10なら全分子safe」「10%削減が常にある」

**配置：** 強いbaselineを置く動機。**照合状態：** 内容をsourceと対応付け済み。Codexの原row・hash照合は未実施。

<a id="CL18"></a>
### CL18｜HClは状態誤差を小さくした機構対照

**本文に使う主張：** HClではCISD/exact重なりがほぼ1で、state substitutionをほぼ除いたproxy診断に使える。

**証拠：** [S06](#S06)、[S07](#S07)。参照箇所：Coordinate-level state controls／hcl_control。区分：限定条件の数値観測。

**必須の限定：** spin・sector・収束の条件がある。大規模・強相関へのtransferではない。

**書かない表現：** 「HClでは無条件にCISD=FCI」「一般分子でCISDは十分」

**配置：** 機構対照の位置付け。**照合状態：** 内容をsourceと対応付け済み。Codexの原row・hash照合は未実施。

<a id="CL19"></a>
### CL19｜D1は少数の非対象clusterへ圧縮

**本文に使う主張：** HCl既存6座標でweight-ranked K≤4のactual/conservative gateが成立。oracle寄与順K≤8でもactual gate成立。

**証拠：** [S08](#S08)、[S09](#S09)。参照箇所：scientific_gates／non_target top_k。区分：post-hoc exact-ground spectral diagnostic。

**必須の限定：** Kは非対象cluster保持数。目的clusterを除く。

**書かない表現：** 「全スペクトルが4成分」「Arnoldi4次・4作用で十分」

**配置：** 限定的な圧縮可能性。**照合状態：** 内容をsourceと対応付け済み。Codexの原row・hash照合は未実施。

<a id="CL20"></a>
### CL20｜圧縮診断は取得法ではない

**本文に使う主張：** D1のweightとq_omitはexact ground・全スペクトルから得る。2q_omit/tが小さいことは未取得重みを運用時に認証できたことではない。

**証拠：** [S08](#S08)、[S09](#S09)。参照箇所：truth_free_route未実装／q_omit計算。区分：定義とaccessの限定。

**必須の限定：** 一般的なスペクトル回収の難易度は未検証。

**書かない表現：** 「weight rankingはtruth-free」「D1で実用校正が完成」

**配置：** 到達点と未達の区別。**照合状態：** 内容をsourceと対応付け済み。Codexの原row・hash照合は未実施。

<a id="CL21"></a>
### CL21｜D2-Aの有限作用predictor

**本文に使う主張：** 元CISDから再直交化unitary Arnoldi、最大m=8。PF/Hの作用上限を分け、予測を凍結後truthで採点。

**証拠：** [S10](#S10)、[S17](#S17)。参照箇所：estimator／freeze boundary／各coordinateの作用会計。区分：development prototype。

**必須の限定：** truth-freeはpredictor入力の性質。HCl既使用条件。

**書かない表現：** 「研究全体にtruth不要」「量子8shotで取得」

**配置：** 回収方法の記述。**照合状態：** 内容をsourceと対応付け済み。Codexの原row・hash照合は未実施。

<a id="CL22"></a>
### CL22｜unwrap座標系監査

**本文に使う主張：** 絶対PF energyのunwrap整数とground除去後shiftの整数の直接一致比較は無効。元0/6を物理的な枝失敗として使わない。

**証拠：** [S12](#S12)。参照箇所：coordinate_system_mismatch_confirmed／original_*_unchanged。区分：post-hoc procedural definition audit。

**必須の限定：** 旧resultは保存し、auditを付けて解釈する。

**書かない表現：** 「元scoringに不一致なし」「元artifactを成功結果へ上書き」

**配置：** 訂正履歴。**照合状態：** 内容をsourceと対応付け済み。Codexの原row・hash照合は未実施。

<a id="CL23"></a>
### CL23｜HCl6点での高精度shift一致

**本文に使う主張：** 表現不変half-gap基準で6/6整合、最大shift誤差1.3825298286693e−8 Ha、最大error/half-gap比1.1629586816034e−7。

**証拠：** [S12](#S12)、[S11](#S11)。参照箇所：summary／6coordinate rows。区分：truth採点による限定的回収結果。

**必須の限定：** 目的枝との事後的整合。独立一般化、運用上のbranch certificateではない。

**書かない表現：** 「全分子で高精度」「ground/branch認証を解決」

**配置：** 肯定的な回収結果。**照合状態：** 内容をsourceと対応付け済み。Codexの原row・hash照合は未実施。

<a id="CL24"></a>
### CL24｜回収精度は資源優位へ直結しなかった

**本文に使う主張：** 棄却1/6、出力予算5/5 safe、主baselineより低予算0/6。幅を決めた成分は6/6でlocal residual width。

**証拠：** [S11](#S11)、[S12](#S12)、[S14](#S14)。参照箇所：budget／abstained／width_determining_component。区分：凍結budget結果と事後分解。

**必須の限定：** 幅は経験的で無条件certificateではない。棄却をsafe達成に数えない。

**書かない表現：** 「6/6で安全実行」「厳密認証が原理的に高価」

**配置：** 資源結果・negative result。**照合状態：** 内容をsourceと対応付け済み。Codexの原row・hash照合は未実施。

<a id="CL25"></a>
### CL25｜D2-Aの古典費用は小系cache条件の記録

**本文に使う主張：** PF48作用・H48作用、wall約2.62秒、peak RSS454,656 KiB。component gateやcacheの費用を別に記録した。

**証拠：** [S17](#S17)。参照箇所：coordinates／wall_seconds／runtime_identity。区分：saved resource measurement。

**必須の限定：** 元cache再利用。総前処理費用、大規模scaling、量子shot・FTQC時間ではない。

**書かない表現：** 「常に数秒で校正」「実機timeで優位」

**配置：** 費用会計。**照合状態：** 内容をsourceと対応付け済み。Codexの原row・hash照合は未実施。

<a id="CL26"></a>
### CL26｜C0は条件付きboundと変換を仕様化

**本文に使う主張：** normal AのRayleigh residualとfull-space gρ,othersを使う二次残差候補を記述し、chord→principal phase→physical liftの条件を分けた。

**証拠：** [S15](#S15)。参照箇所：B1–B4。区分：数理設計・未実証の候補。

**必須の限定：** target、g>r、full action、作用誤差等の条件が必要。projected nonnormal行列へ直接適用しない。

**書かない表現：** 「無条件certificate完成」「既存論文の新規定理を発見」

**配置：** 条件・必要情報の整理。**照合状態：** 内容をsourceと対応付け済み。Codexの原row・hash照合は未実施。

<a id="CL27"></a>
### CL27｜C0でoperational認証は未確立

**本文に使う主張：** truth-free全空間gap、ground/reference、branch/alias、rigorous action-errorは未確立。明示的action bound0はforward-error certificateではない。

**証拠：** [S13](#S13)、[S14](#S14)、[S15](#S15)。参照箇所：unresolved_items／numerical_action_bound_status。区分：design status。

**必須の限定：** 不足情報の整理であり、取得不可能の証明ではない。

**書かない表現：** 「gap取得は不可能」「C1を実施済み」

**配置：** 未解決事項。**照合状態：** 内容をsourceと対応付け済み。Codexの原row・hash照合は未実施。

<a id="CL28"></a>
### CL28｜固定時刻での校正改善には小さい利益上限

**本文に使う主張：** HCl6時刻・未補正task・local CISD γ1.02で完全校正上限0.327975〜2.286462%。現行幅/w_win(0)は1.1062〜167.4915、0/6が必要幅を満たす。

**証拠：** [S14](#S14)、[S15](#S15)。参照箇所：S_max_same_time／current_width_to_w_win_eta_0。区分：post-hoc development arithmetic。

**必須の限定：** 同じ時刻、同じbaseline、同じ費用式。HF capや別時刻・bias補正へ一般化しない。

**書かない表現：** 「今後の全改善余地は最大2.3%」「新手法が2.3%改善した」

**配置：** 情報価値の上限。**照合状態：** 内容をsourceと対応付け済み。Codexの原row・hash照合は未実施。

<a id="CL29"></a>
### CL29｜圧縮・取得・幅・資源価値は別の問い

**本文に使う主張：** D1の圧縮、D2-Aの回収、経験的幅による資源非優位、C0の必要情報整理を、異なる達成段階として接続する。

**証拠：** [S08](#S08)、[S12](#S12)、[S13](#S13)。参照箇所：各stageの主要結果。区分：限定evidenceからの総合的解釈。

**必須の限定：** 一系列の結果に基づく整理。普遍的なno-go theoremではない。

**書かない表現：** 「全PFで圧縮は資源に役立たない」

**配置：** 総括・短縮版の中心。**照合状態：** 内容をsourceと対応付け済み。Codexの原row・hash照合は未実施。

<a id="CL30"></a>
### CL30｜現在の作業は成果整理であり新実験ではない

**本文に使う主張：** 3文書を作り、Codexで証拠監査・repo統合する。将来は有限校正費用下の資源判断を検討候補とするが、C1等を自動開始しない。

**権限根拠：** [S13](#S13)の未承認境界と、同梱の
[`CODEX_research_outcomes_evidence_audit_20260929.md`](CODEX_research_outcomes_evidence_audit_20260929.md)。
区分：`governance_scope`。これはscientific evidence claimではなく、今回の文書作業と将来研究の権限境界である。

**必須の限定：** 将来方針を数値成果に数えない。文書作成は科学計算のauthorizationではない。

**書かない表現：** 「次方式は有効」「gap認証や新PFを承認済み」

**配置：** 引継ぎ・権限境界。**照合状態：** 内容をsourceと対応付け済み。Codexの原row・hash照合は未実施。

## 3．指標を混同しないための規則

- `delta_direct`はsigned shift、`e_direct=abs(delta_direct)`は未補正予算のPF誤差として記述する。古いraw fieldは勝手に変更しない。
- 機構分解のsigned discrepancyと、危険な絶対誤差過小評価は別。guarded errorと中央予測も別に保存する。
- 第一研究の3倍dominanceとR1の2倍dominance、128 caseと16strategy行を統合して頻度にしない。
- `F_total`（凍結予算の比）、`F_t`（選択時刻の必要費用の比）、`regret=比−1`を区別する。
- 1.0、1.01、1.02等のgammaと、各stageのbetaを固定sourceと一緒に記載する。
- D1 top-Kは非対象cluster保持数。Arnoldi m、PF一stepのK_current_m3とは異なる。
- 旧D2-A整数一致の0/6は履歴値。物理解釈には監査後の表現不変採点を必ず併記する。
- 残差上界が「ある固有値」に対して成立しても、ground/target/phase liftが認定されたとは限らない。
- conditional certificate、empirical、heuristic、indeterminateは同じ保証ではない。
- 古典時間とPauli rotationを根拠なく合算しない。未実施の前処理・状態準備・実機費用を無料と主張しない。

## 4．Codex照合で残す確認事項

| ID | 確認事項 | 不足時の扱い |
|---|---|---|
| V01 | 公開H-chain原稿の新4次式とコードID・係数の対応 | 同一視せず背景の記述を維持。新しい係数計算はしない |
| V02 | S0/S4、第二研究、D2-Aの費用式とgamma・beta・候補gridの対応 | stage別に注記。絶対費用を無理に比較しない |
| V03 | 第一研究128 case、R1 16行と局所counterfactualの集計 | 保存CSV/JSONのみで照合。新しいeigentruthは生成しない |
| V04 | D1 top-Kが非対象clusterのみであること | 実装とprotocolを照合し、目的clusterを含む数と分ける |
| V05 | D2-A原判定とauditの同一prediction hash | 元decisionを上書きせず、auditとの対応を記録 |
| V06 | C0 Rayleigh residualとD2-A unit-circle候補残差の意味 | 異なる残差を同じ数として再利用しない |
| V07 | 旧データ使用台帳へのHCl/LiF後続利用の追補 | 当時の独立性は保存し、以後のdevelopment利用を追記 |
| V08 | 各S sourceのcommit・blob・必要rowと本文の値 | 不一致はcorrection logへ。推測や別versionで穴埋めしない |
| V09 | 論文化・C1等の新規研究許可へ誤読される記述 | 今回は成果整理のみ。全科学計算authorizationをfalseで維持 |

## 5．固定source registry

各sourceのURL・commit・locatorは、同梱JSONにも保存した。以下のGit blob SHA-1はコネクタ返却値であり、こちらがraw bytesから独立に計算したSHA-256ではない。全文を取得したもの、関連範囲を取得したもの、会話内で確認済みの本文を再利用したものを、確認範囲に明記する。

<a id="S01"></a>
### S01｜Evaluating higher-order product formulae for molecular ground-state energy estimation

**版：** `arXiv:2605.30967v1`
**著者：** Hiromu Abe, Keita Kanno, Ryosuke Kimura, Masahiko Kamoshita, Kosuke Mitarai
**参照箇所：** Title / authors / Abstract
**根拠へのリンク：** [固定sourceを開く](https://arxiv.org/html/2605.30967v1)
**確認範囲：** 公式arXivのAbstractとv1 HTMLの所在を確認。本文の全数値・係数同一性・査読出版状況は監査していない。

<a id="S02"></a>
### S02｜第一研究：論文主張台帳と完成方針

**Path：** `PF_first_study_paper_claim_ledger_20260926.md`
**Commit：** `fe55a0cb1dfe303eb2e878d6c098b6a7a556c5e3`
**Git blob SHA-1（返却値）：** `82dbdaf9f5f1c243ff681355be61aca160e7da4d`
**参照箇所：** §1–5（中心命題、主張台帳、費用定義）、§8–9（追加計算と停止）
**根拠へのリンク：** [固定sourceを開く](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/fe55a0cb1dfe303eb2e878d6c098b6a7a556c5e3/PF_first_study_paper_claim_ledger_20260926.md)
**確認範囲：** 指定箇所の内容を取得・読解。数値計算・全manifest再hashは未実施。

<a id="S03"></a>
### S03｜第一研究 completion analysis

**Path：** `artifacts/pf_first_study_completion_analysis_20260926_940ee7f/report.md`
**Commit：** `fe55a0cb1dfe303eb2e878d6c098b6a7a556c5e3`
**Git blob SHA-1（返却値）：** `732adc064c330fd0f358920077113f73008affbf`
**参照箇所：** 条件別の費用会計／HF cap境界／S4費用定義監査／Safetyとefficiency
**根拠へのリンク：** [固定sourceを開く](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/fe55a0cb1dfe303eb2e878d6c098b6a7a556c5e3/artifacts/pf_first_study_completion_analysis_20260926_940ee7f/report.md)
**確認範囲：** 指定箇所の内容を取得・読解。数値計算・全manifest再hashは未実施。

<a id="S04"></a>
### S04｜第一研究 統合結果

**Path：** `PF_first_study_results_20260925.md`
**Commit：** `fe55a0cb1dfe303eb2e878d6c098b6a7a556c5e3`
**参照箇所：** §1–6：128 case、3倍dominance、H4・S0の結果。末尾の当時の将来方針は現在の指示には使わない。
**根拠へのリンク：** [固定sourceを開く](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/fe55a0cb1dfe303eb2e878d6c098b6a7a556c5e3/PF_first_study_results_20260925.md)
**確認範囲：** 返却本文の§1–6を読解。末尾に切詰めがあるため文書全体の完読・最新版統合とはしない。

<a id="S05"></a>
### S05｜第二研究 safe-time-domain 完了報告

**Path：** `review_response/second_study_safe_time_domain_completion_report.md`
**Commit：** `fe55a0cb1dfe303eb2e878d6c098b6a7a556c5e3`
**Git blob SHA-1（返却値）：** `71297cea64e29fa9aee90d63d8b29031eeca6f83`
**参照箇所：** 主結果／数値・再現性gate／資源と停止
**根拠へのリンク：** [固定sourceを開く](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/fe55a0cb1dfe303eb2e878d6c098b6a7a556c5e3/review_response/second_study_safe_time_domain_completion_report.md)
**確認範囲：** 指定箇所の内容を取得・読解。数値計算・全manifest再hashは未実施。

<a id="S06"></a>
### S06｜R1 selected-coordinate cause decomposition

**Path：** `artifacts/server_pf_candidate_validation_r1_20260928_fba3383/report.md`
**Commit：** `fe55a0cb1dfe303eb2e878d6c098b6a7a556c5e3`
**Git blob SHA-1（返却値）：** `9c451f5c0a11e98157bca49bdf21640e4277eeb3`
**参照箇所：** Strategy-level decomposition／Coordinate-level state controls／計算件数
**根拠へのリンク：** [固定sourceを開く](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/fe55a0cb1dfe303eb2e878d6c098b6a7a556c5e3/artifacts/server_pf_candidate_validation_r1_20260928_fba3383/report.md)
**確認範囲：** 指定箇所の内容を取得・読解。数値計算・全manifest再hashは未実施。

<a id="S07"></a>
### S07｜R1固定protocol

**Path：** `review_response/pf_candidate_validation_r1_protocol.json`
**Commit：** `a134ba3950a521225a14c46943d0dbe469425e00`
**Git blob SHA-1（返却値）：** `52384c3857e39fee59f43c54f42a668507c657e0`
**参照箇所：** decomposition / fixed_attribution_rule / counterfactual_diagnostics / scientific_role
**根拠へのリンク：** [固定sourceを開く](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/a134ba3950a521225a14c46943d0dbe469425e00/review_response/pf_candidate_validation_r1_protocol.json)
**確認範囲：** この会話中の取得済み完全本文を参照。今回は同一blobの再取得はしていない。

<a id="S08"></a>
### S08｜D1 decision

**Path：** `artifacts/server_pf_spectral_information_pilot_d1_20260928_03747a2/decision.json`
**Commit：** `fe55a0cb1dfe303eb2e878d6c098b6a7a556c5e3`
**Git blob SHA-1（返却値）：** `da6c351383266b48a0359ab4e3e01ee7a30d47cc`
**参照箇所：** scientific_gates / counts / evidence_class / status
**根拠へのリンク：** [固定sourceを開く](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/fe55a0cb1dfe303eb2e878d6c098b6a7a556c5e3/artifacts/server_pf_spectral_information_pilot_d1_20260928_03747a2/decision.json)
**確認範囲：** 指定箇所の内容を取得・読解。数値計算・全manifest再hashは未実施。

<a id="S09"></a>
### S09｜D1解析実装：非対象clusterのtop-K

**Path：** `review_response/run_pf_spectral_information_pilot_d1.py`
**Commit：** `94ba9d6f71c1318ee03b85498e7a0b8b23abfd7a`
**Git blob SHA-1（返却値）：** `c8b33e0d548f4bd618c74c844fe23b67f9dd7273`
**参照箇所：** analyze_coordinate：non_targetの構成、weight_ranked、q_omit、2*q_omit/t
**根拠へのリンク：** [固定sourceを開く](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/94ba9d6f71c1318ee03b85498e7a0b8b23abfd7a/review_response/run_pf_spectral_information_pilot_d1.py)
**確認範囲：** 会話中に取得したanalyze_coordinateの関連範囲を参照。runnerは実行していない。

<a id="S10"></a>
### S10｜D2固定protocol

**Path：** `review_response/pf_spectral_recoverability_d2_protocol_draft.json`
**Commit：** `17e4d6357c7c5ef9bb849d0f787a642f972c7995`
**Git blob SHA-1（返却値）：** `a04e7f2eb381db0ae4dc5569021cf24755a378b3`
**参照箇所：** estimator / branch_rule / prediction_and_budget / resource_accounting / scoring / unresolved_specification_items
**根拠へのリンク：** [固定sourceを開く](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/17e4d6357c7c5ef9bb849d0f787a642f972c7995/review_response/pf_spectral_recoverability_d2_protocol_draft.json)
**確認範囲：** 会話中の取得済み関連範囲を参照。protocolの存在を新たな実行許可とは扱わない。

<a id="S11"></a>
### S11｜D2-A元scoring table

**Path：** `artifacts/server_pf_spectral_recoverability_d2_a_result_20260929_e2e8e5c/coordinate_scoring.csv`
**Commit：** `17e4d6357c7c5ef9bb849d0f787a642f972c7995`
**Git blob SHA-1（返却値）：** `c11e85b33c9ef3298440a27f2a5b6219e1126829`
**参照箇所：** 6座標のshift誤差／e_use／abstained／budget。branch_correctはS12で解釈を訂正。
**根拠へのリンク：** [固定sourceを開く](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/17e4d6357c7c5ef9bb849d0f787a642f972c7995/artifacts/server_pf_spectral_recoverability_d2_a_result_20260929_e2e8e5c/coordinate_scoring.csv)
**確認範囲：** 会話中に取得した6行の全文を参照。元CSVを変更せず、枝判定にはS12を併記。

<a id="S12"></a>
### S12｜D2-A read-only scoring audit decision

**Path：** `artifacts/pf_spectral_recoverability_d2_a_scoring_audit_20260929/decision.json`
**Commit：** `fe55a0cb1dfe303eb2e878d6c098b6a7a556c5e3`
**Git blob SHA-1（返却値）：** `31f37c386a586be8d3a8e428ccd9ac7c66dc4c09`
**参照箇所：** summary / classification / original_d2_a_status_unchanged / research_interpretation
**根拠へのリンク：** [固定sourceを開く](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/fe55a0cb1dfe303eb2e878d6c098b6a7a556c5e3/artifacts/pf_spectral_recoverability_d2_a_scoring_audit_20260929/decision.json)
**確認範囲：** 指定箇所の内容を取得・読解。数値計算・全manifest再hashは未実施。

<a id="S13"></a>
### S13｜C0 decision

**Path：** `artifacts/pf_post_d2a_width_design_readonly_20260929/decision.json`
**Commit：** `fe55a0cb1dfe303eb2e878d6c098b6a7a556c5e3`
**Git blob SHA-1（返却値）：** `6421fbe4d5242847a97ea6161e87dd6a31e35b88`
**参照箇所：** summary / unresolved_items / authorization / next_step
**根拠へのリンク：** [固定sourceを開く](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/fe55a0cb1dfe303eb2e878d6c098b6a7a556c5e3/artifacts/pf_post_d2a_width_design_readonly_20260929/decision.json)
**確認範囲：** 指定箇所の内容を取得・読解。数値計算・全manifest再hashは未実施。

<a id="S14"></a>
### S14｜C0保存scalar再集計

**Path：** `artifacts/pf_post_d2a_width_design_readonly_20260929/budget_headroom_and_widths.csv`
**Commit：** `fe55a0cb1dfe303eb2e878d6c098b6a7a556c5e3`
**Git blob SHA-1（返却値）：** `4b5a62d3aeb293029cca8500aa27276c8931f7e6`
**参照箇所：** 全6行：current_width／w_win_eta_0／S_max_same_time／numerical_action_bound_status
**根拠へのリンク：** [固定sourceを開く](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/fe55a0cb1dfe303eb2e878d6c098b6a7a556c5e3/artifacts/pf_post_d2a_width_design_readonly_20260929/budget_headroom_and_widths.csv)
**確認範囲：** 指定箇所の内容を取得・読解。数値計算・全manifest再hashは未実施。

<a id="S15"></a>
### S15｜C0 quantity・bound・access台帳

**Path：** `review_response/pf_post_d2a_width_design_assumptions.md`
**Commit：** `fe55a0cb1dfe303eb2e878d6c098b6a7a556c5e3`
**Git blob SHA-1（返却値）：** `ed924a55b6a571991dfb5cc13ce6fdb7b87637c8`
**参照箇所：** §1–5：定義／B1–B4／access／claim classes／resource-value。§6は既存文献照合の範囲。
**根拠へのリンク：** [固定sourceを開く](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/fe55a0cb1dfe303eb2e878d6c098b6a7a556c5e3/review_response/pf_post_d2a_width_design_assumptions.md)
**確認範囲：** 指定箇所の内容を取得・読解。数値計算・全manifest再hashは未実施。

<a id="S16"></a>
### S16｜データ使用履歴（9月25日時点）

**Path：** `docs/pf_data_use_ledger.md`
**Commit：** `fe55a0cb1dfe303eb2e878d6c098b6a7a556c5e3`
**Git blob SHA-1（返却値）：** `6c3202482f78e02a7e83d09efc5aa5bf1b901dab`
**参照箇所：** 判定区分／使用済み条件／2026-09-21固定ホールドアウト／独立性の境界
**根拠へのリンク：** [固定sourceを開く](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/fe55a0cb1dfe303eb2e878d6c098b6a7a556c5e3/docs/pf_data_use_ledger.md)
**確認範囲：** 全文を取得。HCl/LiFの後続利用はこの旧台帳だけでなくS06–S13を合わせて扱う。

<a id="S17"></a>
### S17｜D2-A prediction resource audit

**Path：** `artifacts/server_pf_spectral_recoverability_d2_a_prediction_20260929_e2e8e5c/resource_audit.json`
**Commit：** `17e4d6357c7c5ef9bb849d0f787a642f972c7995`
**Git blob SHA-1（返却値）：** `c418f0d6bdb18e68bf799d3373c3ae35f8b815e2`
**参照箇所：** coordinatesの作用会計／runtime_identity／wall_seconds
**根拠へのリンク：** [固定sourceを開く](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/17e4d6357c7c5ef9bb849d0f787a642f972c7995/artifacts/server_pf_spectral_recoverability_d2_a_prediction_20260929_e2e8e5c/resource_audit.json)
**確認範囲：** 会話中の取得済み完全本文を参照。計測・cache identityの独立再検証は未実施。

<a id="S18"></a>
### S18｜R0重複除去済み選択座標

**Path：** `artifacts/pf_candidate_validation_r0_20260928_05649f1/selected_coordinate_plan.csv`
**Commit：** `fe55a0cb1dfe303eb2e878d6c098b6a7a556c5e3`
**Git blob SHA-1（返却値）：** `d31200ef39d4422dd04187d1b1878d7375eef2ab`
**参照箇所：** 全10行：condition/time_hex/strategies/direct_truth_available
**根拠へのリンク：** [固定sourceを開く](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/fe55a0cb1dfe303eb2e878d6c098b6a7a556c5e3/artifacts/pf_candidate_validation_r0_20260928_05649f1/selected_coordinate_plan.csv)
**確認範囲：** 指定箇所の内容を取得・読解。数値計算・全manifest再hashは未実施。

<a id="S19"></a>
### S19｜D0局所予算・位相proxy診断

**Path：** `artifacts/pf_r1_readonly_design_summary_20260928/coordinate_budget_diagnostics.csv`
**Commit：** `94ba9d6f71c1318ee03b85498e7a0b8b23abfd7a`
**Git blob SHA-1（返却値）：** `d2f140526d0ffc33336089ab7359badec738a36e`
**参照箇所：** local_cisd_gamma_required／arg_minus_imag_hartree／signed_exact_direct_gap_hartree
**根拠へのリンク：** [固定sourceを開く](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/94ba9d6f71c1318ee03b85498e7a0b8b23abfd7a/artifacts/pf_r1_readonly_design_summary_20260928/coordinate_budget_diagnostics.csv)
**確認範囲：** 会話中の取得済み全10行を参照。倍率は将来の安全保証として使わない。
