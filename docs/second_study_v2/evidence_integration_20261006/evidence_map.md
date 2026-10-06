# Budget reliabilityと追加情報のdecision value：統合evidence map

H-chainにはsmall-margin cheap-sufficient regimeがある一方、prospective一般分子では固定small marginがすべての選択decisionを安全にしない。M1のpoint accuracy、empirical width、abstention、resource decision valueは別の評価軸である。以下は承認済みDirection Cの資料整理で、普遍的なcheap方式や新spectral selectorの提案ではない。

## 1. Native contractと分母

| Evidence block | 評価単位・coverage | 候補時刻 | 比較anchor / 重複 |
|---|---|---|---|
| HF development | 2条件 ×3 =6座標 | T0, 1.3T0, 1.6T0 | B0は第1研究の継承benchmark |
| HCl development | 2条件 ×3 =6座標 | .5, .65, .8 ×t_ana | native gamma1.02比較。共通B0を作らない |
| H2–H8 native series | 7 attempted、6 reference適格 ×3 =18座標 | .5, .65, .8 ×t_ref | B0=.5t_ref, gamma1.01。H3はreference不適格 |
| Track G H6 geometry | 5 geometry ×3 =15座標 | .5, .65, .8 ×t_ref | 新truth12＋R1.0 anchor reuse3。B0はnative H-chainと同じ |
| Track R rank診断 | 3 systems ×3座標 ×4 ranks =36診断行 | native H6/H7/H8の同一9座標 | truth9点すべてreuse。rank4/8/16/32は独立標本でない |
| Prospective一般分子 | 16 attempted、13 ready/scored ×3 =39座標、4 families | .8, 1, 1.2 ×t_ref | B0=.8t_ref, gamma1.10。benchmarkであってsafe fallbackではない |

これらを合算したindependent Nやsafe率は定義しない。H6 R1.0 anchorはnative H6と重複し、Track Rはnative H6/H7/H8の9座標と重複する。同一conditionの3時刻、同一familyの複数conditionも独立標本とは数えない。H-chain size seriesには異なるcharge/population contractが含まれ、特にH7はcharge+1、multiplicity3、population4/2である。

Prospectiveの分母は最後まで **16 =13 scored＋2 LiH time-domain ineligible＋1 LiF input-reference ineligible**。LiH_R1.40/R2.60とLiF_R2.60はunsafeでも成功でもないterminal recordで、救済・置換していない。CH2は `repository_tracked_family_unseen`、固定population5/3で、global molecular groundやpure-spinのclaimにしない。

## 2. Cheap budgetのsafetyとmargin

| Block / arm | 保存結果 | 読み取れる範囲 |
|---|---|---|
| HF fixed gamma1.01 | 選択decision 1/2 safe（eq unsafe、stretch safe）。座標診断5/6 safe | 条件依存の過小評価とmargin不足。gammaをtruth後に選び直すpolicyを認めない |
| HCl native gamma1.02 | 同時刻座標診断6/6 safe | 既使用developmentデータ。prospective成功と混ぜない |
| H-chain native | 6/6 selected B2/H1 safe、全系q=0。fixed cheap1.01も同じ結果 | H1=B2の実現経路であり、conditional q=1の性能は未測定 |
| Track G fixed gamma1.01 | 15/15座標、5/5 geometry safe | R=.8–1.6 ÅのH6でsmall-margin sufficiency |
| Track G gamma1 post-hoc | 12/15 safe、R1.6の3点のみunsafe。max gamma_req=1.00217938 | 無marginの追加運用armではなく診断。ゼロmargin比率は用いない |
| Prospective B1 gamma1.01 /1.02 /1.05 /1.10 | 選択decisionのsafe数は6 /6 /11 /12（各分母13） | 固定four-arm frontier。結果後のgamma選択でsafe率を改善したとは書かない |
| Prospective B0 benchmark | 11/13 safe、2 unsafe | benchmarkを安全なfallbackと仮定しない |

共通の診断量は `e=abs(delta_direct)`、`c=abs(delta_C)`、underestimation `e-c`、margin `M_gamma`、additive slack `M_gamma-(e-c)`。gamma1ではmarginが0なのでslackを使う。gamma_reqは保存済みtruth診断であり、prediction/budgetの修正に使わない。

H6とprospectiveの対比は「H-chainのsmall-margin sufficiencyを一般分子へ移してはいけない」という適用限界を支持する。ただし15座標のcoordinate safetyと13 selected decisionsは別単位で、候補/B0 contractも異なる。純粋な分子family効果や同一試験の成功率差を推定したとは扱わない。

## 3. M1：point、width、abstention、decision value

| Block | Cheapよりpoint error小 | Empirical width coverage | 元のformal abstention |
|---|---:|---:|---:|
| HF native | 6/6 | 6/6 | 0/6 |
| HCl native | 6/6 | 6/6 | 1/6 |
| H-chain native | 11/18 | 18/18 | 12/18 |
| Track G rank8 | 9/15 | 15/15 | 15/15 |
| Prospective | accepted-performance比較なし | 診断39/39 | 39/39、conditionも13/13 |

Track Gの選択点ではR≤1.2でM1 point errorがcheapより小さく、R≥1.4では大きい。全15座標でwidthがerrorをcoverしても、positive QPE allowanceを得られずformal abstentionは変わらない。Empirical coverageをcertificateと呼ばない。

| Track R primary diagnostic rank | Point改善 | Positive allowance /有限仮想budget | Same-time cheapより小budget | 比較不可budget |
|---|---:|---:|---:|---:|
| 4 | 0/9 | 0/9 | 0/9 | 9/9 |
| 8 | 3/9 | 0/9 | 0/9 | 9/9 |
| 16 | 9/9 | 2/9 | 0/9 | 7/9 |
| 32 | 9/9 | 6/9 | 0/9 | 3/9 |

Rank16/32のpoint改善は、固定widthによるsame-time budget advantageへは到達していない。0/9にはbudget自体が存在しない行を含むため、9個すべての有限budgetが負けたとも、9個のunsafe budgetが得られたとも書かない。Rank32の有限6 budgetは全てsame-time cheapより大きい。この診断はrank rescueや新operational policyではなく、元rank8 formal結果も不変である。

支持される機構上の整理は **geometry/rank → point accuracy → width → QPE allowance / decision window → resource value** を分離すること。Rank8 point accuracyだけを改善すれば利益が出る、という説明では足りない。全スペクトル方式に価値がないという不可能性主張にはしない。

## 4. 誤差分解とheadroom

Same-H・sector・energy origin・physical absolute branchのclosureがある場合だけ、PF-sideとH-reference誤差を分ける。Native H-chain18、Track G15、Track R36診断行では閉じているが、重複を含むので独立件数として合算しない。HF/HCl12座標とprospective39座標は本資料でもindeterminateのまま残す。Prospectiveのbranch/gap互換診断37/39はabsolute target correspondenceの確認ではない。

Track Gでは大きいRでPF-sideとH-reference側の誤差が両方増え、差がshift errorへ寄与する。したがってshift estimateの一致は絶対PF固有値の回収精度を保証しない。閉じた代数的分解も、rank/geometryの独立因果寄与やcertificateではない。

Track G選択点のsame-time cost-free oracle headroomは **0.898–2.690%**。一方、B0比削減は **32.236–33.102%**。Native H-chainではleading modelだけで **32.774%** の削減を説明し、保存結果は **32.830–33.094%**。時刻変更と先頭モデルが説明する構造的部分と、凍結budgetが実際にsafeだった実証を分ける。両者の差を独立因果成分と推定したり、約33%をspectral calibrationの利益とすることは認めない。

Cost-free oracleはtruthを無料で与えた上限的診断で、実測のM1改善やclassical+quantumのnet gainではない。別runのwall/RSSを足したcombined costや共通性能指標も作らない。各blockのstage/resource監査は原本を参照する。

## 5. 論文に渡す対応関係

| 承認済み論点 | 主要evidence | 限界・未確立事項 |
|---|---|---|
| cheap内部安定性とbudget safetyは別 | HF eq反例、prospective fixed gamma1.01の7/13 unsafe | 共通normalized contractの因果比較ではない。B2/H1 gateを改修・復活しない |
| H-chain small-margin regime | Native size series、Gのgeometry15/15 safe、gamma_req | H6以外のgeometryや一般分子へ一般化しない |
| point精度だけではresource valueを説明できない | Gのpoint/width/abstention、Rのrank16/32 point改善・0/9 budget advantage | empirical width・有限rank・保存candidateに限定。スペクトル情報の普遍的無価値ではない |
| shift精度とPF固有値精度を分ける | 同一H/origin/branch closureを持つH-chainの誤差分解 | HF/HCl/prospectiveの不足tupleを推定・追加計算で埋めない |
| 構造的時刻削減と追加校正利益を分ける | H-chain model対実測、Gの小さいsame-time oracle headroom | classical costを含むnet gain、spectral由来の約33%改善とは主張しない |

H-chainの追加scienceは閉じる。次の停止点は、この資料のGPTによる論文配置・claim scope確認であり、H9/H10、rank64、追加geometry/gapの実行ではない。

正確なscalar、origin/result commitとverified snapshotの分離、原本blobの固定リンクは [source registry](../../../artifacts/study2_evidence_integration_20261006/source_registry.json) と [集計JSON](../../../artifacts/study2_evidence_integration_20261006/evidence_scalars.json) を参照する。
