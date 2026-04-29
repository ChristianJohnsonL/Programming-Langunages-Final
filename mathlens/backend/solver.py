import math
from typing import Dict, Any, List, Optional, Tuple


def _collect_poly(node: Dict[str, Any], var: str) -> Dict[int, float]:
    coeffs: Dict[int, float] = {}

    def add(degree: int, coef: float) -> None:
        coeffs[degree] = coeffs.get(degree, 0.0) + coef

    def walk(n: Dict[str, Any], sign: float = 1.0) -> None:
        t = n["type"]
        if t == "Number":
            add(0, sign * n["value"])
        elif t == "Variable":
            if n["name"] != var:
                raise ValueError(f"Unexpected variable {n['name']!r}; expected {var!r}")
            add(1, sign * 1.0)
        elif t == "UnaryMinus":
            walk(n["operand"], -sign)
        elif t == "BinOp":
            op = n["op"]
            if op == '+':
                walk(n["left"], sign); walk(n["right"], sign)
            elif op == '-':
                walk(n["left"], sign); walk(n["right"], -sign)
            elif op == '*':
                lc = _term_to_coef_deg(n["left"], var)
                rc = _term_to_coef_deg(n["right"], var)
                add(lc[1] + rc[1], sign * lc[0] * rc[0])
            else:
                raise ValueError(f"Unsupported operator {op!r} in polynomial")
        elif t == "Power":
            base = n["base"]
            exp = n["exp"]
            if base["type"] == "Variable" and base["name"] == var:
                if exp["type"] != "Number":
                    raise ValueError("Exponent must be a literal number")
                add(int(exp["value"]), sign * 1.0)
            else:
                raise ValueError("Unsupported Power shape in polynomial")
        else:
            raise ValueError(f"Unknown node type: {t}")

    walk(node)
    return coeffs


def _term_to_coef_deg(node: Dict[str, Any], var: str) -> Tuple[float, int]:
    t = node["type"]
    if t == "Number":
        return (node["value"], 0)
    if t == "Variable":
        if node["name"] != var:
            raise ValueError(f"Unexpected variable {node['name']!r}")
        return (1.0, 1)
    if t == "Power":
        base = node["base"]
        exp = node["exp"]
        if base["type"] == "Variable" and base["name"] == var and exp["type"] == "Number":
            return (1.0, int(exp["value"]))
        raise ValueError("Unsupported Power in term")
    if t == "UnaryMinus":
        c, d = _term_to_coef_deg(node["operand"], var)
        return (-c, d)
    raise ValueError(f"Cannot extract coef/deg from {t}")


def _fmt(v: float) -> str:
    return str(int(v)) if v == int(v) else str(v)


def _solve_factor(ast_node: Dict[str, Any]) -> Dict[str, Any]:
    expr = ast_node["expr"]
    var = _find_variable(expr)
    if var is None:
        return {"error": "SolverError", "message": "Expression contains no variable."}

    try:
        coeffs = _collect_poly(expr, var)
    except ValueError as exc:
        return {"error": "SolverError", "message": str(exc)}

    degree = max(coeffs.keys()) if coeffs else 0
    a = coeffs.get(2, 0.0)
    b = coeffs.get(1, 0.0)
    c = coeffs.get(0, 0.0)

    input_str = _poly_to_str(a, b, c, var)
    steps: List[Dict[str, Any]] = []

    if degree == 1:
        root = -c / b
        steps.append({"step": 1, "description": f"Linear polynomial: {b}{var} + {_fmt(c)}"})
        steps.append({"step": 2, "description": f"Set equal to zero: {b}{var} + {_fmt(c)} = 0"})
        steps.append({"step": 3, "description": f"{b}{var} = {_fmt(-c)}, so {var} = {_fmt(root)}"})
        sign = "+" if -root >= 0 else "-"
        factor_str = f"({var} {sign} {_fmt(abs(root))})" if b == 1 else f"{_fmt(b)}({var} {sign} {_fmt(abs(root))})"
        return {
            "type": "factoring",
            "input": input_str,
            "steps": steps,
            "result": factor_str,
            "roots": [root],
            "factorable": True,
        }

    if degree == 2:
        steps.append({"step": 1, "description": f"Identify coefficients: a = {_fmt(a)}, b = {_fmt(b)}, c = {_fmt(c)}"})
        discriminant = b * b - 4 * a * c
        steps.append({"step": 2, "description": f"Compute discriminant: b² − 4ac = ({_fmt(b)})² − 4({_fmt(a)})({_fmt(c)}) = {_fmt(discriminant)}"})

        target_product = a * c
        p, q = _find_integer_factor_pair(target_product, b)

        if p is not None:
            steps.append({"step": 3, "description": f"Find two numbers that multiply to {_fmt(target_product)} and add to {_fmt(b)}: {_fmt(p)} and {_fmt(q)}"})
            r1 = -p / a
            r2 = -q / a
            steps.append({"step": 4, "description": f"Roots are {var} = {_fmt(r1)} and {var} = {_fmt(r2)}"})
            steps.append({"step": 5, "description": "Write in factored form"})

            def _factor_term(root_val: float) -> str:
                sign = "+" if -root_val >= 0 else "-"
                return f"({var} {sign} {_fmt(abs(root_val))})"

            prefix = f"{_fmt(a)}" if a != 1 else ""
            return {
                "type": "factoring",
                "input": input_str,
                "steps": steps,
                "result": prefix + _factor_term(r1) + _factor_term(r2),
                "roots": [r1, r2],
                "factorable": True,
            }
        else:
            steps.append({"step": 3, "description": f"No integer factor pair found for product = {_fmt(target_product)}, sum = {_fmt(b)}"})
            steps.append({"step": 4, "description": f"Apply quadratic formula: {var} = (−b ± √(b²−4ac)) / 2a"})
            if discriminant < 0:
                r_real = -b / (2 * a)
                r_imag = math.sqrt(-discriminant) / (2 * a)
                steps.append({"step": 5, "description": f"Discriminant < 0; complex roots: {var} = {_fmt(r_real)} ± {_fmt(r_imag)}i"})
                return {
                    "type": "factoring",
                    "input": input_str,
                    "steps": steps,
                    "result": f"{var} = {_fmt(r_real)} ± {_fmt(r_imag)}i",
                    "roots": [],
                    "factorable": False,
                }
            else:
                sqrt_disc = math.sqrt(discriminant)
                r1_val = (-b + sqrt_disc) / (2 * a)
                r2_val = (-b - sqrt_disc) / (2 * a)
                steps.append({"step": 5, "description": f"√discriminant = √{_fmt(discriminant)} = {_fmt(sqrt_disc)}"})
                steps.append({"step": 6, "description": f"{var}₁ = ({_fmt(-b)} + {_fmt(sqrt_disc)}) / {_fmt(2*a)} = {_fmt(r1_val)}"})
                steps.append({"step": 7, "description": f"{var}₂ = ({_fmt(-b)} − {_fmt(sqrt_disc)}) / {_fmt(2*a)} = {_fmt(r2_val)}"})
                return {
                    "type": "factoring",
                    "input": input_str,
                    "steps": steps,
                    "result": f"{var} = ({_fmt(-b)} ± √{_fmt(discriminant)}) / {_fmt(2*a)}",
                    "roots": [r1_val, r2_val],
                    "factorable": False,
                }

    return {"error": "SolverError", "message": f"Unsupported polynomial degree: {degree}"}


def _find_integer_factor_pair(product: float, total: float) -> Tuple[Optional[float], Optional[float]]:
    if product == 0:
        return (0.0, total)
    abs_prod = abs(int(round(product)))
    for i in range(1, abs_prod + 1):
        if abs_prod % i == 0:
            for p in [i, -i]:
                q = total - p
                if abs(p * q - product) < 1e-9:
                    return (float(p), float(q))
    return (None, None)


def _solve_linear_system(ast_node: Dict[str, Any]) -> Dict[str, Any]:
    equations = ast_node["equations"]
    if len(equations) != 2:
        return {"error": "SolverError", "message": "Exactly two equations required."}

    try:
        vars_found = set()
        for eq in equations:
            vars_found |= _find_all_variables(eq["left"])
            vars_found |= _find_all_variables(eq["right"])
        vars_found = sorted(vars_found)
        if len(vars_found) != 2:
            return {"error": "SolverError", "message": f"Expected exactly 2 variables, found: {vars_found}"}
        v1, v2 = vars_found[0], vars_found[1]
        rows = [_equation_to_row(eq, v1, v2) for eq in equations]
    except ValueError as exc:
        return {"error": "SolverError", "message": str(exc)}

    (a1, b1, r1), (a2, b2, r2) = rows
    input_strs = [_row_to_str(a1, b1, r1, v1, v2), _row_to_str(a2, b2, r2, v1, v2)]
    steps: List[Dict[str, Any]] = []
    steps.append({"step": 1, "description": f"Equation 1: {input_strs[0]}"})
    steps.append({"step": 2, "description": f"Equation 2: {input_strs[1]}"})

    det = a1 * b2 - a2 * b1
    if abs(det) < 1e-10:
        return {"error": "SolverError", "message": "The system has no unique solution (equations are dependent or inconsistent)."}

    m1, m2 = a2, a1
    new_b = m1 * b1 - m2 * b2
    new_r = m1 * r1 - m2 * r2

    steps.append({
        "step": 3,
        "description": (
            f"Multiply Equation 1 by {_fmt(m1)} and Equation 2 by {_fmt(m2)}, then subtract: "
            f"({_fmt(m1)}×{_fmt(a1)} − {_fmt(m2)}×{_fmt(a2)}){v1} + "
            f"({_fmt(m1)}×{_fmt(b1)} − {_fmt(m2)}×{_fmt(b2)}){v2} = "
            f"{_fmt(m1)}×{_fmt(r1)} − {_fmt(m2)}×{_fmt(r2)}"
        )
    })
    steps.append({
        "step": 4,
        "description": f"0·{v1} + {_fmt(new_b)}·{v2} = {_fmt(new_r)}, so {v2} = {_fmt(new_r)}/{_fmt(new_b)} = {_fmt(new_r/new_b)}"
    })

    val_v2 = new_r / new_b

    if abs(a1) > 1e-10:
        val_v1 = (r1 - b1 * val_v2) / a1
        steps.append({
            "step": 5,
            "description": (
                f"Substitute {v2} = {_fmt(val_v2)} into Equation 1: "
                f"{_fmt(a1)}·{v1} + {_fmt(b1)}·{_fmt(val_v2)} = {_fmt(r1)}, "
                f"so {_fmt(a1)}·{v1} = {_fmt(r1 - b1*val_v2)}, "
                f"{v1} = {_fmt(val_v1)}"
            )
        })
    else:
        val_v1 = (r2 - b2 * val_v2) / a2
        steps.append({
            "step": 5,
            "description": (
                f"Substitute {v2} = {_fmt(val_v2)} into Equation 2: "
                f"{_fmt(a2)}·{v1} = {_fmt(r2 - b2*val_v2)}, "
                f"{v1} = {_fmt(val_v1)}"
            )
        })

    def _clean(v: float) -> Any:
        return int(v) if v == int(v) else round(v, 8)

    return {
        "type": "linear_system",
        "input": input_strs,
        "method": "elimination",
        "steps": steps,
        "result": {v1: _clean(val_v1), v2: _clean(val_v2)},
    }


def _equation_to_row(eq: Dict[str, Any], v1: str, v2: str) -> Tuple[float, float, float]:
    left_coeffs = _collect_poly_multi(eq["left"], {v1, v2})
    right_coeffs = _collect_poly_multi(eq["right"], {v1, v2})
    a = left_coeffs.get(v1, 0.0) - right_coeffs.get(v1, 0.0)
    b = left_coeffs.get(v2, 0.0) - right_coeffs.get(v2, 0.0)
    rhs = right_coeffs.get("_const", 0.0) - left_coeffs.get("_const", 0.0)
    return (a, b, rhs)


def _collect_poly_multi(node: Dict[str, Any], variables: set) -> Dict[str, float]:
    result: Dict[str, float] = {}

    def add(key: str, val: float) -> None:
        result[key] = result.get(key, 0.0) + val

    def walk(n: Dict[str, Any], sign: float = 1.0) -> None:
        t = n["type"]
        if t == "Number":
            add("_const", sign * n["value"])
        elif t == "Variable":
            add(n["name"], sign * 1.0)
        elif t == "UnaryMinus":
            walk(n["operand"], -sign)
        elif t == "BinOp":
            op = n["op"]
            if op == '+':
                walk(n["left"], sign); walk(n["right"], sign)
            elif op == '-':
                walk(n["left"], sign); walk(n["right"], -sign)
            elif op == '*':
                lc = _try_const(n["left"])
                rc = _try_const(n["right"])
                if lc is not None:
                    walk(n["right"], sign * lc)
                elif rc is not None:
                    walk(n["left"], sign * rc)
                else:
                    raise ValueError("Non-linear term encountered in linear system solver")
            else:
                raise ValueError(f"Unsupported operator {op!r} in linear system")
        else:
            raise ValueError(f"Unsupported node type {t} in linear expression")

    walk(node)
    return result


def _try_const(node: Dict[str, Any]) -> Optional[float]:
    if node["type"] == "Number":
        return node["value"]
    if node["type"] == "UnaryMinus" and node["operand"]["type"] == "Number":
        return -node["operand"]["value"]
    return None


def _find_variable(node: Dict[str, Any]) -> Optional[str]:
    t = node["type"]
    if t == "Variable":
        return node["name"]
    for key in ("left", "right", "operand", "base", "exp", "expr"):
        if key in node:
            v = _find_variable(node[key])
            if v:
                return v
    return None


def _find_all_variables(node: Dict[str, Any]) -> set:
    t = node["type"]
    if t == "Variable":
        return {node["name"]}
    result = set()
    for key in ("left", "right", "operand", "base", "exp", "expr"):
        if key in node:
            result |= _find_all_variables(node[key])
    return result


def _poly_to_str(a: float, b: float, c: float, var: str) -> str:
    parts = []
    if a:
        coef = "" if a == 1 else ("−" if a == -1 else _fmt(a))
        parts.append(f"{coef}{var}²")
    if b:
        sign = "+" if b > 0 else "−"
        coef = "" if abs(b) == 1 else _fmt(abs(b))
        if parts:
            parts.append(f"{sign} {coef}{var}")
        else:
            parts.append(f"{'−' if b < 0 else ''}{coef}{var}")
    if c or not parts:
        if parts:
            parts.append(f"{'+'if c >= 0 else '−'} {_fmt(abs(c))}")
        else:
            parts.append(_fmt(c))
    return " ".join(parts)


def _row_to_str(a: float, b: float, r: float, v1: str, v2: str) -> str:
    def term(coef: float, var: str) -> str:
        if coef == 0:
            return ""
        prefix = "" if coef == 1 else ("−" if coef == -1 else _fmt(coef))
        return f"{prefix}{var}"

    t1 = term(a, v1)
    t2 = term(b, v2)
    if t1 and t2:
        sign = "+" if b >= 0 else "−"
        lhs = f"{t1} {sign} {term(abs(b), v2)}"
    else:
        lhs = t1 or t2 or "0"
    return f"{lhs} = {_fmt(r)}"


def _ast_to_str(node: Dict[str, Any]) -> str:
    t = node["type"]
    if t == "Number": return _fmt(node["value"])
    if t == "Variable": return node["name"]
    if t == "UnaryMinus": return f"-{_ast_to_str(node['operand'])}"
    if t == "BinOp": return f"({_ast_to_str(node['left'])} {node['op']} {_ast_to_str(node['right'])})"
    if t == "Power": return f"{_ast_to_str(node['base'])}^{_ast_to_str(node['exp'])}"
    return str(node)


def solve(ast: Dict[str, Any]) -> Dict[str, Any]:
    if "error" in ast:
        return ast
    t = ast.get("type")
    if t == "Factor":
        return _solve_factor(ast)
    if t == "Solve":
        return _solve_linear_system(ast)
    return {"error": "SolverError", "message": f"Unknown statement type: {t!r}"}
