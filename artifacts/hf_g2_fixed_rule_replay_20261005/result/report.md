# HF G2 fixed-rule replay result

Status: `second_study_v2_hf_g2_fixed_rule_replay_complete_review_required`

Classification: `D_gate_false_negative`。既知developmentデータのreplayであり、holdout・新規取得・安全性certificateではない。

| 条件 | q | B2 gamma | B2 safe | H1 safe | H1変更 | 判定 |
|---|---:|---:|---|---|---|---|
| HF_full_eq_sto3g | 0 | 1.01 | False | False | False | D_gate_false_negative |
| HF_full_stretch150_sto3g | 0 | 1.01 | True | True | False | A_cheap_sufficient |

## 解釈と停止

q=0/unsafeが一件でもあればcheap stability gateのfalse negativeであり、低budgetを利益に数えない。q=1の変更はfixed-cheap frontierで再現できるかを別に評価する。Direction Cは暫定のまま、最終RQ・paper landing・gate redesignの判断へ戻る。

新規PF/H action、M1、truth、gap、fit、GPUは全て0。保存作用回数と実際のreplay I/O/runtimeを混同しない。q=1 combined acquisition costは未測定で、保存separate-arm時間のmax/sumはscenarioであり厳密上下界ではない。

元HF robust_signal、元S1A D、過去H-chain/D2-A判定を変更していない。HCl/LiF/C1/D2-B・追加baseline・threshold救済・pushは自動許可しない。
