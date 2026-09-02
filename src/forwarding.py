"""
Data forwarding unit module.

Resolves data hazards by forwarding results from later pipeline stages
to earlier stages, eliminating stalls for most RAW hazards.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pipeline import ID_EXRegister, EX_MEMRegister, MEM_WBRegister


class ForwardSource(str, Enum):
    """Where a forwarded value comes from."""

    NONE = "none"
    ID_EX = "ID/EX"
    EX_MEM = "EX/MEM"
    MEM_WB = "MEM/WB"


@dataclass
class ForwardDecision:
    """Forwarding decisions for rs and rt operands."""

    rs_source: ForwardSource = ForwardSource.NONE
    rs_value: Optional[int] = None
    rt_source: ForwardSource = ForwardSource.NONE
    rt_value: Optional[int] = None


class ForwardingUnit:
    """
    Resolve data hazards using operand forwarding.

    For most RAW hazards, we can forward the needed value from a later
    pipeline stage back to the EX stage, avoiding stalls. Only load-use
    hazards require stalling because the data isn't available until MEM.
    """

    def resolve(
        self,
        id_ex: ID_EXRegister,
        ex_mem: EX_MEMRegister,
        mem_wb: MEM_WBRegister,
    ) -> ForwardDecision:
        decision = ForwardDecision()

        if not id_ex.valid or id_ex.is_bubble or id_ex.instruction is None:
            return decision

        # Get source registers from the instruction in ID/EX
        rs_reg = id_ex.instruction.rs
        rt_reg = id_ex.instruction.rt

        # Forward rs
        if rs_reg != 0:
            decision.rs_source, decision.rs_value = self._forward_for_register(
                rs_reg, ex_mem, mem_wb
            )

        # Forward rt
        if rt_reg != 0:
            decision.rt_source, decision.rt_value = self._forward_for_register(
                rt_reg, ex_mem, mem_wb
            )

        return decision

    def _forward_for_register(
        self,
        reg: int,
        ex_mem: EX_MEMRegister,
        mem_wb: MEM_WBRegister,
    ) -> tuple[ForwardSource, Optional[int]]:
        """
        Determine forwarding source and value for a register.

        Priority: EX/MEM (most recent) > MEM/WB (less recent) > ID/EX (current)
        """
        # Check EX/MEM first (most recent result)
        if ex_mem.valid and ex_mem.reg_write and ex_mem.write_reg == reg:
            if ex_mem.control.mem_to_reg:
                # Loaded data from memory
                return ForwardSource.EX_MEM, ex_mem.mem_to_reg_value
            else:
                # ALU result
                return ForwardSource.EX_MEM, ex_mem.alu_result

        # Check MEM/WB (less recent result)
        if mem_wb.valid and mem_wb.reg_write and mem_wb.write_reg == reg:
            if mem_wb.control.mem_to_reg:
                # Loaded data from memory
                return ForwardSource.MEM_WB, mem_wb.mem_to_reg_value
            else:
                # ALU result
                return ForwardSource.MEM_WB, mem_wb.alu_result

        # No forwarding needed, use current ID/EX value
        return ForwardSource.NONE, None
