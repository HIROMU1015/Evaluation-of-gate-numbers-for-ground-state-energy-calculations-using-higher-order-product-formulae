# Durable scalar recovery

各pass return → private scalar recovery/fsync/hash/create-only → public schema validation/write/roundtrip → Git prediction freeze。検証済みC0 serialization_boundaryを変更せず利用。array/vector/complex/nonfinite/truthをPhase A公開から拒否し、tuple/numpy scalarだけを正規化する。public failure後はprivate bytesからserializationのみ回復し、scienceを自動rerunしない。回復自体のfailureはincidentとして停止。R0はsynthetic試験だけ。
