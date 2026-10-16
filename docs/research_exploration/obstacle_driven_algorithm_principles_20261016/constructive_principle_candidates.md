# 構成原理の仮説と最も近い既存法の比較

2026-10-16 JST。Phase Aの[障害表](problem_and_failure_map.md)からX1/X2だけを取り出し、入力→処理→出力を検討して一次文献を限定照合した。**独立研究候補として残すものは0件。** X1/X2は審査用の仮説名であり、採択候補・新規アルゴリズムではない。

## 1. 比較前に固定した条件

最終対象は、定数項・核反発・normal-order補正を含む元の有限基底電子Hamiltonianの絶対基底エネルギーである。指定sectorが対象問題に対応する根拠、encoded stateの準備・読出し、control後の相対scalar phase、近似誤差と測定誤差を保持する。sector内の古典行列が小さいことを、量子回路の安さと同一視しない。

block-encoding／qubitizationを中心とする変更、単なるPF係数変更、T1の認証接続、U1/U3/U4の再追究、PR内部のlaw／proposal最適化、H1〜H4・N1等の停止系列の再開は対象にしない。[T1D] [U4_CLOSURE] [PR_TRANSITION]

Phase Cで追加した中核一次資料は6件の版固定HTML。該当する構成・入力・比較・限界を読み、証明全文の独立監査は行っていない。公開codeは2 repository・7 textファイルを固定SHAで静的確認した。全文取得、部分読取り、実行成功は別である。版・hash・read scopeは[provenance.json](provenance.json)。

## 2. X1：encoded word全体で代表とparity計算を選ぶ回路生成

### 正確な問いと仮説の処理

O4の原因のうち、termごとに表現を固定してbasis／parity計算を閉じることによる費用を対象とした。**code上で同じ論理作用を持つ代表の選択を、word内のparity計算の再利用と共同で決められるか**という仮説である。

- **入力**：元Hの係数と定数、固定PF wordと角度、既知encoding isometry／stabilizer、対象sector、device／合成精度の指定。E0・exact vector・未知RDMを入力に加えない。
- **概念的処理**：論理回転の候補代表をcodeの同値類から選び、許された演算順序内で共有parity／Clifford frameを保持する。代表変更の符号とscalarを記録し、最後にframeを閉じる。code外へ出る中間操作を、code内での同値関係だけで置換しない。
- **意図する出力**：元の固定wordに対応するcontrolled encoded回路の仕様と、準備／frame／controlを含む費用説明。PF係数や近似対象そのものを変える案ではない。

これは処理目標の具体化であって、効率的な代表選択器、正しさの新証明、生成回路を作ったものではない。任意のstabilizer等価性を全中間状態へ適用してよいという新命題も置かない。

### 最も近い既存研究と包含の範囲

| 固定一次資料 | 既知の構成と適用条件 | X1への判定 |
|---|---|---|
| Gandonほか、`2512.11418v2` [L1] §§III–V・App.B | 交換するfermionic hoppingをflow setにまとめ、encoding後にClifford stabilizer回路で一括実装する。主な具体例は局所Fermi-Hubbard型のhoppingと2D encoding | 「単項より大きい単位でencodingと回路を設計する」ことは既知。gauge制約のstabilizerと、対角化に使うstabilizer群を混同しない。密な一般分子二体項・絶対energy全費用の解決とはしない |
| Williams de la Bastidaほか、`2512.13580v2` [L2] §§3–5 | TOPP-HATTは既存tree構造等の制約下でMajorana配置を最適化し、Pauli weightとqDRIFTのtranspiled depthを評価 | Hamiltonian／hardwareを考慮するencoding最適化は既知。Pauli weightやdepthの改善をcontrolled PF energy総資源へ直結させない。初見v1の数値を新版v2へ混用しない |
| Brownほか、`2511.09322v1` [L3] §§2–3 | 分子GSEでgraphの経路・edge・局所表現を利用し、論理項やstabilizerを測定用Cliffordへ移す | 経路／論理代表の自由度を使うこと自体は差分にならない。示された分子noise／orbital操作の結果を汎用controlled時間発展の保証にしない |
| Liほか、Paulihedral `2109.03371v1` [L4] §§3–5 | Pauli blockの高水準IR、順序制約、合成・gate cancellation・mappingを合わせる | word／blockを跨ぐ再利用や、低level compilerより上での最適化自体は既知。省略されたidentityや許された並替えを、絶対phaseを保つ固定wordへ無条件に移さない |

**残る差分を具体化できたか：できていない。** 本仮説の「代表とネットワークを共同選択する」という部分について、既知の経路探索・Clifford合成・block schedulingを越える選択規則、扱える新しい入力class、費用機構を提示できていない。全手順が一論文と完全同等だと証明したのでもない。現在の記述では、既知要素と未定義の最適化目標の組合せに留まるため、候補に残さない。

### 実装の静的照合と費用

Qiskit/qiskit-fermionsの固定snapshot `e588c45733794260f0b97e5032bb855695e9ba26`では、1D/2D flow-set guideと`MapperFnEvolutionSynthesis`経路を確認した。[CODE_Q1] [CODE_Q2] [CODE_Q3] これらはencoding、grouping、合成callbackを接続する具体例であり、提案概念を新規と扱う根拠にはならない。guideに含まれるtoy検証を今回実行したとはしない。

UCL-CCS/ferrmion `c3ca01f85b2490b91eb74816a72f26dcfbe72e95`にはPython HATT wrapperとRust TOPP-HATT実装がある。[CODE_F1] [CODE_F2] 公開codeの現在snapshotと論文実験版の完全一致、現環境での互換性は未検証。低weight目的関数だけでは、control、routing、state preparation、古典探索を含む改善を保証しない。

既存両repositoryのHamiltonian／PF列／native wrapperは参考にできるが、encoded preparation、isometryとglobal phaseのbinding、新encodingのgate生成は新規実装になる。[PR_G9] 既存dense sector参照を無料運用oracleにしない。実装がないこと自体は研究差分ではない。

### 検証へ進む前の条件

| 項目 | 未確立又は仮定付きの内容 |
|---|---|
| 成功時に変わり得る量 | 同じ元H・固定word・精度で、追加qubit／preparation／controlを含めた回路資源が減る可能性。現在は未実証 |
| 失敗時の知見 | 代表選択の自由度が、既知block合成で尽くされるか、frame／control費用で消えるかを、明示された入力class内で区別できる可能性 |
| 最小検証の目的・必要情報・規模 | 独立した新規則が別途提示された場合のみ、公開2〜4 fermionic modes程度でencoding isometry・sector・signed scalar・controlled意味論を先に確認し、その後同一条件で既知強対照と比較。具体Hamiltonian、角度、gate数、予算は今回設定しない |
| 将来必要な仕事 | 規則の仕様化と既報との差の静的確認が先。回路生成、同値性の数値検査、compile／資源評価、未保証部分の証明は別承認が必要 |
| 科学計算前に取り下げる条件 | 既知mapping／path／block schedulerの比較だけ、汎用最適化器へ目的関数を渡すだけ、code外の作用やscalarを無視、又は停止済みN1/H3等の再開に帰着する場合 |

現在は最初の「独立した新規則」の条件を満たさない。最小検証案は実行提案・科学的GO・停止系列の再開承認ではない。

## 3. X2：energyに特化したjoint測定とcopy間の情報再利用

### 正確な問いと仮説の処理

O5の分解項測定費用に対し、**全RDMを再構成せず、Hのscalar推定に必要な情報へ測定を集中し、相関を利用できるか**を検討した。

- **入力**：定数項を含む既知H、指定target stateのcopies、要求精度・失敗確率。E0・正しい全Pauli符号・真の共分散・coherent inverseを無料入力にしない。
- **概念的処理**：複数observableのjoint測定で得たrecordからHを直接推定し、取得した相関情報で重みを選ぶ。copy間操作が必要なら、2-copy Bell型のrecordと別の符号取得を含めて会計する。
- **意図する出力**：符号とenergy originを保持するenergy推定量、有限標本での誤差条件、コピー・測定・古典処理を含む費用。平方や絶対値だけをE0に読み替えない。

この段階の処理を具体化しても、以下の既報を越える新しい測定生成規則にはならなかった。eigenstate制約を使えば常に測定分散を消せるという命題や、新しいPOVMは作成していない。

### 最も近い既存研究と差分

| 固定一次資料 | 既知の構成と保証・費用の条件 | X2への判定 |
|---|---|---|
| Majsak–McNulty–Oszmaniec、`2402.19230v3` [L5] §§II.2–II.4、Supp.D–G | fermionic joint測定とHamiltonian推定、相関を含むvariance、後処理重み最適化を扱う。分子benchmarkの最適重みには状態情報が必要で、uniform重みも比較する。複数roundの取得費を明示 | energy向けのjoint推定・共分散を利用する重み選択自体が既知。single-copy joint POVMをcollective-copy新手法と呼ばない。ground-statevectorでのbenchmark最適化を無料の運用校正にしない |
| Yanoほか、`2412.14466v1` [L6] §§II、III.2–III.3、IV | 2 copiesへのBell測定でPauli期待値の大きさを得て、符号取得を別に扱う。分子例で符号費・bias・precision依存を比較 | 「2-copyで同時取得し、符号を別取得する」構成は既知。moderate精度での既報利益を無視して一般的不可能性としない一方、高精度・全準備費込みの普遍的優位へも拡張しない |

**独立差分は残らない。** 今回提示できた具体化は、既存joint測定／共分散配分／Bell samplingの範囲だった。状態依存情報をより安く得る独立した手順、又はそれらと異なるPOVM生成規則は構成していない。「新しい測定器があればよい」という要求を候補として残さない。既報のすべての変種・最適性を調査済みとは主張しない。

### 入力・検証・撤回条件

| 項目 | 未確立又は仮定付きの内容 |
|---|---|
| 成功時に変わり得る量 | 仮に独立した手順があれば、同じenergy精度・信頼度のcopies又はcoherent操作が減る可能性。現在の仮説では既知手法以上の根拠なし |
| 失敗時の知見 | 同じstate accessで符号、共分散、training、copy準備、layoutのどの費用が支配するかを限定範囲で分けられる可能性。一般下界ではない |
| 最小検証の目的・必要情報・規模 | 新しい規則が別途得られた場合のみ、公開2〜4 system-qubit程度で、同じコピー準備費・精度・信頼度を課した既知joint／Bell／grouped測定と比較。真値は採点専用、符号・共分散取得と評価recordを分離。今回具体入力は選ばない |
| 将来必要な仕事 | 新推定量／POVMの仕様化が先。有限標本保証、測定回路、sampling、benchmarkには別承認が必要。著者実装が実行可能かの検証も今回していない |
| 科学計算前に取り下げる条件 | 既知測定の組合せだけ、exact signs／RDM／inverseの無料追加、平方だけからsigned energyを認定、又はH2/H4 filter／reference再開に帰着する場合 |

本件はこの条件により候補として残さない。L5/L6の公式benchmark実装の所在・版同一性までは本限定調査で確定しておらず、未取得として記録する。L5の本文アルゴリズムや使用libraryへの言及は、完全な再現codeを取得・実行したことではない。

## 4. Phase Dの結果

| 審査仮説 | 今回確認できた中核 | 独立候補に残さない理由 |
|---|---|---|
| X1 | encoding／経路の自由度、stabilizerによるまとめ実装、block合成は既知 | それらを越える具体的な共同選択規則と費用機構を特定できない |
| X2 | energy-specific joint測定、共分散重み、2-copy Bell＋符号取得は既知 | 具体化した情報取得原理が既報に含まれ、別の新手順を提示できない |

**独立研究候補0件。** 文献の存在だけで全可能性を否定したのではなく、今回の入力→処理→出力の記述に独立した生成・取得規則が残らなかったという限定結果である。新規性不在の一般証明・全資源改善の不可能性・新しい研究STOPは採択しない。

詳細科学レビュー、新証明、実装や数値検証へ自動移行せず、[handoff](research_decision_handoff.md)とprovenanceを公開照合してMandatory STOPする。

<!-- fixed-source-references -->

[CODE_F1]: https://github.com/UCL-CCS/ferrmion/blob/c3ca01f85b2490b91eb74816a72f26dcfbe72e95/python/ferrmion/optimize/hatt.py
[CODE_F2]: https://github.com/UCL-CCS/ferrmion/blob/c3ca01f85b2490b91eb74816a72f26dcfbe72e95/crates/ferrmion-core/src/optimise/ternarytree/topphatt.rs
[CODE_Q1]: https://github.com/Qiskit/qiskit-fermions/blob/e588c45733794260f0b97e5032bb855695e9ba26/docs/guides/1d_fermi_hubbard.rst
[CODE_Q2]: https://github.com/Qiskit/qiskit-fermions/blob/e588c45733794260f0b97e5032bb855695e9ba26/docs/guides/2d_fermi_hubbard.rst
[CODE_Q3]: https://github.com/Qiskit/qiskit-fermions/blob/e588c45733794260f0b97e5032bb855695e9ba26/python/qiskit_fermions/transpiler/passes/synthesis/evolution.py
[L1]: https://arxiv.org/abs/2512.11418v2
[L2]: https://arxiv.org/abs/2512.13580v2
[L3]: https://arxiv.org/abs/2511.09322v1
[L4]: https://arxiv.org/abs/2109.03371v1
[L5]: https://arxiv.org/abs/2402.19230v3
[L6]: https://arxiv.org/abs/2412.14466v1
[PR_G9]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/acfa8674d51ede1d5cd50f1b49873e67de5b71b9/docs/research/qc_existing_technical_foundation_map_20261016.md
[PR_TRANSITION]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/56f1cc55c59ab7bc42c6b24e0953675de9b29b1d/docs/research/qc_new_algorithm_research_scope_20261016/research_state_transition.md
[T1D]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/00311e0326f82e80346417c8feb7097c8b22ec76/docs/research_exploration/t1_withdrawal_20261016/decision_record.md
[U4_CLOSURE]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/00311e0326f82e80346417c8feb7097c8b22ec76/docs/research_audits/pf_u4_candidate_exploration_closure_20261016/audited_candidate_scope_closure.md
