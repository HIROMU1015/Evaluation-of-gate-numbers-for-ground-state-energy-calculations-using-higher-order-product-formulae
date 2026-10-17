# ボトルネックからの操作設計：判断用handoff

2026-10-17 JST。**最終保持する新操作の設計課題は0件。**
二電子係数状態とN電子targetの衝突を1件の操作仕様まで具体化したが、
その生成は既知CG／Paldus変換と3種類のphaseへ明示的に還元できた。
完成した新アルゴリズム、独立した新構成原理、資源優位を得たとは報告しない。
これは今回具体化した操作についての限定結果であり、他の新操作の不存在証明ではない。

## 1. 次に構成すべき操作は残ったか

**新操作としての構成対象は残らなかった。** 検討した仕様は、既知係数行列Vから準備する二電子補助状態を使い、
任意のN電子targetへ相互作用を渡すための、係数非依存な衝突である。

\[
J_N=\binom N2^{-1}\sum_{\alpha\beta}
A_\alpha^\dagger A_\beta\otimes|\beta\rangle\langle\alpha|,
\qquad U(\theta)=e^{-i\theta J_N}.
\]

普通の「二電子を抽出→SWAP→逆抽出」は、反対称空間の抽出imageをSWAPが保存しないため、そのままunitaryにはならない。
M=5、N=3の手で追える例を[操作仕様 §4](operation_design_task.md)に示した。
しかし、この不足を**既存アルゴリズム全体の不足**と判断することはできない。

target／補助を仮想的な二種類のフェルミオンとすると、交換演算子\(K_1\)と固定\(m=(N-2)/2\)について

\[
J_N=\frac{K_1^2+NK_1-2NI}{4\binom N2},\qquad
K_1=N I-S^2+m(m-1)I.
\]

従ってtotal spin \(S=m,m+1,m+2\)のうち許されるsectorに応じ、
\(1/\binom N2,-2/N,1\)のphaseを付ければよい。
pairの符号化、fermion ordering、既知CG/Paldus、phase、逆写像まで対応する。
未知の化学固有値、ground、gap、全Hの発展oracleを入力にした説明ではない。
このCAR対応は今回の短い紙上整理であり、独立査読済みの証明・回路実装とは区別する。

既知HMEは、そもそも\(X\mapsto\Gamma_N(X)/\binom N2\)のfirst-order作用を与える一般機能を持つ。
今回、その機能を新原理とせず、内部のjoint evolutionについても既知生成則へ対応付けた。
[一次文献・公開実装との比較](prior_art_and_limits.md)を参照する。

## 2. 実際に示したことと示していないこと

| 実施・確認したこと | 未確立／未実施 |
|---|---|
| 第一・第二研究、PR Track A/B、P1～P8、J1、NA/NBの固定資料から具体的な入力・合成・情報取得障害を抽出 | これらの再開、再採択、保存値の再集計、新しいlaw・threshold・truth取得 |
| 1件の操作の入力・出力・primitive・追加access・coherent control・生成規則・失敗条件を記述 | 科学コード、回路build／compile、solver、数値最適化、simulation、benchmark |
| SWAP圧縮の失敗例、占有blockの数え上げ、CAR／spinへの短い紙上対応 | 独立の詳細科学レビュー、網羅的な全文献新規性監査、数値による証明 |
| DME／HME、DF、commutator、CG/Paldus、符号化・状態準備との対応を限定照合 | 二電子係数状態の効率的準備、全準備・copies・合成誤差を含む資源優位 |
| D2の元Hを\(cI+d\Gamma(h)+\Gamma_N(V)+R\)として保持し、collisionと絶対E0取得を区別 | scalar・一体項・Rを含むend-to-end E0算法の完成、ground overlap・位相窓の無料認証 |

他の検討方向と不保持理由は[ボトルネック記録](bottleneck_evidence.md) §5。
新instrumentの生成則がないenergy測定要求や、有限基底へのphase圧縮を、数を満たすための候補にはしなかった。
高リスク・未証明だから不採用としたのではなく、具体化不足又は明示的な既知法還元として分けた。

## 3. GPT／ユーザーが次に判断すること

1. **GPT／ユーザー**：新操作課題0件という今回の限定結果と、操作仕様 §6の明示還元を判断する。
   新規性・正式採否・研究全体の方向はここで決定していない。
2. **必要と判断した場合の提案だけ**：M=5、N=3で、CARの符号、非対角pair coherence、controlのrelative scalar phaseを紙上で読み合わせる。
   最初に確認すべきは、\(J_N\)の定義と二species多項式の作用が同じこと。詳細は[操作仕様 §8](operation_design_task.md)。
   これは追加実施済みでも、追加実施の承認でもない。
3. **Codex**：本依頼のcommit・通常push・remote/blob/bytes/hash照合が完了した時点でMandatory STOP。
   採択、詳細科学レビュー、追加探索、科学計算、実装を自動開始しない。次の作業にはユーザーの新しい指示が必要。

新操作の設計課題を別に見つける追加探索も、本handoffにより自動承認されない。
J1は`PAUSED_PENDING_NEW_MECHANISM`のまま。NA/NB、P1～P8、第一・第二研究、PR Track A/Bの状態・SOURCE・結果・grant・承認・STOPを変更しない。
D1のblock-encoding／qubitization中心方向へ移行していない。

## 4. SOURCEと公開identity

- Repository: `HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae`
- 新規branch: `qc-bottleneck-operation-design-20261017`
- verified base snapshot: `813fd44bfd70f9bc4266e35cc8e4dd28037dedce`
- 固定参照: J1保留 `95be62395d3740db39b6830c68f4fd1e25f595ee`、P1～P8 `67d9e3b938b8a03120b836a1c32283b7c9e9a1f0`
- 全sourceのorigin/result commitとverified snapshot commit、GitHub固定リンク、Git blob、bytes、SHA-256、取得・読取り範囲は[source_registry.json](source_registry.json)。
- PR資料は別repositoryの固定commitをread-onlyで確認し、当該repositoryに変更・commit・pushしていない。
- 新規成果物7ファイルのうち、manifest自身を除く6ファイルのidentityは[provenance.json](provenance.json)。自己除外と公開commit自己参照を明記する。
- 新規資料の静的確認、作業境界、元workspaceの観測は[static_audit.json](static_audit.json)。科学testの代用とはしない。

このファイルに自分を含む最終commit SHAを埋め込む循環は作らない。
公開commitの40文字SHA・固定リンクは最終chatに記載し、公開commit自身のtree内の本ファイルと対応させる。
provenanceの公開前記録は履歴として保存し、push後に上書きしない。
公開後はremote refのSHA、独立fetchのcommit／Git blob、commit固定rawのbytes／SHA-256を照合する。
全て成功した場合だけ引渡し完了とし、その時点で停止する。

## 5. 読む順序

1. 本handoff：保持0件の理由と判断事項。
2. [操作仕様](operation_design_task.md)：§§1–4の実際の不足、§6の既知還元、§8の条件付き最小確認案。
3. [比較と限界](prior_art_and_limits.md)、[ボトルネック根拠](bottleneck_evidence.md)。
4. [SOURCE](source_registry.json)、[監査](static_audit.json)、[manifest](provenance.json)。

**公開・照合後Mandatory STOP。今回の資料は提案・限定的な紙上整理であり、新しい研究系列の正式承認ではない。**
