# Resource accounting plan

科学的情報取得費用の新規測定は0。existing time gridは費用測定結果ではなくmetadata一覧である。

## Separate accounts

- shared: input/hash/load、PF component preparation/materialization、cache cost。既存cache費用を0とみなさず provenance付きreusedとして別記録。
- cheap: PF state action 1/coordinate、H exponential action 1/coordinate、echo/diagnostic arithmetic、wall、CPU peak RSS。
- M1: one shared-prefix Arnoldi chain、PF per-vector actions<=8、H matvecs<=8、component gates、sparse multiplies、orthogonalization、projected solves、wall、CPU peak RSS。
- scoring truth: exact reused/computed座標数、full PF/eigensolver等の古典費用をcalibration armから分離。

異種actionを1 scalarに換算しない。cheap expm_multiplyの内部H matvec数は継承実装ではexposedでないためunknownとする。旧H4 proxyはfull PF matrixで取得されており、同じobservableだからといって新vector-only armのcostへ置換しない。M1 costを歴史的direct diagonalization timingで代用しない。

今回はcheap/M1両armを全selected座標で取得する計画であり、selective routingやcombined H1 costは評価しない。共通state/load費用の二重計上を避けると同時に、cache reuseを未測定の利益として宣言しない。

## Limits versus actual missing counts

添付のworst-case構造上限は9 coordinates、cheap PF/Hexp各9、M1 PF/Hmatvec各72、direct truth最大9。しかしtime/state/scorerが未確定なのでexact missing countはnull。今のrequired new actionsはnot_evaluableであり0回の科学計算とは別概念。wall/memory ceilingは別execution reviewで固定する。GPUは不要かつ未承認。
