# Branch contract

初点はmaximum exact-ground-overlap eigenpairでseed。以後singletonはmaximum previous-selected-vector overlap、phase gap<1e-8のclusterはprojector overlapを使う。厳密thresholdは非cluster。seedの退化cluster内もreferenceの投影を使う。

Schur eigenpairをphase/real/imag/original ordinal順に並べ、tieは最初。退化内はP referenceを正規化してlargest-magnitude pivotのphaseを固定。cluster phaseはcircular centroid、選択vectorの固有残差が1e-10を超えるnear-degenerate clusterはunresolvedとして停止。連鎖clusterのcircular diameter>=gap、zero projector、非直交/duplicate eigenbranchesも停止。

continuation時の選択vector overlap>=0.9、unitarity Frobenius/eigenpair 2-norm<=1e-10。ground comparatorはdiagnosticのみ。新source namespaceとladder indexをcheckpointにbindする。旧ID6/9は不可。direct shiftとunwrap0はS0 principal-angle conventionを維持する。

これらは実装上の事前固定規則で、production PASSを意味しない。branch failureはtechnical gate failure、resource successには数えない。
