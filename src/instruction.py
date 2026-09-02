"""
Instruction representation module.

Simple 32-bit RISC instruction set for the pipeline simulator.

Instruction formats (32-bit word)
---------------------------------

R-type (register-register arithmetic):
    | opcode (6) | rs (5) | rt (5) | rd (5) | shamt (5) | funct (6) |

I-type (loads, stores, branches):
    | opcode (6) | rs (5) | rt (5) | immediate (16, signed) |

J-type (unconditional jump):
    | opcode (6) | target (26) |

Opcode map
----------
    0x00  R-type (funct selects operation)
    0x23  LW
    0x2B  SW
    0x04  BEQ
    0x05  BNE
    0x02  JUMP
    0x3F  NOP
    0x3E  HALT

R-type funct codes
------------------
    0x20  ADD
    0x22  SUB
    0x18  MUL

Execution (conceptual)
----------------------
    ADD/SUB/MUL : rd <- f(rs, rt); writes register file in WB.
    LW          : rt <- Mem[rs + sign_ext(imm)]; address in EX, load in MEM.
    SW          : Mem[rs + sign_ext(imm)] <- rt; no register write.
    BEQ/BNE     : if (rs == rt) or (rs != rt), PC <- PC + 4 + (imm << 2).
    JUMP        : PC <- (PC & 0xF0000000) | (target << 2)  (word index in target).
    NOP         : no operation; advances PC by 4.
    HALT        : stops the processor.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, IntEnum
from typing import Optional


WORD_MASK = 0xFFFFFFFF


class Opcode(IntEnum):
    """Primary 6-bit opcode field."""

    R_TYPE = 0x00
    JUMP = 0x02
    BEQ = 0x04
    BNE = 0x05
    LW = 0x23
    SW = 0x2B
    HALT = 0x3E
    NOP = 0x3F


class Funct(IntEnum):
    """R-type 6-bit function field."""

    ADD = 0x20
    SUB = 0x22
    MUL = 0x18


class Mnemonic(str, Enum):
    """Assembly mnemonics supported by the parser."""

    ADD = "ADD"
    SUB = "SUB"
    MUL = "MUL"
    LW = "LW"
    SW = "SW"
    BEQ = "BEQ"
    BNE = "BNE"
    JUMP = "JUMP"
    NOP = "NOP"
    HALT = "HALT"


@dataclass(frozen=True)
class Instruction:
    """Decoded instruction ready for pipeline stages."""

    mnemonic: Mnemonic
    opcode: Opcode
    rs: int = 0
    rt: int = 0
    rd: int = 0
    immediate: int = 0
    funct: Optional[Funct] = None
    source_line: int = 0

    def encode(self) -> int:
        """Pack this instruction into a 32-bit machine word."""
        if self.opcode == Opcode.R_TYPE:
            if self.funct is None:
                raise ValueError("R-type instruction requires funct.")
            word = (
                (Opcode.R_TYPE << 26)
                | ((self.rs & 0x1F) << 21)
                | ((self.rt & 0x1F) << 16)
                | ((self.rd & 0x1F) << 11)
                | ((0 & 0x1F) << 6)  # shamt field (5 bits, set to 0)
                | (self.funct & 0x3F)
            )
        elif self.opcode in (Opcode.LW, Opcode.SW, Opcode.BEQ, Opcode.BNE):
            imm = self.immediate & 0xFFFF
            word = (
                (int(self.opcode) << 26)
                | ((self.rs & 0x1F) << 21)
                | ((self.rt & 0x1F) << 16)
                | imm
            )
        elif self.opcode == Opcode.JUMP:
            target = self.immediate & 0x3FFFFFF
            word = (int(self.opcode) << 26) | target
        elif self.opcode in (Opcode.NOP, Opcode.HALT):
            word = int(self.opcode) << 26
        else:
            raise ValueError(f"Cannot encode unknown opcode {self.opcode!r}.")
        return word & WORD_MASK

    @staticmethod
    def decode(word: int) -> Instruction:
        """Decode a 32-bit machine word into an Instruction."""
        word &= WORD_MASK
        opcode_val = (word >> 26) & 0x3F
        rs = (word >> 21) & 0x1F
        rt = (word >> 16) & 0x1F
        rd = (word >> 11) & 0x1F
        shamt = (word >> 6) & 0x1F
        funct = word & 0x3F
        imm16 = word & 0xFFFF
        if imm16 & 0x8000:
            immediate = imm16 - 0x10000
        else:
            immediate = imm16

        try:
            opcode = Opcode(opcode_val)
        except ValueError:
            raise ValueError(f"Unknown opcode 0x{opcode_val:02X} in word 0x{word:08X}.")

        if opcode == Opcode.R_TYPE:
            try:
                funct_enum = Funct(funct)
            except ValueError:
                raise ValueError(f"Unknown R-type funct 0x{funct:02X}.")
            mnemonic_map = {
                Funct.ADD: Mnemonic.ADD,
                Funct.SUB: Mnemonic.SUB,
                Funct.MUL: Mnemonic.MUL,
            }
            return Instruction(
                mnemonic=mnemonic_map[funct_enum],
                opcode=opcode,
                rs=rs,
                rt=rt,
                rd=rd,
                funct=funct_enum,
            )
        if opcode == Opcode.LW:
            return Instruction(
                mnemonic=Mnemonic.LW, opcode=opcode, rs=rs, rt=rt, immediate=immediate
            )
        if opcode == Opcode.SW:
            return Instruction(
                mnemonic=Mnemonic.SW, opcode=opcode, rs=rs, rt=rt, immediate=immediate
            )
        if opcode == Opcode.BEQ:
            return Instruction(
                mnemonic=Mnemonic.BEQ, opcode=opcode, rs=rs, rt=rt, immediate=immediate
            )
        if opcode == Opcode.BNE:
            return Instruction(
                mnemonic=Mnemonic.BNE, opcode=opcode, rs=rs, rt=rt, immediate=immediate
            )
        if opcode == Opcode.JUMP:
            target = word & 0x3FFFFFF
            return Instruction(
                mnemonic=Mnemonic.JUMP, opcode=opcode, immediate=target
            )
        if opcode == Opcode.NOP:
            return Instruction(mnemonic=Mnemonic.NOP, opcode=opcode)
        if opcode == Opcode.HALT:
            return Instruction(mnemonic=Mnemonic.HALT, opcode=opcode)
        raise ValueError(f"Unhandled opcode {opcode!r}.")


def sign_extend_16(value: int) -> int:
    """Sign-extend a 16-bit immediate to 32 bits."""
    value &= 0xFFFF
    if value & 0x8000:
        return value - 0x10000
    return value
