# Resource accounting plan

## Proposed P1 envelope（未承認）

| Item | Limit |
|---|---:|
| Conditions / coordinates | 2 / 6 |
| Arnoldi dimension | 8 |
| PF vector actions | 8/coordinate, 48 total |
| H matvecs | 8/coordinate, 48 total |
| local-proxy PF actions | 6 total |
| combined PF vector actions | 54 total |
| H exponential actions | 6 total; internal matvecs separate |
| cap-point truth reuse | 2 |
| new cap-exterior truth | maximum 4, separate authorization |
| new anchors | 0 |
| full H/PF eigendecomposition in predictor | 0 |
| CPU / BLAS threads | 1 process / 1 each |
| peak RSS | 4 GiB |
| GPU | 0 |
| wall limit | unresolved before P1 |

## Counters

PF action、block call、component gate materialization、sparse multiply、H matvec、H exponential、inner product、reorthogonalization、projected solveを独立counterにする。state/group preparationは`cached_shared`と`newly_incurred`を分ける。

predictor wall、freeze/commit overhead、scorer truth wallを別々に保存する。stored truth readとnew truth computationも別counterにする。

## P0 actual counts

全て0：PF/H action、Arnoldi、truth生成、gap、GPU、selector/threshold fit。実施したのはtracked sourceの読取、hash、Git provenance、保存scalarのprotocol算術だけである。
