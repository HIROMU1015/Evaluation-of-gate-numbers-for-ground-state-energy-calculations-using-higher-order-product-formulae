# F01/F02/F05 HF bridge preflight（2026-09-22）

## 固定した比較

主比較はYoshida 4次について、同じ全電子HF/STO-3Gの平衡構造（two-term成功）と
1.5倍伸長（two-term失敗）を比較する。分子、基底、電子数、軌道数、PF、分割法を
固定できるため、N2/CO対HFを直接比較するより因果的な交絡が少ない。

`current_m3`は診断対照、N2/COの4 active-space条件は既存成功曲線との外部整合性
確認に限定する。N2/COの3136次元セクターについて密なD8演算子を新たに作ったとは
解釈しない。

## ローカル再構築監査

H01 runnerを使ったHF 2条件の再構築は各条件数秒で完了し、群数49、制限セクター
次元20、protocol hashはserver metadataと一致した。しかしHamiltonian SHA-256は
一致しなかった。

| condition | local SHA-256 | H01 server SHA-256 | 判定 |
|---|---|---|---|
| HF equilibrium | `91ea0e6e283b5538855c362d626046157348fbda67ca4a3ed59c32844fef8dde` | `cd074e4870223646ff51e98a72a679b33019cd96bb013de7536c0ceb3e7456c8` | 不一致 |
| HF stretch150 | `eda0a0f3e4fff1be6e90a59517edb9faf312af99b7331d0698454fb899dc7d45` | `c68722b3f9f98488e765afb49fa2d1153e41b2a8e84b6df21841400650cec499` | 不一致 |

この差は数値環境を跨ぐ再構築差であり、ローカルpilotを科学的結論に使わない。
本計算はGPUサーバー上に残るH01 pickleを直接読み、内部hashとcommit済みmetadataを
照合できた場合だけ実行する。

## 次の停止点

本bridgeでF01/F02/F05の機構を成功・破綻ペアに接続した後、一度停止する。その結果を
見て係数や判定閾値を変更せず、次段のpractical calibration最小版を別の固定protocol
として作る。
