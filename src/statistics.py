"""
Statistics and performance metrics module.

Collects and reports simulation metrics such as cycle counts, stall cycles,
cache hit rates, branch penalties, and CPI for output and analysis.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cache import CacheStatistics


@dataclass
class PerformanceStatistics:
    """Accumulated metrics for one simulation run."""

    total_cycles: int = 0
    instructions_executed: int = 0
    pipeline_stalls: int = 0
    nop_bubbles_inserted: int = 0
    pipeline_flushes: int = 0
    forwarding_ex_mem: int = 0
    forwarding_mem_wb: int = 0
    branch_penalty_cycles: int = 0
    branches_taken: int = 0
    branches_not_taken: int = 0
    icache_hits: int = 0
    icache_misses: int = 0
    dcache_hits: int = 0
    dcache_misses: int = 0
    hazard_events: list[str] = field(default_factory=list)

    def record_hazard(self, description: str) -> None:
        self.hazard_events.append(description)

    @property
    def cpi(self) -> float:
        if self.instructions_executed == 0:
            return 0.0
        return self.total_cycles / self.instructions_executed

    @property
    def ipc(self) -> float:
        if self.total_cycles == 0:
            return 0.0
        return self.instructions_executed / self.total_cycles

    @property
    def icache_hit_rate(self) -> float:
        total = self.icache_hits + self.icache_misses
        return self.icache_hits / total if total else 0.0

    @property
    def dcache_hit_rate(self) -> float:
        total = self.dcache_hits + self.dcache_misses
        return self.dcache_hits / total if total else 0.0

    @property
    def forwarding_count(self) -> int:
        return self.forwarding_ex_mem + self.forwarding_mem_wb

    def merge_cache_stats(
        self, icache: CacheStatistics, dcache: CacheStatistics
    ) -> None:
        self.icache_hits = icache.hits
        self.icache_misses = icache.misses
        self.dcache_hits = dcache.hits
        self.dcache_misses = dcache.misses

    def reset(self) -> None:
        self.total_cycles = 0
        self.instructions_executed = 0
        self.pipeline_stalls = 0
        self.nop_bubbles_inserted = 0
        self.pipeline_flushes = 0
        self.forwarding_ex_mem = 0
        self.forwarding_mem_wb = 0
        self.branch_penalty_cycles = 0
        self.branches_taken = 0
        self.branches_not_taken = 0
        self.icache_hits = 0
        self.icache_misses = 0
        self.dcache_hits = 0
        self.dcache_misses = 0
        self.hazard_events.clear()

    def format_report(self) -> str:
        lines = [
            "=" * 60,
            "PROCESSOR PERFORMANCE REPORT",
            "=" * 60,
            f"Total cycles              : {self.total_cycles}",
            f"Instructions executed     : {self.instructions_executed}",
            f"CPI (cycles / instr)      : {self.cpi:.4f}",
            f"IPC (instr / cycle)       : {self.ipc:.4f}",
            "",
            "Pipeline",
            f"  Stall cycles            : {self.pipeline_stalls}",
            f"  NOP bubbles inserted    : {self.nop_bubbles_inserted}",
            f"  Pipeline flushes        : {self.pipeline_flushes}",
            f"  Forwarding (EX/MEM)     : {self.forwarding_ex_mem}",
            f"  Forwarding (MEM/WB)     : {self.forwarding_mem_wb}",
            "",
            "Branches",
            f"  Taken                   : {self.branches_taken}",
            f"  Not taken               : {self.branches_not_taken}",
            f"  Penalty cycles          : {self.branch_penalty_cycles}",
            "",
            "Instruction cache",
            f"  Hits                    : {self.icache_hits}",
            f"  Misses                  : {self.icache_misses}",
            f"  Hit rate                : {self.icache_hit_rate * 100:.2f}%",
            "",
            "Data cache",
            f"  Hits                    : {self.dcache_hits}",
            f"  Misses                  : {self.dcache_misses}",
            f"  Hit rate                : {self.dcache_hit_rate * 100:.2f}%",
            "=" * 60,
        ]
        if self.hazard_events:
            lines.insert(-1, "")
            lines.insert(-1, f"Recent hazards ({min(5, len(self.hazard_events))} shown):")
            for event in self.hazard_events[-5:]:
                lines.insert(-1, f"  - {event}")
        return "\n".join(lines)
