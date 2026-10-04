# H-chain independent validation protocolization

Status: `hchain_independent_validation_protocol_blocked`

研究質問・物理量・cost model・decision structureをH2/H4/H6内部で定義できることは確認できた。一方、指定された「generated input identityと9点absolute timeを科学実行前に固定」を、新規CISD/cheap計算禁止の今回段階で満たすことはできない。設計案は残すが、complete/execution-readyとは報告しない。これはH-chain routeの科学的失敗ではなく、準備順序と入力可用性のreview blockerである。

## Fixed design

| 項目 | 固定内容 |
| --- | --- |
| Systems / PF | H2,H4,H6、1 Angstrom、STO-3G、neutral singlet、canonical current_m3 |
| K | 108 / 2556 / 14344 |
| State family | frozen RHF reference + singles/doubles、同一physical population rule |
| Sector | H2 4 / H4 36 / H6 400。H2 interleaved、H4/H6 halvesをsource通り保持 |
| Reference fit | first-study leading_fit、geomspace0.02–1.8 34点、window5、order tol0.2、R2>=0.999、floor5e-13、earliest |
| Candidate recipe | r=0.5,0.65,0.8 times each system's CISD t_ref |
| Anchor | T0=0.5t_ref、B0=1.01*C_C(T0)、natural capではない |
| Cost / target | epsilon_E=0.00015936001019904 Ha、beta1.2、continuous proxy、eta0.10 |
| Gamma | 1.01,1.02,1.05,1.10は予算倍率。HF b1_arm_rowsと同じ |
| M1 | uniform rank rule H2 m4 vs m2、H4/H6 m8 vs m4、algorithm core変更なし |
| Secondary | frozen S1A B2/H1 specification、not yet validated policy |
| Scorer | signed estimation errorとabsolute budget errorを区別。shift/gap物理枝診断 |
| Acquisition ceiling | candidate cheap9、M1 PF/H60、reference grid別枠102ずつ、truth9が将来提案 |

## Remaining execution blockers

1. H6 Hamiltonian array / CISD hash、H2個別state hash、sanitized adapterが未固定。Hamiltonian生成権限も自動付与しない。
2. H2/H6のoperational CISD t_refがない。H4 saved t_ref=1.237648718781152は同一fit由来のscalar reuse候補で、3候補のabsolute time/hexをscalar算術だけで記載した。H2/H6の6行は未取得で空欄。H4もsanitized input runtime確認は未実施なので全体の実行用candidate freezeは未成立。
3. first-study fit/selection codeは変更せず継承可能だが、歴史的acquisitionはfull PFを構築し、loaderはexact stateを開く。vector-only sanitized wrapperを「full pipeline byte-identical」と偽らず、implementation差分をreviewする必要がある。
4. H1のq-first actual combined pathとalways-M1比較用補完を共有すれば60上限に収まる設計だが、未実装・未測定。fresh独立H1 replay追加は上限外。standalone wall優位は現時点で評価不能。
5. same-H exact-ground truth sourceと必要な追加生成許可が未固定。H6の旧200次元exact restrictionを400次元predictor sectorへ流用できない。9-coordinate truth ceilingはground-state生成承認ではない。

candidate absolute times / generated H6 identityを先に要求しながら、その生成に必要なscienceを今回禁止するため、次reviewではtruth-free input/reference preparationを別段階として承認するか、freeze順序を修正する必要がある。今回はどちらも勝手に選択しない。

## Integrity and evidence

GitHub read-only git/ref APIでbase branch先端50344a766ffbe40d969471200fe165e438f4c9ecを確認してから独立worktreeを作成した。47 source filesをbase blobとbyte-identicalに照合し、直前manifest記載14件も再hash一致。binary archiveはhashのみで、array/stateをdeserializeしていない。

旧contract auditのnot_justified、component planningのblocked、formal S1A D、旧push_authorized=falseを変更していない。remoteに既に存在するbaseの事実は新registryで別記する。

16成果物を要求通り用意する。content14件とprovenance/source registry + self-excluded manifest2件を分離commitする。sourceのorigin/result publication commitとverified snapshot commitを分ける。現在のscopeはlocal commitまでであり、pushは別指示が必要。

## Counts and next review

New Hamiltonian/state/fit/cheap/M1/direct/gap/toy/scientific tests/GPU: all 0。policy fitting/retuningも0。既存artifactsとroot user editsは変更しない。

次はこのprotocolization bundleのreview。準備段階、adapter差分、H1費用比較、scorer ground sourceを閉じるまでscientific executionへ進まない。review後も別承認が必要。H-chainの有効性や3systemの性能はまだ評価していない。
