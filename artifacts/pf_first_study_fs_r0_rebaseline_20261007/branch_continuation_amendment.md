# FS-R0 truth contract — approved user/GPT amendment

2026-10-07 JST、Codexの照会に対するユーザーの明示回答を反映した。
原指示§44の分類は `NO_GO_PROTOCOL_OR_BACKEND`、具体的な最終statusは承認された
`NO_GO_BRANCH_CONTINUATION_UNCLOSED` とする。

承認済み処理：

- FS-C0.6 one-shot bytesをnew sourceとして固定する作業、4-arm protocol、prediction/truth barrierは完了させる。
- new direct truthはN2/COそれぞれt0の1点、合計2点に固定する。
- historical truth/branch IDs/anchorsを流用しない。
- old S0のphysical branch correspondenceは同一source上のlower-time anchorからのcontinuationである。
- 新sourceにはそのanchorが存在しない。2点capの範囲ではphysical branch correspondenceを閉じられない。
- 単一時刻の最大ground-overlapだけの選択へ変更しない。これはdirect truthの定義の変更となる。
- `NO_GO_BRANCH_CONTINUATION_UNCLOSED` として停止し、FS-R1や追加anchor/intermediate truthを実行しない。

これはsource reconstruction失敗ではなく、truth-generation contractの未完了である。
source freeze、4-arm protocol、barrier、2点cap、physical branch未確立を別々に報告する。

次の研究判断はGPT/user側で行う。branch-anchor extensionを正式承認する場合には、
truth budget（2→4点以上）、anchor time、continuation rule、residual/overlap/tie ruleを別途事前固定する。
もう一つの選択肢はdirect PF truthを用いる路線を止めることである。
いずれもFS-R0内では選択・実行しない。

回答の出典：このセッションのユーザー/GPT回答。Gitで公開する本ファイルは回答の記録であり、
別のscience authorizationを与えるものではない。
