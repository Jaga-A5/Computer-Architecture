"""
Unit tests for the registers module.
"""

import pytest
from registers import RegisterFile, InvalidRegisterError, NUM_REGISTERS, ZERO_REGISTER


class TestRegisterFileInit:
    """Test register file initialization."""

    def test_init_all_registers_zero(self, register_file):
        for i in range(NUM_REGISTERS):
            assert register_file.read(i) == 0

    def test_reset_clears_registers(self, register_file):
        register_file.write(1, 100)
        register_file.write(2, 200)
        register_file.reset()
        assert register_file.read(1) == 0
        assert register_file.read(2) == 0


class TestRegisterFileRead:
    """Test register read operations."""

    def test_read_written_value(self, register_file):
        register_file.write(5, 12345)
        assert register_file.read(5) == 12345

    def test_r0_always_reads_zero(self, register_file):
        register_file.write(ZERO_REGISTER, 100)
        assert register_file.read(ZERO_REGISTER) == 0

    def test_read_invalid_register_negative(self, register_file):
        with pytest.raises(InvalidRegisterError):
            register_file.read(-1)

    def test_read_invalid_register_too_large(self, register_file):
        with pytest.raises(InvalidRegisterError):
            register_file.read(NUM_REGISTERS)


class TestRegisterFileWrite:
    """Test register write operations."""

    def test_write_and_read_back(self, register_file):
        register_file.write(10, 0xABCDEF01)
        assert register_file.read(10) == 0xABCDEF01

    def test_write_masks_to_32_bits(self, register_file):
        register_file.write(1, 0x123456789ABCDEF0)  # 64-bit value
        assert register_file.read(1) == 0x9ABCDEF0  # Lower 32 bits

    def test_write_to_r0_is_ignored(self, register_file):
        register_file.write(ZERO_REGISTER, 100)
        assert register_file.read(ZERO_REGISTER) == 0

    def test_write_invalid_register(self, register_file):
        with pytest.raises(InvalidRegisterError):
            register_file.write(NUM_REGISTERS, 0)


class TestRegisterFileDisplay:
    """Test register file display and output methods."""

    def test_get_all_returns_all_registers(self, register_file):
        register_file.write(1, 100)
        register_file.write(5, 200)
        all_regs = register_file.get_all()
        assert all_regs[1] == 100
        assert all_regs[5] == 200
        assert len(all_regs) == NUM_REGISTERS

    def test_display_contains_register_labels(self, register_file):
        display = register_file.display()
        assert "Register File:" in display
        assert "R0:" in display
        assert "R31:" in display

    def test_repr_all_zero(self, register_file):
        repr_str = repr(register_file)
        assert "all zero" in repr_str

    def test_repr_shows_non_zero_registers(self, register_file):
        register_file.write(1, 100)
        register_file.write(5, 200)
        repr_str = repr(register_file)
        assert "R1" in repr_str
        assert "R5" in repr_str
