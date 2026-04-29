import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from normalizer import normalize


def norm(text: str) -> str:
    result, _ = normalize(text)
    return result

def corrections(text: str):
    _, c = normalize(text)
    return c

# ------------------------------------------------------------------
# OCR corrections
# ------------------------------------------------------------------

def test_times_symbol():
    assert norm("2 × 3") == "2 * 3"

def test_division_symbol():
    assert norm("6 ÷ 2") == "6 / 2"

def test_superscript_squared():
    assert norm("x²") == "x^2"

def test_superscript_cubed():
    assert norm("x³") == "x^3"

def test_superscript_zero():
    assert norm("x⁰") == "x^0"

def test_capital_x_to_lower():
    assert norm("X^2") == "x^2"

def test_letter_o_after_digit():
    assert norm("1O") == "10"

def test_letter_o_before_digit():
    assert norm("O1") == "01"

def test_double_equals():
    assert norm("x == 5") == "x = 5"

def test_implicit_exponent_x2():
    assert norm("x2") == "x^2"

def test_implicit_exponent_y3():
    assert norm("y3") == "y^3"

def test_stray_period_removed():
    result = norm("x. + 2")
    assert "." not in result

def test_corrections_list_populated():
    _, c = normalize("X × 2")
    assert len(c) > 0

def test_no_corrections_for_clean_input():
    _, c = normalize("factor x^2 + 5x + 6")
    assert c == []

# ------------------------------------------------------------------
# Synonym substitutions
# ------------------------------------------------------------------

def test_squared():
    assert "^2" in norm("x squared")

def test_cubed():
    assert "^3" in norm("x cubed")

def test_times_word():
    assert "*" in norm("2 times x")

def test_plus_word():
    assert "+" in norm("x plus 3")

def test_minus_word():
    assert "-" in norm("x minus 3")

def test_subtract_word():
    assert "-" in norm("x subtract 3")

def test_equals_word():
    assert "=" in norm("x equals 5")

def test_is_equal_to():
    assert "=" in norm("x is equal to 5")

def test_divided_by():
    assert "/" in norm("x divided by 2")

def test_factor_keyword():
    result = norm("factorize x^2 + 5x + 6")
    assert result.startswith("factor")

def test_factor_out():
    result = norm("factor out x^2 + x")
    assert result.startswith("factor")

def test_solve_find():
    result = norm("find x + y = 5 and x - y = 1")
    assert result.startswith("solve")

def test_solve_calculate():
    result = norm("calculate x + y = 5 and x - y = 1")
    assert result.startswith("solve")

def test_solve_what_is():
    result = norm("what is x + 2 = 5")
    assert "solve" in result

def test_given_to_and():
    result = norm("solve x = 1 given y = 2")
    assert "and" in result

def test_with_to_and():
    result = norm("solve x = 1 with y = 2")
    assert "and" in result

# ------------------------------------------------------------------
# Combinations
# ------------------------------------------------------------------

def test_full_ocr_phrase():
    result = norm("X² + 5X + 6")
    assert "x^2" in result

def test_full_speech_phrase():
    result = norm("factor x squared plus 5 x plus 6")
    # "squared" → "^2" leaves the preceding space, giving "x ^2"
    assert result == "factor x ^2 + 5 x + 6"
