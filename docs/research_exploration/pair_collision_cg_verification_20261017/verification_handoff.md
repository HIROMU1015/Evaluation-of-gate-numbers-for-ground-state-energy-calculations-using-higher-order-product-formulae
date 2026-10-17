# 二電子補助衝突のCG／Paldus還元：独立紙上検証handoff

2026-10-17 JST。対象SOURCE `b5c49323957f1bfa2a24cb2786a0ebd1f3932925`。
**総合判定：確認。今回の既知CG／Paldus＋phaseへの還元は維持できる。**
対象とした式・fermion符号・pair添字・正規化・scalar・control・label対応に、訂正が必要な誤りは発見しなかった。
独立性は、過去の結論を仮定せず定義からCARとCGの二経路で導出したことを指す。
別モデル／第三者による査読、数値再現、実装検証を行ったという意味ではない。

## 1. 判断の要点

| 検証対象 | 分類 | 結果・根拠 |
|---|---|---|
| \(J=(K^2+NK-2NI)/(4\binom N2)\) | 確認 | double contraction、片側2種類、無縮約の4項から独立導出。無縮約はordered pair化でfactor 4 |
| tensor積、CAR、pair添字 | 確認 | all-a then all-bのisometryとparityを固定。\(B_\beta^\dagger B_\alpha=\vert\beta\rangle\langle\alpha\vert\)、余分な\((-1)^N\)なし |
| weight block次元 | 確認 | M=5・N=3で10,3,1。fixed-m multiplicityも保持し、全体100次元と整合 |
| spinと3値 | 確認 | S=1/2,3/2,5/2へJ=1/3,−2/3,1。各weightで存在するものだけ |
| 指定状態のcoherence | 確認 | \(J\vert123;45\rangle=(\vert345;12\rangle-\vert245;13\rangle+\vert145;23\rangle)/3\)。入力iを含む発展の符号も一致 |
| 有限角度のCG照合 | 確認 | 明示した4本のCG pathからprojector overlapと遷移振幅を得て、直接作用と一致 |
| control／scalar | 確認 | \(\langle\Psi\vert U\vert\Psi\rangle=\tfrac34e^{-i\theta/3}+\tfrac15e^{2i\theta/3}+\tfrac1{20}e^{-i\theta}\)。scalar脱落では相対位相が変わることも確認 |
| CG／Paldusの操作対応 | 確認 | 符号化→fermionic permutation→spin／multiplicity label→条件付きphase→同じ変換の逆。全workを返す理想構成 |
| 実際のgate精度・総費用 | 未解決（今回の対象外） | compile、科学実装、noise評価、rho2準備費、資源比較は行っていない |

「要修正」に該当する対象式は0件。
「未解決」は演算子還元が曖昧だからではなく、今回実施していない実装・費用・絶対E0の全算法の項目に限定する。
前回の研究判断や保持0件という正式判断を、Codexが新しく採択・変更するものではない。

## 2. 小例と一般保証

- **M=5・N=3の具体的確認**：全weightの型、存在spinとmultiplicity、指定のu,v,x,y,z、複素coherence、有限角度、controlを手で照合した。
- **一般有限M、\(2\le N\le M\)、補助粒子数2の代数保証**：CARを記号のまま展開し、JとK、KとSの恒等式を導いた。小例の固有値から外挿していない。
- **一般の理想構成対応**：singleのCG再帰、spin-0の区別、全path保持、既知の3値phaseと逆変換からなる。存在しないspin sectorを仮定しない。N=2では3値のうち二つが同じ+1。
- **実装の保証**：有限精度gate列を作成・compileしていない。既知変換の論文に本書のJ式がそのままあるとも、任意の化学HをCGだけで対角化できるとも言わない。

二電子補助状態の消費後のtarget channelは、有限角度では一般にunitary evolutionそのものではない。
今回検証したのはjoint collisionの演算子還元とfirst-order情報の一致であり、絶対E0取得の完成ではない。
D2の元\(cI+d\Gamma(h)+\Gamma_N(V)+R\)、state準備・overlap・位相窓・読出しの条件は維持する。
D1の中心方向を変更していない。

## 3. 訂正箇所と残る条件

元SOURCEを編集して訂正すべき数学的誤りは見つからなかった。
前回省略されていた導出とlabelの対応を、新しい検証資料として追加した。
実操作の対応を使うときは次を明示したままにする。

1. 全a→全bからsite順へ移す符号\((-1)^{\sum_{i<j}m_i n_j}\)を省かない。
2. CG／Paldusはmultiplicityとempty／doubleの区別を保持し、w又はpathを測定・消去しない。
3. controlled Dは全phaseを含む。N=3で\(-I/2\)を落とした場合、controlの1枝に\(e^{+i\theta/2}\)を戻す。
4. Paldus論文の総粒子数は今回のN+2、論文のspin projection記号Mは今回のmであり、軌道数Mと混同しない。
5. 一般の\(\rho_2\)準備、変換・reset・誤差・success・元Hへの接続を無料にしない。

これらの条件を外した実装について、今回の確認をそのまま移してはならない。
実装後の再現や資源評価を追加で実施する必要性・範囲は、今回決定していない。

## 4. GPT／ユーザーに戻す判断

**GPT／ユーザー**：この紙上検証を、前回還元を維持する根拠として受け取るか判断する。
新しい研究系列、候補の正式採択、実装又は追加計算の判断を本検証から自動生成しない。

**Codex**：本資料をcommit・通常pushし、remote SHA、独立fetch、Git blob、bytes、SHA-256を照合した時点でMandatory STOP。
追加の紙上レビュー、計算、回路実装、探索を自動で開始しない。
現依頼を完了するための追加科学作業は不要。後続作業は新しいユーザー指示がある場合だけ。

J1は`PAUSED_PENDING_NEW_MECHANISM`のまま。
既存SOURCE、結果、grant、科学契約、承認、全STOP・PAUSEを変更していない。
元SOURCEの公開前provenance記録も歴史としてそのまま残す。

## 5. 公開identityと読む順序

- Repository: `HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae`
- 新規branch: `qc-pair-collision-cg-paper-verification-20261017`
- 起点verified snapshot: `b5c49323957f1bfa2a24cb2786a0ebd1f3932925`
- sourceのorigin/result commitとverified snapshot commitは[source_registry.json](source_registry.json)で別fieldに保持する。
- manifestは[provenance.json](provenance.json)。自分自身のhashを除外し、公開commitの自己参照も作らない。
- 静的文書・identity監査は[static_audit.json](static_audit.json)。科学test又は新規科学計算を実施した証拠とはしない。

読む順序は本handoff→[CAR再導出](independent_car_derivation.md)→[小例と制御](small_example_and_control.md)→[CG／Paldus操作対応](cg_operation_mapping.md)→SOURCE／監査／provenance。
既知操作の必要箇所は[Bacon–Chuang–Harrow](https://arxiv.org/html/quant-ph/0601001v1) §IV、
[Burkat–Fitzpatrick](https://arxiv.org/pdf/2506.09151v2) Table I、II.F、III.Aを限定確認した。
論文全文の科学レビューや公開実装の再取得・実行は行っていない。

最終40文字commitとGitHub固定リンクは最終chatへ記載し、そのcommit自身のtreeで資料を固定する。
provenanceは公開前記録として凍結し、実際の公開・照合成功は最終chatで別に報告する。
**Mandatory STOP：資料公開・照合後に停止。**
