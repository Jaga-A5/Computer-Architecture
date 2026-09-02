"""
Instruction parser module.

Reads and parses assembly instruction files from the instructions/
directory into executable instruction objects for the simulator.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import List, Optional, Union

from instruction import Funct, Instruction, Mnemonic, Opcode
from registers import NUM_REGISTERS


DEFAULT_PROGRAM_PATH = (
    Path(__file__).resolve().parents[1] / "instructions" / "program.txt"
)

# ADD R1,R2,R3  |  LW R6,0(R2)  |  BEQ R1,R2,10  |  JUMP 100  |  NOP  |  HALT
R3_PATTERN = re.compile(
    r"^(?P<mnemonic>ADD|SUB|MUL)\s+"
    r"R(?P<rd>\d+)\s*,\s*R(?P<rs>\d+)\s*,\s*R(?P<rt>\d+)\s*$",
    re.IGNORECASE,
)
LOAD_STORE_PATTERN = re.compile(
    r"^(?P<mnemonic>LW|SW)\s+"
    r"R(?P<rt>\d+)\s*,\s*(?P<offset>-?\d+)\s*\(\s*R(?P<rs>\d+)\s*\)\s*$",
    re.IGNORECASE,
)
BRANCH_PATTERN = re.compile(
    r"^(?P<mnemonic>BEQ|BNE)\s+"
    r"R(?P<rs>\d+)\s*,\s*R(?P<rt>\d+)\s*,\s*(?P<offset>-?\d+)\s*$",
    re.IGNORECASE,
)
JUMP_PATTERN = re.compile(
    r"^JUMP\s+(?P<target>\d+)\s*$",
    re.IGNORECASE,
)
NOP_PATTERN = re.compile(r"^NOP\s*$", re.IGNORECASE)
HALT_PATTERN = re.compile(r"^HALT\s*$", re.IGNORECASE)


class ParseError(SyntaxError):
    """Raised when a source line cannot be parsed or fails validation."""

    def __init__(self, message: str, line_number: int, line: str = "") -> None:
        self.line_number = line_number
        self.line = line
        detail = f"Line {line_number}: {message}"
        if line:
            detail = f"{detail} — '{line.strip()}'"
        super().__init__(detail)


class InstructionParser:
    """Parse assembly text into Instruction instances."""

    def __init__(self, path: Optional[Union[str, Path]] = None) -> None:
        self.path = Path(path) if path is not None else DEFAULT_PROGRAM_PATH

    def parse_file(self, path: Optional[Union[str, Path]] = None) -> List[Instruction]:
        """Read and parse all instructions from a program file."""
        file_path = Path(path) if path is not None else self.path
        if not file_path.is_file():
            raise FileNotFoundError(f"Program file not found: {file_path}")
        text = file_path.read_text(encoding="utf-8")
        return self.parse_text(text)

    def parse_text(self, text: str) -> List[Instruction]:
        """Parse multi-line assembly source."""
        instructions: List[Instruction] = []
        for line_number, raw_line in enumerate(text.splitlines(), start=1):
            line = self._strip_comment(raw_line).strip()
            if not line:
                continue
            instructions.append(self.parse_line(line, line_number))
        return instructions

    def parse_line(self, line: str, line_number: int = 1) -> Instruction:
        """Parse a single non-empty, comment-free instruction line."""
        line = line.strip()
        if not line:
            raise ParseError("Empty instruction line.", line_number, line)

        match = R3_PATTERN.match(line)
        if match:
            return self._parse_r_type(match, line_number, line)

        match = LOAD_STORE_PATTERN.match(line)
        if match:
            return self._parse_load_store(match, line_number, line)

        match = BRANCH_PATTERN.match(line)
        if match:
            return self._parse_branch(match, line_number, line)

        match = JUMP_PATTERN.match(line)
        if match:
            target = int(match.group("target"))
            if target < 0 or target > 0x3FFFFFF:
                raise ParseError(
                    f"JUMP target must be in [0, {0x3FFFFFF}], got {target}.",
                    line_number,
                    line,
                )
            return Instruction(
                mnemonic=Mnemonic.JUMP,
                opcode=Opcode.JUMP,
                immediate=target,
                source_line=line_number,
            )

        if NOP_PATTERN.match(line):
            return Instruction(
                mnemonic=Mnemonic.NOP,
                opcode=Opcode.NOP,
                source_line=line_number,
            )

        if HALT_PATTERN.match(line):
            return Instruction(
                mnemonic=Mnemonic.HALT,
                opcode=Opcode.HALT,
                source_line=line_number,
            )

        raise ParseError(
            "Unrecognized instruction syntax. Expected ADD, SUB, MUL, LW, SW, "
            "BEQ, BNE, JUMP, NOP, or HALT.",
            line_number,
            line,
        )

    @staticmethod
    def _strip_comment(line: str) -> str:
        if "#" in line:
            return line.split("#", 1)[0]
        if "//" in line:
            return line.split("//", 1)[0]
        return line

    def _parse_r_type(self, match: re.Match[str], line_number: int, line: str) -> Instruction:
        mnemonic_str = match.group("mnemonic").upper()
        rd = self._parse_register(match.group("rd"), "rd", line_number, line)
        rs = self._parse_register(match.group("rs"), "rs", line_number, line)
        rt = self._parse_register(match.group("rt"), "rt", line_number, line)
        funct_map = {
            Mnemonic.ADD: Funct.ADD,
            Mnemonic.SUB: Funct.SUB,
            Mnemonic.MUL: Funct.MUL,
        }
        mnemonic = Mnemonic(mnemonic_str)
        return Instruction(
            mnemonic=mnemonic,
            opcode=Opcode.R_TYPE,
            rs=rs,
            rt=rt,
            rd=rd,
            funct=funct_map[mnemonic],
            source_line=line_number,
        )

    def _parse_load_store(
        self, match: re.Match[str], line_number: int, line: str
    ) -> Instruction:
        mnemonic_str = match.group("mnemonic").upper()
        rs = self._parse_register(match.group("rs"), "rs", line_number, line)
        rt = self._parse_register(match.group("rt"), "rt", line_number, line)
        offset = self._parse_immediate(match.group("offset"), line_number, line)
        opcode = Opcode.LW if mnemonic_str == "LW" else Opcode.SW
        return Instruction(
            mnemonic=Mnemonic(mnemonic_str),
            opcode=opcode,
            rs=rs,
            rt=rt,
            immediate=offset,
            source_line=line_number,
        )

    def _parse_branch(self, match: re.Match[str], line_number: int, line: str) -> Instruction:
        mnemonic_str = match.group("mnemonic").upper()
        rs = self._parse_register(match.group("rs"), "rs", line_number, line)
        rt = self._parse_register(match.group("rt"), "rt", line_number, line)
        offset = self._parse_immediate(match.group("offset"), line_number, line)
        opcode = Opcode.BEQ if mnemonic_str == "BEQ" else Opcode.BNE
        return Instruction(
            mnemonic=Mnemonic(mnemonic_str),
            opcode=opcode,
            rs=rs,
            rt=rt,
            immediate=offset,
            source_line=line_number,
        )

    def _parse_register(self, token: str, field: str, line_number: int, line: str) -> int:
        try:
            index = int(token)
        except ValueError as exc:
            raise ParseError(
                f"Register {field} must be an integer, got '{token}'.",
                line_number,
                line,
            ) from exc
        if index < 0 or index >= NUM_REGISTERS:
            raise ParseError(
                f"Register index must be in [0, {NUM_REGISTERS - 1}], got R{index}.",
                line_number,
                line,
            )
        return index

    def _parse_immediate(self, token: str, line_number: int, line: str) -> int:
        try:
            value = int(token, 0)
        except ValueError as exc:
            raise ParseError(
                f"Immediate must be an integer, got '{token}'.",
                line_number,
                line,
            ) from exc
        if value < -0x8000 or value > 0x7FFF:
            raise ParseError(
                f"16-bit immediate out of range [-32768, 32767], got {value}.",
                line_number,
                line,
            )
        return value


def parse_program(source: Union[str, Path]) -> List[Instruction]:
    """Convenience entry point: parse a file path or inline program text."""
    parser = InstructionParser()
    path = Path(source)
    if path.is_file():
        return parser.parse_file(path)
    return parser.parse_text(str(source))
