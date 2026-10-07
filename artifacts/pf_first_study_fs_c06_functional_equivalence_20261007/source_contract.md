# Source contract

historical source（missingのH01 pickle）、validation source（decode/reconstructして検証した4候補）、operational source（全gate PASS後にoracleを除いたexport）を区別する。今回は最後のsourceは存在しない。

規範はdecode前に固定した[validation_contract.json](validation_contract.json)。whole-pickle SHA mismatch aloneは不採用理由にしないが、historical H SHA完全一致は必須。historical SHAは履歴として保持し、別SHAのsourceをhistorical original recoveredとは呼ばない。

順序は、H/metadata/sector/geometry/current_m3 → ordered group identity → CISD fingerprints → M00 3-point proxy/fit → echo/backend → independent cold replay → sanitized export。Hが不一致なら後続PF/echo/fitはNOT_RUN。既存候補の失敗後に限りhistorical pipelineで各条件1回再構成を認め、設定変更による2回目を禁止する。

metadata許容差1e−9 Ha、state fingerprint1e−6、proxy/echo1e−9 Haはhistorical H02由来。追加norm1e−10はhistorical scalar-invariance由来。selected prediction1e−9 Ha、係数・budgetへの伝播規則もdecode前に固定した。許容差を結果後に変えない。

group count、term count列、ordered SHA列、application/component order、numerical contentを区別する。group数が一致してもordered identityが通ったとはしない。既存候補のnumerical contentは単なるmetadata attestationでは保証しない。今回の順序付きgroup hash attestationは不一致、numerical contentチェックはH棄却で未実施。

H digestはhistorical sparse hashのshape int64、CSR indptr/indices/dataのstored contiguous bytes。sort、dtype cast、丸め、再orderingによる一致化をしない。CISD standalone historical hashは残っていないためbitwise一致を必須にせず、norm/energy/error/variance/residual/PySCF diagnostics/sector outside normを比較する。ground overlapはvalidation sandboxだけで確認する。

exportは全gate PASSのときだけallowlistから作る。許可fieldはH、ordered component spectra、CISD、restricted basis、sector/mapping metadata、removed constant、current_m3 order。exact ground/vector/overlap/gap、direct PF truth、branch truth、旧成否labelは除く。今回exportはなく、operational identityのSHA/dtype/shapeはnull。候補のdigestをoperational identityとして流用しない。

M00保存proxy/係数/B0は変更しない。original H01 echoの他の時刻をM00 trainingへ流用しない。v3のtrainingはC0.5で閉じた3点、M10は同一絶対時刻、M11 primary、M01 challenger。source受理後のproduction backend成功pathは今回未確立。unit testsのsynthetic backendでその未確立を埋めない。
