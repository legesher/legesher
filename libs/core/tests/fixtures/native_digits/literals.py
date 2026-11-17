# Every numeric literal form a file written in native digits can hold.
# tests/unit/test_native_digits.py translates this file into each language
# whose registry entry names a native digit block, writes its decimal
# literals in that language's digits, and reads it back.
# Prose keeps its digits in every script: ٠١٢٣ ۰۱۲۳ ०१२३ ০১২৩ ๐๑๒๓ ၀၁၂၃
# مَرْحَبًا ٣ بِالْعَالَمِ · שָׁלוֹם 3 עוֹלָם · नमस्ते ४ दुनिया

integer = 123
zero = 0
zeros = 00
underscored = 1_000_000
decimal = 3.25
leading = 0.5
padded = 000.125
trailing = 10.
exponent = 1.5e-3
upper_exponent = 2E10
imaginary = 7j
float_imaginary = 2.5j
mixed = 456 + 789
hexadecimal = 0x1F
binary = 0b101
octal = 0o17
var3 = 4
مَبْلَغ = 250
סְכוּם = مَبْلَغ + 1
राशि = 30
จำนวน = 40
数量 = 50
label = "Price: ١٢٣ ۴۵۶ १२३ ১২৩ ๑๒๓ ၁၂၃"
raw = r"\d{3} ٤٥٦ ۷۸۹"
template = f"{integer + 1} items, ٧٨٩ left"
single = 'qty ٩ / ९ / ๙'
bytes_value = b"123"
nested = [1, (2, 3), {4: 5.0}]


def scale(value, factor=2):
    """Doc string with digits: ١٢ ۱۲ १२."""
    return value * factor + 0.25


RESULT = (
    integer,
    zero,
    zeros,
    underscored,
    decimal,
    leading,
    padded,
    trailing,
    exponent,
    upper_exponent,
    imaginary,
    float_imaginary,
    mixed,
    hexadecimal,
    binary,
    octal,
    var3,
    مَبْلَغ,
    סְכוּם,
    राशि,
    จำนวน,
    数量,
    label,
    raw,
    template,
    single,
    bytes_value,
    nested,
    scale(4),
    scale(1.5, 3),
)
