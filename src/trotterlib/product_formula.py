from typing import List

from .config import PFLabel
from .pf_decomposition import inverse_s2_sequence, symmetric_s2_sequence


def morales_8th_list() -> List[float]:
    """Morales arXiv v2 の旧 8次(m=8)係数列を返す。"""
    # 係数リストを構築
    w_1to8 = [
        0.29137384767986663096528500968049,
        0.26020394234904150277316667709864,
        0.18669648149540687549831902999911,
        -0.40049110428180105319963667975074,
        0.15982762208609923217390166127256,
        -0.38400573301491401473462588779099,
        0.56148845266356446893590729572808,
        0.12783360986284110837857554950443,
    ]

    w0_1to8 = [1 - 2 * sum(w_1to8)]
    w = w0_1to8 + w_1to8
    return w


def morales_2025_y8m10b_list() -> List[float]:
    """Morales et al. (QIC 2025) の Y8m10b 8次係数列を返す。

    Published Table 1, ``Best 8th order for eigenvalue error``.
    DOI: 10.2478/qic-2025-0001.  The returned representation is
    ``[w0, w1, ..., w10]`` with ``w0 = 1 - 2 * sum(w1, ..., w10)``.
    """
    w1to10 = [
        0.10467636532245895252340732579853,
        -0.57896999331780988041471955125778,
        0.57503350160061785946141563279891,
        0.12231011868707029786561397542663,
        0.27793149999039524816733903301747,
        -0.37349605088056728482635987352576,
        0.11575566589480463220616543972403,
        0.1464645610975800618712569230326,
        -0.39443578322284085764474498594073,
        0.44370228726021218923197141183196,
    ]
    return [1 - 2 * sum(w1to10)] + w1to10


def morales_2025_yp8m8_kernel_list() -> List[float]:
    """Morales et al. (QIC 2025) の YP8m8 kernel 係数列を返す。

    These are the kernel coefficients in published Table 2.  A complete
    processed formula also requires the processor returned by
    :func:`morales_2025_yp8m8_processor_gamma_list`.
    """
    w1to8 = [
        0.21784176681731006074681969186513,
        0.1947017706053903224022456342907,
        0.18372413281145589944261642180363,
        -0.37307499512657736825709230652023,
        0.15757644257569146373033662060461,
        -0.33342207567391682979227850551172,
        0.51788649682987924281787142226803,
        0.21456475499897766986381219621761,
    ]
    return [1 - 2 * sum(w1to8)] + w1to8


def morales_2025_yp8m8_processor_gamma_list() -> List[float]:
    """Y8m10b と同じ公開論文 Table 2 の YP8m8 processor 係数を返す。

    The paper lists gamma_1 through gamma_9 and specifies gamma_10 by the
    zero-sum condition.
    """
    gamma1to9 = [
        -0.44324901019570126590495430949294,
        0.25459857192003772850622377066944,
        -0.73862036266779261573694538099739,
        -0.00024139614958652134370419495289618,
        0.73873460354125365739379753874964,
        -0.20285971152536085519251666906017,
        0.44989521689676869571827637424046,
        0.29538398007876871184026747505657,
        -0.3364996155865700091428329802017,
    ]
    return gamma1to9 + [-sum(gamma1to9)]


def morales_2025_yp8m8_processor_sequence() -> List[float]:
    """Return the S2-block sequence for the YP8m8 processor P.

    Appendix B defines ``P = Q(t) Q(-t)`` with
    ``Q(t) = S2(gamma_10 t) ... S2(gamma_1 t)``.
    """
    gamma = morales_2025_yp8m8_processor_gamma_list()
    q_plus = list(reversed(gamma))
    q_minus = [-value for value in reversed(gamma)]
    return q_plus + q_minus


# Yoshida's 8th order product formula
def yoshida_8th_list() -> List[float]:
    """Yoshida 8次の係数列を返す。"""
    # 係数リストを構築
    w_1to7 = [
        -1.61582374150097,
        -2.44699182370524,
        -0.0071698941970812,
        2.44002732616735,
        0.157739928123617,
        1.82020630970714,
        1.04242620869991,
    ]
    w0_1to7 = [1 - 2 * sum(w_1to7)]
    # パラメータの設定
    w = w0_1to7 + w_1to7
    return w


# Mauro's 10th order product formula(m=15)
def morales_10th_m15_list() -> List[float]:
    """Morales 10次(m=15)の係数列を返す。"""
    # 係数リストを構築
    w_1to15 = [
        0.14552859955499429739088135596618,
        -0.48773512068133537309419933740564,
        0.12762011242429535909727342301656,
        0.70225450019485751220143080587959,
        -0.62035679146761710925756521405042,
        0.39099152412786178133688869373114,
        0.17860253604355465807791041367045,
        -0.80455783177921776295588528272593,
        0.053087216442758242118687385646283,
        0.86836307910275556258687030904753,
        -0.85326297197907834671536254437991,
        -0.11732457198874083224967699358383,
        0.03827345494186056632406947772047,
        0.74843529029532498233997793305357,
        0.30208715621975773712410948025906,
    ]

    w0_1to8 = [1 - 2 * sum(w_1to15)]
    # パラメータの設定
    # w_0 = 1 - 2sum(w_i)
    w = w0_1to8 + w_1to15
    return w


# Mauro's 10th order product formula(m=16)
def morales_10th_m16_list() -> List[float]:
    """Morales arXiv v2 の旧 10次(m=16)係数列を返す。"""
    # 係数リストを構築
    w_1to16 = [
        -0.4945013179955571856347147977644,
        0.2904317222970121479878414292093,
        0.34781541068705330937913890281003,
        -0.98828132118546184603769781410676,
        0.98855187532756405235733957305613,
        -0.34622976933123177430694714630668,
        0.20218952619073117554714280367018,
        0.13064273069786247787208895471461,
        -0.26441199183146805554735845490359,
        0.060999140559210408869096992291531,
        -0.6855442489606141359108973267028,
        -0.15843692473786584550599206557006,
        0.15414691779958299150286452215575,
        0.66715205827214320371061839297055,
        0.20411874474696598289603677693511,
        0.081207318210272593225087711441684,
    ]

    w0 = [1 - 2 * sum(w_1to16)]
    w = w0 + w_1to16
    return w


def morales_2025_10th_m17_list() -> List[float]:
    """Morales et al. (QIC 2025) Table 3 の 10次(m=17)係数列。

    This is the formula with the lowest eigenvalue error in their numerical
    search. DOI: 10.2478/qic-2025-0001.
    """
    w1to17 = [
        -0.28371232689144296279654621726493,
        0.046779504778147381605331000278223,
        0.36845892382797770619657504217539,
        0.19186204094674514739760408197461,
        -0.53123134392680669702873064192428,
        -0.0081253242720827266680816105600661,
        -0.16389450414378567860032917538393,
        0.18514766119291405032528647881,
        0.5383584694754681989174668806505,
        -0.30583981835573485697292316732177,
        0.43199935609523301289295473774488,
        0.1510502301631786853020124612813,
        -0.35051099204829676098801520498121,
        0.1032971125844291674511513007661,
        0.15043936943817152697371946806229,
        0.12118469498650736511410491586846,
        0.10437742779547826358296681557444,
    ]
    return [1 - 2 * sum(w1to17)] + w1to17


# Yoshida's 4th order product formula
def yoshida_4th_list() -> List[float]:  # s3odr4
    """Yoshida 4次の係数列を返す。"""
    # 係数リストを構築
    w = [-1 * (2 ** (1 / 3)) / (2 - 2 ** (1 / 3)), 1 / (2 - 2 ** (1 / 3))]
    return w


def trotter_2nd_list() -> List[float]:
    """2次(Trotter)の係数列を返す。"""
    # 係数リストを構築
    w = [1.0]
    return w


def new_4th_m3_list() -> List[float]:
    """新構築 4次(m=3)の係数列を返す。"""
    # 係数リストを構築
    w1to3 = [0.40653666, 0.21638706, 0.14924614]
    w0_1to3 = [1 - 2 * sum(w1to3)]
    w = w0_1to3 + w1to3
    return w


def new_4th_m2_list() -> List[float]:
    """新構築 4次(m=2)の係数列を返す。"""
    # 係数リストを構築
    w1to2 = [0.42008729, 0.40899193]
    w0_1to3 = [1 - 2 * sum(w1to2)]
    w = w0_1to3 + w1to2
    return w


def eigenvalue_optimized_4th_m6_list() -> List[float]:
    """固有値基準で得た 4次 non-processed m=6 係数列を返す。"""
    w1to6 = [
        0.1227066520995599,
        0.16285552801149286,
        0.5309407524995627,
        0.1639498695441385,
        0.24930555720329972,
        -0.4604943478237616,
    ]
    return [1 - 2 * sum(w1to6)] + w1to6


def actual_circuit_optimized_4th_m5_list() -> List[float]:
    """H3 実回路コスト探索で使った 4次 non-processed m=5 係数列を返す。"""
    w1to5 = [
        0.11225428783206336,
        0.14181961643121604,
        0.1211920365713068,
        0.13781643533753404,
        0.12547397927357543,
    ]
    return [1 - 2 * sum(w1to5)] + w1to5


def _get_w_list(num_w: PFLabel) -> List[float]:
    """積公式パラメータ w の系列を取得（分岐を関数化）。"""
    if num_w == "8th(Morales)":
        return morales_8th_list()
    if num_w == "8th(Morales-Y8m10b)":
        return morales_2025_y8m10b_list()
    if num_w == "10th(Morales)":
        return morales_10th_m16_list()
    if num_w == "10th(Morales-QIC-m17)":
        return morales_2025_10th_m17_list()
    if num_w == "4th":
        return yoshida_4th_list()
    if num_w == "8th(Yoshida)":
        return yoshida_8th_list()
    if num_w == "2nd":
        return trotter_2nd_list()
    if num_w == "4th(new_3)":
        return new_4th_m3_list()
    if num_w == "4th(new_2)":
        return new_4th_m2_list()
    if num_w == "4th(m6)":
        return eigenvalue_optimized_4th_m6_list()
    if num_w == "4th(m5_best)":
        return actual_circuit_optimized_4th_m5_list()
    raise ValueError(f"Unsupported num_w: {num_w}")


def _get_kernel_s2_sequence(num_w: PFLabel) -> List[float]:
    """Return the repeated kernel as an explicit sequence of S2 blocks."""
    if num_w == "8th(Morales-YP8m8)":
        return symmetric_s2_sequence(morales_2025_yp8m8_kernel_list())
    return symmetric_s2_sequence(_get_w_list(num_w))


def _get_processor_s2_sequence(num_w: PFLabel) -> List[float]:
    """Return the one-sided processor P, or an empty sequence."""
    if num_w == "8th(Morales-YP8m8)":
        return morales_2025_yp8m8_processor_sequence()
    return []


def _get_s2_sequence(num_w: PFLabel, *, kernel_steps: int = 1) -> List[float]:
    """Return the complete S2 sequence, including processing when required.

    A processed formula is returned as ``P K**kernel_steps P^-1`` so the
    processor is paid only once around all repeated kernel steps.
    """
    if kernel_steps < 1:
        raise ValueError("kernel_steps must be at least 1")
    kernel = _get_kernel_s2_sequence(num_w)
    processor = _get_processor_s2_sequence(num_w)
    return (
        processor
        + kernel * int(kernel_steps)
        + inverse_s2_sequence(processor)
    )
