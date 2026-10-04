# Test plan — not executed

今回実施するのはJSON/CSV parsing、source blob SHA-256、manifest、Git差分の非科学的静的監査だけ。toy matrix、numeric experiment、pytest科学tests、科学ライブラリimport、array deserializationを行わない。

## Future truth-free tests (separate review/authorization)

実装とexact test allowlist/source hashをfreeze後にだけ実施する設計。

1. Source/input identity：wrong PF ULP、H/sector/CISD hash、missing H6 cache、full archiveのexact fieldを拒否する。
2. Fit contract：same leading_fit/grid/gates、earliest qualifying、no fit→stopを確認する。現在new fitまたはtoy dataで実行しない。
3. Candidate freeze：9 absolute time/hex、r、t_ref、K、source matching。H4の保存fit算術3行を含め全input identityを再照合する。空欄6行を持つ現在のCSVは実行入力として拒否する。
4. Rank：H2 primary4/lower2、H4/H6 primary8/lower4、実rank不足はabstain、prefix再生成なし、action60上限を確認する。
5. Budget：gammaはcost multiplier、abs shiftを使用、nonpositive denominatorはinvalid、A_eta<=0 reject、ties smaller time、fallbackB0を確認する。
6. B2/H1：four-gamma frontier完全性、noise-floor sign、cheap instability、q freeze、q=0一致、q=1 consistency、conditional M1 access、unusable path、数値tieでB2を確認する。
7. Access negative cases：before final freezeにtruthを開いたら失敗。q=0 M1がH1へ漏れたら失敗。historical full runnerをpredictorへimportしない。
8. Freeze commit：7 artifact exact bytes、HEAD、source/input/protocol/candidate identityを拒否条件込みで確認する。
9. H1 accounting：q-first取得、shared/comparator completion、追加fresh chainなし、PF blockとvector数分離、actual combined timingとstandalone未測定区分を確認する。

## After prediction freeze

既存truth-readを含むfocused/full testsはこの後だけ。source/scorer testsの一覧とpass/skip gateはimplementation review時に固定する。pennylane任意依存skipを継承する場合も明示allowlistが必要で、未知skipを黙認しない。

scorerではsame-H reference、exact time hex、gap欠損/degeneracy、strict physical branch inequality、width coverage、abs direct continuous safety、baseline unsafeを検証する。old unwrap integer compareを使わない。

pre/post command、Python/package identity、開始終了時刻、pass/fail/skip、resource countersを軽量logとして保存。production科学値やthresholdをtest都合で変更しない。

現在これらのimplementation/testsは作成・実行していない。本文を「テスト済み」と読まない。
