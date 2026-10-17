# Q1：一時保留の正式判断記録

2026-10-17 JST。**ユーザーの明示承認に基づき、研究課題Q1の追加探索を PAUSED_PENDING_NEW_LEVEL_INSERTION_RULE として一時保留する。**

| 項目 | 記録 |
| --- | --- |
| 判断記録ID | Q1-DECISION-20261017-PAUSE-01 |
| 対象 | 研究課題Q1（inhomogeneous pairing Hamiltonianの係数からcoherentな基底変換を生成できるか）の追加探索 |
| 正式状態 | **PAUSED_PENDING_NEW_LEVEL_INSERTION_RULE** |
| 判断権者・承認根拠 | 本作業を依頼したユーザーの「Q1の一時保留を正式記録」という明示指示 |
| 承認の内容 | 「ユーザーは、研究課題Q1の追加探索を PAUSED_PENDING_NEW_LEVEL_INSERTION_RULE として一時保留する方針を正式承認した。」 |
| 判断根拠の固定commit | d33fc8b690df13c6aaa0835b7d10f1a96fb789d1 |
| 元の研究課題定式化 | 3abef73cdd8a578d56f1d96d070862c71749e403 |
| 記録・公開担当 | Claude Code。承認済み判断の文書化、commit・通常push・同一性照合のみ |
| 管理方式 | 新規ファイルによる追記型。過去の正式状態記録・handoff・provenanceを上書きしない |

承認referenceは今回のユーザー指示であり、外部の承認ID・grant番号・承認済み科学実行planを作ったことにはしない。
固定commitでは、Q1は未採択の研究課題案のままで、追加探索の一時保留が第一推奨として記録され、正式状態は変更されていなかった。
その履歴を維持し、**今回の承認による正式判断を、この新規記録で追加する**。
この記録はQ1の採択・終了・否定ではなく、固定資料の「未採択の研究課題案」という記載も書き換えない。

読む順序：本記録 → [provenance](provenance.json) → 下記の固定判断資料。
今回は保存された結論と承認範囲の確認であり、数学的な再導出・科学計算・詳細レビューを行っていない。

## 保留理由

| 保留理由 | 固定資料に記録された内容 | 限定・未主張の範囲 |
| --- | --- | --- |
| 1. 独立2次元回転の挿入文法は不成立 | L=4・m=2の3＋3空間を三つの独立した2次元channelへ分け、各channelに回転／phaseを適用する文法Gには \([h_2,TT^\dagger]=0\) と \([h_1,T^\dagger T]=0\) が必要。\([\mathsf d,J]_{12}=-1/2\ne0\) により、g∈[1/8,1/2]の全域でこの条件が破れる。[挿入障害記録][insertion-obstruction] §1–2 | 明示した一段の独立channel文法だけの限定的障害。複数段でchannelを混ぜるunitary、別のcompactな規則、近似的operator残差は排除していない。 |
| 2. Fと可換な非対角Yの文法はRiccati条件と矛盾 | \([Y,F]=0\) を課す文法G_Fでは、Riccati条件 \([\Lambda,Y]+Y-gF+gYFY=0\) から \([\Lambda,F^2]=0\) が従い、\([\Lambda,F^2]\ne0\) と矛盾する。明示候補 \(Y_0=q_g(F)\) はparent energy labelを混ぜるが、残差 \([\Lambda,Y_0]\) が非零。[Riccati紙上導出][riccati-derivation] §2 | G_Fのどのbranchも指定g全域で厳密解を与えないことに限る。一般のY、全てのHermitian Y、Fと非可換なYの不成立、近似解の誤差下界は示していない。 |
| 3. 固定Sylvester逆は連続パラメータ域のγ=√2で特異 | 一つのSylvester逆を全域で用いる文法G_Sでは、連続interval [1/2,2] の内部 \(\gamma_*=\sqrt2\)（\(g_*=\sqrt2/4\)）で \(\lambda_2-\lambda_1=1\) となり、\(\mathcal L_{g_*}(\lvert1\rangle\langle2\rvert)=0\)。[Riccati紙上導出][riccati-derivation] §3–4 | γ*は有理数ではなく、有限bit有理入力で厳密に分母零が起こるとは主張しない。有理入力列が近づけるため一定のconditioningを無料で仮定できないことに留め、poly(bit長)算法の不能性やbit数・gate数の下界とはしない。full Hamiltonianのgap閉鎖やgraphの発散も示していない。 |
| 4. 既知法を越える係数生成規則と共通unitary Bは得られなかった | Sylvester逆・不変部分空間・block diagonalization・Bethe/F-basisへ書ける部分は既知法へ還元され、独立した係数生成則の実例は残らなかった。実際のRiccati解Yと共通unitary Bは未構成。[既知法比較][known-reductions] §1・§4・§5、[最新handoff][latest-handoff] §1–2 | 一般のY又はBの不存在、Q1の不能性、全文献での新規性の有無は未検証。文献未発見を不存在の証拠にしない。 |

元の課題定義は[研究課題定式化][research-problem]、理由1の判断材料は[挿入検証handoff][insertion-handoff]にもある。
固定資料の同一性は[判断根拠のprovenance][latest-provenance]と本記録の[provenance](provenance.json)で照合した。

Fとも非可換なlabel混合を係数から生成し、child spectrum情報を外部入力せずに残差を閉じる規則が得られず、
追加探索で識別すべき具体的な独立機構を固定できないことを、今回の保留理由とする。
未証明又は高リスクという性質だけを理由に、Q1の数学的な問いや一般的な研究価値を否定する判断ではない。

## 再開を判断する条件

**Hamiltonian係数から、非対角なlabel混合と共通unitary挿入則を生成する、既知法へ還元されない具体的規則が提示されること。**

提示内容は、Q1の(Q1)–(Q2)で定義済みの係数とcompactな再帰labelを入力として、Fとも非可換なparent label間の混合を生成し、
それをlevel挿入の共通unitaryと新energy評価へ接続する規則を、具体的な入力・操作・共通label更新として記述するものとする。
child root、全固有vector、spectral projector等を外部から与えてY又はBを定義する規則や、
既知のSylvester逆・不変部分空間・block diagonalization・Bethe/F-basis準備への書き換えだけでは、この再開条件の充足とはしない。

これは提示された規則について再開の採否・範囲を判断するための条件であり、今回その規則を探索・実装する指示ではない。
提示があっても自動再開しない。ユーザー／GPTの判断と、別途明示承認された範囲に従う。
(Q3)–(Q7)の成立、新規性、資源優位が未確立であるという既存の留保は維持する。

## 適用範囲と保全

正式な一時保留の対象は**Q1の追加探索のみ**。
Q1全体やRichardson–Gaudin模型一般の不可能性を主張しない。
有限bit有理入力について一般的な不能性を認定しない。
今回までの限定的障害を、gate数・bit数・conditioningの下界や科学的NO-GO定理として扱わない。

J1は[正式判断記録][j1-record]の **PAUSED_PENDING_NEW_MECHANISM** のまま維持する。
Q1の正式一時保留以外の研究状態、他研究のSTOP・CLOSED・PAUSED・HOLD等を変更しない。
既存SOURCE、結果、grant、承認、科学契約、凍結provenance、STOP、他worktreeを保全する。
D1（block-encoding／qubitization中心へ移行しない）と、D2（scalar・一体項・self項・絶対E0、seniority・blocked sector・Rの区別）を維持する。
新規科学計算・solver・追加探索・実装・詳細科学レビューは開始しない。

この記録を将来更新する必要が生じた場合も、新しい判断記録から本IDと公開commitを参照する。
過去の「正式状態未変更」「未採択の研究課題案」等の記載を遡って書き換えない。

**Mandatory STOP：本記録とprovenanceの公開・照合後に停止する。追加作業は不要。将来、再開条件を満たし得る規則が提示された場合の採否はユーザー／GPTが判断し、Claude Codeは別途承認まで作業を開始しない。**

[latest-handoff]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/d33fc8b690df13c6aaa0835b7d10f1a96fb789d1/docs/research_exploration/q1_riccati_final_paper_check_20261017/decision_handoff.md
[riccati-derivation]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/d33fc8b690df13c6aaa0835b7d10f1a96fb789d1/docs/research_exploration/q1_riccati_final_paper_check_20261017/riccati_paper_derivation.md
[known-reductions]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/d33fc8b690df13c6aaa0835b7d10f1a96fb789d1/docs/research_exploration/q1_riccati_final_paper_check_20261017/known_reductions_and_limits.md
[latest-provenance]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/d33fc8b690df13c6aaa0835b7d10f1a96fb789d1/docs/research_exploration/q1_riccati_final_paper_check_20261017/provenance.json
[insertion-obstruction]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/2a3e6898087fc248656123e7c67fb62c49b2d0f8/docs/research_exploration/q1_level_insertion_paper_check_20261017/insertion_obstruction_and_checks.md
[insertion-handoff]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/2a3e6898087fc248656123e7c67fb62c49b2d0f8/docs/research_exploration/q1_level_insertion_paper_check_20261017/verification_handoff.md
[research-problem]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/3abef73cdd8a578d56f1d96d070862c71749e403/docs/research_exploration/open_problem_research_design_20261017/research_problem.md
[j1-record]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/95be62395d3740db39b6830c68f4fd1e25f595ee/docs/research_exploration/p1star_j1_pause_decision_20261017/research_decision_record.md
