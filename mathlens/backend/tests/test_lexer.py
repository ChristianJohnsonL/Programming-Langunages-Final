import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from lexer import tokenize, LexerError, Token


def types(text: str):
    """Return just the token type list (excluding EOF)."""
    return [t.type for t in tokenize(text) if t.type != "EOF"]


def values(text: str):
    return [(t.type, t.value) for t in tokenize(text) if t.type != "EOF"]


# ------------------------------------------------------------------
# Basic atoms
# ------------------------------------------------------------------

def test_single_number():
    assert types("42") == ["NUMBER"]

def test_decimal_number():
    assert values("3.14") == [("NUMBER", "3.14")]

def test_single_variable():
    assert values("x") == [("VARIABLE", "x")]

def test_multiple_variables_implicit_star():
    result = values("xy")
    assert result == [("VARIABLE", "x"), ("STAR", "*"), ("VARIABLE", "y")]

# ------------------------------------------------------------------
# Operators
# ------------------------------------------------------------------

def test_all_operators():
    t = types("a + b - c * d / e ^ f")
    assert t == ["VARIABLE","PLUS","VARIABLE","MINUS","VARIABLE","STAR",
                  "VARIABLE","SLASH","VARIABLE","CARET","VARIABLE"]

def test_parentheses():
    assert types("(x + 1)") == ["LPAREN","VARIABLE","PLUS","NUMBER","RPAREN"]

def test_equals():
    assert "EQUALS" in types("x = 5")

# ------------------------------------------------------------------
# Keywords
# ------------------------------------------------------------------

def test_keyword_factor():
    assert values("factor") == [("KEYWORD", "factor")]

def test_keyword_solve():
    assert values("solve") == [("KEYWORD", "solve")]

def test_keyword_and():
    assert values("and") == [("KEYWORD", "and")]

# ------------------------------------------------------------------
# Implicit multiplication
# ------------------------------------------------------------------

def test_implicit_mul_number_var():
    t = types("2x")
    assert t == ["NUMBER", "STAR", "VARIABLE"]

def test_implicit_mul_number_paren():
    t = types("3(x+1)")
    assert t == ["NUMBER","STAR","LPAREN","VARIABLE","PLUS","NUMBER","RPAREN"]

def test_implicit_mul_paren_var():
    t = types("(x+1)y")
    assert t == ["LPAREN","VARIABLE","PLUS","NUMBER","RPAREN","STAR","VARIABLE"]

def test_no_implicit_mul_between_numbers():
    t = types("2 3")
    # Two numbers separated by whitespace — no implicit star
    assert "STAR" not in t

# ------------------------------------------------------------------
# Complex expressions
# ------------------------------------------------------------------

def test_quadratic():
    t = types("x^2 + 5x + 6")
    assert t == ["VARIABLE","CARET","NUMBER","PLUS","NUMBER","STAR","VARIABLE","PLUS","NUMBER"]

def test_linear_equation():
    t = types("2x + y = 5")
    assert t == ["NUMBER","STAR","VARIABLE","PLUS","VARIABLE","EQUALS","NUMBER"]

def test_negative_number():
    t = types("-3x")
    assert t == ["MINUS","NUMBER","STAR","VARIABLE"]

def test_full_factor_input():
    toks = tokenize("factor x^2 + 5x + 6")
    assert toks[0].type == "KEYWORD"
    assert toks[0].value == "factor"

def test_full_solve_input():
    toks = tokenize("solve 2x + y = 5 and x - y = 1")
    kw_vals = [t.value for t in toks if t.type == "KEYWORD"]
    assert kw_vals == ["solve", "and"]

# ------------------------------------------------------------------
# Error cases
# ------------------------------------------------------------------

def test_unknown_character_raises():
    with pytest.raises(LexerError):
        tokenize("x @ 2")

def test_trailing_decimal_raises():
    with pytest.raises(LexerError):
        tokenize("3.")

def test_eof_token_present():
    toks = tokenize("x")
    assert toks[-1].type == "EOF"
