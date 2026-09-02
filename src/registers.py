"""
Register file module.

Manages the general-purpose register file, program counter, and related
processor state used during instruction execution.
"""

from __future__ import annotations

from typing import Dict, List


# Number of general-purpose registers in a standard 32-bit RISC architecture.
NUM_REGISTERS: int = 32

# R0 is hardwired to zero and cannot hold any other value.
ZERO_REGISTER: int = 0


class InvalidRegisterError(ValueError):
    """Raised when a register index is outside the valid range [0, 31]."""

    def __init__(self, register: int) -> None:
        self.register = register
        super().__init__(
            f"Invalid register index: {register}. "
            f"Valid range is 0 to {NUM_REGISTERS - 1}."
        )


class RegisterFile:
    """
    Simulates a 32-register general-purpose register file.

    Register R0 is hardwired to zero: reads always return 0 and writes are
    silently ignored, matching common RISC conventions (e.g., RISC-V x0).
    """

    def __init__(self) -> None:
        """Initialize all registers to zero."""
        # Internal storage for R1–R31; R0 is not stored because it is always 0.
        self._registers: List[int] = [0] * NUM_REGISTERS
        self.reset()

    def _validate_register(self, register: int) -> None:
        """
        Validate that a register index is within the allowed range.

        Args:
            register: Register index to validate.

        Raises:
            InvalidRegisterError: If the index is not in [0, NUM_REGISTERS).
        """
        if not isinstance(register, int):
            raise InvalidRegisterError(register)  # type: ignore[arg-type]

        if register < 0 or register >= NUM_REGISTERS:
            raise InvalidRegisterError(register)

    def read(self, register: int) -> int:
        """
        Read the value stored in a register.

        Args:
            register: Register index (0–31).

        Returns:
            The 32-bit value held by the register. R0 always returns 0.

        Raises:
            InvalidRegisterError: If the register index is invalid.
        """
        self._validate_register(register)

        # R0 is hardwired to zero regardless of internal state.
        if register == ZERO_REGISTER:
            return 0

        return self._registers[register]

    def write(self, register: int, value: int) -> None:
        """
        Write a value into a register.

        Writes to R0 are ignored because it is hardwired to zero.

        Args:
            register: Register index (0–31).
            value: Integer value to store (simulated as a 32-bit word).

        Raises:
            InvalidRegisterError: If the register index is invalid.
        """
        self._validate_register(register)

        # Ignore writes to the zero register.
        if register == ZERO_REGISTER:
            return

        # Mask to 32 bits to mimic fixed-width register behavior.
        self._registers[register] = value & 0xFFFFFFFF

    def reset(self) -> None:
        """Reset all registers to zero."""
        self._registers = [0] * NUM_REGISTERS

    def get_all(self) -> Dict[int, int]:
        """
        Return a snapshot of all register values.

        Returns:
            A dictionary mapping register indices to their current values.
            R0 is always reported as 0.
        """
        return {index: self.read(index) for index in range(NUM_REGISTERS)}

    def display(self) -> str:
        """
        Format all register values for display.

        Returns:
            A multi-line string listing each register and its value in
            hexadecimal and decimal notation.
        """
        lines: List[str] = ["Register File:"]
        lines.append("-" * 40)

        for index in range(NUM_REGISTERS):
            value = self.read(index)
            lines.append(f"R{index:2d}: 0x{value:08X}  ({value:10d})")

        return "\n".join(lines)

    def __repr__(self) -> str:
        """Return a concise representation of non-zero registers."""
        non_zero = {
            f"R{index}": value
            for index, value in self.get_all().items()
            if value != 0
        }
        return f"RegisterFile({non_zero if non_zero else 'all zero'})"
