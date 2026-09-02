"""
ALU (Arithmetic Logic Unit) simulation module.

Implements the arithmetic and logical operations that the processor's ALU can perform,
including addition, subtraction, multiplication, bitwise operations, shifts, and comparisons.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ALUOperation(str, Enum):
    """Operations supported by the ALU."""

    ADD = "add"
    SUB = "sub"
    MUL = "mul"
    AND = "and"
    OR = "or"
    XOR = "xor"
    NOT = "not"
    SLL = "sll"  # Shift Left Logical
    SRL = "srl"  # Shift Right Logical
    SRA = "sra"  # Shift Right Arithmetic
    EQUAL = "equal"
    LESS_THAN = "less_than"


@dataclass
class ALUResult:
    """Result of an ALU operation including flags."""

    result: int
    zero: bool
    negative: bool
    carry: bool
    overflow: bool


class ALU:
    """
    Simulates a 32-bit Arithmetic Logic Unit.

    Performs arithmetic, logical, and comparison operations on 32-bit operands
    and produces a 32-bit result along with condition codes (flags).
    """

    WORD_MASK = 0xFFFFFFFF
    SIGN_BIT = 0x80000000

    def execute(self, operation: ALUOperation, operand1: int, operand2: int = 0) -> ALUResult:
        """
        Execute an ALU operation.

        Args:
            operation: The operation to perform.
            operand1: First operand (or only operand for unary operations).
            operand2: Second operand (ignored for unary operations).

        Returns:
            ALUResult containing the result and condition flags.
        """
        op1 = operand1 & self.WORD_MASK
        op2 = operand2 & self.WORD_MASK

        if operation == ALUOperation.ADD:
            return self._add(op1, op2)
        elif operation == ALUOperation.SUB:
            return self._sub(op1, op2)
        elif operation == ALUOperation.MUL:
            return self._mul(op1, op2)
        elif operation == ALUOperation.AND:
            return self._and(op1, op2)
        elif operation == ALUOperation.OR:
            return self._or(op1, op2)
        elif operation == ALUOperation.XOR:
            return self._xor(op1, op2)
        elif operation == ALUOperation.NOT:
            return self._not(op1)
        elif operation == ALUOperation.SLL:
            return self._sll(op1, op2)
        elif operation == ALUOperation.SRL:
            return self._srl(op1, op2)
        elif operation == ALUOperation.SRA:
            return self._sra(op1, op2)
        elif operation == ALUOperation.EQUAL:
            return self._equal(op1, op2)
        elif operation == ALUOperation.LESS_THAN:
            return self._less_than(op1, op2)
        else:
            raise ValueError(f"Unknown ALU operation: {operation}")

    def _add(self, a: int, b: int) -> ALUResult:
        """Addition with overflow detection."""
        result = (a + b) & self.WORD_MASK
        
        # Detect unsigned overflow (carry)
        carry = (a + b) > self.WORD_MASK
        
        # Detect signed overflow
        sign_a = bool(a & self.SIGN_BIT)
        sign_b = bool(b & self.SIGN_BIT)
        sign_result = bool(result & self.SIGN_BIT)
        overflow = (sign_a == sign_b) and (sign_result != sign_a)
        
        return ALUResult(
            result=result,
            zero=(result == 0),
            negative=bool(result & self.SIGN_BIT),
            carry=carry,
            overflow=overflow,
        )

    def _sub(self, a: int, b: int) -> ALUResult:
        """Subtraction with borrow/overflow detection."""
        result = (a - b) & self.WORD_MASK
        
        # Detect unsigned borrow (carry flag is set if we borrowed)
        carry = a < b
        
        # Detect signed overflow
        sign_a = bool(a & self.SIGN_BIT)
        sign_b = bool(b & self.SIGN_BIT)
        sign_result = bool(result & self.SIGN_BIT)
        overflow = (sign_a != sign_b) and (sign_result != sign_a)
        
        return ALUResult(
            result=result,
            zero=(result == 0),
            negative=bool(result & self.SIGN_BIT),
            carry=carry,
            overflow=overflow,
        )

    def _mul(self, a: int, b: int) -> ALUResult:
        """Multiplication with overflow detection."""
        result = (a * b) & self.WORD_MASK
        
        # Detect overflow (if full product doesn't fit in 32 bits)
        full_product = a * b
        overflow = (full_product & ~self.WORD_MASK) != 0
        
        return ALUResult(
            result=result,
            zero=(result == 0),
            negative=bool(result & self.SIGN_BIT),
            carry=False,  # Carry not defined for multiplication
            overflow=overflow,
        )

    def _and(self, a: int, b: int) -> ALUResult:
        """Bitwise AND."""
        result = a & b
        return ALUResult(
            result=result,
            zero=(result == 0),
            negative=bool(result & self.SIGN_BIT),
            carry=False,
            overflow=False,
        )

    def _or(self, a: int, b: int) -> ALUResult:
        """Bitwise OR."""
        result = a | b
        return ALUResult(
            result=result,
            zero=(result == 0),
            negative=bool(result & self.SIGN_BIT),
            carry=False,
            overflow=False,
        )

    def _xor(self, a: int, b: int) -> ALUResult:
        """Bitwise XOR."""
        result = a ^ b
        return ALUResult(
            result=result,
            zero=(result == 0),
            negative=bool(result & self.SIGN_BIT),
            carry=False,
            overflow=False,
        )

    def _not(self, a: int) -> ALUResult:
        """Bitwise NOT (unary)."""
        result = (~a) & self.WORD_MASK
        return ALUResult(
            result=result,
            zero=(result == 0),
            negative=bool(result & self.SIGN_BIT),
            carry=False,
            overflow=False,
        )

    def _sll(self, a: int, b: int) -> ALUResult:
        """Shift Left Logical."""
        shift_amount = b & 0x1F  # Only use lower 5 bits
        result = ((a << shift_amount) & self.WORD_MASK)
        return ALUResult(
            result=result,
            zero=(result == 0),
            negative=bool(result & self.SIGN_BIT),
            carry=False,
            overflow=False,
        )

    def _srl(self, a: int, b: int) -> ALUResult:
        """Shift Right Logical."""
        shift_amount = b & 0x1F  # Only use lower 5 bits
        result = (a >> shift_amount) & self.WORD_MASK
        return ALUResult(
            result=result,
            zero=(result == 0),
            negative=bool(result & self.SIGN_BIT),
            carry=False,
            overflow=False,
        )

    def _sra(self, a: int, b: int) -> ALUResult:
        """Shift Right Arithmetic (sign-extended)."""
        shift_amount = b & 0x1F  # Only use lower 5 bits
        if a & self.SIGN_BIT:
            # Sign bit is set, so we need to sign-extend
            result = (a >> shift_amount) | (~self.WORD_MASK << (32 - shift_amount))
        else:
            result = a >> shift_amount
        result = result & self.WORD_MASK
        return ALUResult(
            result=result,
            zero=(result == 0),
            negative=bool(result & self.SIGN_BIT),
            carry=False,
            overflow=False,
        )

    def _equal(self, a: int, b: int) -> ALUResult:
        """Comparison: equal."""
        result = 1 if a == b else 0
        return ALUResult(
            result=result,
            zero=(result == 0),
            negative=False,
            carry=False,
            overflow=False,
        )

    def _less_than(self, a: int, b: int) -> ALUResult:
        """Comparison: signed less than."""
        # Convert to signed for comparison
        a_signed = a if a < 0x80000000 else a - 0x100000000
        b_signed = b if b < 0x80000000 else b - 0x100000000
        result = 1 if a_signed < b_signed else 0
        return ALUResult(
            result=result,
            zero=(result == 0),
            negative=False,
            carry=False,
            overflow=False,
        )
