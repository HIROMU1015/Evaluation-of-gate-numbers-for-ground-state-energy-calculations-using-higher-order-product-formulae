# 集団遷移生成研究：現探索系列の一時保留判断

2026-10-18 JST。判断記録ID：`COLLECTIVE-TRANSITION-DECISION-20261018-PAUSE-01`。

**正式状態：PAUSED。対象は、固定2段階で検討した集団遷移生成の現構成・探索系列のみ。** ユーザーが承認した保留判断を記録する。研究全体のCLOSED、候補一般の不可能性、独立した証明認証には読み替えない。

## 1. 判断対象・承認の出所

Repository：`HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae`。新規branch：`qc-collective-transition-pause-decision-20261018`。起点は複数jump／有限cycleの固定commit `12324144a3d4f7a247f1944b4866549e9cc19152`。

承認者はユーザー。承認の出所は本作業の直接チャット「Codex作業指示：集団遷移生成研究の一時保留記録」であり、「現探索系列を一時保留する方針を承認」「現在の集団遷移生成探索系列をPAUSEDとして正式に記録する」と明示された。Codexはその判断の記録・SOURCE確認・公開同一性監査を担当した。別の承認ID、科学grant、GPTによる詳細科学レビュー完了は認定していない。

固定SOURCEは次の2段階である。過去handoffにある「正式状態を変更しない」「次に継続・保留を判断」は当時の記録として保持し、今回の新しい承認を本書で追記する。

- 初期構成：`b7ec04fb84cd01eb846b9e3cc6d545bdf833e657`、[初期構成handoff](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/b7ec04fb84cd01eb846b9e3cc6d545bdf833e657/docs/research_exploration/collective_transition_initial_construction_20261017/research_decision_handoff.md)。
- 複数jump／有限cycle：`12324144a3d4f7a247f1944b4866549e9cc19152`、[複数jump／cycle handoff](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/12324144a3d4f7a247f1944b4866549e9cc19152/docs/research_exploration/collective_transition_multijump_cycle_20261018/research_decision_handoff.md)。

## 2. 固定SOURCEに記録された構成成果と還元

以下は既存結果の整理であり、新しい数学的導出・検算ではない。技術分類B/C/Dは元資料の分類を維持し、正式状態PAUSEDと区別する。

| 段階 | 記録済みの構成成果 | 既知法への還元・限界 |
| --- | --- | --- |
| 初期構成 | 対角係数からのpair下降predicate。さらに4 modes・N=2の相互作用＋非可換hopping模型H*で、係数から条件付き回転Wを作りW†／pair reset／Wを指定。限定模型でenergy下降を記録 | 解析的小ブロック基底変換＋標準rank-one振幅減衰。target自身の直接準備も可能。一般Hの新しい生成規則・資源優位は得ていない（B） |
| 複数jump／有限cycle | 境界hoppingを残す5 modes・N=2のH5で、source P=span{12,23,25}、target b=34、共通減衰率の3-jump cycle。係数条件δ=2μ−t−abs(τ)>0でenergy下降と粗いcutoff以下の人口増加を記録 | チャネル全体がPの弱測定＋成功branchの既知bへの条件付きresetと一致。source選択は保存flag・occupation支持・係数norm証拠による。独立した新生成規則は得ていない（B） |

初期の具体的生成規則と還元は [構成 §1–4](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/b7ec04fb84cd01eb846b9e3cc6d545bdf833e657/docs/research_exploration/collective_transition_initial_construction_20261017/collective_transition_construction.md)、既知法との比較は [初期比較 §2–3](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/b7ec04fb84cd01eb846b9e3cc6d545bdf833e657/docs/research_exploration/collective_transition_initial_construction_20261017/prior_art_and_mechanism_comparison.md) に記録されている。有限cycleの操作・出力coherenceまで含む還元は [cycle構成 §3–7](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/12324144a3d4f7a247f1944b4866549e9cc19152/docs/research_exploration/collective_transition_multijump_cycle_20261018/coefficient_to_cycle_construction.md)、[cycle比較 §1–2](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/12324144a3d4f7a247f1944b4866549e9cc19152/docs/research_exploration/collective_transition_multijump_cycle_20261018/prior_art_overlap_and_latest_sources.md) にある。同じgate集合を使ったという理由だけの還元判断ではない。

## 3. 限定的な障害と未解決事項

初期の [紙上検証 V8–V12](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/b7ec04fb84cd01eb846b9e3cc6d545bdf833e657/docs/research_exploration/collective_transition_initial_construction_20261017/noncommuting_paper_verification.md) は、固定rank-one振幅減衰で全状態・一stepのenergy非増加を要求すると、sourceのH不変性とtargetへのenergy順序が必要になると記録している。5番目のmodeへの境界hoppingにより、旧dressingを固定したままの全状態単調性は破れる。限定inputの下降十分条件は残る。これはrank-one文法の結果に限る。

複数jumpの [紙上導出 M1・M8–M12](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/12324144a3d4f7a247f1944b4866549e9cc19152/docs/research_exploration/collective_transition_multijump_cycle_20261018/cycle_paper_derivations.md) では、同じrank-one resetの細分化・反復は同じ振幅減衰に戻る。source全体を共通率で減衰する固定部分空間resetでは、0≤z<1の全状態単調性は `PHQ=0` と `PHP≥E_b P` を要する、と記録されている。Pはsource projector、Q=I−P、E_b=〈b|H|b〉、zは共通cosineである。

flagを変えるhoppingを加えたH_etaでは `PHQ≠0` となり、この固定cycleの全状態単調性は破れる。occupation連結成分のclosureを拡大するだけではtargetも含まれ、このsource拡大文法は止まる（C）。一方、P/Q block-diagonal inputとlogical cycle列に限る反復energy下降や、coherenceに条件を付けた一cycleの十分条件は残る。途中にH_etaの物理時間発展を入れると、そのinput classは一般に保存されない。

元Hが作るP/Q coherenceを扱う独立した係数生成則は未構成・未判定（D）。有用なsource／target／cycleの一般的生成費、接続性、dark成分除去、groundへの収束、同accessの強いbaselineに対する総費用差も未確立である。低energy人口の増加やenergy期待値の下降を、任意精度の絶対E0推定の完成としない。これらは保留後に自動実行する課題一覧ではない。

## 4. 正式な保留理由と適用範囲

1. 具体化できた初期構成は解析的小ブロック変換＋振幅減衰、有限cycleは部分空間の弱測定＋条件付きresetへ還元された。
2. 境界hoppingの一部はsource拡大で取り込めたが、`PHQ≠0` に由来するcoherenceを扱い、既知resetを越える独立した新生成規則は得られていない。
3. 得られた限定進捗だけでは、一般電子Hのground準備や元Hamiltonianの絶対E0に対する総資源優位を示せない。
4. ユーザーはこの証拠の範囲で、現探索系列の追加探索を一時保留する方針を承認した。

**保留は現在の構成系列のみ。** 一般の冷却、複数jump／cycle、別の入力class、feedbackやcoherentなbath等の不可能性は主張しない。既知法への還元や限定文法の失敗を一般NO-GOへ拡張せず、全冷却研究の新規性・最良性を網羅認定しない。数学的な詳細独立認証を実施したとも記録しない。

## 5. 再開を提案できる条件

Hamiltonian係数から生成可能で、`PHQ≠0` に由来するcoherenceを扱い、既知reset等との差分を持つ**具体的な新機構**が提示されることを必要条件とする。

提示には少なくとも、合法な入力・操作・出力、係数から有限操作を作る規則、coherenceを含む適用input classと進捗命題、既知法との操作上の差分を明記する。未知のground state・固有projector・gap・全H時間発展を無料入力へ移さない。jumpの数・名前・角度の変更、現resetの再提示だけでは条件を満たさない。

これは再開承認でも新規性の事前認定でもない。新しい機構が提示されても自動再開せず、**GPT／ユーザーが再開可否と必要な検証範囲を判断する**。科学計算・実装等には別途必要な明示承認を要する。今回新機構の探索や候補の作成は行っていない。

## 6. 他系列・科学条件・SOURCEの保全

本書が変更する正式状態は、現集団遷移生成探索系列のPAUSEDだけである。J1の `PAUSED_PENDING_NEW_MECHANISM`、Q1の `PAUSED_PENDING_NEW_LEVEL_INSERTION_RULE`、R1-Pの独立候補不保持、SOS-PF A2および他系列の正式状態を変更しない。第一・第二研究、PR Track A/B、A1、M1-S等についても再開・採択・保留解除を行わない。

D1のblock-encoding／qubitization中心への無断移行禁止、D2の元有限基底電子Hamiltonianの絶対E0を保持する。scalar・一体項・相互作用・残余・sector対応・誤差や情報取得費を省略しない。ただし今回、E0出力を新たに構成・検証していない。

既存SOURCE・raw結果・grant・authorization・固定科学契約・STOP／PAUSEは上書きしない。過去の公開未実施等の文言も作成時点の記録として保持する。他worktree・共有設定・他jobの変更や、承認済み資源契約の変更は行わない。

## 7. 監査・handoff・停止点

読む順序は本判断記録 → 2段階の固定handoff → 必要な構成・限定障害の引用箇所 → [SOURCE registry](source_registry.json) → [静的監査](static_audit.json)・[provenance](provenance.json)。

今回の監査は、固定17資料のGit blob・bytes・SHA-256と固定raw、既存manifestの初期9件／cycle6件（各provenance自己除外）、JSON・文書参照、既存worktreeのGit状態保全を対象とする。origin/result commitとverified snapshot commitは分離して記録した。過去registryにある全transitive SOURCEや一次文献の再取得・詳細レビューを完了したという意味ではない。

新規追加は本dirの判断記録・SOURCE registry・静的監査・provenanceの4件のみ。科学探索、科学計算、solver、simulation、数値再解析、新規数学証明、科学用記号計算、回路build／compile、benchmark、詳細科学レビュー、新grantは実施していない。

新規4件を明示stageして通常commit・non-force pushし、remote SHA・独立した空bareへのfetch・全4件のGit blob／bytes／SHA-256・commit固定rawを照合する。provenanceのmanifestは自己除外を明示し、provenance自身も公開後照合する。本書はprecommit記録であり、公開commitと照合完了の事実は最終handoffで別途示す。

**Mandatory STOP：公開・同一性照合後にCodexは停止する。** GPT／ユーザーが次の判断を担う。現時点で承認済みの追加探索・科学計算・詳細科学レビューはない。
