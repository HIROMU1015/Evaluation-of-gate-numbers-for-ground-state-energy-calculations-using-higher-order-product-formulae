# Q1：最初の紙上検証と失敗判別

2026-10-17 JST。**以下は次段階の提案であり、今回実施した証明・数値実験・科学実装ではない。**
正式採択と実施範囲はGPT／ユーザーが判断する。公開後に自動開始しない。

## 1. 最初に確認すべき命題

最初の問いは「Bethe rootを渡せばstateが作れるか」ではなく、
**level追加の(Q5)に対し、全columnを個別に構成せず、一つの可逆な係数再帰でunitaryなBを生成できるか**である。
小例でこの規則が書けなければ、分子benchmark又はgate数測定へ進む理由はない。

対象は4対軌道・4電子、seniority zeroで2 pairs。
\(\epsilon=(-3,-1,1,3)/8\)、\(g=\gamma/4\)、\(1/2\le\gamma\le2\)というsymbolic familyとする。
scalar cはsymbolicに保持し、R=0の厳密模型例で始める。
全電子問題のE0をこのsectorの最低値へ読み替える実験ではない。

基底labelは1100、1010、1001、0110、0101、0011の6個。
最後のlevelが空ならparentの2-pair sector、占有なら1-pair sectorで、parentは各3次元。
parentでも\(g=\gamma/4\)と元の三つの\(\epsilon\)を使う。
新しい行列を計算機で作るのではなく、symbolicな3＋3の直和作用として扱う案である。

## 2. 紙上の確認順序

1. **親子の作用を固定する。** \(2\epsilon_4-g\)とoff-diagonal \(-gF\)を含めて(Q5)をoccupation演算子から確認する。
   fermion pairは偶演算子として扱い、別の積分規約のfactorを入れない。
2. **Fのcompactな生成関係を調べる。** 既知overlap／form-factor式を使う場合、入力がどのroot set・eigenlabelを必要とするかを明記する。
   6個の解をsolverで集めた表を入力しない。root symbolを式へ残しただけでも係数compilerの完成としない。
3. **挿入則を一つ書く。** \(B^\dagger B=I\)、\(\mathcal K B\simeq BD\)を同時に満たす、
   reversible label更新と回転／phaseの再帰を提案する。\(B\)の存在やgenericな6次元対角化は新規則に数えない。
4. **二つのinputを同時に確認する。** 例えばlabel 1100と1010のsuperpositionに、同じBを線形に作用させる。
   その二つを別々に準備する回路の列挙で代用しない。
5. **garbageとcontrolを確認する。** eigenlabel／root情報をworkに残さず逆変換できるか。
   cとself-pair項を含むcontrolled phaseの0/1間を追う。
6. **再帰を一段拡げた場合の費用式を先に点検する。** 全mをuniformに扱って(Q7)型になるか。
   各branchの再帰を二つずつ複製するだけなら、6次元例が動いてもextensive fillingでの目標を満たさない。

最初の成果物は、**挿入則の明示又は、その提案族に対する具体的な障害**とする。
小例の結果だけで一般Lのpoly bound又は一般不能性を主張しない。

## 3. 先に潰すべき誤った短絡

\(V:|z\rangle|0\rangle\mapsto|z\rangle|E_z\rangle\)というcontrolled state準備だけでは、
任意入力を\(W:|z\rangle\mapsto|E_z\rangle\)へ写しworkを返す操作を得たことにならない。
最初のzをtrace／測定すると、labelのsuperpositionのcoherenceが失われる。
それを消すには、追加の実操作か、一つのunitaryな再帰の説明が必要。
これは不能性定理ではなく、無料label erasureの見落としを判別する最小の確認点。

また、全columnの個別誤差が\(\delta\)というだけでは、作用素誤差は最大で\(\sqrt d\delta\)まで増え得る。
dが指数次元なら、「全stateで良い準備精度だった」をそのまま(Q3)へ移さない。
同じWと逆Wで消えるcolumn phaseの任意性自体は誤りではない。
問題は、共通のunitary・Dとの対応・garbage返却・norm誤差が保証されるかである。

## 4. 成功・失敗の判別

| 小例での観測／導出 | 判断する内容 |
|---|---|
| 係数とcompactなlabelから全columnを同じ再帰で生成、直交性とphaseが閉じる | 次に一般Lへ拡張する定理の形をGPTが判断。まだpoly complexityの成功ではない |
| 既知のABCs又は既知CGと全て同じ入出力・同じ必要情報になる | その提案の独立性なし。既知法との対応を記録する |
| dense QR、全固有vector、全root一覧、正しいbranch／gapが必要 | 本契約は未達。入力を無料化して救済しない |
| root座標にpole／collisionが出る | その座標の失敗か、物理変換の失敗かを区別。charge／symmetric polynomial等への移送も費用が必要 |
| approximateな縮退subspace内の基底が一意でない | 直ちに失敗としない。(Q3)のoperator残差とphaseを満たすかで判断 |
| nonunitarity／garbage／scalar誤差が残る | 提案した挿入則は失敗。一般RGの不能性へ拡張しない |

## 5. もし数値又は実装が必要になったら

本依頼では実行しない。将来提案する場合は、対象Hamiltonianとsector、g／精度の座標、
truth access、比較法、出力scalarとhash、stop点を新しい科学契約へ明記する。
solver、root追跡、行列生成・対角化、回路build／compile、benchmarkはそれぞれ別途必要な明示承認を得る。
既存のgrant・resource契約を流用・変更しない。共有環境へ影響する設定変更もしない。

**次の担当**：GPT／ユーザーがQ1の採否と、上記1–3に限る紙上検討を実施するか判断する。
Codexは新しい明示指示がある場合だけ、その範囲の導出と記録を担当する。
現在は資料公開・照合後Mandatory STOP。
