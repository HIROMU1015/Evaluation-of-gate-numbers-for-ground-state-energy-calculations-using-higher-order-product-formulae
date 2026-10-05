# HF G2：two-condition fixed-rule replay

Direction C（追加calibration情報のdecision value）をユーザーが暫定承認したことを受けた、一回だけの既存scalar replay。最終RQ・論文story・現状ページはまだfreezeしない。

## Scopeと規則

HF equilibrium / stretch150のcurrent_m3、保存CISD identity、全6候補T0/1.3T0/1.6T0を使う。元S1A Rules 1–3、gamma 1.01/1.02/1.05/1.10、sign floor、HF native eligibility/selector、epsilon/beta/K/etaを変更しない。元HFのB0をそのまま使い、新cheap T0から作り直さない。

旧S1A実装は4-condition contract欠損で停止するrunnerだった。今回は別scope・別runner・別classificationであり、旧S1AのDを解除するものではない。[protocol](protocol.json)と[source registry](source_registry.json)をexecution前にcommitする。

## 情報境界

Combined HF predictionはtrusted lexical projectorがraw bytesを読みSHAを照合する。Cheap段階ではB1 allowlistの値だけをJSON復号し、M1 subtreesはlexical skipする。これはfield-level procedural boundaryであり、OS sandboxや既知結果を忘れる実験ではない。

cheap/q commit → q=1だけ保存M1を開く → H1 commit → q=0 M1 comparator completion → final prediction commit → HEAD/blob照合 → 保存truth6点で一回採点、という順で停止する。H1がq=0 comparatorの結果を事前に使ったことにしない。

## 判定とcost

Budget安全性はabs(delta_direct)+beta*K/(t*B_frozen)<=epsilon_E。T0 reproduction failはcap-outのprocedural invalidity。Branchはshift/gapで採点しunwrap整数を比較しない。Empirical width coverageとcertificateを分ける。

G2 taxonomyはユーザー承認のA/B/C/Dに沿う別分類。q=0/unsafeがあればDを優先。q=1の改善もfixed-cheap frontierで再現できればunique spectral valueとはしない。Contract不足はincompleteであり0効果ではない。Selective positiveには非自明なq混在も必要。

保存cheap6 PF/6 H exponential、M1 48 PF/48 H matvecは既存取得費用のattributionであり今回の作用回数ではない。今回の新科学作用は0。Separate-arm時間max/sumはscenarioのみでcombined acquisitionの厳密上下界ではなく、q=1 actual combined costは未測定。実際のreplay I/O/decision/runtime/RSSは別記録する。

## 停止と未確定事項

Practical spectral effect、classical ceiling、noninferiority margin、新規性の最終確認は未解決のまま。結果後にthreshold/gamma/width/q規則を変更しない。HCl/LiF/C1/D2-B、追加分子・PF・時刻、外部baseline、combined取得計測へ進まない。Pushは未承認。既存成果物・current_research_status.mdは変更せず、G2 result commit後に人間の最終方針レビューへ戻る。

実装testsはstdlib/syntheticのみで分子artifactを読まない。Full legacy suiteや旧科学runnerを呼ばず、保存snapshotの既知nongreen legacy状況を今回のtest成功で置き換えない。
