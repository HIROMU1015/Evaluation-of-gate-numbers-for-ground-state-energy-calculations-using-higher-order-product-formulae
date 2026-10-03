# S1A no-fit replay protocolization

Status: `s1a_no_fit_rules_frozen_execution_not_started`

## Purpose

既存HF/HCl 4条件・12座標だけを使い、policy fittingを行わず、cheap instabilityに基づく単一B2/H1 probeを一度replayする。これは`post_hoc_development_diagnostic`であり、独立性能評価ではない。

## Frozen boundary

- B2は4つの既存gamma armのcandidate/eligibility disagreementと、cap外proxy sign instabilityだけで`gamma=1.01`または`1.10`を選ぶ。
- H1は同じcheap policyから開始し、cheap instabilityまたはB2 fallbackの場合だけ既存M1を論理的に開く。
- q=0条件のM1をdecisionへ使用しない。
- combined H1は再実行せず、保存armからlower/upper envelopeだけを作る。
- 分類順は`D -> B -> A -> C -> E`で固定する。

## Existing-frontier gate

Rule 1が要求するのは、各conditionについて保存済みのgamma exact 4 arm、eligible set、selected candidate、fallback、frozen budgetである。欠落frontierを保存cheap値から新たに生成・fitして救済しない。欠落時は`contract_not_replayable`としてpredictionへfreezeし、優先分類Dとする。

このgateは、candidate contractの違いを結果後に埋める自由度を排除するためのものである。

## Execution boundary

protocol commit後だけ実装する。predictorはtruth pathを受け取らず、cheap decisionとqを先にfreezeする。prediction commit後だけscorerを実行する。新しい科学計算、missing M1取得、combined run、threshold変更は行わない。

終了statusは`second_study_v2_s1a_no_fit_replay_complete_review_required`であり、A–Eのどの結果でも研究方針レビューへ戻る。
