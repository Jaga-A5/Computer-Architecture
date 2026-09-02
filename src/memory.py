"""
Memory system simulation module.

Implements separate instruction and data memories with configurable sizes,
word-aligned addressing, and program loading capabilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

WORD_SIZE = 4  # 32-bit word size in bytes


class MemoryAccessError(Exception):
    """Raised for invalid memory access (out of range, unaligned, etc.)."""

    def __init__(self, address: int, reason: str) -> None:
        self.address = address
        self.reason = reason
        super().__init__(f"Memory access error at 0x{address:08X}: {reason}")


class Memory:
    """
    Word-addressable memory with sparse storage.

    Words are stored on 4-byte boundaries. Unwritten addresses return 0.
    """

    def __init__(self, size: int = 4096, name: str = "Memory") -> None:
        """
        Initialize memory.

        Args:
            size: Total memory size in bytes (must be multiple of WORD_SIZE).
            name: Descriptive name for this memory instance.
        """
        if size % WORD_SIZE != 0:
            raise ValueError(f"Memory size must be multiple of {WORD_SIZE}.")
        self.size = size
        self.name = name
        self._data: Dict[int, int] = {}
        self._locked: bool = False

    def read(self, address: int) -> int:
        """
        Read a 32-bit word from memory.

        Args:
            address: Byte address (must be word-aligned).

        Returns:
            32-bit word at address, or 0 if never written.

        Raises:
            MemoryAccessError: If address is out of range or unaligned.
        """
        self._validate_access(address)
        return self._data.get(address, 0)

    def write(self, address: int, value: int) -> None:
        """
        Write a 32-bit word to memory.

        Args:
            address: Byte address (must be word-aligned).
            value: 32-bit value to store (masked to 32 bits).

        Raises:
            MemoryAccessError: If address is out of range, unaligned, or memory is locked.
        """
        self._validate_access(address)
        if self._locked:
            raise MemoryAccessError(address, "Memory is locked (read-only).")
        self._data[address] = value & 0xFFFFFFFF

    def _validate_access(self, address: int) -> None:
        """Validate memory access address."""
        if address < 0:
            raise MemoryAccessError(address, "Negative address.")
        if address >= self.size:
            raise MemoryAccessError(address, f"Address out of range (size={self.size}).")
        if address % WORD_SIZE != 0:
            raise MemoryAccessError(address, "Unaligned address (must be multiple of 4).")

    def reset(self) -> None:
        """Clear all memory contents and unlock."""
        self._data.clear()
        self._locked = False

    def lock(self) -> None:
        """Make memory read-only (for instruction memory after program load)."""
        self._locked = True

    def unlock(self) -> None:
        """Make memory writable again."""
        self._locked = False

    def dump(self, start_address: int = 0, num_words: int = 16) -> str:
        """
        Format memory contents for display.

        Args:
            start_address: Starting byte address.
            num_words: Number of words to display.

        Returns:
            Formatted string showing address and data.
        """
        lines = [f"{self.name} dump:"]
        for i in range(num_words):
            addr = start_address + i * WORD_SIZE
            if addr >= self.size:
                break
            value = self.read(addr)
            lines.append(f"  0x{addr:08X}: 0x{value:08X}")
        return "\n".join(lines)


class InstructionMemory(Memory):
    """Instruction memory with program loading capabilities."""

    def __init__(self, size: int = 4096) -> None:
        super().__init__(size, "Instruction Memory")

    def load_program(self, words: list[int], lock: bool = True) -> int:
        """
        Load a program into instruction memory.

        Args:
            words: List of 32-bit instruction words.
            lock: If True, make memory read-only after loading.

        Returns:
            Number of words loaded.

        Raises:
            MemoryAccessError: If program doesn't fit in memory.
        """
        required_size = len(words) * WORD_SIZE
        if required_size > self.size:
            raise MemoryAccessError(
                0, f"Program too large: needs {required_size} bytes, have {self.size}."
            )

        self.reset()
        for i, word in enumerate(words):
            self.write(i * WORD_SIZE, word)

        if lock:
            self.lock()

        return len(words)

    def load_program_from_file(self, path: str, lock: bool = True) -> int:
        """
        Load program from a binary file containing 32-bit words.

        Args:
            path: Path to binary file.
            lock: If True, make memory read-only after loading.

        Returns:
            Number of words loaded.
        """
        with open(path, "rb") as f:
            data = f.read()
        
        words = []
        for i in range(0, len(data), WORD_SIZE):
            word_bytes = data[i:i+WORD_SIZE]
            if len(word_bytes) < WORD_SIZE:
                break
            word = int.from_bytes(word_bytes, byteorder='big', signed=False)
            words.append(word)
        
        return self.load_program(words, lock)


class DataMemory(Memory):
    """Data memory with standard memory operations."""

    def __init__(self, size: int = 4096) -> None:
        super().__init__(size, "Data Memory")


class MemorySystem:
    """
    Combined instruction and data memory system.

    Implements Harvard architecture with separate address spaces for
    instructions and data.
    """

    def __init__(
        self,
        instruction_size: int = 4096,
        data_size: int = 4096,
    ) -> None:
        """
        Initialize memory system.

        Args:
            instruction_size: Size of instruction memory in bytes.
            data_size: Size of data memory in bytes.
        """
        self.instruction_memory = InstructionMemory(instruction_size)
        self.data_memory = DataMemory(data_size)

    def reset(self) -> None:
        """Reset both instruction and data memory."""
        self.instruction_memory.reset()
        self.data_memory.reset()
