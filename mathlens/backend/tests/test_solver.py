import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import math
import pytest
from parser import parse
from solver import solve


def run(text: str) -> dict:
    return solve(parse(text))


# ------------------------------------------------------------------
# Factoring — factorable over integers
# ------------------------------------------------------------------

def test_factor_x2_plus_5x_plus_6():
    result = run("factor x^2 + 5x + 6")
    assert result["type"] == "factoring"
    assert result["factorable"] is True
    assert set(result["roots"]) == {-2.0, -3.0}
    assert "(x + 2)(x + 3)" in result["result"] or "(x + 3)(x + 2)" in result["result"]

def test_factor_x2_minus_5x_plus_6():
    result = run("factor x^2 - 5x + 6")
    assert result["factorable"] is True
    assert set(result["roots"]) == {2.0, 3.0}

def test_factor_difference_of_squares():
    result = run("factor x^2 - 4")
    assert result["factorable"] is True
    roots = set(result["roots"])
    assert roots == {2.0, -2.0}

def test_factor_x2_plus_x():
    result = run("factor x^2 + x")
    # roots: x=0, x=-1
    assert result["factorable"] is True
    assert 0.0 in result["roots"]

def test_factor_perfect_square():
    result = run("factor x^2 + 2x + 1")
    assert result["factorable"] is True
    assert result["roots"].count(-1.0) == 2 or set(result["roots"]) == {-1.0}

# ------------------------------------------------------------------
# Factoring — not factorable over integers (quadratic formula)
# ------------------------------------------------------------------

def test_factor_not_factorable_irrational():
    result = run("factor x^2 + x + 1")
    # discriminant = 1 - 4 = -3 < 0 → complex roots
    assert result["factorable"] is False

def test_factor_not_factorable_irrational_real_roots():
    result = run("factor x^2 - 3")
    assert result["factorable"] is False
    assert len(result["roots"]) == 2
    r1, r2 = sorted(result["roots"])
    assert abs(r1 + math.sqrt(3)) < 1e-9
    assert abs(r2 - math.sqrt(3)) < 1e-9

def test_factor_step_count():
    result = run("factor x^2 + 5x + 6")
    assert len(result["steps"]) >= 3

def test_factor_steps_show_numbers():
    result = run("factor x^2 + 5x + 6")
    full_text = " ".join(s["description"] for s in result["steps"])
    assert "5" in full_text and "6" in full_text

def test_factor_linear():
    result = run("factor 2x + 4")
    assert result["type"] == "factoring"

# ------------------------------------------------------------------
# Linear system solving
# ------------------------------------------------------------------

def test_solve_basic_system():
    result = run("solve 2x + y = 5 and x - y = 1")
    assert result["type"] == "linear_system"
    assert result["result"]["x"] == 2
    assert result["result"]["y"] == 1

def test_solve_simple_system():
    result = run("solve x + y = 3 and x - y = 1")
    assert result["result"]["x"] == 2
    assert result["result"]["y"] == 1

def test_solve_system_method_elimination():
    result = run("solve 3x + 2y = 12 and x + y = 5")
    assert result["method"] == "elimination"

def test_solve_system_step_count():
    result = run("solve 2x + y = 5 and x - y = 1")
    assert len(result["steps"]) >= 4

def test_solve_system_steps_show_numbers():
    result = run("solve 2x + y = 5 and x - y = 1")
    full_text = " ".join(s["description"] for s in result["steps"])
    assert "5" in full_text

def test_solve_fractional_result():
    result = run("solve 2x + 3y = 7 and x + y = 3")
    # x=2, y=1
    assert abs(result["result"]["x"] - 2) < 1e-9
    assert abs(result["result"]["y"] - 1) < 1e-9

# ------------------------------------------------------------------
# Error propagation
# ------------------------------------------------------------------

def test_solver_passes_through_parse_error():
    result = run("x^2 + 5x + 6")  # missing 'factor' keyword
    assert "error" in result

def test_solve_dependent_system():
    # 2x + 2y = 4 is a multiple of x + y = 2 → no unique solution
    result = run("solve x + y = 2 and 2x + 2y = 4")
    assert "error" in result
