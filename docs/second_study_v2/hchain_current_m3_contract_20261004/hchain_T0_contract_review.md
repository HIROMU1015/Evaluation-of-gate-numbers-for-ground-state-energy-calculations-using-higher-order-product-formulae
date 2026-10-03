# H-chain T0 contract review

結論: H2/H4/H6へ共通の `T0=0.5*t_ana` を採用する根拠は未成立。数値の半分を計算できることと、HFと同じbaselineの意味を持つことは別である。

## 回復できたscaleと情報境界

- H4: 第一研究Phase AのCISD decision trackに `alpha=1.3583752443385904e-5`、`t_ana=1.237648718781152` が凍結されている。leading fitはearliest qualifying window、次数4、noise floor `5e-13`、order tolerance `0.2`、R²下限 `0.999`。新fitは行っていない。
- H2: H01のCISD D4 expectationから `t_ana=1.847045747947876` は回復できる。ただしD4 coefficientのmodelであり、HFの有限時刻cheap echo proxyから得たscaleと同じ取得規約ではない。
- H6: canonical係数の旧holdoutに `t_ana=1.130328683486731` はあるが、exact-ground stateとexact energyを使用した診断値。CISD predictorのscaleとしては使わない。
- 旧H2/H4 refinementおよび初期H6 holdoutはexact-informedで、compact係数の末尾2個がcanonicalと各1 ULP異なる。近さによるreuseは認めない。

## HFでhalf-scaleが使われた理由

HF protocolの2条件はともに `cap_active=true`、`fallback_reason=cancellation`。実装ではcancellation、sentinel residual、sign mismatch/indeterminateのいずれかでfallbackが発火したときだけ最大時刻を `0.5*t_ana` に制限する。これは普遍的なanalytic baselineではない。さらにcapは探索上限であり、一般には最小費用時刻が必ずcap端点になるとは限らない。

H4のnative第一研究selectorは `[0.25,2.0]*proxy_t_ana` の401点上で二項CISD modelを使い、current_m3内では時刻 `1.2397952598800155` を選択している。これはhalf-scale fallback baselineではない。全PFでの保存selectionはm5_bestであり、その時刻・予算をcurrent_m3へ移さない。

## 5条件の判定

| 必須条件 | 判定 |
| --- | --- |
| canonical current_m3のoperational t_anaが一意 | H4の既存CISD decision trackでは回復。H2はD4という別model、H6はoracle由来で共通規約未成立 |
| 0.5 t_anaが数値的に有効 | H4の半scaleは有限正値でmodel/proxy signalもepsilon未満。ただしtruth safetyやbaseline正当性の証明ではない |
| baselineにscorer truth/direct optimumを使わない | 本監査はどちらもT0/B0構築に使っていない |
| H2/H4/H6で同一の定義 | 未成立。proxyとD4とexact-ground scaleを混ぜない |
| HFと同じ保守的domain baselineの意味 | 未成立。H-chainでHF fallbackに対応するdomain-loss契約がない |

## H4 half-scaleの既存scalar診断（candidateではない）

`0.5*1.237648718781152=0.618824359390576`、hex `0x1.3cd68be319f20p-1`。既存CISD primary trainingにexact同時刻が1件あり、signed proxyは `-1.992711385932872e-6 Ha`。canonical first-study positive truth格子は `0.1--2.475297437562304` を含むが、このhalf-scaleのexact truth行は0件。格子の範囲内というだけでnearest/interpolationのtruthを代入しない。保存branch不合格がこの点に「ない」とも認定しない。

`T0` は全系 `null`。上記診断時刻を3候補へ展開せず、別途baseline design reviewへ戻る。
