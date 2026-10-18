# P-c限定照合のscopeと固定仕様

2026-10-18 JST。直接ユーザー指示「適応的部分空間生成規則Gの独立性に関する限定照合（P-c）」に基づく。**P-cの技術照合のみ。P-d、候補探索、数値計算、科学用symbolic checker、回路build/compile、科学実行契約・grant、正式状態変更、GPT詳細科学レビューは行わない。**

## 1. 固定入力と読み方

Evaluationのbaseは `7bbcc6c35a3d53bcdbbf720526c5cae0d885c7cd`、元packetは `docs/research_exploration/coherent_adaptive_subspace_initial_paper_20261018/`。6本文、SOURCE/literature registry、provenance、静的監査、publication receipt、入力原本を含む14ファイルのGit bytesを確認した。6本文を読み、前回manifestの12件・receiptの親payload13件を管理上のhashで検査した。旧数値・標本の再解析ではない。

追加の固定参照は、横断整理609a6323…の対応表・状態表、差分c6419859…、PR側d09ba606…の重複表、7af83266…のA2 handoff。今回の[source registry](source_registry.json)は計19ファイルのorigin/result commit、verified snapshot commit、blob、bytes、SHA-256、固定rawを分離して記録する。旧資料の全transitive科学監査を行った意味ではない。

J1・Q1のPAUSE、R1-P不保持、集団遷移生成PAUSE、A2等の正式状態・grant・marker・STOPは変更しない。A2の別chatの新資料・現行jobを今回の研究入力へ取り込まない。全chatの活動台帳を確認したとはしない。

## 2. 比較に固定する入力

\[
I=(H=cI+J,\ A,\ D,\mathcal F,K_{\max},m_H,m_S,
e_H,e_S,\alpha_H,\alpha_S,\epsilon_{RR},a_s,a_a,a_m,
\text{固定tie規約と算術規約}).
\]

全て前回の記号のままで、値を選ばない。Hの係数・scalar・mode順・sectorを維持する。Aは純粋seedの再準備accessであり、ground／全振幅表ではない。逆Aやcontrolled-Aを追加要求しない。原GのΛ=0のscalar終了branchもそのまま比較する。

比較を二つに分ける。

- **同じ記録を入力する比較**：GのR_H/R_Sを既知QSE／diagonal後処理にもそのまま与える。取得費は両者へ同額を計上する。
- **それぞれの実際の測定を使う比較**：原Gのancilla測定、VQNHEの2種の配置対測定、SSEの標準local shadowsを区別する。状態準備回数、標本分布、分散、処理費を明示する。同じ期待値を得られるだけでは同shotとしない。

前回の入力仕様は理想・純粋seedである。hardware noise、native価格、最適compiler、最適sampling lawの比較を新しく認定しない。

## 3. Gの固定された定義

| 部位 | 前回の定義 |
| --- | --- |
| graph | canonical fermion termの支持I_μ、w_pq=Σ_{μ:p,q∈I_μ}abs(b_μ) |
| 集合族 | singleton、term支持、重み降順Kruskalのunion直後のcluster。構文のみ重複除去 |
| 辞書 | q_{C,k}(x)=1[Σ_{p∈C}x_p≤k]、0≤k<サイズ(C)。Q=O(n(L+n)) |
| 候補 | 現treeの一leafを一predicateで二分。全固定D-tree class F、K≤K_max |
| basis | χ_a=Π_aψ。seed support内のcoherenceを保持。新supportは作らない |
| 記録 | lをabs(j_l)/Λ、βをX/Y等確率、ancilla符号sとsystem x。別poolのZ人口記録 |
| matrix | G3の複素一entry標本を平均後Hermitian化、Shat=diag(phat)、Hhat=c Shat+Jhat |
| confidence | 全Fの同時event。phat_min>2e_S、u_f=(e_H+Λe_S)/(phat_min−2e_S)。有限精度なら別途e_solve |
| gain | g_L=Ehat_f−Ehat_f′−u_f−u_f′。両u≤ε_RR、g_L>0の候補だけ |
| 費用 | 前回W_f、solve・集計・storage重みを用いたC_add。全screening実費は候補の和 |
| 選択と終了 | g_L/C_add最大、固定tie。候補なし／上限／証拠不足で停止。追加shotなし |

Gにはzero-weight edgeをgraphへ含めるかという記述上の余地がある。孤立点を残す文脈では正weightのedgeを使う解釈が自然だが、今回凍結Gを修正して選択しない。以下の同値性は、zero edge・同率edge・leaf順・算術・失敗時処理の**同じ規約を両者へ渡した各場合**について成り立つ。未指定の数値・規約から一意な実run結果があるとはしない。

## 4. 結論の型と停止点

主判定は[独立性評価](pc_independence_assessment.md)に一つ記録する。literalな既存論文のアルゴリズムとの一致、既知部品の明示した組合せへの還元、未確認のpriorityを区別する。Bと判定しても研究系列をCLOSED/PAUSEDへ変更しない。

独立branch `qc-coherent-subspace-pc-mapping-20261018`、専用worktreeでAGENTS.mdを確認した。追加の直接ユーザー規約も適用する。管理作業開始時の利用可能CPUは32、MemAvailableは51,759,936 kB。作業は読取・文書・Git/hash管理で科学計算のdominant workloadはない。資源上限や共有設定の変更を加えない。

成果物の通常commit/non-force push、remote SHA・独立fetch・blob／bytes／SHA-256・固定rawの照合後にMandatory STOP。今回の指示はP-dを許可していない。
