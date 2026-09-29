# Design discrepancies and unresolved execution fields

## Resolved during P0

- `B0`は`C_hat`ではなく第一研究の`B_frozen=1.01*C_hat`とした。
- HF 2条件はいずれも`T0=0.5*t_ana`でcap-activeだった。
- cap点2件はS0 exact-time v1.1にexact coordinateで存在する。
- cap外4候補はtracked artifactにexact coordinateがなく、将来のnew truth候補である。
- branch scoringはD2-A scoring auditのrepresentation-independent定義を採用し、old integer equalityを禁止した。
- related-work role mapとexternal-baseline gateを正式成果物へ追加した。

## Blocking before P1

1. `eta=0.10`はproposalであり、人間承認がない。
2. frozen sourceはcontinuous budget proxyだけを定義し、integerization/ceiling ruleを定義していない。
3. P1 wall-time limitが未固定。
4. このtracked snapshotにはsource pickle/cache本体がなく、将来実行pathのbyte identityを未確認。
5. cap外4件のdirect truth取得は未承認。
6. HF adapter、selector、freeze artifact、scorer、testsは未実装。

## Instruction tension

最新指示は「budget discretizationが未定なら`unresolved_requires_approval`でprotocol completion前に停止」と、「明示的未解決でもP0 completion conditionを満たす」の両方を含む。より保守的に、P0文書作成は完了させる一方、execution protocolは未承認・blockedとした。ceiling規則は発明していない。

## No discrepancy

pre-designのHF headroom、分類I=0、D2-A/C0解釈と今回の研究ストーリーに矛盾は見つからなかった。既存結果・status・artifactは変更していない。
