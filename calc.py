#!/usr/bin/env python3
"""
A command-line calculator with Pratt parsing.

Supports:
  - Arithmetic:  +  -  *  /  %  //  **
  - Unary minus:  -3, -(2+4)
  - Parentheses:  (1+2)*3
  - Constants:    pi, e
  - Functions:    sqrt, sin, cos, tan, log (base-10), ln (natural log),
                  abs, floor, ceil, round
  - REPL mode when no arguments given.
  - Direct evaluation:  calc "1 + 2 * 3"
"""

import math
import sys
import re
from typing import List, Optional


# ---------------------------------------------------------------------------
# Tokeniser
# ---------------------------------------------------------------------------

TOKEN_RE = re.compile(r"""
    \s* (?:                                           # optional whitespace
        (?P<number>   \d+ (?:\.\d*)? (?:[eE][+-]?\d+)? )  # number
      | (?P<ident>    [a-zA-Z_][a-zA-Z0-9_]* )              # ident (func / const)
      | (?P<op>       \*\*|//|[-+*/%()^!] )                  # operators & parens
    )
""", re.VERBOSE)

class Token:
    NUMBER   = "NUMBER"
    PLUS     = "+"
    MINUS    = "-"
    STAR     = "*"
    SLASH    = "/"
    PERCENT  = "%"
    FLOORDIV = "//"
    POWER    = "**"
    CARET    = "POWER"       # treat ^ as power too
    BANG     = "!"           # factorial
    LPAREN   = "("
    RPAREN   = ")"
    # Internally unified
    def __init__(self, kind: str, value=None):
        self.kind = kind
        self.value = value

    def __repr__(self):
        return f"Token({self.kind}, {self.value!r})"

# Map operator strings → canonical kind
OPS = {
    "+": Token.PLUS, "-": Token.MINUS, "*": Token.STAR,
    "/": Token.SLASH, "%": Token.PERCENT,
    "//": Token.FLOORDIV, "**": Token.POWER, "^": Token.POWER,
    "(": Token.LPAREN, ")": Token.RPAREN,
    "!": Token.BANG,
}

FUNCTIONS = {
    "sqrt": math.sqrt, "sin": math.sin, "cos": math.cos,
    "tan": math.tan,  "log": math.log10, "ln": math.log,
    "abs": abs,       "floor": math.floor, "ceil": math.ceil,
    "round": round,
}

CONSTANTS = {
    "pi": math.pi, "e": math.e, "tau": math.tau,
    "inf": math.inf, "nan": math.nan,
}

def tokenise(expr: str) -> List[Token]:
    """Convert a string expression into a list of Tokens."""
    tokens: List[Token] = []
    pos = 0
    implicit_mul = False   # track if an implicit '*' is needed
    while pos < len(expr):
        m = TOKEN_RE.match(expr, pos)
        if not m:
            raise SyntaxError(f"Unexpected character at position {pos}: {expr[pos:]!r}")
        pos = m.end()

        if m.lastgroup == "number":
            t = Token(Token.NUMBER, float(m.group("number")))
            if implicit_mul:
                tokens.append(Token(Token.STAR, "*"))
            tokens.append(t)
            implicit_mul = True
        elif m.lastgroup == "ident":
            name = m.group("ident")
            # Check if the previous token was a number/rparen — implicit multiply
            if implicit_mul:
                tokens.append(Token(Token.STAR, "*"))
            if name in CONSTANTS:
                tokens.append(Token(Token.NUMBER, CONSTANTS[name]))
                implicit_mul = True
            elif name in FUNCTIONS:
                tokens.append(Token("FUNC", name))
                implicit_mul = False
            else:
                raise NameError(f"Unknown identifier: {name!r}")
        elif m.lastgroup == "op":
            text = m.group("op")
            kind = OPS[text]
            if kind == Token.LPAREN:
                if implicit_mul:
                    tokens.append(Token(Token.STAR, "*"))
                tokens.append(Token(kind, text))
                implicit_mul = False
            elif kind == Token.RPAREN:
                tokens.append(Token(kind, text))
                implicit_mul = True
            elif kind == Token.MINUS:
                # Distinguish unary from binary minus
                if not tokens or tokens[-1].kind in (
                    Token.LPAREN, Token.PLUS, Token.MINUS, "UNARY",
                    Token.STAR, Token.SLASH, Token.PERCENT,
                    Token.FLOORDIV, Token.POWER, Token.BANG,
                ) or (tokens[-1].kind == "FUNC"):
                    tokens.append(Token("UNARY", "-"))
                else:
                    tokens.append(Token(kind, text))
                implicit_mul = False
            elif kind == Token.BANG:
                tokens.append(Token(kind, text))
                implicit_mul = True
            else:
                tokens.append(Token(kind, text))
                implicit_mul = False
    return tokens


# ---------------------------------------------------------------------------
# Pratt parser
# ---------------------------------------------------------------------------

# Precedence table  (lower binds tighter)
PREC = {
    "LOWEST": 0,
    Token.PLUS:  1,  Token.MINUS: 1,
    Token.STAR:  2,  Token.SLASH: 2, Token.PERCENT: 2, Token.FLOORDIV: 2,
    Token.BANG:  3,  # postfix !
    "UNARY":     4,  # unary -
    Token.POWER: 5,  # right-associative
    "CALL":      6,  # func()
}

# Right-associative token kinds
RIGHT_ASSOC = {Token.POWER}

# ---------------------------------------------------------------------------
# Prefix handlers – called when token appears at the start of an expression
# ---------------------------------------------------------------------------

class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def peek(self) -> Optional[Token]:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def advance(self) -> Token:
        if self.pos >= len(self.tokens):
            raise SyntaxError("Unexpected end of expression")
        t = self.tokens[self.pos]
        self.pos += 1
        return t

    def expect(self, kind: str) -> Token:
        t = self.advance()
        if t.kind != kind:
            raise SyntaxError(f"Expected {kind}, got {t.kind}")
        return t

    # -- prefix handlers ---------------------------------------------------

    def prefix_number(self, t: Token) -> float:
        return t.value

    def prefix_paren(self, t: Token) -> float:
        v = self.expr(PREC["LOWEST"])
        self.expect(Token.RPAREN)
        return v

    def prefix_unary(self, t: Token) -> float:
        right = self.expr(PREC["UNARY"])
        return -right

    def prefix_func(self, t: Token) -> float:
        self.expect(Token.LPAREN)
        arg = self.expr(PREC["LOWEST"])
        self.expect(Token.RPAREN)
        return FUNCTIONS[t.value](arg)

    # -- infix handlers ----------------------------------------------------

    def infix_binary(self, left: float, t: Token) -> float:
        prec = PREC[t.kind]
        if t.kind in RIGHT_ASSOC:
            prec -= 1
        right = self.expr(prec)
        op = t.kind
        if op == Token.PLUS:        return left + right
        if op == Token.MINUS:       return left - right
        if op == Token.STAR:        return left * right
        if op == Token.SLASH:       return left / right
        if op == Token.PERCENT:     return left % right
        if op == Token.FLOORDIV:    return left // right
        if op == Token.POWER:       return left ** right
        raise SyntaxError(f"Unknown binary operator: {op}")

    def infix_bang(self, left: float, t: Token) -> float:
        # Factorial only works on non-negative integers
        if left < 0 or left != int(left):
            raise ValueError(f"Factorial requires non-negative integer, got {left}")
        return math.factorial(int(left))

    # -- Pratt core --------------------------------------------------------

    def expr(self, min_prec: int = 0) -> float:
        """Parse and evaluate an expression with Pratt parsing."""
        t = self.advance()
        # Prefix
        prefix_map = {
            Token.NUMBER: self.prefix_number,
            Token.LPAREN: self.prefix_paren,
            "UNARY":      self.prefix_unary,
            "FUNC":       self.prefix_func,
        }
        handler = prefix_map.get(t.kind)
        if handler is None:
            raise SyntaxError(f"Unexpected token: {t}")

        left = handler(t)

        # Infix loop
        while True:
            next_t = self.peek()
            if next_t is None:
                break
            prec = PREC.get(next_t.kind, None)
            if prec is None or prec <= min_prec:
                break
            # Handle right-associativity
            if next_t.kind in RIGHT_ASSOC and prec < PREC.get(next_t.kind, 0):
                break
            self.advance()  # consume the operator

            infix_map = {
                Token.PLUS:     self.infix_binary,
                Token.MINUS:    self.infix_binary,
                Token.STAR:     self.infix_binary,
                Token.SLASH:    self.infix_binary,
                Token.PERCENT:  self.infix_binary,
                Token.FLOORDIV: self.infix_binary,
                Token.POWER:    self.infix_binary,
                Token.BANG:     self.infix_bang,
            }
            h = infix_map.get(next_t.kind)
            if h is None:
                # Unknown infix — break (or we could error)
                break
            left = h(left, next_t)

        return left


def evaluate(expr: str) -> float:
    """Tokenise, parse, compute. Returns a float."""
    tokens = tokenise(expr)
    if not tokens:
        return 0.0
    parser = Parser(tokens)
    result = parser.expr()
    if parser.peek() is not None:
        raise SyntaxError(f"Unexpected token after expression: {parser.peek()}")
    return result


# ---------------------------------------------------------------------------
# Pretty-printing
# ---------------------------------------------------------------------------

def fmt_result(val: float) -> str:
    """Return a nice string representation of the result."""
    if val == int(val) and not (math.isinf(val) or math.isnan(val)):
        return str(int(val))
    return f"{val:.15g}"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

HELP = """
calc — a Pratt-parser calculator.

USAGE
  calc [EXPRESSION]          Evaluate and print result.
  calc                       Start interactive REPL (type 'quit' or Ctrl-D to exit).

EXAMPLES
  calc "2 + 3 * 4"            → 14
  calc "(1 + 2) * 3"          → 9
  calc "2 ** 10"              → 1024
  calc "sqrt(9) + sin(pi/2)"  → 4
  calc "5!"                   → 120
""".strip()


def repl():
    import readline  # optional, enables line-editing on *nix
    print("calc — type an expression, 'help', or 'quit'.  Ctrl-D to exit.")
    while True:
        try:
            line = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line:
            continue
        if line.lower() in ("quit", "exit"):
            break
        if line.lower() == "help":
            print(HELP)
            continue
        try:
            val = evaluate(line)
            print(f"  {fmt_result(val)}")
        except Exception as exc:
            print(f"  Error: {exc}")


def main():
    args = sys.argv[1:]
    if not args:
        repl()
    else:
        expr = " ".join(args)
        try:
            result = evaluate(expr)
            print(fmt_result(result))
        except Exception as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
