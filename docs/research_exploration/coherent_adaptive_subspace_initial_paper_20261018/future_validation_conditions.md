# 将来の検証条件：実行契約ではない

2026-10-18 JST。今回の承認は紙上構成と公開で終了する。本書は将来の判断用条件であり、科学契約・authorization・grant・計算実行許可ではない。分子・geometry・rank・時刻・seed・shots・threshold・truthを新たに選んでいない。

## 1. 最初の候補作業

**GPT／ユーザーが継続を判断する。** 判断材料は、Gの新規性として残せる部位が係数dictionaryと選択規則の組だけであること、その組も既知適応法のheuristicな特殊化の可能性があることである。

**Codex（別途指示があれば）**：VQNHEのcomplex FとSSEのfilter／regularizationへGの同一辞書を代入し、入力・出力・必要なrecord・選択・保証・総費用の対応を一枚に固定する。全く同じなら「既知法の組合せ」としてこの構成を区切る。違う順序を試す無制限探索へ移らない。科学計算を必要としない限定照合である。

## 2. 計算が判断を変え得るのはいつか

P-cに独立の具体差が得られ、かつ非自明なconnected familyで検証すべき命題が固定された場合だけ、GPT／ユーザーが科学検証を検討する。計算で判別したいのは、同じseed accessでの最適化された再利用対照に対し、同じεと成功率を得る総取得費・古典費をその差が変えるかである。

「energyが下がる」「Kが小さい」「同じ記録が使える」は既に紙上または既知法で説明できるため、それだけを確かめる新runは提案しない。数値的な成功を新規性の代用にしない。

## 3. 将来の契約に必要なfield

| field | 未決の内容 |
| --- | --- |
| 対象とidentity | Hの係数・mode順・sector・scalar、近似モデルなら元Hとの差、入力hashとSOURCE |
| seed access | Aの生成規則・準備費・精度、対照も同じaccess、support・overlapをtruthから選ばない方針 |
| 候補 | dictionary・K上限・更新数・gain/費用規則を結果前固定。変更時は新versionとして別承認 |
| 測定 | Pauli sampling law・record形式・複素符号、固定shotsまたは正当な逐次confidence、系統誤差 |
| 強対照 | 同じ関数classのVQNHE、shadow／biased QSE、QSCI、古典が容易ならHCI/TPSCI等。追加accessは実費を加える |
| 目標と停止 | ε_E0とε_RRの違い、失敗率配分、近似誤差またはlower boundの扱い、未解像・失敗・retry条件 |
| 科学callとtruth | 許可する演算・call数、oracle／referenceの範囲・開封順、出力・log・instruction上限、Mandatory STOP |
| 資源 | phase／total wall-time cap、CPU/GPU/RAM/workerへの人工capを設けない。実際のCPU/GPU/memoryとdominant workloadを確認し、適切な並列化・cache・batch処理を準備。必要な参照検査を先に行い、precision・seeds・比較条件を維持 |

toolのpolling timeoutは科学runの時間上限ではない。共有環境・他jobを変更せず、既存の固定資源契約も書き換えない。

## 4. 既に承認された次の科学runはない

本packetの公開と同一性確認でCodexの作業は終了する。追加の紙上照合も実装も数値検証も、GPT／ユーザーが対象・範囲を選ぶまで実行しない。既存系列のPAUSE解除やA2証拠生成をここから派生させない。
