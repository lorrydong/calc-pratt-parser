#!/usr/bin/env python3
"""Tests for the Pratt-parser calculator."""

import math
import unittest
from calc import evaluate, tokenise, Token


class TestTokenise(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(tokenise(""), [])

    def test_single_number(self):
        tokens = tokenise("42")
        self.assertEqual(len(tokens), 1)
        self.assertEqual(tokens[0].kind, Token.NUMBER)
        self.assertEqual(tokens[0].value, 42.0)

    def test_float(self):
        tokens = tokenise("3.14")
        self.assertEqual(tokens[0].value, 3.14)

    def test_sci_notation(self):
        tokens = tokenise("1e10")
        self.assertEqual(tokens[0].value, 1e10)
        tokens = tokenise("1.5e-3")
        self.assertEqual(tokens[0].value, 0.0015)

    def test_simple_expr(self):
        tokens = tokenise("1+2")
        kinds = [t.kind for t in tokens]
        self.assertEqual(kinds, [Token.NUMBER, Token.PLUS, Token.NUMBER])

    def test_unary_minus(self):
        tokens = tokenise("-5")
        kinds = [t.kind for t in tokens]
        self.assertEqual(kinds, ["UNARY", Token.NUMBER])

    def test_unary_in_expr(self):
        tokens = tokenise("3 * -2")
        kinds = [t.kind for t in tokens]
        self.assertEqual(kinds, [Token.NUMBER, Token.STAR, "UNARY", Token.NUMBER])

    def test_constants(self):
        tokens = tokenise("pi")
        self.assertEqual(len(tokens), 1)
        self.assertAlmostEqual(tokens[0].value, math.pi)

    def test_implicit_mul_number_const(self):
        tokens = tokenise("2pi")
        kinds = [t.kind for t in tokens]
        self.assertEqual(kinds, [Token.NUMBER, Token.STAR, Token.NUMBER])

    def test_implicit_mul_paren(self):
        tokens = tokenise("2(3+4)")
        kinds = [t.kind for t in tokens]
        self.assertIn(Token.STAR, kinds)

    def test_factorial_token(self):
        tokens = tokenise("5!")
        kinds = [t.kind for t in tokens]
        self.assertIn(Token.BANG, kinds)


class TestEvaluate(unittest.TestCase):
    # Basic arithmetic
    def test_addition(self):
        self.assertEqual(evaluate("1 + 2"), 3)

    def test_subtraction(self):
        self.assertEqual(evaluate("10 - 3"), 7)

    def test_multiplication(self):
        self.assertEqual(evaluate("6 * 7"), 42)

    def test_division(self):
        self.assertEqual(evaluate("10 / 4"), 2.5)

    def test_floor_div(self):
        self.assertEqual(evaluate("10 // 4"), 2)

    def test_modulo(self):
        self.assertEqual(evaluate("10 % 3"), 1)

    def test_power(self):
        self.assertEqual(evaluate("2 ** 10"), 1024)

    def test_caret_power(self):
        self.assertEqual(evaluate("2 ^ 10"), 1024)

    # Precedence
    def test_precedence_basic(self):
        self.assertEqual(evaluate("2 + 3 * 4"), 14)

    def test_precedence_paren(self):
        self.assertEqual(evaluate("(2 + 3) * 4"), 20)

    def test_right_assoc_power(self):
        # 2 ** 3 ** 2  = 2 ** (3 ** 2) = 2 ** 9 = 512,  NOT (2 ** 3) ** 2 = 64
        self.assertEqual(evaluate("2 ** 3 ** 2"), 512)

    def test_chained_ops(self):
        self.assertAlmostEqual(evaluate("1 + 2 * 3 - 4 / 2 + 5 % 3"), 1 + 2*3 - 4/2 + 5%3)

    # Unary minus
    def test_neg_number(self):
        self.assertEqual(evaluate("-5"), -5)

    def test_neg_expr(self):
        self.assertEqual(evaluate("-(2 + 3)"), -5)

    def test_double_neg(self):
        self.assertEqual(evaluate("--5"), 5)

    def test_unary_in_mul(self):
        self.assertEqual(evaluate("3 * -2"), -6)

    # Constants
    def test_pi(self):
        self.assertAlmostEqual(evaluate("pi"), math.pi)

    def test_e(self):
        self.assertAlmostEqual(evaluate("e"), math.e)

    def test_tau(self):
        self.assertAlmostEqual(evaluate("tau"), math.tau)

    # Functions
    def test_sqrt(self):
        self.assertEqual(evaluate("sqrt(9)"), 3)
        self.assertAlmostEqual(evaluate("sqrt(2)"), math.sqrt(2))

    def test_sin(self):
        self.assertAlmostEqual(evaluate("sin(pi/2)"), 1.0)

    def test_cos(self):
        self.assertAlmostEqual(evaluate("cos(pi)"), -1.0)

    def test_tan(self):
        self.assertAlmostEqual(evaluate("tan(0)"), 0.0)

    def test_log10(self):
        self.assertAlmostEqual(evaluate("log(100)"), 2.0)

    def test_ln(self):
        self.assertAlmostEqual(evaluate("ln(e)"), 1.0)

    def test_abs(self):
        self.assertEqual(evaluate("abs(-5)"), 5)

    def test_floor(self):
        self.assertEqual(evaluate("floor(3.7)"), 3)

    def test_ceil(self):
        self.assertEqual(evaluate("ceil(3.2)"), 4)

    # Factorial
    def test_factorial(self):
        self.assertEqual(evaluate("5!"), 120)

    def test_factorial_zero(self):
        self.assertEqual(evaluate("0!"), 1)

    # Implicit multiplication
    def test_implicit_number_paren(self):
        self.assertEqual(evaluate("2(3+4)"), 14)

    def test_implicit_number_const(self):
        self.assertAlmostEqual(evaluate("2pi"), 2 * math.pi)

    def test_implicit_number_func(self):
        self.assertAlmostEqual(evaluate("2sin(pi/2)"), 2.0)

    def test_implicit_const_paren(self):
        self.assertAlmostEqual(evaluate("pi(2)"), 2 * math.pi)

    # Edge cases
    def test_float_result_int_repr(self):
        # 1.0 should display as 1 (handled in fmt_result, but eval returns float)
        self.assertEqual(evaluate("2.0 + 2.0"), 4.0)
        self.assertIsInstance(evaluate("2.0 + 2.0"), float)

    def test_large_power(self):
        self.assertEqual(evaluate("2 ** 100"), 2 ** 100)

    def test_negative_power(self):
        self.assertAlmostEqual(evaluate("2 ** -1"), 0.5)

    def test_div_zero(self):
        with self.assertRaises(ZeroDivisionError):
            evaluate("1 / 0")

    def test_factorial_negative(self):
        with self.assertRaises(ValueError):
            evaluate("(-1)!")

    def test_unknown_ident(self):
        with self.assertRaises(NameError):
            evaluate("foo")

    def test_unclosed_paren(self):
        with self.assertRaises(SyntaxError):
            evaluate("(1+2")

    def test_implicit_mul_numbers(self):
        """1+2 3 is treated as 1+2*3 via implicit multiplication."""
        self.assertEqual(evaluate("1+2 3"), 7)


if __name__ == "__main__":
    unittest.main()
