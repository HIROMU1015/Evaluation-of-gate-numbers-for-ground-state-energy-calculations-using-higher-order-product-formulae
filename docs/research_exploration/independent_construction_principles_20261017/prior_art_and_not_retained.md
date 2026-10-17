# 既知法との照合、独立性の限界、保持しなかった方向

2026-10-17 JST。本文の[構成仮説](construction_hypotheses.md)を具体化してから、必要な一次文献と公開実装へ照合した。
発想前に既存プロジェクトの資料・既知研究を読んでいるため、文献から完全独立な発想やblind preregistrationは主張しない。
全文取得、必要箇所の精読、全証明の独立監査、実装実行を区別する。

## 1. 既存の失敗・入力障害から何を引き継ぐか

| 固定資料の障害 | 今回の構成へ課す条件 | 別名で再開しないもの |
|---|---|---|
| P1* J1の既知loop／echoへの還元、残留bus作用 [S03] | 目的演算子の生成と補助系の処理を具体的に書く。補助系を付けただけで新原理としない | J1のword・factor・pulse数・次数の再探索 |
| proxy・finite-time modelの改善が選択費用の改善へ結び付かない [S04] | 仮説の原理差と、後段の運用・総資源を区別する | 第一／第二研究のselector・threshold・truth barrierの変更 |
| coherent平均、channel、trajectory、visibility、phaseは異なる [S04, R01, R05] | 作用又は情報の出力対象を定義する。非unitary振幅更新をunitary実装と呼ばない | PR Track Bのlaw・shared ±・DF拡張 |
| 回路費用の経験的点優位と母平均・最終E0費用は異なる [R04] | 新原理の証拠を、既存の費用順位から推論しない | Track Aの再compile・保存値の再解析・新candidate取得 |
| 表現proxyとcoherent回路生成の間の隔たり [S04, S05, R01] | isometry／表現対応の存在だけでは作用生成を達成したとしない | X1、N1、旧mixed-block、H3等の名称変更 |
| ground copiesと全Hの安い測定器は別の入力 [S04, S05] | 未知振幅・RDM・位相・逆準備を無料で追加しない | X2、H2/H4のfilter／phase-reference再開 |

これらは固定資料のscopeに限定した障害であり、広い不能性定理ではない。
Track Aの取得済み集合の点優位を「強対照で消えた」と変更しない。
Track Bの後続限定理論を古いsnapshotだけで一括PAUSEDとしない。
本作業の新規候補に移さず、それぞれの既存scopeと状態を保全する。[R01–R05]

## 2. P1～P8との重複確認

| 既存発想（S01/S02、67d9e3b…） | 今回との関係・除外した再提案 |
|---|---|
| P1/P1*：複数電子密度×busの共同閉路 | NAはirrep表現、NBは振幅座標を対象とし、閉路・force・共同Magnus条件を使わない。busを別の場と呼び換えるだけの案は除外 |
| P2：配置依存の励起閉路・可解cell | 配置graphのcycle／labelの工夫だけならP2。今回のNBでもexcitorの列挙を新しい回路生成と数えない |
| P3：等スペクトルdefect、processed PF | NAのintertwinerは近似PFのeigenphase補正ではない。ただし表現対応だけで計算が容易になるとも主張しない |
| P4：基準energyからHellmann–Feynman微分を積分 | NBは固定Hの振幅scalar。Hamiltonian経路上の固有stateを追う案ではないが、虚時間による既知投影の別名化も新規にしない |
| P5：Cayley／resolvent型散乱 | rotorのexpをresolvent／block embeddingで実装する修正は採用しない。D1を保つ |
| P6：定常commutatorの測定制御変量 | NBの振幅対数と、observableの零期待値再表現を区別する。制御変量だけの案は再提案しない |
| P7：誤差だけをsyndromeへ移すlift | NAはPF誤差のrecoveryではない。Gauss制約をQECの新生成と呼び換えない |
| P8：自律的energy clock | NBのscalarはclockへの新しい転送操作ではない。scalar追跡を自律読出しの発明としない |

S03の正式状態は **PAUSED_PENDING_NEW_MECHANISM**。今回のNA/NBはJ1再開条件の充足を審査する作業ではなく、
J1/P1*の一般的不成立・再開・終了の新判断を含まない。

## 3. 今回追加した一次文献の必要箇所

取得byte数・SHA-256、固定version、読取り範囲は[source_registry.json](source_registry.json)に記録した。
HTMLの表示生成日を元論文versionの提出日と混同しない。出版版との差分監査は行っていない。

| ID | 一次資料と読取り範囲 | 支持する対応／支持しない主張 |
|---|---|---|
| L01 | Dobrautz–Smart–Alavi, [1905.01346v2](https://arxiv.org/html/1905.01346v2), §II Eqs. (2)–(14) | 電子Hのunitary-group生成子による二次表示、GUGAのirrep構造は既知。NA全体のrotorアルゴリズムやgeneric化学Hの安いexpの出典にはしない |
| L02 | Davoudi–Raychowdhury–Shaw, [2009.11802v1](https://arxiv.org/html/2009.11802v1), §II、特にII.1 Eqs. (3)–(10)、§Vの費用対象 | 非Abelian場の左右運動量・Gauss制約は既知。SU(2)格子理論の構成を任意の分子積分への新生成保証へ移さない。主な費用解析は古典側 |
| L03 | Kvaal, [1201.5548v2](https://arxiv.org/pdf/1201.5548v2), §§III.B–E（PDF pp.11–19）のexponential parametrization、可換excitor、非切捨て／切捨ての区別 | NBの有限励起代数とCC座標、orbital-adaptiveな拡張は既知。全rankの情報量が常にpolynomialという保証にはしない |
| L04 | Pigg–Hagen–Nam–Papenbrock, [1205.4002v1](https://arxiv.org/html/1205.4002v1), §II.1 Eqs. (7)–(14)、§III.3 | NBのscalar振幅を含むTDCC方程式、虚時間との関係に直接対応。NBの一般chart変更の全同値や、量子回路実装・最終絶対E0保証まで示す資料ではない |
| L05 | Temmeら, [0911.3635v2](https://arxiv.org/abs/0911.3635v2), abstract・版情報のみ | eigenstateを直接sampleする量子Metropolisは既存方向。今回全文・mixing／全費用は審査していない |
| L06 | Zhang, [1111.3940v1](https://arxiv.org/abs/1111.3940v1), abstract・版情報のみ | Yang–Baxter条件を量子gateの構成に使うことは既知。一般化学係数のintegrable embedding不能性を示すものではない |
| L07 | Jnaneら, [2606.19457v2](https://arxiv.org/abs/2606.19457v2), withdrawal notice・author comment | 検索中に見つかった一般CAS状態の効率的準備claimはwithdrawnであると確認。NA/NBの肯定的根拠に採用しない。全QPT又はGUGA一般の否定にも使わない |
| L08 | Juillet–Chomaz–Lacroix–Gulminelli, [nucl-th/0104085v1](https://arxiv.org/abs/nucl-th/0104085v1), abstract・版情報のみ | stochasticな一体軌道に従うSlater determinantのcoherent平均から多体状態を表すことは既知。deterministic量子発展の回路やsampling費用の保証としては使わない |

L05/L06/L08は早期screenの境界だけに使用し、abstractから未読のアルゴリズム詳細を補完しない。
L07ではv1の本文表示だけを見て現行の有効な効率性定理としないよう、version履歴を確認した。
新原理の不存在を示すための網羅的文献調査・特許調査は行っていない。

## 4. 公開実装との比較

HyQD/coupled-clusterのsnapshotを **780591f6d3595be058332fc653862d1aea1509e3** に固定した。
以下4textファイルを取得し、GitHub treeのblob SHAとraw bytesのGit blob計算を照合した。
import、solver、テスト、状態生成は実行していない。論文の実験版との完全一致、動作環境、正しさの全監査は未確認。

| ID | 固定source | 読んだ内容と今回への含意 |
|---|---|---|
| C01 | [README.md](https://github.com/HyQD/coupled-cluster/blob/780591f6d3595be058332fc653862d1aea1509e3/README.md) | time-dependent／ground-state CCの公開実装というscope |
| C02 | [tdcc.py](https://github.com/HyQD/coupled-cluster/blob/780591f6d3595be058332fc653862d1aea1509e3/coupled_cluster/tdcc.py) | amplitude templateに\(t_0\)、`compute_right_phase`に\(\exp(t_0)\)。scalarを保持すること自体は新規ではない |
| C03 | [oatdcc.py](https://github.com/HyQD/coupled-cluster/blob/780591f6d3595be058332fc653862d1aea1509e3/coupled_cluster/oatdcc.py) | orbital係数、双対係数、積分変換とrhs経路。orbital座標を動かすだけでは独立差分にならない |
| C04 | [ccsd/tdccsd.py](https://github.com/HyQD/coupled-cluster/blob/780591f6d3595be058332fc653862d1aea1509e3/coupled_cluster/ccsd/tdccsd.py) | scalar rhsにreference energyとcorrelation energy。NBのscalar読出し案と直接近い |

NAに対応する「一般の化学\(K\)を一括実装するrotor compiler」の著者実装は、今回特定していない。
この未取得を、世界に実装が存在しない証拠又はNAの新規性の証拠にはしない。

本repositoryのS07–S09も静的に確認した。
`chemistry_hamiltonian.py`は分子積分・JWとexact sparse eigensolverを含み、
`product_formula.py`は既知PF列、`component_sector_pf.py`はsector内小成分の参照構成を持つ。
これらを今回呼び出していない。exact ground vectorによるsector選択の経路を新アルゴリズムの運用入力に流用しない。
既存の小成分対角化を、新しいrotor primitiveの無料実装とも扱わない。

## 5. その他に検討したが保持しなかった方向

下表は短い発想screenであり、全方向に対する新しい詳細理論・不可能性証明は作っていない。
最大2件という保持数を満たすために、ここから既知法を候補へ昇格させない。

| 方向・異分野の発想 | 考えた生成の核 | 不保持の具体的理由 |
|---|---|---|
| 配置graphのfermion符号をgauge holonomyとして局所移送 | 閉路の符号・pathからcoherent配置更新を作る | 今回はP2のlabel/cell又はX1の代表・path選択を越える規則を得ていない。[S01, S05] |
| Yang–Baxter型の衝突因子から化学発展を組み立てる | 化学係数をspectral-parameter依存\(R\)へ移し、多体衝突を二体散乱へ因子化 | 条件をgateに使う骨格は既知。[L06] 元H係数から条件を満たす\(R\)と全残余を生成する新規則を提示できず、単なるintegrabilityの希望に留まった。一般的不可能性とはしない |
| エネルギー降下を局所jumpの出生・消滅へ移す | 励起／脱励起をbathへ振り分ける | 真のBohr周波数の分類を無料にできない。eigenstate sampling自体は既知方向。[L05] 今回は分類を生成する別の操作を定義できない |
| 群上のSlater軌道の平均からNAの二次式を作る | stochasticな一体軌道の平均を多体状態へ対応させる | このcoherent平均の骨格は既知。[L08] 平均を表すこととdeterministicな量子操作の構成を同定できない。PRのlawやnormalization探索は開始しない。[R01] |
| connectedな相関・copy操作からE0だけを抽出 | 全RDMを作らずenergy scalarへ情報を集中 | X2／P6で確認されたjoint測定・符号・共分散の枠を越えるPOVM生成則を今回定義できない。[S01, S05] |

## 6. 何が結論を変え得るか

NAについては、非可換な\(K\)一例を既知平方gateの列や全H exp oracleなしで生成する**明示した操作**。
NBについては、未知のchart係数を入力せずにrelative scalarを保って座標を移す**明示した量子手順**。
この種の追加規則があれば、未証明・未評価でも再検討対象になり得る。
今回それを提示できなかったことを、周辺原理すべての排除や新しい正式STOPへ拡張しない。

最初に検証するなら、分子benchmarkや詳細実装の前に上の一例で**生成規則の差分**を確認する。
ただし保持候補0件の現状では、その科学的検証の自動開始理由はなく、計算・証明・追加探索は未承認。
採否と次の研究scopeはGPT／ユーザーが判断する。

[S01]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/67d9e3b938b8a03120b836a1c32283b7c9e9a1f0/docs/research_exploration/cross_domain_mechanism_ideation_20261016/principle_ideation_map.md
[S02]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/67d9e3b938b8a03120b836a1c32283b7c9e9a1f0/docs/research_exploration/cross_domain_mechanism_ideation_20261016/prior_art_and_novelty_boundaries.md
[S03]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/95be62395d3740db39b6830c68f4fd1e25f595ee/docs/research_exploration/p1star_j1_pause_decision_20261017/research_decision_record.md
[S04]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/60bf810df6559cc41686f3fcff90fd5108435b1a/docs/research_exploration/obstacle_driven_algorithm_principles_20261016/problem_and_failure_map.md
[S05]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/60bf810df6559cc41686f3fcff90fd5108435b1a/docs/research_exploration/obstacle_driven_algorithm_principles_20261016/constructive_principle_candidates.md
[R01]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/56f1cc55c59ab7bc42c6b24e0953675de9b29b1d/docs/research/qc_new_algorithm_research_scope_20261016/research_coverage_map.md
[R01–R05]: source_registry.json
[R04]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/dd695e6584f15b88341d2446ed010c7bdfef1666/docs/research/track_a_h6_native_b0i_full_family_results_20261015.md
[R05]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/373b8e4b9831f4d00bdc00ffc741ac61e03f0841/docs/tracks/algorithm_codesign/m1s_g0t1_s0_formal_theory_contract_20261016.md
[L05]: https://arxiv.org/abs/0911.3635v2
[L06]: https://arxiv.org/abs/1111.3940v1
[L08]: https://arxiv.org/abs/nucl-th/0104085v1
