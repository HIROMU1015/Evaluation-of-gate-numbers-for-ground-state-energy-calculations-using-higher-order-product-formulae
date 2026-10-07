# Complete cold replay

将来のPhase Aは各passでarchiveの検証/loadからRitz basis/state、PF gate caches、exact-H echo、proxy、fit、budgetまで独立に再構築。immutable source bytesのみ再利用可能。cached state/HZ/expm/gate/proxy/fitは共有しない。initial/cold各16 evaluations、fits各4を別カテゴリで記録。rank0ならRitz=CISD、small solve0、実際のH1+retained rankを数える。各pass scalar return後の回復snapshotは別create-only file。R0ではsynthetic冷再構築だけを試験する。
