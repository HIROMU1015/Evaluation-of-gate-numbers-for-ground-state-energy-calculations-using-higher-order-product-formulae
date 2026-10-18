# 未解決事項とCLOSEDの適用範囲

2026-10-18 JST。[ユーザー承認済み判断](research_closure_decision.md)を適用する。**CLOSEDは固定された現Gの独立新アルゴリズム探索だけに及ぶ。未解決事項を不可能性証明へ変更しない。**

## 未解決のまま保全する事項

| 事項 | 現在の意味 | 今回実施しない作業 |
| --- | --- | --- |
| P-d | 非自明な連結電子Hamiltonian familyでの有用性は未判定。P-dの追加構成・数値検証は未実施 | family構成、追加紙上検証、simulation、数値solver、改良heuristic探索 |
| native資源費用 | 回路・noise・routingを含む実費・優位は未確立。理想record lawの対応からhardware同等性は出ない | 回路build／compile／benchmark、native最適化 |
| 元Hの絶対E0精度 | Ritz energyと統計幅だけでは有用な絶対E0保証は得られていない。conditioning・support等も残る | lower bound／certificateの新構成、追加truth、他系列保証の移送 |
| 網羅的priority | P-cの限定照合は世界的priorityの網羅認証ではない | 文献探索のやり直し、新しい重要科学レビュー |

これらは「不可能と証明済み」ではない。一方、**現Gを独立新アルゴリズムとして継続する根拠が得られなかったため、追加検証へ進まない**という判断は確定している。未解決欄は実行backlogや継続grantではない。初期packetに残る将来検証案も、現在のCLOSEDを自動的に解除しない。

## 他系列とD1／D2

| 対象 | 今回維持する状態・境界 |
| --- | --- |
| J1・Q1 | PAUSEを維持。新しいpulse／level挿入規則を探索しない |
| R1-P | 独立候補不保持を維持 |
| 集団遷移生成 | PAUSEDを維持 |
| SOS-PF A2 | NOT_ADOPTEDを維持。GのCLOSEDをA2のCLOSEDへ読み替えない |
| 第一・第二研究 | 既存状態・claim・承認・STOPを変更しない |
| PR Track A/Bと他系列 | 既存状態・law・価格・結果・grantを変更しない。再開しない |
| QSE・QSCI・VQNHE・coherence保持部分空間法全般 | 今回のCLOSEDの対象外。領域全体への否定や採否判断を行わない |

D1の既存制約を維持し、block-encoding／qubitization中心への無断移行を行わない。D2では元の有限基底電子Hamiltonianと指定sectorの絶対E0を保持する。scalar・一体項・残余相互作用、モデル／実装誤差の会計を省略せず、部分空間Ritz値を絶対E0の精度保証と取り違えない。今回新しいHamiltonian、近似モデル、access、成功条件へ切り替えない。

根拠はSOURCE registryのX01–X03、P01–P02、初期packetの`research_problem_and_access.md`。横断整理の古い状態表は作成時点の記録として読む。現在のユーザー指示が明示する維持状態を記録し、別chatの最新科学結果を統合・査読したとはしない。

## 将来再検討する場合

再検討の必要性・対象・価値はユーザー／GPTが別途判断する。今回の固定Gとの関係、既知法に同じ有利な条件を許した具体的な差、合法な情報取得・費用・保証の範囲を示した材料と、明示的な再検討指示が必要となる。これは将来条件の記録であり、新しい候補の提案・採択や実行契約ではない。

再検討が承認されても、新しい科学計算・保存値再解析・回路実行等には、その対象と範囲に対する別の明示承認が必要である。旧SOURCE・結果・grant・authorization・marker・STOP・固定資源条件を書き換えたり、使用済みgrantを流用したりしない。

**Codexは今回の公開・照合で停止する。既に承認された後続研究作業はない。** 次の方向の探索、実装、科学計算、詳細科学レビューを自動開始しない。
