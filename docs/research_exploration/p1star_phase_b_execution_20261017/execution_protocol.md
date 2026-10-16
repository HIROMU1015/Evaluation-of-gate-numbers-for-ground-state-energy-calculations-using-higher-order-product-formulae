# P1STAR-A-v1 実行と技術回復の範囲

2026-10-17 JST。ユーザーの最新指示 `user_execution_authority.txt` が今回の実行承認である。freeze commitは `77f6b450ac6a4899b537e22420dfa8a7833bccf2`、入力SHA-256は `eb6581e351cabae863eab4bb40ef659a91655c25685fdd5a0fb988ab9a2521a5`。既存の未承認draft・source・STOP・grantは履歴として維持し、新しい実行記録を作成する。

最新指示は、同じ科学入力の計算を進め、技術的中断を修正して計算を完了する承認として扱う。旧「中断後に自動retryしない」という運用は今回の技術回復campaignに限って更新する。各attemptのlauncher自体は一回限りで、旧markerや失敗結果を削除しない。campaign内で新しいrun ID、実際のユーザー指示reference、source commit/hash、settings hashを固定して順次実行する。科学的結論が出た後の別問題探索や正式採択は含めない。

## 科学条件

4 modes、元契約のL1/L2、K=L1²+L2²、N=2識別用、full Fock主判定、共通bus、12 segment、12実パラメータの閉box、4次のformal-log一致を維持する。入力の変更、別sectorへの救済、次数削減、parameter固定、追加cleanup、数値fit、別ansatz、Molecular simulation、回路生成、外部truthは使わない。

因子適格性gateから開始し、非退化・非可換性・二体作用をexactに確認する。通過した場合だけ固定4次logと、一つのfull Fock係数条件集合を生成し、全box付きでexact solverへ渡す。SATなら同じ元条件とboxにexact再代入し限定screenへ進む。UNSATはこの固定問題内のsolver依存結論であり、独立証明書・一般no-goではない。資源・実装・保存の問題はINCONCLUSIVEとして保存する。

## 技術回復

1. 元driver commit `d1d57110238d2ea283fb6f49bfcc519d2e8ef11e` をfreezeのまま最初に実行。管理出力上限で停止した。
2. `0aebf2df13de19286b07030626348842e19798ee`：foundationの同じCAR/Weyl normalizer結果をpure operator wordでcache。初回の導出・内容hash・reuse countersを保存し、重複traceを繰り返さない。元74件＋追加4件の人工テストPASS。科学条件も数値資源枠も維持して実行したが、20万管理termsで停止した。
3. `82a55a4fbec165e681e8ea19def5f785dca67301`：低いRSS実測に基づき、管理terms上限を有限な200万件へ広げた。別途追補hashと技術回復承認を要求し、defaultの20万上限と過去のlockを維持する。79人工テストPASS。次数を検査する前の巨大なcross-product列挙をsourceで確認し、operatorがこのattemptの固有planに一致するworkerだけへSIGTERMを送り、INCONCLUSIVEとして保存した。
4. `227d1541b98aa48147cf92cc91856da5cb87f1e6`：右operandをη次数ごとに分類し、もともと打切り対象だった次数和>4の組合せを列挙しない。元の厳密な積・打切りと同じ条件。進捗のterms/counters/RSSを小さいJSONに記録する。80人工テストPASS。資源設定は直前と同じ。

cacheのrelationは普遍的なCAR/CCRのみで、factor固有・sector固有の恒等式はcacheしない。η・parameter powersはcacheから独立に保持する。cache中のnonzero entriesもTermLedgerへ算入し、sticky limit・cleanupを維持する。cacheと次数分類の人工検証は、非可換な電子/bus積・4次formal-logと既存reference表現のexact係数比較、既知の非zero4次BCH、既知scalar convolutionを含む。新しい数学的定理を証明する作業ではない。

## 実行・保存

各attemptは元の隔離CPython3.11.1、SymPy1.13.3、mpmath1.3.0、Z3 4.13.3.0を再利用し、毎回runtime snapshotとmapped native library hashを確認する。sourceの新しいcombined code hashも実行前に記録する。環境lockと科学契約は変更しない。

科学workerは1個、CPU affinityは1個、native parallel無効。RSS 12 GiB、RLIMIT_AS 16 GiB、worker wall 1,800秒、solver最大900秒、trace上限100万、管理出力19 MiBを維持する。controller前後も外部launcherで有限化し、stdout/stderr/receipt合計20 MiB内に保存する。native全termsやjob全体RAM hard capを保証しない。

runtimeのapproved plan、marker、raw result、stderr、receipt、進捗は指定`.runtime`へ保存し、`.runtime`自体をGitへ追加しない。公開資料には必要なscalar結果、判定範囲、source/condition/inputのhash、追補、tests、attempt receiptを含める。computed matrix/vector、unitary、exact stateを公開しない。normalization traceの全event等を省く場合はprojectionと原本bytes/hashを明記し、raw原本を変更しない。

数学的判定と実装上の中断を区別し、exit0だけから科学的成功を判定しない。計算完了後は結果・限界・全attemptの来歴を報告して停止する。研究方針変更、新原理の認定、科学的GO、既存研究のSTOP解除は行わない。
