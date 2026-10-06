# FS-C1実行前に閉じる項目

1. 原baseline3点と設計記述「元5点」の違い。原3点へ揃える場合も明示amendmentにし、scienceは別承認。5点案を残す場合は新baseline/元B0の関係・新座標/対照・cost countsをGPT側で設計し直す。勝手にsentinelをtrainingへ昇格しない。
2. 元private H01 cacheまたは同一byteを引き継ぐsanitized/exportがローカルにない。whole-cache expected SHAはあるが、現配列を確認できない。元保存場所からidentity-only extractionして、CISD/basis/component-spectraのcanonical hashes・shape/dtype/read-onlyとsector/orbital/order/originを閉じる。missing入力をmolecule/ground/state再生成で補わない。
3. native PF/exact-H echo数値契約とaccounting。任意vectorへの構造上の対応はあるが、Ritzのecho誤差、unitarity/norm/cold diagnostics、内部H作用/norm estimation、memory/wall上限は未完了。別backendへ推測で置換しない。
4. 元M00/B0再現gate。元relative-time/response-scaled3点solverと新column-scaledOLSの関係を明記し、sourceに基づく事前許容差を固定する。既存のsignal/noise/sign thresholdはbackend誤差boundではない。C0 production refit禁止なので今回データを再fitしてtoleranceを作らない。

元S0の2point exact-time/branch/source-attestation joinは成立済み。C0の数学・保存テストがpassしても上記closureの代わりではない。C1 predictionを生成していないため、新intervention benefit、budget reduction、安全性の成否は未測定。
