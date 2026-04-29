import re
from typing import Tuple, List

_OCR_RULES: List[Tuple[str, str, str]] = [
    (r'×',                      '*',      'Replace × with *'),
    (r'÷',                      '/',      'Replace ÷ with /'),
    (r'⁰',  '^0',  'Replace superscript ⁰ with ^0'),
    (r'¹',  '^1',  'Replace superscript ¹ with ^1'),
    (r'²',  '^2',  'Replace superscript ² with ^2'),
    (r'³',  '^3',  'Replace superscript ³ with ^3'),
    (r'⁴',  '^4',  'Replace superscript ⁴ with ^4'),
    (r'⁵',  '^5',  'Replace superscript ⁵ with ^5'),
    (r'⁶',  '^6',  'Replace superscript ⁶ with ^6'),
    (r'⁷',  '^7',  'Replace superscript ⁷ with ^7'),
    (r'⁸',  '^8',  'Replace superscript ⁸ with ^8'),
    (r'⁹',  '^9',  'Replace superscript ⁹ with ^9'),
    (r'\bX\b',                  'x',      'Replace capital X with x'),
    (r'(?<=\d)O',               '0',      'Replace letter O with 0 after digit'),
    (r'O(?=\d)',                 '0',      'Replace letter O with 0 before digit'),
    (r'==',                     '=',      'Replace == with ='),
    (r'([a-zA-Z])(\d)(?!\d)',   r'\1^\2', 'Insert ^ for implicit exponent (e.g. x2 → x^2)'),
    (r'(?<!\d)\.(?!\d)',        '',       'Remove stray period'),
]

_SYNONYM_RULES: List[Tuple[str, str, str]] = [
    (r'\bis equal to\b',  '=',      'Replace "is equal to" with ='),
    (r'\bdivided by\b',   '/',      'Replace "divided by" with /'),
    (r'\bfactor out\b',   'factor', 'Replace "factor out" with factor'),
    (r'\bfactorize\b',    'factor', 'Replace "factorize" with factor'),
    (r'\bwhat is\b',      'solve',  'Replace "what is" with solve'),
    (r'\bcalculate\b',    'solve',  'Replace "calculate" with solve'),
    (r'\bsquared\b',      '^2',     'Replace "squared" with ^2'),
    (r'\bcubed\b',        '^3',     'Replace "cubed" with ^3'),
    (r'\btimes\b',        '*',      'Replace "times" with *'),
    (r'\bplus\b',         '+',      'Replace "plus" with +'),
    (r'\bsubtract\b',     '-',      'Replace "subtract" with -'),
    (r'\bminus\b',        '-',      'Replace "minus" with -'),
    (r'\bequals\b',       '=',      'Replace "equals" with ='),
    (r'\bis\b',           '=',      'Replace "is" with ='),
    (r'\bfactor\b',       'factor', 'Normalise "factor"'),
    (r'\bfind\b',         'solve',  'Replace "find" with solve'),
    (r'\bsolve\b',        'solve',  'Normalise "solve"'),
    (r'\bgiven\b',        'and',    'Replace "given" with and'),
    (r'\bwith\b',         'and',    'Replace "with" with and'),
]


def normalize(text: str) -> Tuple[str, List[str]]:
    corrections: List[str] = []
    result = text

    for pattern, replacement, description in _OCR_RULES:
        new_result = re.sub(pattern, replacement, result)
        if new_result != result:
            corrections.append(f"OCR: {description}")
            result = new_result

    for pattern, replacement, description in _SYNONYM_RULES:
        new_result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        if new_result != result:
            corrections.append(f"Synonym: {description}")
            result = new_result

    result = re.sub(r'  +', ' ', result).strip()
    return result, corrections
