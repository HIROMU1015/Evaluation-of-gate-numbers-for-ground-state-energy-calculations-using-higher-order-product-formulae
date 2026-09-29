# PF研究成果整理bundle｜2026-09-29

**v1.0：Git evidence audit済み内部成果整理版。人間レビュー待ち。**

固定snapshot：`fe55a0cb1dfe303eb2e878d6c098b6a7a556c5e3`
元ZIP SHA-256：`b3a3d0054a17c428cfe0d8958c70892b36538c84fdf72061d6e4f1b36726cc85`

## 読む順序

1. [短縮版](PF_research_storyline_20260929.md)
2. [研究成果整理レポート](PF_research_outcomes_20260929.md)
3. [主張・証拠台帳](PF_research_claim_evidence_ledger_20260929.md)
4. [証拠監査報告](evidence_audit_report.md)
5. [訂正履歴](correction_log.md)

機械可読資料：

- [source registry](PF_research_source_registry_20260929.json)
- [source manifest](source_manifest.json)
- [claim audit](claim_evidence_audit.json)
- [decision](decision.json)
- [bundle manifest](bundle_manifest.json)

## 監査範囲

CL01–CL30を指定commit・pathへ照合し、主要な保存CSV/JSONのcount・分類・表示単位・費用値を再確認した。
科学数値の訂正は0件。修正はprovenance二層化、CL30の`governance_scope`分離、manifest自己除外明示である。

これは文書監査であり、分子生成、状態計算、PF/H作用、Arnoldi、gap計算、toy実験、GPU操作は行っていない。
C1、D2-B、holdout、新PF、追加分子は未承認のままである。

## 証拠の境界

公開H-chain研究は指定プレプリント版の報告として扱う。第一研究、第二研究、R1、D1、D2-A、audit、C0は、
それぞれのevidence classと独立性を維持する。未解決事項は`decision.json`と監査報告に残しており、
文書統合完了を研究上の未解決問題の解消とは扱わない。
