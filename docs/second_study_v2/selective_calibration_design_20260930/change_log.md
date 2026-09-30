# Change log

## Source reviewからrepo protocolへの変更

1. HF bridgeを`user_report_only`から直接検証済みsourceへ更新した。
   - origin content: `d74d9020c2e1e97cdf120e8a0974d45cb296da4a`
   - provenance/verified snapshot: `36989cd0a2fe8b843ec2375ec344bebcc2c9ef0c`
   - manifest SHA-256: `03be5b9ca8aadc2eef444b3bade9a4b9d512228e48517a601f1418eee9fcaf9f`
2. B2とH1を別方式として固定し、H1がB2と同じcheap policyを共有する公平性条件を追加した。
3. acquisition decisionとfinal-action decisionを別freeze対象にした。
4. domain、adaptive-cheap、spectral-incremental、selective-acquisitionの4効果を分離した。
5. HF/HCl/LiF/N2/COを、完全matched、contract違い、M1欠落、未監査へ保守的に分類した。
6. combined H1費用は保存arm時間の加算で実測済みとはしないことを固定した。
7. B2 threshold、H1 threshold、非劣性幅、古典budget上限、実用効果量を未確定のまま保持した。
8. 新科学計算、fit、holdout、external baseline、pushを承認しなかった。

## 変更していないもの

- 第1研究およびclosed second-studyの正式判定。
- HF pilotの`robust_signal`。
- B1 gamma frontier、M1 module、candidate/prefix/widthの保存定義。
- HF prediction/result artifact。
- bridgeの内容・provenance commit。
