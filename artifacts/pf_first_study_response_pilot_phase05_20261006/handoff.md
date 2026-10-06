# GitHub handoff — Phase 0.5 design

Repository: `HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae`
Branch: `pf-first-study-response-pilot-phase05-20261006`
Base/source verified snapshot: `1b7b2fc959185ca1be06581682a67d28e02db21c`
Publication commit: the immutable commit containing this file; full40 SHA, pinned link and independent remote verification are supplied in the final handoff message (avoids commit self-reference).

読み順はREADME→normative JSON／protocol.md→algorithm→cost→novelty→GO/no-go→verification/source manifest/tests。

検証対象はsynthetic kernelsとsource byte identity、freeze/hash境界、予定counterである。H4のHamiltonian/state archiveをdecodeしてscienceはしていない。Origin/result commitとverified snapshotはsource manifestの別field。Manifestは自分自身を除外する。既存formal、Phase0、S4資料は全てbaseと同じblobを維持する。

science_ready=trueは設計準備状態。実行許可false、production adapter未接続。将来の実装タスクとexact science action planはGO_NO_GO_FOR_SCIENCE.jsonに固定した。現在のscience countersは全て0。

GPT/userに判断してほしい項目：このprotocolをH4 scienceへ進めるか、ZVZBとの代数対応を踏まえてPF-specific統合の新規性をどの程度のcandidate claimとして置くか。H4実測、response-specific tradeoff、net resource gainは未確立で、今回は研究中心claimを変更していない。

公開状態は今回のGitHub handoffで別報告する。旧artifactにあるpush未実施／未承認などは作成時点の記録として保持し、後の公開で書き換えない。No new production matrices/vectors/states/binaries are published.
