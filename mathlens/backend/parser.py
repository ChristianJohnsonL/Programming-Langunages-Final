from typing import List, Dict, Any, Optional
from lexer import Token, tokenize, LexerError


class ParseError(Exception):
    def __init__(self, message: str, pos: int, suggestion: str = ""):
        super().__init__(message)
        self.pos = pos
        self.suggestion = suggestion


class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def _current(self) -> Token:
        return self.tokens[self.pos]

    def _peek_type(self) -> str:
        return self._current().type

    def _advance(self) -> Token:
        tok = self.tokens[self.pos]
        if tok.type != "EOF":
            self.pos += 1
        return tok

    def _expect(self, ttype: str, value: Optional[str] = None) -> Token:
        tok = self._current()
        if tok.type != ttype:
            hint = f"expected {value!r}" if value else f"expected {ttype!r}"
            raise ParseError(
                f"Unexpected token {tok.value!r} at position {tok.pos}: {hint}",
                tok.pos,
                _suggest_fix(tok),
            )
        if value is not None and tok.value != value:
            raise ParseError(
                f"Expected keyword {value!r} but got {tok.value!r} at position {tok.pos}",
                tok.pos,
                f"Did you mean '{value}'?",
            )
        return self._advance()

    def parse_program(self) -> Dict[str, Any]:
        node = self._parse_statement()
        self._expect("EOF")
        return node

    def _parse_statement(self) -> Dict[str, Any]:
        tok = self._current()
        if tok.type != "KEYWORD":
            raise ParseError(
                f"Statement must begin with 'factor' or 'solve', got {tok.value!r}",
                tok.pos,
                "Try: 'factor x^2 + 5x + 6' or 'solve 2x + y = 5 and x - y = 1'",
            )
        if tok.value == "factor":
            return self._parse_factor_stmt()
        if tok.value == "solve":
            return self._parse_solve_stmt()
        raise ParseError(
            f"Unknown keyword {tok.value!r}",
            tok.pos,
            "Valid keywords are 'factor' and 'solve'",
        )

    def _parse_factor_stmt(self) -> Dict[str, Any]:
        self._expect("KEYWORD", "factor")
        expr = self._parse_expression()
        return (
            {
                "type": "Factor",
                "expr": expr,
            }
        )

    def _parse_solve_stmt(self) -> Dict[str, Any]:
        self._expect("KEYWORD", "solve")
        eq1 = self._parse_equation()
        self._expect("KEYWORD", "and")
        eq2 = self._parse_equation()
        return (
            {
                "type": "Solve",
                "equations": [eq1, eq2],
            }
        )

    def _parse_equation(self) -> Dict[str, Any]:
        left = self._parse_expression()
        self._expect("EQUALS")
        right = self._parse_expression()
        return (
            {
                "type": "Equation",
                "left": left,
                "right": right,
            }
        )

    def _parse_expression(self) -> Dict[str, Any]:
        node = self._parse_term()
        while self._peek_type() in ("PLUS", "MINUS"):
            op = self._advance().value
            right = self._parse_term()
            node = (
                {
                    "type": "BinOp",
                    "op": op,
                    "left": node,
                    "right": right,
                }
            )
        return node

    def _parse_term(self) -> Dict[str, Any]:
        node = self._parse_unary()
        while self._peek_type() in ("STAR", "SLASH"):
            op = self._advance().value
            right = self._parse_unary()
            node = (
                {
                    "type": "BinOp",
                    "op": op,
                    "left": node,
                    "right": right,
                }
            )
        return node

    def _parse_unary(self) -> Dict[str, Any]:
        if self._peek_type() == "MINUS":
            self._advance()
            operand = self._parse_unary()
            return (
                {
                    "type": "UnaryMinus",
                    "operand": operand,
                }
            )
        return self._parse_power()

    def _parse_power(self) -> Dict[str, Any]:
        base = self._parse_atom()
        if self._peek_type() == "CARET":
            self._advance()
            exp = self._parse_unary()
            return (
                {
                    "type": "Power",
                    "base": base,
                    "exp": exp,
                }
            )
        return base

    def _parse_atom(self) -> Dict[str, Any]:
        tok = self._current()
        if tok.type == "NUMBER":
            self._advance()
            return (
                {
                    "type": "Number",
                    "value": float(tok.value),
                }
            )
        if tok.type == "VARIABLE":
            self._advance()
            return (
                {
                    "type": "Variable",
                    "name": tok.value,
                }
            )
        if tok.type == "LPAREN":
            self._advance()
            expr = self._parse_expression()
            self._expect("RPAREN")
            return expr
        raise ParseError(
            f"Unexpected token {tok.value!r} at position {tok.pos}: expected number, variable, or '('",
            tok.pos,
            _suggest_fix(tok),
        )


def _suggest_fix(tok: Token) -> str:
    if tok.type == "EOF":
        return "The expression appears to be incomplete. Check that all operators have operands."
    if tok.type in ("PLUS", "MINUS", "STAR", "SLASH", "CARET"):
        return f"Operator {tok.value!r} is missing an operand."
    if tok.type == "RPAREN":
        return "Found ')' with no matching '('. Check your parentheses."
    if tok.type == "EQUALS":
        return "Unexpected '='. For factoring use 'factor expr'; for systems use 'solve eq1 and eq2'."
    return f"Check the input around '{tok.value}' at position {tok.pos}."


def parse(text: str) -> Dict[str, Any]:
    try:
        tokens = tokenize(text)
    except LexerError as exc:
        return (
            {
                "error": "LexerError",
                "message": str(exc),
                "suggestion": f"Unexpected character at position {exc.pos}.",
            }
        )
    try:
        p = Parser(tokens)
        return p.parse_program()
    except ParseError as exc:
        return (
            {
                "error": "ParseError",
                "message": str(exc),
                "suggestion": exc.suggestion,
            }
        )
