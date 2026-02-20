"""Buckwalter transliteration ↔ Arabic Unicode mapping."""

# Standard Buckwalter-to-Arabic mapping
BUCKWALTER_TO_ARABIC = {
    "'": "\u0621",  # hamza
    "|": "\u0622",  # alef with madda
    ">": "\u0623",  # alef with hamza above
    "&": "\u0624",  # waw with hamza
    "<": "\u0625",  # alef with hamza below
    "}": "\u0626",  # ya with hamza
    "A": "\u0627",  # alef
    "b": "\u0628",  # ba
    "p": "\u0629",  # ta marbuta
    "t": "\u062A",  # ta
    "v": "\u062B",  # tha
    "j": "\u062C",  # jeem
    "H": "\u062D",  # ha
    "x": "\u062E",  # kha
    "d": "\u062F",  # dal
    "*": "\u0630",  # thal
    "r": "\u0631",  # ra
    "z": "\u0632",  # zay
    "s": "\u0633",  # seen
    "$": "\u0634",  # sheen
    "S": "\u0635",  # sad
    "D": "\u0636",  # dad
    "T": "\u0637",  # ta (emphatic)
    "Z": "\u0638",  # za (emphatic)
    "E": "\u0639",  # ain
    "g": "\u063A",  # ghain
    "_": "\u0640",  # tatweel
    "f": "\u0641",  # fa
    "q": "\u0642",  # qaf
    "k": "\u0643",  # kaf
    "l": "\u0644",  # lam
    "m": "\u0645",  # meem
    "n": "\u0646",  # noon
    "h": "\u0647",  # ha
    "w": "\u0648",  # waw
    "Y": "\u0649",  # alef maksura
    "y": "\u064A",  # ya
    "F": "\u064B",  # fathatan
    "N": "\u064C",  # dammatan
    "K": "\u064D",  # kasratan
    "a": "\u064E",  # fatha
    "u": "\u064F",  # damma
    "i": "\u0650",  # kasra
    "~": "\u0651",  # shadda
    "o": "\u0652",  # sukun
    "`": "\u0670",  # superscript alef
    "{": "\u0671",  # alef wasla
    "P": "\u067E",  # pe (for Persian loanwords)
    "J": "\u0686",  # che
    "V": "\u06A4",  # ve
    "G": "\u06AF",  # gaf
}

ARABIC_TO_BUCKWALTER = {v: k for k, v in BUCKWALTER_TO_ARABIC.items()}


def buckwalter_to_arabic(bw: str) -> str:
    """Convert a Buckwalter string to Arabic Unicode."""
    return "".join(BUCKWALTER_TO_ARABIC.get(ch, ch) for ch in bw)


def arabic_to_buckwalter(ar: str) -> str:
    """Convert an Arabic Unicode string to Buckwalter."""
    return "".join(ARABIC_TO_BUCKWALTER.get(ch, ch) for ch in ar)


def space_root(root_arabic: str) -> str:
    """Add spaces between root letters (skip diacritics) for display.
    e.g. 'ملك' → 'م ل ك'
    """
    base_letters = [ch for ch in root_arabic if "\u0621" <= ch <= "\u064A"]
    return " ".join(base_letters)
