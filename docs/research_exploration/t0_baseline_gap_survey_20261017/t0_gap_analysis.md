# T0：gap台帳と既存研究との境界

分類は、(U)確認した文献内の未解決問題、(L)既知構成の保証・適用範囲制限、
(E)構成は既知で価格・情報が不足、(H)過去の閉鎖／保留問題との重複。
文献未発見を未解決性・新規性の根拠にはしない。

## 1. B′の三条件

| gap | 具体的費用／保証 | 根拠 | 既知道具との照合 | 最終扱い |
| --- | --- | --- | --- | --- |
| G1 finite-stepの実用誤差保証 | 安全step数と誤差係数の取得費 | B1/B2の保証範囲、PR A2 | commutator／QPE-aware／lowenergy法は既知。汎用不足だけでは差分なし | L/H：新候補にしない |
| G2 randomized信号からE0へ | 全round shotsとbranch成功率 | B3/B6に既知の統合定理 | L04/L08は接続済み。M1-S固有の接続不足は既存問題 | E/H：一般gap主張を不採用 |
| G3 浅いGSEEの認証費 | Gaussian呼出し期待数とdepth/runtime | L07の明示した費用差・下界問題 | gap-free CDFも既知。gap既知推定との情報差を残す | U/L：D1中心候補へ移さない |
| G4 overlap・準備保証 | 準備回数×Pとetaの正当化費 | L02の停止基準、各定理の入力条件 | exact stateを無料化できない。クラス・新補題未特定 | L：一般論として候補にしない |
| G5 低energy外挿の保証 | 相殺次数とcutoff依存を両立する有限r誤差 | L08 §1.7が明示的open、L09は通常PFの到達点 | triangle bound／sectorだけでの解消を最初に確認 | U/L：R1として条件付き保持 |
| G6 native総費用の欠落 | wrapper・rare event・P・全roundの価格 | PRA/PRMの保存scope | 価格取得やcompileを要する部分。新しい構成問題とは限らない | E/H：新数学課題にしない |

G5の「既知法で未解消」は、引用した到達点で対象命題が与えられず、著者が対応問題をopenとした範囲での評価。
後続論文・既存証明からの直接還元を網羅的に否定した判定ではない。R1を正式採択する前の必須gateに残す。

## 2. 各gapの十項目

### G1：finite-stepで小さい保証係数を安く得ること

1. 対象項はPF stepを決めるrigorousな誤差定数・剰余と、その情報取得費。
2. 強い対照はB0のcommutator上界、B2のenergy-aware評価、B6のsector／低energy上界。
3. 不足の根拠は、B1の経験校正・B2の漸近／gap条件が任意有限stepの証明ではないこと。保証そのものが存在しないわけではない。
4. 改善すれば保証に従って選べるstep幅が変わり、運用費が減り得る。
5. 必要なのは同一情報で既知上界より小さい有限step証明書と、その安価な取得補題。今回は独立した具体式を得ていない。
6. 入力は係数・合法state記述。unknown ground期待値・gapは使えない（S1未充足なら条件付き）。
7. 既知BCH／sector／lowenergy boundsへの還元、およびSOS-PF A2との重複が強い。
8. 最小案は過去A2の条件と既知上界の対応表確認。新たなbias計算・step最適化は実施しない。
9. 新しい差分がない現時点では候補にしない。「保証に価値なし」という否定にも変えない。
10. A2はNOT_ADOPTEDでCLOSEDではない。第一・第二研究、J1/Q1を再開しない。

### G2：乱択simulationと絶対E0の接続

1. 対象項は \(N_j\)、signal damping、phase branch、全round成功率。
2. 強い対照はL04のRTE＋RPE、L08の外挿PF＋CDF。小overlapではB0も必要。
3. 一般の接続は既知。M1-Sについて残るのは固定joint lawの有限δ・state・価格に固有の不足（PRM）。
4. M1-S固有の接続が成立すれば、単時刻診断から総費用taskへ進める可能性はある。
5. 追加の単時刻上界ではなく、実装・全round・state混合を扱う保証が必要。今回それを新規定式化・構成しない。
6. overlap、energy window、fresh-shot law、HD内部PF、directional control単価を払う。
7. 「接続するだけ」では既知構成への還元か、既存M1-S Task Bの再開に当たる。
8. 最小案は元定理の入力／出力／native単価をL04と照合する静的作業。追加計算はしない。
9. 一般的未解決gapという分類を棄却し、新しい研究課題にはしない。
10. Track B正式休止、M1-Sの個別状態を維持。T1-Dの認証・phase推定接続も復活させない。

### G3：浅い推定と認証の費用差

1. 対象はL07 Theorem 5.1の期待Gaussian block-encoding呼出し数、および最大depthを制約したruntime下界。
2. 同一accessならL07を比較、gap下限なしのE0推定にはL02/L08も含める。
3. L07 §6は低depth runtime下界等を明示的に未解決として挙げ、推定と認証の費用差も記す。
4. 解決すれば、浅い回路での保証取得に必要な統計・時間費を特徴付けられる。
5. 必要な命題の雛形は、同一promiseでのsoundness／completeness付き認証の費用上界または下界。
6. 正しいinitial bracket、eta、準備、各Gaussian関数の合成を無料にしない。gap既知の推定とgap未知認証を同一情報として比べない。
7. 既知QET-U／filter／CDFへの還元リスク。oracle下界を係数可読な電子Hamiltonianへ無条件に移すこともできない。
8. 最小案は、許可accessと認証promiseを揃え、既知CDFとの比較を紙上で固定すること。
9. 文献上のgapは認めるが、今回はD1中心の候補にしない。D1変更を推奨・実行したものではない。
10. T1-Dのhardware accreditation接続とは異なる問題だが、別task・方法範囲の判断が必要。STOP不変。

### G4：状態準備とoverlap下限の正当化

1. 対象は \(N_{prep}P\)、etaに依存するshots、eta証拠の取得費。
2. B0/B3/B6/B7は、それぞれ明示したoverlap条件の下で強い構成を持つ。
3. L02はetaが停止基準に必要である理由を述べる。準備回路が容易なこととeta保証は別。
4. 低費用で下限を証明できる非自明クラスがあれば総費用改善になる可能性がある。
5. 今回はそのクラスと証拠生成補題を特定していない。一般に「良いstateを作る」を研究問題にしない。
6. 係数・準備回路のみ。exact state／全振幅・未知gapをoracle化しない。
7. 既知のstate preparationやclassical electronic structureへの還元、モデル固有仮定の隠蔽リスク。
8. 最小案は既存taskのeta証拠欄を埋める静的確認。新規state最適化は不可。
9. 費用をゼロにした比較は保留するが、独立研究候補数には含めない。
10. 第二研究のspectral診断や既存state準備の契約を拡張しない。

### G5：外挿と低energy保証の同時利用

1. 対象項はB6の誤差係数・必要r、sign-weight付きshotsとの積。
2. 強い対照はL08の全空間／sector外挿、L09の通常4次／高次PF。弱いfull-Fock上界だけを比較しない。
3. L08 §1.7が低energy性を外挿へ継承できるか明示的openとして残す。通常PFの改善はL09ですでに成立。
4. 有限rで相殺と小cutoff依存が両立すれば、既知外挿法の保証範囲を広げられる。総E0優位は追加条件。
5. 目標は [R1-P](t0_research_problem_candidates.md) のrestricted高次係数・積・leakageの上界。
6. PSD local係数、sector、J、明示state準備、lowenergy tailとetaの合法な証拠。P_E射影は記述用でoracleではない。
7. 通常PFの既知証明とMPF定理から直接従う可能性を最初に潰す。成立しても既知アルゴリズムの新保証であり新操作ではない。
8. 最小案は4 modes・2 electronsの非可換layerで相殺と剰余の必要項を紙上で照合し、独立block familyで反例を探す。今回は未実施。
9. 数学的新規差分・合法情報・強い対照に対する余地が残る場合だけ次段階を提案。直接還元や費用差消失なら棄却／保留。
10. SOS分割生成やA2の一般保証不足を名称変更したものではなく、固定した既知外挿作用への定理問題。過去の採択・STOPは変更しない。

### G6：公開回路費用と全taskの間の未取得項目

1. 対象はrare event単価、control方式、RZ→FT合成、P、全round測定費。
2. B4-Aの固定wrapper価格と、B3/B6の全protocol定理を、それぞれの適用域で使う。
3. PRA/PRM自身が未価格／未確立とする項目が根拠。アルゴリズムが存在しない根拠ではない。
4. 価格を取得すれば公平な総費用比較はできるが、新規数学成果とは限らない。
5. 必要なのはまず同一taskの価格表。新しい操作生成補題を今回は特定しない。
6. 元H係数、wrapper、compiler、shot contract、seed/provider等の固定が必要。
7. 既存Track Aの追加compileやM1-S資源路線を、新規候補として始めるリスク。
8. 最小案は公開済み価格の欠落欄の列挙。科学compile・保存値の再解析は行わない。
9. T0の未取得情報として残し、研究候補にしない。
10. 既存承認は各固定契約のまま。新benchmark・rare-tail実行・Track B再開は認めない。

## 3. 重複の最終確認

P1*固定word／J1のbus代数、rotor／対数振幅輸送、二電子補助衝突のCG／Paldus還元、
Q1のpairing level挿入・Riccatiは、今回構成・再検証していない（E01/E04/E14/E15）。
PRのSOS-PF、occupation保証N3、M系列、H1–H4、THRIFT、T1-D等の履歴はE04およびPRS/PRG/PRCを根拠に保持する。
R1は既知外挿作用に対するrestricted誤差命題に限る。元の広い探索課題や新primitiveの採択に読み替えない。

未確認のまま残るのは、R1-Pの成立性・priority、非自明な電子クラスでの準備証拠とcutoff、通常高次PFを含む総費用差。
したがって条件付き数学課題1件、正式採択0件、完成アルゴリズム0件で終了する。
