# matched-data coverage review後の研究判断事項

次の外部レビューでは、保存結果の良否に合わせて数値を選ばず、以下だけを判断する。

1. HF/HCl 12座標の`no-fit S1A replay`を、科学的prevalidationではなく実装・leakage監査として承認するか。
2. development familyをHF/HCl/LiF/N2/COのどこまでとし、condition単位・family単位のfoldをどう固定するか。
3. 異なるcandidate contractを保持してpolicyをcontract-invariantに設計するか、一つの共通contractを事前固定するか。
4. LiF 4座標とN2/CO 12座標のM1欠落について、全16点、条件単位のsubset、または取得なしのどれを選ぶか。
5. selective H1 costを実測するか、shared/reuseを0としないconservative no-reuse scenarioで比較するか。
6. B2/H1 threshold、quantum noninferiority、classical ceiling、minimum effect sizeを、既存10条件のoutcomeを見ずに固定できる根拠を何に置くか。

レビュー前にはS1A/S1Bの実装、deterministic cheap materialization、M1取得、truth生成を開始しない。
