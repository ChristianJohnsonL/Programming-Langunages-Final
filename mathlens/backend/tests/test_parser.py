import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from parser import parse


# ------------------------------------------------------------------
# Factor statements
# ------------------------------------------------------------------

def test_parse_factor_type():
    ast = parse("factor x^2 + 5x + 6")
    assert ast["type"] == "Factor"

def test_parse_factor_has_expr():
    ast = parse("factor x^2 + 5x + 6")
    assert "expr" in ast

def test_factor_quadratic_structure():
    ast = parse("factor x^2 + 5x + 6")
    # Top-level expr should be a BinOp (+)
    assert ast["expr"]["type"] == "BinOp"

def test_factor_simple_linear():
    ast = parse("factor x + 3")
    assert ast["type"] == "Factor"
    assert ast["expr"]["type"] == "BinOp"
    assert ast["expr"]["op"] == "+"

def test_factor_negative_constant():
    ast = parse("factor x^2 - 4")
    assert ast["type"] == "Factor"

def test_factor_with_coefficient():
    ast = parse("factor 2x^2 + 4x")
    assert ast["type"] == "Factor"

# ------------------------------------------------------------------
# Solve statements
# ------------------------------------------------------------------

def test_parse_solve_type():
    ast = parse("solve 2x + y = 5 and x - y = 1")
    assert ast["type"] == "Solve"

def test_parse_solve_two_equations():
    ast = parse("solve 2x + y = 5 and x - y = 1")
    assert len(ast["equations"]) == 2

def test_solve_equation_type():
    ast = parse("solve x + y = 3 and x - y = 1")
    for eq in ast["equations"]:
        assert eq["type"] == "Equation"
        assert "left" in eq
        assert "right" in eq

# ------------------------------------------------------------------
# Expression structure (AST node shapes)
# ------------------------------------------------------------------

def test_binop_node():
    ast = parse("factor x + 2")
    expr = ast["expr"]
    assert expr["type"] == "BinOp"
    assert expr["op"] == "+"

def test_power_node():
    ast = parse("factor x^2")
    expr = ast["expr"]
    assert expr["type"] == "Power"
    assert expr["base"]["type"] == "Variable"
    assert expr["exp"]["type"] == "Number"
    assert expr["exp"]["value"] == 2.0

def test_number_node():
    ast = parse("factor 5")
    assert ast["expr"]["type"] == "Number"
    assert ast["expr"]["value"] == 5.0

def test_variable_node():
    ast = parse("factor x")
    assert ast["expr"]["type"] == "Variable"
    assert ast["expr"]["name"] == "x"

def test_unary_minus_node():
    ast = parse("factor -x")
    assert ast["expr"]["type"] == "UnaryMinus"
    assert ast["expr"]["operand"]["type"] == "Variable"

def test_nested_unary_minus():
    ast = parse("factor -3")
    assert ast["expr"]["type"] == "UnaryMinus"

def test_parenthesised_expression():
    ast = parse("factor (x + 2)")
    assert ast["expr"]["type"] == "BinOp"

# ------------------------------------------------------------------
# Operator precedence
# ------------------------------------------------------------------

def test_mul_before_add():
    ast = parse("factor 2*x + 3")
    # Top node should be + with left = 2*x (BinOp *) and right = 3
    expr = ast["expr"]
    assert expr["op"] == "+"
    assert expr["left"]["op"] == "*"

def test_power_before_mul():
    ast = parse("factor x^2 * 3")
    # Top node should be * with left = x^2 (Power)
    expr = ast["expr"]
    assert expr["op"] == "*"
    assert expr["left"]["type"] == "Power"

def test_right_assoc_power():
    ast = parse("factor x^2^3")
    # x^(2^3) — right branch of the outer Power should itself be a Power
    expr = ast["expr"]
    assert expr["type"] == "Power"
    assert expr["exp"]["type"] == "Power"

# ------------------------------------------------------------------
# Error cases
# ------------------------------------------------------------------

def test_missing_keyword():
    result = parse("x^2 + 5x + 6")
    assert result.get("error") is not None

def test_incomplete_expression():
    result = parse("factor x +")
    assert result.get("error") is not None

def test_unmatched_paren():
    result = parse("factor (x + 2")
    assert result.get("error") is not None

def test_extra_paren():
    result = parse("factor x + 2)")
    assert result.get("error") is not None

def test_error_has_suggestion():
    result = parse("factor x +")
    assert "suggestion" in result

def test_empty_input():
    result = parse("")
    assert result.get("error") is not None

def test_unknown_keyword():
    result = parse("integrate x^2")
    assert result.get("error") is not None

def test_solve_missing_and():
    result = parse("solve x = 1 x = 2")
    assert result.get("error") is not None
