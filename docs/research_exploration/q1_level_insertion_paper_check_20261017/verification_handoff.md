# Q1 unitary level挿入則：最小紙上検証handoff

2026-10-17 JST。**子の共通unitary Bは具体化できなかった。判定は「限定的な障害＋親Fの既知法への還元、Q1の挿入則全体は未解決」。**
Q1は未採択の研究課題案のまま。新アルゴリズム成立、一般不可能性、新規性、資源優位を認定しない。

Repository：`HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae`

Branch：`qc-q1-level-insertion-paper-check-20261017`

固定SOURCE／起点：**3abef73cdd8a578d56f1d96d070862c71749e403**。
この資料の最終commitは自己参照を避けて埋め込まず、公開・照合後の最終chatで40文字SHAと固定リンクを提示する。

## 1. 読む順序と主要結果

1. 本handoff。
2. [親子Hamiltonian・Fの紙上導出](parent_form_factor_derivation.md)：occupationからの符号とQ5、一対secular表現、親反転関係。
3. [挿入文法の障害・各確認条件](insertion_obstruction_and_checks.md)：どの文法を否定したか、B未確認事項、control phase、次の有限例の命題。
4. [既知法・scope比較](prior_art_and_scope.md)。
5. [source registry](source_registry.json) → [static audit](static_audit.json) → [provenance](provenance.json)。

| 依頼 | 今回示したこと | 判定 |
|---|---|---|
| A 親子Hamiltonian | L4,m2の3＋3分解、親g=γ/4不変、新self−g、off-diagonal−gF、全self−2g | 確認 |
| B compactなF | 三準位parentの反転関係と一対rank-one secular座標を使う共通の点ごとの式 | 既知法への限定還元。新しい量子生成規則ではない |
| C unitary挿入 | 三つの独立2次元channelの文法Gは非零交換子により不成立 | 限定的な障害。別のBは未解決 |
| C unitarity等 | 実際の子B、Dchild、superposition、label/work返却は未構成。scalarの必要条件だけ確認 | Bの確認済みとはしない |
| D 一般L | 具体的Bという前提がないため拡張検討を開始しない | 未実施／poly費用等は未確立 |

## 2. 何が障害だったか

occupation基底ではpair raisingはT=J−Iであり、F=U2†TU1。
Tのsingular valuesは(2,1,1)で、一つのrank-one couplingではない。
さらに \([h_1,T^\dagger T]=[\mathsf d,J]\)、その(1,2)成分は **−1/2**。
\([h_2,TT^\dagger]\) も非零で、指定された全gで消えない。
よってTをsingular channelへ分けても、親の非一様一体energyがchannelを再結合する。
これは単に未知Bethe rootsを表から除くことで解消する障害ではない。

親Fの式は、label付き三次secular根を係数から定義して書けた。
root取得・正規化・有限精度arithmeticを実行又は無料化したわけではなく、全child固有状態も列挙していない。
不足するのは、**非可換な親energyとFによるlabel間混合を、一つの可逆な挿入と新energy評価として生成する規則**。
明示されたG以外を否定してはいない。

scalar cと全self−2gはcontrolled evolutionのcontrol=1 branchに \(e^{-it(c-2g)}\) を残す。
下段の新self−gだけを落とすとbranch依存のHamiltonian誤差になる。
この紙上のphase監査は、未構成Bの実操作の確認を意味しない。

## 3. GPT／ユーザーが次に判断する事項

**提案・未承認**：この限定的障害を踏まえ、非対角なlabel混合の明示則を検討する価値があるか、それともQ1を未解決として止めるか。
正式採択、研究方針の変更、追加検証範囲はGPT／ユーザーが判断する。

続行する場合の最初の紙上テストは、検証記録(21)の
\([\Lambda,Y]+Y-gF+gYFY=0\) を満たす**係数生成の非対角Y(g)**の明示である。
これは既知Riccati表現による不足の判別であり、新しい解法の提案・発見ではない。
child root／全固有vectorを渡してYを定義するだけでは不合格。
この段階でGを越える混合を実際に生成できるか確認し、できても正規化・残る対角化・返却が別に残る。
別の文法を選ぶ場合も、その具体的な入力・操作・共通label更新を先に固定する必要がある。

**担当**：GPT／ユーザーが続行の要否とこの有限例の紙上命題の範囲を決める。
Codexは新しい明示指示があった場合だけ、指定された導出・資料化を行う。
solver、数値対角化、記号計算プログラム、回路実装等が必要なら、対象・精度・truth access・出力・停止点を持つ別科学契約と必要な明示承認を先に得る。
今回これらは提案しても実行していない。

## 4. SOURCE・公開・保全

必須のSOURCE六資料（handoff、問題、最小検証、比較、registry、provenance）を固定commitで読み、
既存provenanceの非自己manifestを照合する。追加の既存survey／auditとAGENTS、J1 pause記録も静的確認に限る。
各資料のorigin/result commitとverified snapshot commitを別fieldで残す。
一次文献の版、取得byte、SHA-256、読取り範囲、実装の固定snapshotもregistryに記録する。
式・ket・blockは紙上の説明であり、科学行列／固有vector／exact state等のデータファイルを公開しない。

公開対象は新規Markdown4件とJSON3件のみ。
provenanceのmanifestは自己を除外し、そのbyte同一性は公開commitの独立fetchと固定rawで別途照合する。
commit・通常push後、remote branch SHA、独立した空のGit repositoryからのfetch、全7ファイルのGit blob・bytes・SHA-256・raw取得を照合する。
本節は公開前に準備した監査手順の記録であり、実際の成功は最終chatで報告する。

既存のscience SOURCE・結果・grant・承認・固定契約・STOP/PAUSEは変更しない。
J1は **PAUSED_PENDING_NEW_MECHANISM** のまま。D1・D2を維持する。
独立worktree以外の編集を行わず、共有サービス・他ユーザーのprocess・環境設定を操作しない。
実施した技術処理はGit、文書・JSON読取り、HTTP、text/hash監査のみ。
**新規科学計算、solver、数値行列計算、記号計算プログラム、simulation、科学実装、compile、benchmarkは零。**

**Mandatory STOP：資料の公開・同一性照合後に停止する。追加探索、Q1採択、詳細科学レビュー、新規科学計算・実装を自動開始しない。**
