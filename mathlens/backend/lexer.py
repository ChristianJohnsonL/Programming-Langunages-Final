from dataclasses import dataclass
from typing import List

KEYWORDS = {"factor", "solve", "and"}


@dataclass
class Token:
    type: str
    value: str
    pos: int

    def __repr__(self):
        return f"Token({self.type}, {self.value!r}, @{self.pos})"


class LexerError(Exception):
    def __init__(self, message: str, pos: int):
        super().__init__(message)
        self.pos = pos


def tokenize(text: str) -> List[Token]:
    tokens: List[Token] = []
    i = 0
    n = len(text)

    while i < n:
        ch = text[i]

        if ch in " \t\r\n":
            i += 1
            continue

        if ch.isdigit() or (ch == '.' and i + 1 < n and text[i + 1].isdigit()):
            start = i
            while i < n and text[i].isdigit():
                i += 1
            if i < n and text[i] == '.':
                i += 1
                if i >= n or not text[i].isdigit():
                    raise LexerError("Expected digit after decimal point", i)
                while i < n and text[i].isdigit():
                    i += 1
            tokens.append(Token("NUMBER", text[start:i], start))
            continue

        if ch.islower():
            start = i
            while i < n and text[i].islower():
                i += 1
            word = text[start:i]
            if word in KEYWORDS:
                tokens.append(Token("KEYWORD", word, start))
            else:
                for idx, letter in enumerate(word):
                    if idx > 0:
                        tokens.append(Token("STAR", "*", start + idx))
                    tokens.append(Token("VARIABLE", letter, start + idx))
            continue

        simple = {
            '+': "PLUS",
            '-': "MINUS",
            '*': "STAR",
            '/': "SLASH",
            '^': "CARET",
            '(': "LPAREN",
            ')': "RPAREN",
            '=': "EQUALS",
        }
        if ch in simple:
            tokens.append(Token(simple[ch], ch, i))
            i += 1
            continue

        raise LexerError(f"Unexpected character {ch!r}", i)

    tokens = _insert_implicit_mul(tokens)
    tokens.append(Token("EOF", "", n))
    return tokens


def _insert_implicit_mul(tokens: List[Token]) -> List[Token]:
    result: List[Token] = []
    for i, tok in enumerate(tokens):
        result.append(tok)
        if i + 1 < len(tokens):
            nxt = tokens[i + 1]
            if _needs_implicit_star(tok, nxt):
                result.append(Token("STAR", "*", tok.pos + len(tok.value)))
    return result


def _needs_implicit_star(left: Token, right: Token) -> bool:
    if left.type == "NUMBER" and right.type in ("VARIABLE", "LPAREN"):
        return True
    if left.type == "RPAREN" and right.type in ("VARIABLE", "LPAREN", "NUMBER"):
        return True
    if left.type == "VARIABLE" and right.type == "LPAREN":
        return True
    return False
