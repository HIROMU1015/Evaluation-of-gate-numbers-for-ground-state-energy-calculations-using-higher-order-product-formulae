# P1STAR-A-v1 実行中断からの技術回復に関する追補

2026-10-17 JST。今回のユーザー指示「計算を行って　中断された場合は修正も行ってよいので計算完了まで進めて」を、同じ固定科学問題についての実行と、技術的中断の修正・再実行の承認として記録する。以前のfreeze・一回限りの実行・中断後STOPの記録は上書きせず、この最新指示が今回の回復campaignに限って優先する。その他の研究のSTOP/PAUSE、科学的GO・正式採択は変更しない。

最初のattemptは詳細traceが管理出力19 MiBに達してOUTPUT_LIMIT。2回目は同じ科学入力・数値資源上限のまま、pure CAR/Weyl正規形をcacheし重複traceを除去したが、管理mapのlive termsが200,000に達して停止した。そのときの観測worker RSSは137,220,096 bytesで、12 GiB閾値に余裕があった。どちらも科学的UNSATではない。

次の技術回復では、自前TermLedgerの管理上限を**200,000から2,000,000 live entries**へ変更する。メモリ使用の実測と既存12 GiB監視のもとで、重複中間表現を保持できるようにする有限な運用変更である。個々のentryのメモリ量、全体必要量、完走は保証しない。OSのRSS監視・AS制限を優先し、超過はINCONCLUSIVEとして保存する。

wall 1,800秒、RSS 12 GiB、RLIMIT_AS 16 GiB、solver最大900,000 ms、trace 1,000,000 events、管理出力19 MiBと外部metadata 1 MiB、1計算worker/1 CPUは維持する。native内部termsの包括的計数やjob全体RAM hard capを保証しない。cgroup変更や権限昇格による資源設定は行わない。

入力SHA-256は `eb6581e351cabae863eab4bb40ef659a91655c25685fdd5a0fb988ab9a2521a5` のまま。4 modes、固定L1/L2/K、N=2識別用、full Fock主判定、共通bus、固定12 word、全12実変数の閉box、4次展開を変更しない。別ansatz・factor・sector・次数・targetへの救済を承認しない。

既存attemptのmarker・失敗・結果は保持する。回復ごとに新しいrun IDとsource hash・settings hash・本追補hashを記録し、各launcherは1 attemptだけを実行する。campaign内の技術的再実行を、元のone-shot記録を削除して隠さない。終了した数学的判定はその範囲を報告し、新研究採択・詳細科学レビュー・新証明へ自動進行しない。
