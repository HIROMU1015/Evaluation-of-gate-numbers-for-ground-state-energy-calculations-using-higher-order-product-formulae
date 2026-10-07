# Complete cold replay contract

FS-C1は未承認。将来のinitial/coldはそれぞれ独立source load、state refinement、PF、exact-H echo、proxy、fitを再構築する。immutable source bytesの再利用だけは許可し、state/Krylov/HZ/group-gate/expm/proxy/fit cacheは共有しない。同じ保存絶対時刻と同じrank/tie rulesを使う。

§27のfit独立再構築に合わせ、2分子×2passesのM00 validation4 + M10 fits4 (initial operational2/cold validation2) =8を予定callとして明示。M00 primaryは保存値のまま。4training/local時刻×2states×2分子×2passesのPF/echo32、explicit refinement H36 (rank8)、small Ritz4。実行値はすべて0。synthetic fixtureのcold passだけを新規object/state/spectra/ledgerで試験する。
