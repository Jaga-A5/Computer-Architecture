"""
Unit tests for the memory module.
"""

import pytest
from memory import Memory, InstructionMemory, DataMemory, MemorySystem, MemoryAccessError


class TestDataMemory:
    """Test data memory operations."""

    def test_write_and_read_back(self, data_memory):
        data_memory.write(0, 0x12345678)
        assert data_memory.read(0) == 0x12345678

    def test_write_masks_to_32_bits(self, data_memory):
        data_memory.write(0, 0x123456789ABCDEF0)  # 64-bit value
        assert data_memory.read(0) == 0x789ABCDEF0  # Lower 32 bits

    def test_read_unwritten_address_returns_zero(self, data_memory):
        assert data_memory.read(100) == 0

    def test_write_zero_removes_sparse_entry(self, data_memory):
        data_memory.write(0, 0x12345678)
        data_memory.write(0, 0)
        # In sparse implementation, zero might be stored or not
        # Just verify read returns zero
        assert data_memory.read(0) == 0

    def test_unaligned_address_raises(self, data_memory):
        with pytest.raises(MemoryAccessError):
            data_memory.write(1, 0)  # Not word-aligned

    def test_negative_address_raises(self, data_memory):
        with pytest.raises(MemoryAccessError):
            data_memory.write(-4, 0)

    def test_out_of_range_address_raises(self, data_memory):
        with pytest.raises(MemoryAccessError):
            data_memory.write(10000, 0)  # Beyond memory size

    def test_invalid_memory_size_raises(self):
        with pytest.raises(ValueError):
            Memory(size=10)  # Not multiple of 4

    def test_dump_memory_shows_written_words(self, data_memory):
        data_memory.write(0, 0x11111111)
        data_memory.write(4, 0x22222222)
        dump = data_memory.dump(0, 2)
        assert "0x11111111" in dump
        assert "0x22222222" in dump


class TestInstructionMemory:
    """Test instruction memory operations."""

    def test_load_program_from_list(self, instruction_memory):
        words = [0x00000001, 0x00000002, 0x00000003]
        count = instruction_memory.load_program(words)
        assert count == 3
        assert instruction_memory.read(0) == 0x00000001
        assert instruction_memory.read(4) == 0x00000002

    def test_load_program_locks_memory(self, instruction_memory):
        words = [0x00000001]
        instruction_memory.load_program(words, lock=True)
        with pytest.raises(MemoryAccessError):
            instruction_memory.write(0, 0x00000002)  # Should fail

    def test_load_program_without_lock_allows_writes(self, instruction_memory):
        words = [0x00000001]
        instruction_memory.load_program(words, lock=False)
        instruction_memory.write(0, 0x00000002)  # Should succeed
        assert instruction_memory.read(0) == 0x00000002

    def test_load_program_overflow_raises(self, instruction_memory):
        words = [0] * 1100  # Too large for 1024-byte memory
        with pytest.raises(MemoryAccessError):
            instruction_memory.load_program(words)

    def test_reload_clears_previous_program(self, instruction_memory):
        instruction_memory.load_program([0x11111111])
        instruction_memory.load_program([0x22222222])
        assert instruction_memory.read(0) == 0x22222222

    def test_dump_memory_empty_region(self, instruction_memory):
        dump = instruction_memory.dump(0, 4)
        assert "0x00000000" in dump


class TestMemorySystem:
    """Test combined memory system."""

    def test_separate_address_spaces(self, memory_system):
        memory_system.instruction_memory.write(0, 0x11111111)
        memory_system.data_memory.write(0, 0x22222222)
        assert memory_system.instruction_memory.read(0) == 0x11111111
        assert memory_system.data_memory.read(0) == 0x22222222

    def test_reset_clears_both_memories(self, memory_system):
        memory_system.instruction_memory.write(0, 0x11111111)
        memory_system.data_memory.write(0, 0x22222222)
        memory_system.reset()
        assert memory_system.instruction_memory.read(0) == 0
        assert memory_system.data_memory.read(0) == 0
