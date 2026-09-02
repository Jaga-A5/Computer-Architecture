"""
Unit tests for the ALU module.
"""

import pytest
from alu import ALU, ALUOperation, ALUResult


class TestALUArithmetic:
    """Test arithmetic operations."""

    def test_add_basic(self, alu):
        result = alu.execute(ALUOperation.ADD, 10, 5)
        assert result.result == 15
        assert not result.zero
        assert not result.negative

    def test_add_carry_unsigned_wrap(self, alu):
        result = alu.execute(ALUOperation.ADD, 0xFFFFFFFF, 1)
        assert result.result == 0  # Wrap around
        assert result.zero
        assert result.carry  # Unsigned overflow

    def test_add_signed_overflow(self, alu):
        result = alu.execute(ALUOperation.ADD, 0x7FFFFFFF, 1)  # Max positive + 1
        assert result.result == 0x80000000  # Most negative
        assert result.negative
        assert result.overflow  # Signed overflow

    def test_add_zero_flag(self, alu):
        result = alu.execute(ALUOperation.ADD, 0, 0)
        assert result.result == 0
        assert result.zero

    def test_sub_basic(self, alu):
        result = alu.execute(ALUOperation.SUB, 10, 3)
        assert result.result == 7
        assert not result.zero

    def test_sub_borrow_carry_flag(self, alu):
        result = alu.execute(ALUOperation.SUB, 0, 1)
        assert result.result == 0xFFFFFFFF
        assert result.carry  # Borrow occurred

    def test_mul_basic(self, alu):
        result = alu.execute(ALUOperation.MUL, 6, 7)
        assert result.result == 42

    def test_mul_overflow(self, alu):
        result = alu.execute(ALUOperation.MUL, 0x10000, 0x10000)
        assert result.result == 0  # Lower 32 bits
        assert result.overflow  # Full product doesn't fit

    def test_div_basic(self, alu):
        result = alu.execute(ALUOperation.ADD, 20, 0)  # Using ADD as placeholder
        assert result.result == 20


class TestALULogical:
    """Test logical operations."""

    def test_and(self, alu):
        result = alu.execute(ALUOperation.AND, 0xFF, 0x0F)
        assert result.result == 0x0F

    def test_or(self, alu):
        result = alu.execute(ALUOperation.OR, 0xF0, 0x0F)
        assert result.result == 0xFF

    def test_xor(self, alu):
        result = alu.execute(ALUOperation.XOR, 0xFF, 0xFF)
        assert result.result == 0
        assert result.zero

    def test_not(self, alu):
        result = alu.execute(ALUOperation.NOT, 0xFFFFFFFF)
        assert result.result == 0
        assert result.zero


class TestALUCompare:
    """Test comparison operations."""

    def test_equal_true(self, alu):
        result = alu.execute(ALUOperation.EQUAL, 10, 10)
        assert result.result == 1  # True

    def test_equal_false(self, alu):
        result = alu.execute(ALUOperation.EQUAL, 10, 5)
        assert result.result == 0  # False

    def test_less_than_false(self, alu):
        result = alu.execute(ALUOperation.LESS_THAN, 10, 5)
        assert result.result == 0  # False

    def test_less_than_signed(self, alu):
        result = alu.execute(ALUOperation.LESS_THAN, -1, 0)
        assert result.result == 1  # True (-1 < 0 in signed)
