# Change log

## 2026-09-30

- `18939483cfba23c5bce992c9cd9825ae4b8dd6b6`のselective-calibration designをbaseにread-only matched-data coverage reviewを開始。
- HF/HClの12 coordinate tupleをstrictly materialized cheap/M1/truth tupleとして確認。
- LiFの4 coordinateをcheap/truth-only tupleとして確認。
- N2/COについて、初期inventoryの「truth exact tuple未監査」を修正。first-study exact-time triplet 12点のtruthを確認し、center cheapはmaterialized、非center cheapはfrozen modelからreplay可能、M1は欠落と分類。
- source-pickle、Hamiltonian、CISD-state identityの強度をfamily別に分離。
- combined H1 shared/reuse costが全条件で未測定であることを固定。
- existing dataはno-fit S1A replayに限り十分、policy developmentと追加取得範囲は外部レビュー前には未確定と判定。
- 新しい科学計算、値materialization、policy/threshold fit、artifact変更は実施していない。
