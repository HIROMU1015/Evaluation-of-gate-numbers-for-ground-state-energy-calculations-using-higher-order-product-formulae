# GPT/userによる研究判断の反映とclaim scope

今回の方針判断はユーザー提供FS_C0_design.mdがauthorityであり、Codexが新規に選んだ研究路線ではない。ユーザーはその指示書に従うFS-C0を承認した。N2/COのscience実行、新truth、後段のFS-C2は未承認。

主題: 有限時間PF校正の追加計算を、推定器の精度競争ではなく、資源判断を改善する校正介入として評価する。主RQは、同じH/PF/時刻/目標精度で、状態改善とselected-time local proxy評価のどちらが、安全性を損なわず予算を減らせるか。

古典的offline校正であり、QPE入力状態・状態準備・初期重なりを変えない。新Response production armを作らず、H4 Response/Ritzはmechanismと対照evidenceとして保持する。Ritz、Krylov、線形response、OLS自体の発明や一般safe certificateを主張しない。

論文着地点の候補は *Decision-relevant calibration of product-formula errors for molecular phase estimation*。formalの誤差・費用分解、HF domain境界、H4介入を、新しい固定2×2比較へ接続する。介入が実際の資源判断を変えるという数値的支持は、C1未実行の現在はない。

新規性候補: 誤差原因とstate/local介入の対応、same-coordinate safe saving、truth-free domain下限による取得前除外、古典取得費とQPE rotation費の分離という組合せ。先行研究不存在・掲載可能性・優先権は未確立。設計書の文献リストはユーザー/GPT提供であり、FS-C0では新しい文献調査や独立の新規性確証を行っていない。

旧formal結果の停止・主張台帳は履歴として保持する。本設計は別の承認済み準備layerであり、formalの中心claimやsuccess数を書き換えない。H4 Outcome C point_onlyはbaseline S_under=0のstrict decrease条件に関係し、refitが利益を消したという意味ではない。raw Ritz underestimationも消去しない。

第2研究v2のevidence mapは `0a18168ae56852d7c754c28d05d5ce21bbce5b06` の版を明示して使用する。point/width/adoptionとsafety/resource valueを分ける設計上の参考であり、第1研究の成功数へ足さない。formal128 case、Phase0 pooled H4 588行、H4今回12座標、N2/CO予定2条件を独立Nへ合算しない。

C0で未解決にした項目をGPT/userへ返す。入力が欠けるためのNO-GOと、未実行介入への科学的不支持を区別する。C1の将来の結果でrank/gamma/fit/条件を救済変更しない。
