"""
Hazard detection module.

Detects data hazards, control hazards, and structural hazards that can stall
or flush pipeline stages to preserve correct program execution.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, TYPE_CHECKING

from instruction import Opcode

if TYPE_CHECKING:
    from pipeline import ID_EXRegister, EX_MEMRegister, MEM_WBRegister, IF_IDRegister


class HazardType(str, Enum):
    RAW = "RAW"
    WAR = "WAR"
    WAW = "WAW"
    LOAD_USE = "LOAD_USE"
    BRANCH = "BRANCH"
    STRUCTURAL = "STRUCTURAL"


class HazardAction(str, Enum):
    NONE = "none"
    STALL = "stall"
    INSERT_NOP = "insert_nop"
    FLUSH = "flush"


@dataclass(frozen=True)
class HazardReport:
    hazard_type: HazardType
    reason: str
    action: HazardAction
    registers: tuple[int, ...] = ()


@dataclass
class HazardControl:
    stall_if: bool = False
    stall_id: bool = False
    flush_if_id: bool = False
    flush_id_ex: bool = False
    insert_bubble_id_ex: bool = False
    reports: List[HazardReport] = field(default_factory=list)


class HazardDetectionUnit:
    """
    Detect pipeline hazards and recommend stall / bubble / flush actions.

    Classic 5-stage in-order pipelines eliminate WAR/WAW between integer
    registers by reading in ID and writing in WB; we still report WAW when two
    in-flight writers target the same register for teaching purposes.
    """

    def evaluate(
        self,
        if_id: IF_IDRegister,
        id_ex: ID_EXRegister,
        ex_mem: EX_MEMRegister,
        mem_wb: MEM_WBRegister,
    ) -> HazardControl:
        control = HazardControl()

        if id_ex.valid and not id_ex.is_bubble:
            load_use = self._load_use_hazard(id_ex, if_id)
            if load_use:
                control.stall_if = True
                control.stall_id = True
                control.insert_bubble_id_ex = True
                control.reports.append(load_use)

        if not id_ex.is_bubble and id_ex.valid:
            raw_reports = self._raw_hazards(if_id, id_ex, ex_mem, mem_wb)
            for report in raw_reports:
                if report.action == HazardAction.STALL and not control.stall_id:
                    control.stall_if = True
                    control.stall_id = True
                    control.insert_bubble_id_ex = True
                control.reports.append(report)

        waw = self._waw_hazard(ex_mem, mem_wb)
        if waw:
            control.reports.append(waw)

        war = self._war_hazard(id_ex, ex_mem, mem_wb)
        if war:
            control.reports.append(war)

        # Structural Hazard Check: Simultaneous Memory access in IF and MEM stages
        if if_id.valid and not if_id.is_bubble and ex_mem.valid and not ex_mem.is_bubble:
            if ex_mem.control.mem_read or ex_mem.control.mem_write:
                mem_op = "LW" if ex_mem.control.mem_read else "SW"
                control.reports.append(
                    HazardReport(
                        hazard_type=HazardType.STRUCTURAL,
                        reason=(
                            f"Structural: IF stage fetching instruction at 0x{if_id.pc:04X} while MEM stage "
                            f"executes {mem_op}. Resolved by split I-Cache / D-Cache."
                        ),
                        action=HazardAction.NONE,
                    )
                )

        if ex_mem.valid and ex_mem.jump_taken:
            control.reports.append(
                HazardReport(
                    hazard_type=HazardType.BRANCH,
                    reason="Unconditional JUMP (handled in pipeline flush).",
                    action=HazardAction.FLUSH,
                )
            )

        return control

    def _load_use_hazard(
        self, id_ex: ID_EXRegister, if_id: IF_IDRegister
    ) -> Optional[HazardReport]:
        if not if_id.valid or if_id.is_bubble or if_id.instruction is None:
            return None
        if id_ex.instruction is None or id_ex.instruction.opcode != Opcode.LW:
            return None
        load_reg = id_ex.instruction.rt
        consumer = if_id.instruction
        if consumer is None:
            return None
        uses = self._source_registers(consumer)
        if load_reg in uses and load_reg != 0:
            return HazardReport(
                hazard_type=HazardType.LOAD_USE,
                reason=(
                    f"Load-use: LW targets R{load_reg} but next instruction "
                    f"({consumer.mnemonic.value}) needs that value in ID."
                ),
                action=HazardAction.STALL,
                registers=(load_reg,),
            )
        return None

    def _raw_hazards(
        self,
        if_id: IF_IDRegister,
        id_ex: ID_EXRegister,
        ex_mem: EX_MEMRegister,
        mem_wb: MEM_WBRegister,
    ) -> List[HazardReport]:
        if not if_id.valid or if_id.is_bubble or if_id.instruction is None:
            return []
        instr = if_id.instruction
        reports: List[HazardReport] = []
        for reg in self._source_registers(instr):
            if reg == 0:
                continue
            if ex_mem.valid and ex_mem.reg_write and ex_mem.write_reg == reg:
                if ex_mem.instruction and ex_mem.instruction.opcode == Opcode.LW:
                    reports.append(
                        HazardReport(
                            hazard_type=HazardType.RAW,
                            reason=(
                                f"RAW/load-use path: R{reg} from LW in MEM; "
                                "stall or wait for MEM/WB."
                            ),
                            action=HazardAction.STALL,
                            registers=(reg,),
                        )
                    )
                else:
                    reports.append(
                        HazardReport(
                            hazard_type=HazardType.RAW,
                            reason=(
                                f"RAW: R{reg} in ID; value in EX/MEM "
                                "(forwarding from EX/MEM in EX stage)."
                            ),
                            action=HazardAction.NONE,
                            registers=(reg,),
                        )
                    )
        return reports

    def _waw_hazard(
        self, ex_mem: EX_MEMRegister, mem_wb: MEM_WBRegister
    ) -> Optional[HazardReport]:
        if (
            ex_mem.valid
            and mem_wb.valid
            and ex_mem.reg_write
            and mem_wb.reg_write
            and ex_mem.write_reg == mem_wb.write_reg
            and ex_mem.write_reg != 0
        ):
            return HazardReport(
                hazard_type=HazardType.WAW,
                reason=(
                    f"WAW: R{ex_mem.write_reg} written by instructions in EX/MEM and MEM/WB; "
                    "WB order preserves architected state in this in-order core."
                ),
                action=HazardAction.NONE,
                registers=(ex_mem.write_reg,),
            )
        return None

    def _war_hazard(
        self,
        id_ex: ID_EXRegister,
        ex_mem: EX_MEMRegister,
        mem_wb: MEM_WBRegister,
    ) -> Optional[HazardReport]:
        if not id_ex.valid or id_ex.is_bubble or id_ex.instruction is None:
            return None
        for reg in self._source_registers(id_ex.instruction):
            if reg == 0:
                continue
            if mem_wb.valid and mem_wb.reg_write and mem_wb.write_reg == reg:
                return HazardReport(
                    hazard_type=HazardType.WAR,
                    reason=(
                        f"WAR (informational): younger op in EX reads R{reg} while older "
                        "writer is in WB; classic 5-stage avoids this by reading in ID."
                    ),
                    action=HazardAction.NONE,
                    registers=(reg,),
                )
        return None

    @staticmethod
    def _source_registers(instr) -> List[int]:
        if instr.opcode == Opcode.R_TYPE:
            return [instr.rs, instr.rt]
        if instr.opcode in (Opcode.LW, Opcode.SW, Opcode.BEQ, Opcode.BNE):
            return [instr.rs, instr.rt]
        return []
