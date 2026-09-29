# PF研究成果整理レポート
## 性能比較から、有限時間校正の信頼性と資源判断へ

**整理日：2026年9月29日｜版：v1.0（Git evidence audit済み内部成果整理版）**
**研究結果の参照snapshot：`fe55a0cb1dfe303eb2e878d6c098b6a7a556c5e3`**
**目的：成果・限界・研究のつながりを保存する。投稿論文原稿や新規実験protocolではない。**

このレポートは、公開H-chain研究と、その後の第一研究、第二研究、R0/R1、D1、D2-A、scoring audit、C0を整理したものである。数値は保存成果物に記録された値を採用し、今回、新しい分子計算・PF作用・Arnoldi計算・gap取得・モデル調整は行っていない。保存結果の読解と、全manifestの再hash・独立再実行は別であり、後者は実施済みと主張しない。

本文の［S番号］は「主張・証拠台帳」の固定sourceへつながる。CL番号は同台帳の主張IDである。末尾の将来方針は、結果からの**研究判断**として記載し、実証済みの成果とは分ける。

---

## 要旨

本研究系列は、分子基底状態エネルギー推定におけるproduct formula（PF）の資源性能を出発点として、その性能を有限時間の校正情報からどこまで信頼して利用できるかを調べてきた。中心にあるのは、PFの形式次数や先頭誤差係数だけでなく、状態近似、proxy、model fit、許容時刻域、QPEへの誤差配分を含めた資源判断である。

第一研究では、校正誤差の三分解と資源費用の因子分解を行った。固定case集合で状態置換誤差が支配する場合が多かった一方、安全な凍結予算でも低コストとは限らなかった。N₂/CO/HFのdevelopment 6条件では1%余裕付き予算が全条件で目標を満たしたが、HFの費用は元2 PF・保存grid基準の約2.15倍、2.10倍だった。状態感度を用いた追加診断も、固定比較で資源改善を示さなかった。[S02](PF_research_claim_evidence_ledger_20260929.md#S02)[S03](PF_research_claim_evidence_ledger_20260929.md#S03)[S04](PF_research_claim_evidence_ledger_20260929.md#S04)

第二研究のmultiple-window方式は、独立4条件の事前固定評価でbenefit条件を満たさず終了した。R1の事後原因分離を経て、D1ではHClのスペクトル寄与が少数の非対象clusterへ圧縮できること、D2-Aでは近似状態からの有限作用回数で目的shiftと高精度に一致する点推定を得られることが確認された。ただし、後者の枝判定は座標系の不一致を監査して解釈を訂正したものであり、独立な一般化や運用上の枝認証ではない。また、付与した経験的幅では予算優位を得られなかった。[S05](PF_research_claim_evidence_ledger_20260929.md#S05)[S06](PF_research_claim_evidence_ledger_20260929.md#S06)[S08](PF_research_claim_evidence_ledger_20260929.md#S08)[S12](PF_research_claim_evidence_ledger_20260929.md#S12)

C0は、必要な分離情報を明示した条件付きboundと資源価値の定義を整理した。現行幅は6点すべてでbaseline同等に必要な幅より大きいが、同じ時刻の校正を完全にしても改善余地は約0.33〜2.29%に限られる。したがって、ここまでの総合的な知見は、**誤差の小ささ、情報の圧縮可能性、取得可能性、誤差幅の妥当性、資源価値を同一視しないこと**である。[S13](PF_research_claim_evidence_ledger_20260929.md#S13)[S14](PF_research_claim_evidence_ledger_20260929.md#S14)

## 1．研究全体の問い

### 1.1 性能・信頼性・情報費用を分ける

研究全体は三つの問いに整理できる。第一は「どのPFが指定した精度で低コストか」、第二は「その費用予測を有限の情報からどこまで信頼できるか」、第三は「予測を改善するために追加の古典計算を行う価値があるか」である。これは既存成果をつなぐための編集上の整理であり、三つ全てを既に解決したという主張ではない。

対象となる最終判断は、PF、時刻、量子予算の組合せである。PFの先頭係数を小さくすることやfit residualを小さくすることは、その判断を改善するための手段であり、最終目的そのものではない。第一研究の固定主張台帳も、この資源判断を中心に据えている。[S02](PF_research_claim_evidence_ledger_20260929.md#S02)

### 1.2 stage名と成果単位

本書で「第一研究」と呼ぶのは、この会話・リポジトリにおける有限時間校正の研究であり、先行する公開H-chain研究とは分ける。また、R1やD1をそれぞれ独立した論文と見なすのではなく、後続の問いを絞るためのstageとして扱う。

| 層 | 研究上の役割 | 主な証拠の性質 |
|---|---|---|
| 公開H-chain研究 | PFの性能比較 | 公開プレプリントに報告されたbenchmark |
| 第一研究 | 校正誤差と資源損失の分離 | 固定機構実験、development評価、保存結果再解析 |
| 第二研究 | 時間域拡張方式の評価 | 当時の独立4条件による事前固定評価 |
| R0/R1 | 第二研究の原因診断 | 結果確認後のdevelopment解析 |
| D1 | スペクトル情報の圧縮診断 | exact-groundと全スペクトルを使った事後診断 |
| D2-A＋audit | 有限作用回数での取得と採点定義の確認 | development prototypeと手続き監査 |
| C0 | 条件付き幅・必要情報・利益上限の整理 | 数理設計と保存scalarの事後算術 |

出典：S01–S16。各行の独立性は、その時点で固定された問いに対してのものである。

## 2．用語・評価量・主張範囲

### 2.1 固有値シフトと絶対誤差

後続のspectral解析では、リポジトリの規約に合わせて \(U_P(t)\approx e^{+iHt}\) を使う。目的枝のエネルギーを \(\widetilde E_{0,P}(t)\)、元のHamiltonianの基底エネルギーを \(E_0\) とし、

\[
\delta_P(t)=\widetilde E_{0,P}(t)-E_0,
\qquad e_P(t)=|\delta_P(t)|
\]

を区別する。前者はsigned shift、後者は未補正QPE予算に入るPF誤差である。旧文書には`e_direct`をsigned量として用いた箇所もあるため、本書では上記の記号に統一して説明するが、元artifactのfieldは変更しない。[S10](PF_research_claim_evidence_ledger_20260929.md#S10)[S15](PF_research_claim_evidence_ledger_20260929.md#S15)

### 2.2 凍結予算と事後必要費用

後続研究のcontinuous Pauli-rotation cost proxyでは、\(t>0\)、\(e_P(t)<\epsilon_E\) のもとで、

\[
C_{\rm req}(P,t)=
\frac{\beta K_P}{t[\epsilon_E-e_P(t)]}
\]

が、その時刻で参照誤差を知った場合の必要費用である。一方、運用側は予測値 \(\widehat e\) や幅込みの \(e_{\rm use}\) を使って、truthを見る前に予算 \(B\) を固定する。目標達成の採点は、

\[
e_P(t)+\frac{\beta K_P}{tB}\le\epsilon_E
\]

で行う。第二研究以降の比較では \(\beta=1.2\)、\(\epsilon_E=1.5936001019904\times10^{-4}\) Haを用いる。\(\gamma\) はstageごとに異なるため、全結果へ一つの倍率を適用しない。[S03](PF_research_claim_evidence_ledger_20260929.md#S03)[S10](PF_research_claim_evidence_ledger_20260929.md#S10)[S15](PF_research_claim_evidence_ledger_20260929.md#S15)

本書の「safe」「安全」は、このモデル上の目標誤差条件を指す。実機の故障率、QPEの全成功確率、状態準備費用、routing、magic-state factoryを含むend-to-end runtimeを保証する言葉ではない。公開H-chain研究と後続研究の絶対費用を、定数・対象・精度を照合せず合算しない。[S01](PF_research_claim_evidence_ledger_20260929.md#S01)[S02](PF_research_claim_evidence_ledger_20260929.md#S02)

また、\(K_P\) は一PF stepの回転数、\(K_{\rm D1}\) は保持する非対象cluster数、\(m\) はArnoldi次元であり、相互に置き換えない。[S09](PF_research_claim_evidence_ledger_20260929.md#S09)[S15](PF_research_claim_evidence_ledger_20260929.md#S15)

### 2.3 証拠の強さ

「固定した方法が評価集合で目標を満たしたこと」「仮定の下で数学的上界が成立すること」「将来の方法として有望であること」は別である。C0の区分に合わせ、conditional certificate、empirically validated width、heuristic width、indeterminateを分ける。条件を満たさないcertificateを、説明なしに小さい経験幅へ置き換えない。[S15](PF_research_claim_evidence_ledger_20260929.md#S15)

独立評価にも時間的な境界がある。第二研究で独立だったHCl/LiFは、その結果をR1以降の方法設計に使う時点からdevelopmentとなる。過去の独立性を消さず、将来の独立性にも転用しない。[S05](PF_research_claim_evidence_ledger_20260929.md#S05)[S06](PF_research_claim_evidence_ledger_20260929.md#S06)[S07](PF_research_claim_evidence_ledger_20260929.md#S07)[S16](PF_research_claim_evidence_ledger_20260929.md#S16)

## 3．出発点：高次PFの性能比較

公開プレプリント *Evaluating higher-order product formulae for molecular ground-state energy estimation* は、H₂〜H₁₅をbenchmarkとし、摂動的な固有値誤差推定を用いて総ゲート数と \(R_Z\)-rotation layer depthを比較している。Abstractでは、既存比較候補中のMorales 8次式の優位、10次化が必ずしも低コスト化にならないこと、新4次式のゲート数上の改善が報告されている。[S01](PF_research_claim_evidence_ledger_20260929.md#S01)

この結果は、形式次数・誤差係数・一step費用を合わせてPFを選ぶ出発点である。本整理では原稿を**公開プレプリント**として扱い、査読出版済みとは記さない。また、原稿中の新4次式と後続コードの`current_m3`等の係数同一性は、今回照合していないため同一とは断定しない。後続の校正研究は、この性能比較と関連するが、対象分子・情報条件・費用定義の異なる結果として記載する。（CL01）


後続のN₂/COの固定PF・モデル比較では、凍結内殻CAS(10e,8o)の4条件で、Yoshida 4次＋二項、`current_m3`＋二項、`two_term_center`＋二項、Yoshida 6次＋三項が4/4合格し、合格PF中では`current_m3`が低費用だったと使用履歴に記録されている。ただし、この段階は各Hamiltonianの直接固有値点を使う**oracle-assisted target calibration**であり、未知分子に対する安価な予測法の完成ではない。後に同じ分子を方法設計へ使ったため、その後のselectorに対するholdoutとも見なさない。（CL02）[S16](PF_research_claim_evidence_ledger_20260929.md#S16)

## 4．第一研究：有限時間校正の信頼性と資源損失

### 4.1 校正誤差を三つの段階へ分ける

対称4次PFの有限時間モデルとして、符号付き二項モデル

\[
f_P(t)=a_4t^4+a_6t^6
\]

を用いる。近似状態によるproxyを \(g_{\psi,P}\)、exact groundによる同じproxyを \(g_{0,P}\)、直接PF固有枝のshiftを \(\delta_P\) とすると、

\[
f_P-\delta_P
=
\underbrace{f_P-g_{\psi,P}}_{\text{model / extrapolation}}
+
\underbrace{g_{\psi,P}-g_{0,P}}_{\text{state substitution}}
+
\underbrace{g_{0,P}-\delta_P}_{\text{proxy--eigenvalue}}.
\]

この恒等式によって、fitを改善すべきなのか、状態を改善すべきなのか、proxy自体を変える必要があるのかを区別できる。恒等式が成り立つことと、特定成分が実際に支配することは別の結果である。[S04](PF_research_claim_evidence_ledger_20260929.md#S04)[S07](PF_research_claim_evidence_ledger_20260929.md#S07)

### 4.2 機構実験で観測された状態置換誤差の支配

固定したH4と人工二準位系の128 caseでは、79 caseが状態置換誤差支配、49 caseがmixedであった。H4の56 caseでは49 case、二準位系の72 caseでは30 caseが状態置換支配だった。第一研究のdominanceは、同一caseのresolved点の過半数で、一成分が他の各成分の3倍以上となるという規則に基づく。R1の2倍規則とは異なる。[S04](PF_research_claim_evidence_ledger_20260929.md#S04)

ここでの成果は、状態の近似が有限時間校正の独立した誤差軸になることを、同じ \(H,P,t\) で切り分けた点にある。一方、「分子一般で状態誤差が支配する」「stateを直せば全問題が解決する」とは結論しない。（CL03–CL04）

H4の凍結selectorはこの実験では`m5_best`を選び、1%余裕付き予算で目標を満たしたが、joint regretは約64.51%、凍結予算はdirect grid基準より約98.35%大きかった。これは後述するN₂/CO/HFの6条件を採点したS0とは別の結果である。機構実験での安全性も、資源効率の十分条件ではなかった。[S04](PF_research_claim_evidence_ledger_20260929.md#S04)

### 4.3 development 6条件：安全性と効率の分離

第一研究のS0では、既存predictionを固定したまま実際の選択時刻で採点した。N₂/COの凍結内殻active-space 4条件とHF全電子2条件の全6条件で、\(\gamma=1.01\) の予算が目標を満たした。\(\gamma=1.0\) ではHF平衡のみ未達だった。ただし、これらは既に方法選択に使用したdevelopment条件であり、独立な分子transfer評価ではない。[S03](PF_research_claim_evidence_ledger_20260929.md#S03)[S04](PF_research_claim_evidence_ledger_20260929.md#S04)

completion analysisの保存表を以下に示す。\(F_t\) は選択したPF内の時刻損失、\(F_P\) は元2 PF・保存gridでのPF選択因子、\(F_{\rm total}\) は凍結予算の総費用因子である。

| 条件 | 保存 \(F_t\) | \(F_P\) | \(F_{\rm total}\) | 支配的な費用要因 |
|---|---:|---:|---:|---|
| N₂平衡 | 1.021338 | 1.000000 | 1.100631 | calibration / budget |
| N₂伸長 | 1.227600 | 1.000000 | 1.423985 | time selection |
| CO平衡 | 1.031843 | 1.000000 | 1.120734 | calibration / budget |
| CO伸長 | 1.071820 | 1.000000 | 1.193383 | calibration / budget |
| HF平衡 | 2.141534 | 1.000000 | 2.150313 | capによるdomain制約 |
| HF伸長 | 2.076361 | 1.000000 | 2.102857 | capによるdomain制約 |

出典：S03「条件別の費用会計」。N₂/COは保存grid会計、HFのdomain/within分離は境界点からの上下界であり、同じ精度の連続時間oracle評価ではない。（CL06–CL08）

全6条件で \(F_P=1\) だったことは、その元2 PF集合における選択損失が0であったことを意味する。候補集合外にさらに良いPFが存在しないことや、新PF設計一般が不要であることは意味しない。

### 4.4 HFの費用は、cap内の微調整では大きく減らない

completion analysisは、HFのfallback上限点について、

\[
F_{\rm within}\le1.012709,\quad F_{\rm domain}\ge2.114659
\]

（平衡）、

\[
F_{\rm within}\le1.003236,\quad F_{\rm domain}\ge2.069664
\]

（伸長）という上下界を示した。cap内で削減可能な費用は最大でも約1.254948%、0.322572%である。[S03](PF_research_claim_evidence_ledger_20260929.md#S03)

したがって、このHFの大きな費用損失に対し、cap内の最適化精度だけを上げる余地は小さい。これは時間域を利用可能と判断する情報が重要になる根拠である。ただし、cap外が安全であることや、連続時間の大域最適点が確定したことは示していない。（CL08）

### 4.5 誤差を減らすことと、資源損失を減らすこと

第一研究では、

\[
F_{\rm total}
=F_{\rm model}F_{\rm margin}F_{\rm within}F_{\rm domain}F_P
\]

として費用を分けた。同一時刻で \(\widehat e=e+b\) と置くと、

\[
F_{\rm model}
=\frac{\epsilon_E-e}{\epsilon_E-e-b}
=\frac{1}{1-b/(\epsilon_E-e)}
\]

である。資源への影響は、誤差そのものに対する相対biasだけでなく、残余予算 \(\epsilon_E-e\) に対するbiasで決まる。従って、同じ絶対biasでも選択時刻によって重要度は異なる。[S02](PF_research_claim_evidence_ledger_20260929.md#S02)

この関係は費用式の恒等的な整理であり、新たな最適化アルゴリズムの成功証拠ではない。それでも、何を高精度化する価値があるかを判断する尺度になる。（CL09）

### 4.6 S4：risk検出が資源改善につながらなかった

operator-sensitiveな二状態診断とfallbackを固定して比較したS4では、riskを検出してもbaselineより資源効率を改善せず、`no_benefit`が維持された。第一研究全体を「成果なし」とするのではなく、機構・資源分解の成果と、改善法のnegative resultを分けて残す。[S02](PF_research_claim_evidence_ledger_20260929.md#S02)[S03](PF_research_claim_evidence_ledger_20260929.md#S03)

S4の保存scoringには \(\beta=0.105\)、practical/S0とdirect費用には \(\beta=1.2\) が使われていた。completion analysisで1.2へ統一したところ、42/42の精度条件は維持され、成否変更は0、資源改善なしという結論も不変だった。元S4の絶対phase-errorやenergy-marginをそのまま引用せず、統一監査値を優先する。この訂正は、新しいselectorの独立評価ではない。（CL10–CL11）

## 5．第二研究：multiple-windowによる時間域拡張

### 5.1 問いと比較設計

第一研究で見えた許容時刻域の制約を受け、`current_m3`を固定し、近似状態proxyのmultiple-window consistencyを使って時間域を拡張できるかを検証した。LiFとHClの平衡・1.5倍伸長の4条件について、predictionを凍結してからdirect truthを開く一回の独立評価である。結果後のthreshold、候補時刻、PFの調整は行っていないと完了報告に記録されている。[S05](PF_research_claim_evidence_ledger_20260929.md#S05)[S18](PF_research_claim_evidence_ledger_20260929.md#S18)

### 5.2 成績

| strategy | 目標達成条件数 | aggregate frozen budget | mean selection regret | max selection regret |
|---|---:|---:|---:|---:|
| current fallback | 2/4 | 11,721,643,230.73 | 0.915322 | 2.289789 |
| equal-information | 2/4 | 8,359,846,080.46 | 0.487379 | 1.036689 |
| multiple-window | 3/4 | 10,471,889,449.41 | 0.714556 | 1.486727 |
| uncapped counterfactual | 3/4 | 8,689,143,504.85 | 0.387317 | 1.036689 |

出典：S05「主結果」。regret欄は保存値の無次元比であり、百分率表示ではない。aggregate budgetは全条件の凍結値の和で、unsafe条件も含むため「同じ精度を達成する方法の費用比較」として単独で順位付けしない。uncapped counterfactualは診断専用である。

multiple-windowはcurrent fallback比でaggregate budgetを0.8933806671倍にしたが、equal-information比では1.2526414181倍だった。coverage、拡張件数、同一情報会計等の一部条件を満たす一方、unsafe 0やregret条件を満たさず、正式結果は`complete_no_benefit`である。（CL12）[S05](PF_research_claim_evidence_ledger_20260929.md#S05)

### 5.3 何が否定され、何が否定されていないか

否定されたのは、この固定規則が事前のbenefit条件を満たすという期待である。時間域拡張や複数窓情報一般の無効性ではない。

また、元のfallback自身も4条件中2条件で目標未達だった。R0/R1を見ると、LiF平衡ではmultiple-windowも元の通常選択を継承し、HCl平衡では0.65 \(t_{\rm ana}\) へ拡張して目標を満たしている。HCl伸長ではmultiple-windowが0.5へ戻った一方、equal-informationは0.65を選び未達だった。従って「拡張したために唯一の失敗が起きた」という要約は不正確である。[S06](PF_research_claim_evidence_ledger_20260929.md#S06)[S18](PF_research_claim_evidence_ledger_20260929.md#S18)

この結果を受け、次の問いは、単にcapを緩めることから、実際の選択点でどの誤差が重要だったかへ移った。（CL13）

## 6．R0/R1：同じ選択点での事後原因分離

### 6.1 対象と独立性

R0は4条件×4strategyの16行を、重複除去後10座標へまとめた。R1はこの既存10座標で、CISD proxy、exact-state proxy、保存direct shiftを比較した。新規direct truthは0、既存CISD proxyの再利用5、不足座標の新CISD proxy5、新exact-state proxy10と記録されている。[S06](PF_research_claim_evidence_ledger_20260929.md#S06)[S18](PF_research_claim_evidence_ledger_20260929.md#S18)

R1は第二研究の結果を見た後のdevelopment診断であり、第二研究の判定を再評価した独立試験ではない。16行は10座標を共有し、さらに4条件に属するため、16件の独立な成功・失敗例とは数えない。（CL14）

### 6.2 条件ごとに異なる誤差構造

| 条件 | 保存結果で見えた主要構造 | 資源判断上の解釈 | 限定 |
|---|---|---|---|
| LiF平衡 | model支配。state成分もmaterial | 局所観測でmodel誤差を除いてもCISD biasが残る | modelだけを直せば安全とは言えない |
| LiF伸長 | 4strategyでstate支配 | 元の予算は4行ともsafe | 大きな成分を「失敗原因」と呼ばない |
| HCl平衡 | currentはmixed、0.65のmultiple-windowはsafe | modelとproxy差を区別する必要 | 符号不一致だけで危険と決めない |
| HCl伸長 | equal-informationの0.65ではproxy–eigenvalue支配 | exact-stateへ置換しても当該予算は未達 | state精度だけでは解消しない |

出典：S06。R1の規則は、元予算のallowed underestimationを超えることをmaterialとし、最大成分が次成分の2倍以上なら単独支配とする。第一研究の3倍規則と集計母集団が異なる。[S07](PF_research_claim_evidence_ledger_20260929.md#S07)

16strategy行の分類はmodel 6、state 4、proxy–eigenvalue 2、mixed/none 4だった。これらの件数を、どの手法を優先すべきかの単純な頻度推定には使わない。（CL15）

### 6.3 局所proxyへの置換counterfactual

既存時刻を固定し、予算に使う誤差だけをlocal CISD proxyへ置換すると11/16、exact-state proxyへ置換すると15/16が目標を満たすcounterfactualだった。exactでも残る1行はHCl伸長equal-informationである。[S06](PF_research_claim_evidence_ledger_20260929.md#S06)[S07](PF_research_claim_evidence_ledger_20260929.md#S07)

これは「局所CISD法の成功率が11/16」と実証した独立結果ではない。目的は、時刻を固定したまま情報の一部を理想化した場合に、どの誤差が残るかを調べることである。（CL16）

D0の保存算術では、local CISDを使う場合の必要倍率の最大が10座標全体で1.0981387383、HClの問題点では1.0166546542だった。ただし、これらはtruthを見て計算した値である。1.10や1.02を将来の分子へ一般的に安全な倍率として転用しない。高度な校正法が、単純な予算増額に対して何を得るべきかを考える比較材料として残す。（CL17）[S19](PF_research_claim_evidence_ledger_20260929.md#S19)

## 7．D1：echoと固有値の差をスペクトルから説明する

### 7.1 HClの役割

R1のHClでは、CISDとexact groundの重なりが報告精度でほぼ1で、状態残差もLiFより小さかった。D1はそのHClの既存6座標を使い、state substitutionの影響をほぼ除いてproxy–eigenvalue差を調べた機構対照と位置付ける。一般分子でCISDが常に十分という実証にはしない。[S06](PF_research_claim_evidence_ledger_20260929.md#S06)[S08](PF_research_claim_evidence_ledger_20260929.md#S08)

このHClを説明する際も、「CISD=FCI」を無条件に短縮表現しない。spin adaptation、対象sector、solver収束、全spin sectorのground認定は別の条件である。（CL18）[S07](PF_research_claim_evidence_ledger_20260929.md#S07)

### 7.2 exact-ground echoの分解

\(U_P|u_j\rangle=e^{it\widetilde E_j}|u_j\rangle\)、\(p_j=|\langle u_j|0\rangle|^2\) とすると、D1で扱うechoは、

\[
z_0(t)=\langle0|e^{-iHt}U_P(t)|0\rangle
=\sum_j p_j e^{it(\widetilde E_j-E_0)}.
\]

\(g_0=\operatorname{Im}z_0/t\) と目的shift \(\delta_0\) の差には、対象位相のsin非線形性と非対象成分の寄与が含まれる。D1はこの関係を全スペクトルから再構成し、cluster単位で寄与を調べた。[S09](PF_research_claim_evidence_ledger_20260929.md#S09)

重みの小さい非対象成分でも、評価対象のshift自体が小さい場合には無視できない。R1のHCl伸長0.65では、exact proxyとdirect shiftのsigned gapは約 \(-7.42\times10^{-6}\) Haで、Imをargへ変更した差は約 \(5.81\times10^{-13}\) Haにとどまった。従って、この点の差を単なるIm/arg変換だけで説明することはできない。[S19](PF_research_claim_evidence_ledger_20260929.md#S19)

### 7.3 圧縮できた情報と、まだ取得していない情報

D1では全6座標で、weight-rankedの非対象clusterを最大4個保持すればactual omissionとconservative omissionのgateを満たした。省略上界は \(2q_{\rm omit}/t\) である。oracle寄与順でも \(K\le8\) のactual compression条件を満たした。[S08](PF_research_claim_evidence_ledger_20260929.md#S08)[S09](PF_research_claim_evidence_ledger_20260929.md#S09)

ここで \(K\le4\) は**目的clusterを除いた保持数**であり、全スペクトルの次元でも、Arnoldi次元でも、PF作用回数でもない。weight順という名前でも、D1ではexact-ground由来の重みを全スペクトルから取得しているため、truth-freeな情報取得法ではない。（CL19–CL20）

D1の肯定的結果は、必要な寄与が少数成分に集中する事例を得たことである。これを実運用で取得できるか、未取得重みをどう認定するかは次段階の問いとして残った。

## 8．D2-Aとscoring audit：回収精度と資源優位の分離

### 8.1 有限作用回数による点推定

D2-Aでは、元CISD状態からexplicit-vectorの二重再直交化unitary Arnoldiを使い、共通部分空間へ \(U_P(t)\) と \(H\) を射影した。最大次元8、1座標あたりPF作用8回・H作用8回を上限とし、全PF行列の構築や全Hamiltonianの対角化をpredictorに許さない設計である。predictionをfreezeした後にscorerが既存truthを開く境界を置いた。[S10](PF_research_claim_evidence_ledger_20260929.md#S10)[S17](PF_research_claim_evidence_ledger_20260929.md#S17)

truth-freeなのはこの**predictorの入力**であり、研究全体の採点にtruthを使っていないという意味ではない。またHClは既使用のdevelopmentデータである。（CL21）

### 8.2 旧branch判定と監査後の解釈

元のscorerは、D2-Aの「絶対PF energyをH-Ritz参照へunwrapする整数」と、D1の「exact-ground phase除去後のshiftをunwrapする整数」を直接比較していた。その結果、元artifactのbranch正解数は0/6になった。

read-only scoring auditは、この座標系不一致を確認した。表現不変なhalf-phase-gap基準では全6点で目的shiftと整合し、最大誤差は \(1.3825298286693\times10^{-8}\) Ha、最大誤差／half-gap比は \(1.1629586816034\times10^{-7}\) だった。[S12](PF_research_claim_evidence_ledger_20260929.md#S12)

本書は、旧`d2_a_complete_close_spectral_route_stop`を履歴として記録する一方、旧0/6を物理的な回収失敗とは解釈しない。監査の6/6も、truthを用いた採点規則上の一致であり、運用時にfull-spaceの目的枝を認証したという結果ではない。（CL22–CL23）

### 8.3 高精度でも、経験的幅では低予算にならなかった

| 条件 | \(t/t_{\rm ana}\) | 点推定誤差 [Ha] | 保存幅 [Ha] | 凍結予算の結果 |
|---|---:|---:|---:|---|
| HCl平衡 | 0.50 | 1.38253×10⁻⁸ | 3.49721×10⁻⁴ | 棄却 |
| HCl平衡 | 0.65 | 2.94810×10⁻¹² | 7.51149×10⁻⁶ | 目標達成、主baselineより高費用 |
| HCl平衡 | 0.80 | 6.81441×10⁻¹² | 4.31424×10⁻⁶ | 目標達成、主baselineより高費用 |
| HCl伸長 | 0.50 | 3.80922×10⁻¹³ | 3.56970×10⁻⁶ | 目標達成、主baselineより高費用 |
| HCl伸長 | 0.65 | 6.56005×10⁻¹⁰ | 5.61366×10⁻⁵ | 目標達成、主baselineより高費用 |
| HCl伸長 | 0.80 | 5.65040×10⁻¹⁰ | 1.25812×10⁻⁴ | 目標達成、主baselineより高費用 |

出典：S11・S14。表の幅はC0 CSVの`current_width_hartree`。新方式で再推定した値ではない。

D2-Aでは、\(r_H\)、PFの残差位相幅、prefix差等から経験的幅を作り、\(e_{\rm use}=|\widehat\delta|+w\) として予算化した。全6点で幅を決定していたのはlocal residual widthだった。棄却1/6、残り5/5は目標達成、主baselineより低予算は0/6である。[S10](PF_research_claim_evidence_ledger_20260929.md#S10)[S12](PF_research_claim_evidence_ledger_20260929.md#S12)[S14](PF_research_claim_evidence_ledger_20260929.md#S14)

この結果は「厳密certificateが本質的に高価」という証明ではない。ground/referenceとrigorous action errorは未認定であり、実装の幅は経験的なものだからである。ここで確認したのは、**点推定が高精度であることと、その点推定を小さい安全側予算へ変換できることの違い**である。（CL24）

### 8.4 古典費用について言える範囲

保存resource auditでは6座標合計PF作用48回、H作用48回、predictor wall time約2.62秒、peak CPU RSS 454,656 KiBだった。ただし、元の状態・Hamiltonian・group spectraを含むcacheを再利用している。これは小さなHCl系での当該runの費用であり、前処理を含む大規模問題の総校正費用ではない。[S17](PF_research_claim_evidence_ledger_20260929.md#S17)

PF per-vector action、Python call、component gate materialization、sparse multiply、H matvec、H exponential actionは別に数える。量子測定のshot数や実機時間への優位性は、今回のclassical explicit-vector計算からは示していない。（CL25）

## 9．C0：使える誤差幅に必要な情報と、改善余地

### 9.1 条件付きboundを仕様化した

C0は新規数値実験ではなく、既存推定器を固定した設計・保存scalar再集計である。normal作用素 \(A\)、正規化ベクトル \(y\)、

\[
\rho=y^\dagger Ay,\qquad r=\|(A-\rho)y\|
\]

に対し、対象固有値の同定、元作用素に対する残差、非対象スペクトルの分離下界 \(g>r\) が与えられる場合に、

\[
|\lambda_0-\rho|
\le\frac{r^2}{g(1-r^2/g^2)}
\]

という条件付き候補を整理した。[S15](PF_research_claim_evidence_ledger_20260929.md#S15)

必要なのは \(g_{\rho,\mathrm{others}}=\min_{j\ne0}|\lambda_j-\rho|\) の有効な下界であり、\(g_{\rm target}=\min_{j\ne0}|\lambda_j-\lambda_0|\) と同じではない。projected Ritz gapをfull-space下界として使えない。元のnormal作用素に対するRayleigh residualと、unit-circleへ投影した値に対する残差も混同しない。

chordからprincipal phaseへの変換には、\(\rho=a e^{i\phi}\)、\(a>0\)、\(|1-a|\le d<1+a\) の条件の下で

\[
\alpha_{\max}=\arccos\frac{1+a^2-d^2}{2a}
\]

を使い、丸め処理とphysical phase liftを別条件にした。条件不足ならindeterminateとする。この設計を、新たな普遍的認証法や先行研究にない定理の確立とは呼ばない。（CL26）[S15](PF_research_claim_evidence_ledger_20260929.md#S15)

### 9.2 operationalな認証は未達

C0では、truth-freeなfull-space分離下界、ground/reference certificate、branch/alias certificate、rigorous forward-error boundの取得経路は未確立である。保存式の明示的numerical action boundが0でも、作用誤差が厳密に0だと認証したことにはならない。[S13](PF_research_claim_evidence_ledger_20260929.md#S13)[S14](PF_research_claim_evidence_ledger_20260929.md#S14)[S15](PF_research_claim_evidence_ledger_20260929.md#S15)

これは「認証が不可能」という結果ではなく、現在の情報契約で不足する入力を明らかにした設計結果である。C1は未承認であり、D2-B、LiF、新gap取得、toy数値実験へ進んだことにはしない。（CL27）

### 9.3 同じ時刻では、完全校正しても利益が小さい

同時刻のlocal CISD＋\(\gamma=1.02\) の予算を \(B_0(t)\) とし、

\[
S_{\max}(t)=1-\frac{C_{\rm req}(t)}{B_0(t)}
\]

を、未補正タスクで完全校正した場合の最大削減率とする。C0の保存算術は次の通りである。

| 条件 | \(t/t_{\rm ana}\) | 完全校正時の最大削減率 | 現行幅／baseline同等に必要な幅 |
|---|---:|---:|---:|
| HCl平衡 | 0.50 | 1.326867% | 167.4915 |
| HCl平衡 | 0.65 | 1.903762% | 2.4803 |
| HCl平衡 | 0.80 | 2.286462% | 1.1956 |
| HCl伸長 | 0.50 | 2.032779% | 1.1062 |
| HCl伸長 | 0.65 | 0.327975% | 111.0242 |
| HCl伸長 | 0.80 | 2.036368% | 39.8584 |

出典：S14。百分率は保存fractionの表示変換のみ。新方式の改善成績ではない。（CL28）

さらに、\(\eta\) の予算削減を狙う幅の必要条件は、

\[
w\le w_{\rm win}(t;\eta)
=\epsilon_E-|\widehat\delta|
-\frac{\beta K_P}{t(1-\eta)B_0}.
\]

現行幅は全6点で \(w_{\rm win}(t;0)\) より大きかった。[S14](PF_research_claim_evidence_ledger_20260929.md#S14)[S15](PF_research_claim_evidence_ledger_20260929.md#S15)

重要なのは、「幅を縮めれば大きい利益が出る」とは限らない点である。現行HCl固定時刻での利益上限は小さい。しかし、これはHFのcap外に関する結果でも、別時刻・別PF・bias補正を含む上限でもない。第一研究のHFで得た約2倍の費用損失と、同じ対象・baselineの数値として混ぜない。（CL28）

## 10．研究系列から得られた知見

### 10.1 四つの段階を区別する

ここまでの結果は、次の四段階を分ける必要を示す。

**情報の圧縮可能性**：全情報を知った後、少数の成分で説明できるか。D1はこの例を与えた。

**有限費用での取得可能性**：実際に許した状態・作用から必要な値を得られるか。D2-Aは特殊なHCl development条件で肯定的な点推定結果を与えた。

**値に付ける幅の妥当性**：目的枝・参照・数値精度を含めて、どこまで誤差を抑えたといえるか。ここは現在も条件付きである。

**資源判断での価値**：追加情報によって同じ仕事の予算が改善するか。D2-Aの現行構成では優位を得ず、C0は同時刻の利益上限も小さいことを明示した。

これは既存結果をつないだ限定的な解釈であり、全PFや全分子に対する不可能性定理ではない。（CL29）[S08](PF_research_claim_evidence_ledger_20260929.md#S08)[S12](PF_research_claim_evidence_ledger_20260929.md#S12)[S13](PF_research_claim_evidence_ledger_20260929.md#S13)

### 10.2 大きな誤差成分、危険な過小評価、資源損失は異なる

signedな分解成分が大きくても、絶対誤差として過大評価なら予算は安全側になり得る。逆に、小さな過小評価でも残余予算が小さければ未達になり得る。R1のLiF伸長とHClの条件差は、この区別が必要な実例である。[S06](PF_research_claim_evidence_ledger_20260929.md#S06)[S07](PF_research_claim_evidence_ledger_20260929.md#S07)

今後の説明では、因果分類の大きさだけでなく、符号、予算に使ったguarded error、allowed underestimation、実際のmarginを併記する。

### 10.3 negative resultの範囲を限定する

S4、第二研究、D2-Aはそれぞれ別の固定方式を評価している。それらのno-benefitや費用優位なしを一括して「PF研究が失敗」とは解釈しない。同様に、D2-Aの高精度点推定を根拠に、未確認のスケーラブルな認証法が完成したとも言わない。

履歴上のstatusを残すことと、後から定義不一致が判明した物理解釈を訂正することは両立する。重要なのは、どの主張にどの版のevidenceを使っているかを明示することである。

## 11．現在までに達成していないこと

本書は次を未達・未確認として残す。未知分子に対する低regret selectorの一般化、1%または2%等の普遍的な安全倍率、truth-freeなfull-space gap認証、近似状態の質が落ちる場合のArnoldi transfer、rigorous action-error certificate、実機全体のruntime優位、新PFの必要性とその設計成果である。[S02](PF_research_claim_evidence_ledger_20260929.md#S02)[S10](PF_research_claim_evidence_ledger_20260929.md#S10)[S13](PF_research_claim_evidence_ledger_20260929.md#S13)[S15](PF_research_claim_evidence_ledger_20260929.md#S15)

HCl6座標の結果は一つの分子family内の2条件・3時刻ずつであり、6独立分子の証拠ではない。HClで状態近似の影響が小さいことは機構切り分けには役立つが、強相関・大規模系への外部妥当性を保証しない。[S06](PF_research_claim_evidence_ledger_20260929.md#S06)[S18](PF_research_claim_evidence_ledger_20260929.md#S18)

数値gateやtestの合格は、固定計算の整合性を支持する。しかし、その数をもって物理仮説の一般性、新規性、実用性を証明したことにはしない。

## 12．成果として保持するものと、将来判断

### 12.1 今回保持する成果

第一研究の三分解・費用因子・HFのdomain制約・S4 negative resultを中核の記述として保持する。第二研究からC0までは、一つの改善案を固定評価し、原因を分け、圧縮・取得・誤差幅・資源価値へ問いが移った追跡結果として保持する。

現時点では投稿論文へ仕立て直さず、このレポート、主張台帳、短縮版を研究相談や将来の発表・修論の材料とする。第二研究以降を第一研究の完成条件として差し戻したり、各stageを独立論文と決め付けたりしない。

### 12.2 将来方針（研究判断であり、成果ではない）

直近の全体再検討では、full-space gap認証を研究全体の必須主路線とはせず、PFの性能・校正の信頼性・追加情報の資源価値をつなぐことを中心に置く方針が提案された。新規研究を選ぶ場合は、有限の校正費用で時刻・QPE予算の判断をどこまで改善できるかを問い、幅の改善やArnoldi自体を目的化しない。

ただし、この方針から新しい方法の有効性が既に得られたわけではない。C1、D2-B、LiFの追加計算、独立holdout、新PF探索、bias補正は、この成果整理作業によって承認されない。この段落は実験結果ではなく、今回の`governance_scope`である。（CL30）

## 13．Codexでの証拠監査に残す確認事項

この内容整理稿では、報告書・decision・protocol・主要CSVを読み、数値と解釈の対応を確認した。次のrepo統合では、CLごとの原CSV/JSONへの照合、source blob/hashの確認、現在入口文書と履歴文書の区別を行う。

特に、公開原稿の新4次式とコード上のPF IDの対応、stageごとの費用定数、原R1の全16行の集計、D1のtop-Kの分母、D2-Aの元labelとaudit、C0のRayleigh残差と旧unit-circle残差の区別を確認する。確認できない項目は注記を残し、新しい科学計算で埋めない。

旧`pf_data_use_ledger.md`は9月25日時点の台帳であり、HCl/LiFの後続利用はR1以降のevidenceと合わせて追記する。既存資料を上書きして当時の独立性を消すのではなく、どの時点から何の設計に使用したかを追加する。[S16](PF_research_claim_evidence_ledger_20260929.md#S16)

本稿に付した数値は、この照合の対象となる内容であって、Codex監査完了の証明ではない。対応関係と残る確認事項は、別ファイルの「主張・証拠台帳」を正本とする。
