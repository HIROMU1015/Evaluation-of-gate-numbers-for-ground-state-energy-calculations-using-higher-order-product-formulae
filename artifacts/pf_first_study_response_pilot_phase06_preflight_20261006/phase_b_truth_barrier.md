# Phase B truth barrier

Phase AとPhase Bは別module、別CLI action。Phase Aはproduction truth CSV、exact state、exact energy、controlled state、D4/D6/D8を読む経路を持たない。A3もPhase Aから参照しない。source archiveのbyte hashは許可されたidentity確認であり、非allowlist memberをdecodeしない。

## Freeze order

1. 承認済みPhase Aを2-pass実行し、fixed schemaを検証する。
2. 新directoryへ`phase_a.json`と自己除外`phase_a_manifest.json`をexclusive-createする。既存directoryは拒否。
3. prediction bytesのSHA-256、source identity、全実装とschemaのhash、protocol hashを固定する。
4. 実fetch/push URLsが許可されたHIROMU1015 repositoryか確認し、専用non-main branchへ2個のpublic scalar filesだけを明示stage・commitする。unrelated staged fileがあれば停止する。
5. normal push後にremote branchの40-char SHAをlocal HEADと照合し、committed scalar blobsを保存bytesと照合する。失敗時はfreeze receiptを返さない。
6. 40-char commitとprediction path/hash、source/code/protocol hashを含むreceiptをrepository外へcreate-only保存する。
7. 別途承認されたPhase B invocationだけがreceiptを消費する。Phase Aから自動開始しない。

## Reader preconditions

実際のremote URLs、remote branch tip、full commit、normative protocol committed blob、prediction local bytes＝committed blob、SHA-256、committed manifest、schema、receipt全identityを先に検証する。実装/schemaのcommitted/current bytesも照合する。production sourceはallowlist identity-only reloadでfreeze時のsource hashと照合する。**全て通過する前にtruth callbackは呼ばない。** synthetic Phase A freezeはproduction truth readerに接続できない。

readerは保守的にremote tip＝Phase A freeze commitを要求する。Phase B scoring前にそのbranchをadvanceさせない。freeze後のsource/code/prediction変更は別freezeが必要であり、既存artifactを上書きして救済しない。

## Allowed saved scalars

Phase0.5 registryとjoin contractをfixed base commitから参照し、source CSV bytesのhash/blobを検証する。このactual content accessは将来の承認済みPhase B内だけ。`branch_audit.csv`からB/H4/current_m3/mechanism_fixedの12 signed evaluation coordinates、`observables.csv`からB/H4/current_m3/exactの22 signed coordinatesだけを数値化する。他rowのscalar valuesは解釈・使用しない。whole-file bytesとCSV row textの走査はsource integrity/filteringのために必要で、選択外scalarの科学的利用は行わない。

direct rowはfrozen branch id/sign/time/reliabilityを照合。exact rowはsign/absolute timeを照合。missing、duplicate、unreliable、identity mismatch、nonfiniteで停止。replacement、interpolation、新truth生成は禁止。

A3の3 reference fitsだけをsaved exact proxyから作り、frozen Phase A predictionsを変更せず12 evaluation rows全てをscoringする。S_abs、S_under、E_max、nonadditive sign crossings、row比較、continuous ratios、固定outcome precedenceを維持する。score後にもprediction payload bytesの不変性を確認する。

## Phase 0.6 evidence

truth-free実装のimportsとallowlistを監査し、mock Git/CSVでmissing freeze、changed identity、missing/duplicate/unreliable truth、synthetic freeze misuseを検証した。現在のproduction saved direct / exact proxy accessは0。arbitrary Pythonや手動ファイル読み出しを隔離するsecurity sandboxを主張するものではない。
