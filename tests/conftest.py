"""
Pytest configuration and shared fixtures for the RISC Pipeline Simulator tests.
"""

import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from alu import ALU
from registers import RegisterFile
from memory import MemorySystem, Memory, InstructionMemory, DataMemory
from instruction import Instruction
from parser import InstructionParser


@pytest.fixture
def alu():
    """Fixture providing a fresh ALU instance."""
    return ALU()


@pytest.fixture
def register_file():
    """Fixture providing a fresh RegisterFile instance."""
    return RegisterFile()


@pytest.fixture
def instruction_memory():
    """Fixture providing a fresh InstructionMemory instance."""
    return InstructionMemory(size=1024)


@pytest.fixture
def data_memory():
    """Fixture providing a fresh DataMemory instance."""
    return DataMemory(size=1024)


@pytest.fixture
def memory_system():
    """Fixture providing a fresh MemorySystem instance."""
    return MemorySystem(instruction_size=1024, data_size=1024)


@pytest.fixture
def instruction_parser():
    """Fixture providing a fresh InstructionParser instance."""
    return InstructionParser()


@pytest.fixture
def sample_instruction():
    """Fixture providing a sample ADD instruction."""
    return Instruction(
        mnemonic="ADD",
        opcode=0,
        rs=1,
        rt=2,
        rd=3,
        funct=0x20
    )
