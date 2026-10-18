# B-01：最小着手判定

**総合技術判定：E（現時点で新たな構成研究の着手を推奨する技術的根拠なし）。** B-01の正式CLOSED・PAUSED・採択を記録する判断ではない。数学命題の不可能性も示していない。最終の研究判断はGPT／ユーザーへ返す。

理由は、D1の必要情報との関係は具体化できたが、目標費用の保証付き手順、対象familyで有用なetaの取得費、標準統計を越える独立した機構の三点が閉じなかったためである。別seed・別family・別認証法の追加探索で救済していない。

## A～Eの切り分け

| 区分 | 今回の判断 | 根拠・限界 |
|---|---|---|
| A 限定構成研究へ進む根拠 | 未充足 | Hadamard情報からの接続はあるが、eta取得費と同時保証/費用が未確立 |
| B 既知方法で目標を解決 | 未確認 | gap不要E0法やfilter認証は既知。ただし指定T_max・N_target・D1を同時に満たす対照を特定していない |
| C 限定障害 | あり | 既知二次moment検定の精度、Gaussian背景variance、条件付き正規化・拒否費用。全認証の下界ではない |
| D 未判定 | 数学的存在性・実用接続に該当 | D1内での目標同時達成、実用eta、先行保証の最適な統計改良は未判定 |
| E 着手推奨の技術根拠なし | 総合判断 | 主要三点が未確立のまま。新機構・新規性・資源改善を支持する証拠がない |

根拠を[access/定理](b01_access_and_theorem_audit.md)、[eta/coarse](b01_eta_and_coarse_interval.md)、[標準統計](b01_standard_statistics_screening.md)に分けた。これらは技術照合であり、重要GPT科学レビューを代行したものではない。

比較した目標は次式であり、今回得た保証ではない。

\[
N_{\rm target}=\widetilde O\left[
\eta^{-1}(\sigma^2\epsilon^{-2}+\log\sigma^{-1})
\log\delta^{-1}\right],\qquad
T_{\max}=\widetilde O(\sigma^{-1}).
\]

coarseとetaの取得費を含む総Nなのか、取得済み入力に対する追加認証Nなのかを分ける。前回カードの目標は後者の比較式であり、総費用改善を認定していない。

## 成立している部分と未解決部分

- **条件付き問題の定式化：可能。** 既知eta、合法なcoarse区間、理想controlled evolutionの枝なら公表法のインターフェースを記述できる。
- **D1の情報取得：一律NO-GOではない。** Fourier/HadamardからGaussian convolutionを評価する既知法がある。ただしfilter成功標本のlaw・分散・費用とは別である。
- **Soundness：既知定理への条件付き接続。** coarse/etaと必要moment精度のeventが成立した場合の公表決定部分を参照できる。同時確率と条件付き誤答率を混同しない。
- **Completeness：追加の入力class条件が必要。** 真のgapとsigmaの関係、seed重み、windowとmoment精度を保つ必要がある。gap値をテストへ渡さずに、この関係を満たすclassで受理するという命題である。
- **eta取得：限定経路はある。** 既知energy/fidelity評価、可解参照と小摂動の十分条件、moment＋spectral enclosure法。前回の2×L ladder/一般分子について正の保証と有用費用は未取得。
- **coarse区間：既知etaなら既知経路あり。** Lin–Tongのsigma精度取得費を総費用へ加える。
- **標準統計：目標を閉じた証拠なし。** 一部上界を改善し得るが、epsilon/etaの目標powerを同時達成したとはしない。失敗したscreeningを新アルゴリズム必要性の証明にしない。

## 次に判断を変え得る最小の証拠

以下は新規作業の発注・科学実行契約ではない。ユーザーが別途対象を承認する場合の判断条件である。

1. **条件付きmomentの精度接続。** 公表Appendixの未正規化momentsから条件付きmean/varianceへ、q>=c etaを保持した全誤差配分を示す証拠。必要な精度が公表費用または既知統計改良で満たされるかを確定する。新しいfilter設計より前に必要な、既知式の接続である。
2. **同じD1 accessの費用命題。** 合法eta/coarseを条件に、同じsoundnessと指定classでのcompletenessを持ち、全freshコピー数・T_max・Fourier/古典処理費がN_targetと両立する既知定理、または対象record模型に限定された障害。存在命題も不可能性も今回未証明。
3. **対象familyのeta証拠。** 既に指定したseed/sector/係数条件について、FCI正解や推定gapを無料化せずに正のetaを保証し、その取得・検証費を示す資料。weak-perturbationの空でない十分条件があることだけでは、前回の強相関ladderへの接続にならない。

これらが既知統計・既知certificateで閉じるなら新量子アルゴリズムの必要性は低い。閉じなくても独立新機構が残るとは限らない。現時点で新しい認証機構を探索するための根拠を作ったとは扱わない。

## 総費用とD2

`C_input + C_eta + C_coarse + N_prep C_prep + C_evolution + C_readout + C_classical + C_memory`を分離する。D1外対照ではfilter、反射、A†、そのancilla/成功費も加える。原Hへの絶対energy復元、モデル/係数近似、simulation、state品質の誤差を含める。Nや総queryの漸近だけからnative優位・実用性は結論しない。

既存A2 NOT_ADOPTED・現実用経路の追加投資なし、R1-P独立候補不保持、G CLOSED、集団遷移PAUSED、固定条件付き測定CLOSEDを維持する。J1/Q1、第一・第二研究、PR Track A/B等の状態も変更しない。

**公開・独立同一性・保全照合後にMandatory STOP。** 次の継続・保留・終了はGPT／ユーザーの別判断とし、今回から構成研究・計算・実装・重要科学レビューへ自動進行しない。
