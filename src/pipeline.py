"""
Pipeline stage simulation module.

Implements the five-stage RISC pipeline (IF, ID, EX, MEM, WB) and manages
instruction flow, stage registers, and pipeline state transitions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from cache import CacheHierarchy
from cpu import CPUCore, ControlSignals
from forwarding import ForwardDecision, ForwardingUnit
from hazard import HazardControl, HazardDetectionUnit
from instruction import Instruction, Mnemonic, Opcode
from memory import WORD_SIZE
from parser import InstructionParser, parse_program
from statistics import PerformanceStatistics


@dataclass
class IF_IDRegister:
    pc: int = 0
    instruction_word: int = 0
    instruction: Optional[Instruction] = None
    valid: bool = False
    is_bubble: bool = True


@dataclass
class ID_EXRegister:
    pc: int = 0
    instruction: Optional[Instruction] = None
    control: ControlSignals = field(default_factory=ControlSignals)
    rs: int = 0
    rt: int = 0
    rs_value: int = 0
    rt_value: int = 0
    valid: bool = False
    is_bubble: bool = True
    reg_write: bool = False
    write_reg: int = 0


@dataclass
class EX_MEMRegister:
    pc: int = 0
    instruction: Optional[Instruction] = None
    control: ControlSignals = field(default_factory=ControlSignals)
    alu_result: int = 0
    rt_value: int = 0
    valid: bool = False
    is_bubble: bool = True
    reg_write: bool = False
    write_reg: int = 0
    branch_taken: bool = False
    branch_resolved: bool = False
    jump_taken: bool = False
    branch_target_pc: int = 0


@dataclass
class MEM_WBRegister:
    instruction: Optional[Instruction] = None
    control: ControlSignals = field(default_factory=ControlSignals)
    alu_result: int = 0
    mem_data: int = 0
    valid: bool = False
    is_bubble: bool = True
    reg_write: bool = False
    write_reg: int = 0

    @property
    def mem_to_reg_value(self) -> int:
        return self.mem_data if self.control.mem_to_reg else self.alu_result


def _bubble_if_id() -> IF_IDRegister:
    return IF_IDRegister(is_bubble=True, valid=False)


def _bubble_id_ex() -> ID_EXRegister:
    return ID_EXRegister(is_bubble=True, valid=False)


def _bubble_ex_mem() -> EX_MEMRegister:
    return EX_MEMRegister(is_bubble=True, valid=False)


def _bubble_mem_wb() -> MEM_WBRegister:
    return MEM_WBRegister(is_bubble=True, valid=False)


class FiveStagePipeline:
    """Cycle-accurate five-stage pipeline with hazards, forwarding, and caches."""

    BRANCH_FLUSH_PENALTY = 2

    def __init__(self) -> None:
        self.cpu = CPUCore()
        self.caches = CacheHierarchy(
            self.cpu.memory.instruction_memory,
            self.cpu.memory.data_memory,
        )
        self.hazard_unit = HazardDetectionUnit()
        self.forwarding_unit = ForwardingUnit()
        self.stats = PerformanceStatistics()
        self.if_id = _bubble_if_id()
        self.id_ex = _bubble_id_ex()
        self.ex_mem = _bubble_ex_mem()
        self.mem_wb = _bubble_mem_wb()
        self.last_hazard: HazardControl = HazardControl()
        self.last_forward: ForwardDecision = ForwardDecision()
        self.running: bool = False
        self.paused: bool = False
        self.status_log: List[str] = []

    def reset(self) -> None:
        self.cpu.reset()
        self.caches.reset()
        self.stats.reset()
        self.if_id = _bubble_if_id()
        self.id_ex = _bubble_id_ex()
        self.ex_mem = _bubble_ex_mem()
        self.mem_wb = _bubble_mem_wb()
        self.running = False
        self.paused = False
        self.status_log.clear()

    def load_program_from_file(self, path: str) -> int:
        words = [instr.encode() for instr in parse_program(path)]
        return self.cpu.load_program_words(words)

    def load_program_text(self, text: str) -> int:
        words = [instr.encode() for instr in InstructionParser().parse_text(text)]
        return self.cpu.load_program_words(words)

    @property
    def halted(self) -> bool:
        return self.cpu.halted

    def step(self) -> bool:
        """Advance one clock cycle. Returns False when HALT has retired."""
        if self.cpu.halted:
            return False

        self.stats.total_cycles += 1
        self.last_hazard = self.hazard_unit.evaluate(
            self.if_id, self.id_ex, self.ex_mem, self.mem_wb
        )
        for report in self.last_hazard.reports:
            self.stats.record_hazard(
                f"{report.hazard_type.value}: {report.reason} -> {report.action.value}"
            )
            if report.action.value == "stall":
                self.stats.pipeline_stalls += 1
            if report.action.value == "flush":
                self.stats.pipeline_flushes += 1

        self.last_forward = self.forwarding_unit.resolve(
            self.id_ex, self.ex_mem, self.mem_wb
        )
        if self.last_forward.rs_source.value == "EX/MEM":
            self.stats.forwarding_ex_mem += 1
        if self.last_forward.rt_source.value == "EX/MEM":
            self.stats.forwarding_ex_mem += 1
        if self.last_forward.rs_source.value == "MEM/WB":
            self.stats.forwarding_mem_wb += 1
        if self.last_forward.rt_source.value == "MEM/WB":
            self.stats.forwarding_mem_wb += 1

        next_mem_wb = self._stage_mem(self.ex_mem)
        next_ex_mem = self._stage_ex(self.id_ex, self.last_forward)
        next_id_ex, next_if_id, pc_next = self._stage_id_if(
            self.if_id, self.last_hazard, next_ex_mem
        )

        self.write_back(self.mem_wb)
        self.mem_wb = next_mem_wb
        self.ex_mem = next_ex_mem
        self.id_ex = next_id_ex
        self.if_id = next_if_id
        self.cpu.pc = pc_next

        self.stats.merge_cache_stats(
            self.caches.icache.stats, self.caches.dcache.stats
        )
        self._log_cycle_status()
        return not self.cpu.halted

    def run_until_halt(self, max_cycles: int = 100_000) -> None:
        self.running = True
        self.paused = False
        cycles = 0
        while cycles < max_cycles and self.step():
            cycles += 1
        self.running = False

    def write_back(self, mem_wb: MEM_WBRegister) -> None:
        if not mem_wb.valid or mem_wb.is_bubble:
            return
        if mem_wb.control.halt:
            self.cpu.halted = True
        if mem_wb.control.is_nop:
            return
        self.stats.instructions_executed += 1
        self.cpu.write_back(mem_wb.control, mem_wb.alu_result, mem_wb.mem_data)

    def _stage_mem(self, ex_mem: EX_MEMRegister) -> MEM_WBRegister:
        if not ex_mem.valid or ex_mem.is_bubble:
            return _bubble_mem_wb()
        mem_data = ex_mem.alu_result
        if ex_mem.control.mem_read:
            mem_data = self.caches.load_word(ex_mem.alu_result)
        elif ex_mem.control.mem_write:
            self.caches.store_word(ex_mem.alu_result, ex_mem.rt_value)
        return MEM_WBRegister(
            instruction=ex_mem.instruction,
            control=ex_mem.control,
            alu_result=ex_mem.alu_result,
            mem_data=mem_data,
            valid=True,
            is_bubble=False,
            reg_write=ex_mem.reg_write,
            write_reg=ex_mem.write_reg,
        )

    def _stage_ex(
        self, id_ex: ID_EXRegister, forward: ForwardDecision
    ) -> EX_MEMRegister:
        if not id_ex.valid or id_ex.is_bubble:
            return _bubble_ex_mem()
        rs_val = forward.rs_value if forward.rs_value is not None else id_ex.rs_value
        rt_val = forward.rt_value if forward.rt_value is not None else id_ex.rt_value
        instr = id_ex.instruction
        ctrl = id_ex.control
        assert instr is not None

        alu_result, branch_taken, jump_taken, target = self.cpu.execute(
            instr, ctrl, rs_val, rt_val, id_ex.pc
        )

        if ctrl.branch:
            if branch_taken:
                self.stats.branches_taken += 1
            else:
                self.stats.branches_not_taken += 1

        return EX_MEMRegister(
            pc=id_ex.pc,
            instruction=instr,
            control=ctrl,
            alu_result=alu_result,
            rt_value=rt_val,
            valid=True,
            is_bubble=False,
            reg_write=ctrl.reg_write,
            write_reg=ctrl.write_reg,
            branch_taken=branch_taken,
            branch_resolved=True,
            jump_taken=jump_taken,
            branch_target_pc=target,
        )

    def _stage_id_if(
        self, if_id: IF_IDRegister, hazard: HazardControl, ex_mem_next: EX_MEMRegister
    ) -> tuple[ID_EXRegister, IF_IDRegister, int]:
        pc = self.cpu.pc

        # Handle branch/jump flushes
        if ex_mem_next.jump_taken or (
            ex_mem_next.branch_resolved and ex_mem_next.branch_taken
        ):
            self.stats.pipeline_flushes += 1
            self.stats.branch_penalty_cycles += self.BRANCH_FLUSH_PENALTY
            self.stats.record_hazard(
                "BRANCH: taken — flush IF/ID and ID/EX, redirect PC"
            )
            target = ex_mem_next.branch_target_pc
            fetched = self._fetch(target)
            return _bubble_id_ex(), fetched, (target + WORD_SIZE) & 0xFFFFFFFF

        if hazard.stall_id:
            if hazard.insert_bubble_id_ex:
                self.stats.nop_bubbles_inserted += 1
            return _bubble_id_ex(), if_id, pc

        next_id_ex = self._decode(if_id)
        fetched = self._fetch(pc)
        return next_id_ex, fetched, (pc + WORD_SIZE) & 0xFFFFFFFF

    def _fetch(self, pc: int) -> IF_IDRegister:
        if self.cpu.halted:
            return _bubble_if_id()
        word = self.caches.fetch_instruction(pc)
        # If we encounter a zero word, treat it as end of program
        if word == 0:
            return _bubble_if_id()
        try:
            instr, _ = self.cpu.decoder.decode_word(word)
        except ValueError:
            # If we can't decode the instruction, treat it as end of program
            return _bubble_if_id()
        return IF_IDRegister(
            pc=pc,
            instruction_word=word,
            instruction=instr,
            valid=True,
            is_bubble=False,
        )

    def _decode(self, if_id: IF_IDRegister) -> ID_EXRegister:
        if not if_id.valid or if_id.is_bubble or if_id.instruction is None:
            return _bubble_id_ex()

        instr = if_id.instruction
        ctrl = self.cpu.decoder.control_for(instr)
        rs_val = self.cpu.registers.read(instr.rs)
        rt_val = self.cpu.registers.read(instr.rt)

        return ID_EXRegister(
            pc=if_id.pc,
            instruction=instr,
            control=ctrl,
            rs=instr.rs,
            rt=instr.rt,
            rs_value=rs_val,
            rt_value=rt_val,
            valid=True,
            is_bubble=False,
            reg_write=ctrl.reg_write,
            write_reg=ctrl.write_reg,
        )

    def _log_cycle_status(self) -> None:
        status = f"Cycle {self.stats.total_cycles}: PC=0x{self.cpu.pc:08X}"
        if self.cpu.halted:
            status += " (HALTED)"
        self.status_log.append(status)
