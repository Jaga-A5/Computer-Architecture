"""
Unit tests for the parser module.
"""

import pytest
from parser import InstructionParser, ParseError
from instruction import Instruction, Mnemonic, Opcode, Funct


class TestInstructionParserLines:
    """Test parsing individual instruction lines."""

    def test_add_r_type(self, instruction_parser):
        instr = instruction_parser.parse_line("ADD R1,R2,R3", 1)
        assert instr.mnemonic == Mnemonic.ADD
        assert instr.opcode == Opcode.R_TYPE
        assert instr.rd == 1
        assert instr.rs == 2
        assert instr.rt == 3
        assert instr.funct == Funct.ADD

    def test_sub_and_mul(self, instruction_parser):
        sub = instruction_parser.parse_line("SUB R5,R6,R7", 1)
        assert sub.mnemonic == Mnemonic.SUB
        assert sub.funct == Funct.SUB

        mul = instruction_parser.parse_line("MUL R8,R9,R10", 1)
        assert mul.mnemonic == Mnemonic.MUL
        assert mul.funct == Funct.MUL

    def test_load_store(self, instruction_parser):
        lw = instruction_parser.parse_line("LW R4,0(R2)", 1)
        assert lw.mnemonic == Mnemonic.LW
        assert lw.opcode == Opcode.LW
        assert lw.rt == 4
        assert lw.rs == 2
        assert lw.immediate == 0

        sw = instruction_parser.parse_line("SW R5,4(R3)", 1)
        assert sw.mnemonic == Mnemonic.SW
        assert sw.opcode == Opcode.SW
        assert sw.rt == 5
        assert sw.rs == 3
        assert sw.immediate == 4

    def test_branch(self, instruction_parser):
        beq = instruction_parser.parse_line("BEQ R1,R2,10", 1)
        assert beq.mnemonic == Mnemonic.BEQ
        assert beq.opcode == Opcode.BEQ
        assert beq.immediate == 10

        bne = instruction_parser.parse_line("BNE R3,R4,-5", 1)
        assert bne.mnemonic == Mnemonic.BNE
        assert bne.opcode == Opcode.BNE
        assert bne.immediate == -5

    def test_jump_nop_halt(self, instruction_parser):
        jump = instruction_parser.parse_line("JUMP 100", 1)
        assert jump.mnemonic == Mnemonic.JUMP
        assert jump.opcode == Opcode.JUMP
        assert jump.immediate == 100

        nop = instruction_parser.parse_line("NOP", 1)
        assert nop.mnemonic == Mnemonic.NOP
        assert nop.opcode == Opcode.NOP

        halt = instruction_parser.parse_line("HALT", 1)
        assert halt.mnemonic == Mnemonic.HALT
        assert halt.opcode == Opcode.HALT

    def test_whitespace_and_case_insensitive(self, instruction_parser):
        instr = instruction_parser.parse_line("  add  r1 ,  r2 ,  r3  ", 1)
        assert instr.mnemonic == Mnemonic.ADD
        assert instr.rd == 1

    def test_comments_stripped_in_text(self, instruction_parser):
        instructions = instruction_parser.parse_text("ADD R1,R2,R3 # This is a comment")
        assert len(instructions) == 1
        assert instructions[0].mnemonic == Mnemonic.ADD

    def test_invalid_register(self, instruction_parser):
        with pytest.raises(ParseError):
            instruction_parser.parse_line("ADD R33,R2,R3", 1)

    def test_invalid_syntax(self, instruction_parser):
        with pytest.raises(ParseError):
            instruction_parser.parse_line("INVALID INSTRUCTION", 1)

    def test_immediate_out_of_range(self, instruction_parser):
        with pytest.raises(ParseError):
            instruction_parser.parse_line("LW R1,100000(R2)", 1)


class TestInstructionParserFile:
    """Test parsing instruction files."""

    def test_parse_program_file(self, instruction_parser, tmp_path):
        program_file = tmp_path / "test.asm"
        program_file.write_text("ADD R1,R2,R3\nSUB R4,R5,R6\nHALT")
        instructions = instruction_parser.parse_file(program_file)
        assert len(instructions) == 3
        assert instructions[0].mnemonic == Mnemonic.ADD
        assert instructions[2].mnemonic == Mnemonic.HALT

    def test_missing_file(self, instruction_parser):
        with pytest.raises(FileNotFoundError):
            instruction_parser.parse_file("nonexistent.asm")

    def test_program_file_exists(self, instruction_parser):
        # Test with the default program path if it exists
        try:
            instructions = instruction_parser.parse_file()
            assert isinstance(instructions, list)
        except FileNotFoundError:
            pass  # Default file doesn't exist, which is fine


class TestInstructionEncodeDecode:
    """Test instruction encoding and decoding round-trip."""

    def test_r_type_round_trip(self):
        original = Instruction(
            mnemonic=Mnemonic.ADD,
            opcode=Opcode.R_TYPE,
            rs=1,
            rt=2,
            rd=3,
            funct=Funct.ADD
        )
        encoded = original.encode()
        decoded = Instruction.decode(encoded)
        assert decoded.mnemonic == original.mnemonic
        assert decoded.rs == original.rs
        assert decoded.rt == original.rt
        assert decoded.rd == original.rd
        assert decoded.funct == original.funct
