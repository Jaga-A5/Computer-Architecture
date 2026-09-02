"""
Cache simulation module.

Models instruction and data caches with direct-mapped, set-associative, and
fully associative organizations, plus FIFO/LRU replacement.
"""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Optional, Tuple

from memory import WORD_SIZE, Memory


class CacheOrganization(str, Enum):
    DIRECT_MAPPED = "direct"
    SET_ASSOCIATIVE = "set_associative"
    FULLY_ASSOCIATIVE = "fully_associative"


class ReplacementPolicy(str, Enum):
    FIFO = "FIFO"
    LRU = "LRU"


@dataclass
class CacheStatistics:
    hits: int = 0
    misses: int = 0
    replacements: int = 0

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total else 0.0

    def reset(self) -> None:
        self.hits = 0
        self.misses = 0
        self.replacements = 0


@dataclass
class CacheLine:
    tag: int = -1
    valid: bool = False
    data: Dict[int, int] = field(default_factory=dict)
    order: int = 0


@dataclass
class CacheConfig:
    name: str = "Cache"
    total_size: int = 256
    block_size: int = 16
    associativity: int = 1
    organization: CacheOrganization = CacheOrganization.DIRECT_MAPPED
    replacement: ReplacementPolicy = ReplacementPolicy.LRU

    num_sets: int = field(init=False, default=1)

    def __post_init__(self) -> None:
        if self.block_size < WORD_SIZE:
            raise ValueError("Block size must be at least one word.")
        if self.total_size % self.block_size != 0:
            raise ValueError("Cache size must be a multiple of block size.")
        num_lines = self.total_size // self.block_size
        if self.organization == CacheOrganization.DIRECT_MAPPED:
            object.__setattr__(self, "associativity", 1)
            object.__setattr__(self, "num_sets", num_lines)
        elif self.organization == CacheOrganization.FULLY_ASSOCIATIVE:
            object.__setattr__(self, "num_sets", 1)
            object.__setattr__(self, "associativity", num_lines)
        else:
            if num_lines % self.associativity != 0:
                raise ValueError("Number of lines must divide associativity.")
            object.__setattr__(self, "num_sets", num_lines // self.associativity)

    @property
    def offset_bits(self) -> int:
        return (self.block_size - 1).bit_length() if self.block_size > 1 else 0

    @property
    def index_bits(self) -> int:
        return (self.num_sets - 1).bit_length() if self.num_sets > 1 else 0


class Cache:
    """Word-oriented cache backed by a Memory instance."""

    def __init__(
        self,
        backing: Memory,
        config: CacheConfig,
    ) -> None:
        self.backing = backing
        self.config = config
        self.stats = CacheStatistics()
        self._lines: List[List[CacheLine]] = [
            [CacheLine() for _ in range(config.associativity)]
            for _ in range(config.num_sets)
        ]
        self._fifo_counter = 0
        self._lru: Dict[Tuple[int, int], int] = {}
        self._access_counter = 0

    def reset(self) -> None:
        self.stats.reset()
        for ways in self._lines:
            for line in ways:
                line.valid = False
                line.tag = -1
                line.data.clear()
        self._fifo_counter = 0
        self._lru.clear()
        self._access_counter = 0

    def access(self, address: int, is_write: bool = False, write_data: int = 0) -> int:
        """
        Perform a cache access for one word at byte address.

        Returns data word on read; on write returns written data.
        """
        address &= 0xFFFFFFFF
        block_offset = address % self.config.block_size
        block_base = address - block_offset
        index = self._index(block_base)
        tag = self._tag(block_base)

        hit_way = self._probe(index, tag)
        if hit_way is not None:
            self.stats.hits += 1
            self._touch(index, hit_way)
            line = self._lines[index][hit_way]
            word_addr = block_base + (block_offset // WORD_SIZE) * WORD_SIZE
            if is_write:
                line.data[word_addr] = write_data & 0xFFFFFFFF
                self.backing.write(word_addr, write_data)
                return write_data & 0xFFFFFFFF
            return line.data.get(word_addr, self.backing.read(word_addr))

        self.stats.misses += 1
        way = self._allocate(index, tag, block_base)
        line = self._lines[index][way]
        if is_write:
            word_addr = block_base + (block_offset // WORD_SIZE) * WORD_SIZE
            line.data[word_addr] = write_data & 0xFFFFFFFF
            self.backing.write(word_addr, write_data)
            return write_data & 0xFFFFFFFF
        word_addr = block_base + (block_offset // WORD_SIZE) * WORD_SIZE
        return line.data.get(word_addr, self.backing.read(word_addr))

    def _index(self, block_base: int) -> int:
        if self.config.num_sets == 1:
            return 0
        return (block_base // self.config.block_size) % self.config.num_sets

    def _tag(self, block_base: int) -> int:
        shift = self.config.index_bits + (
            (self.config.block_size - 1).bit_length() if self.config.block_size > 1 else 0
        )
        return block_base >> shift

    def _probe(self, index: int, tag: int) -> Optional[int]:
        for way, line in enumerate(self._lines[index]):
            if line.valid and line.tag == tag:
                return way
        return None

    def _load_block(self, block_base: int) -> Dict[int, int]:
        data: Dict[int, int] = {}
        for offset in range(0, self.config.block_size, WORD_SIZE):
            addr = block_base + offset
            data[addr] = self.backing.read(addr)
        return data

    def _allocate(self, index: int, tag: int, block_base: int) -> int:
        ways = self._lines[index]
        for way, line in enumerate(ways):
            if not line.valid:
                line.valid = True
                line.tag = tag
                line.data = self._load_block(block_base)
                line.order = self._fifo_counter
                self._fifo_counter += 1
                self._touch(index, way)
                return way

        if self.config.replacement == ReplacementPolicy.FIFO:
            way = min(range(len(ways)), key=lambda w: ways[w].order)
        else:
            way = min(
                range(len(ways)),
                key=lambda w: self._lru.get((index, w), 0),
            )

        self.stats.replacements += 1
        victim = ways[way]
        victim.tag = tag
        victim.valid = True
        victim.data = self._load_block(block_base)
        victim.order = self._fifo_counter
        self._fifo_counter += 1
        self._touch(index, way)
        return way

    def _touch(self, index: int, way: int) -> None:
        self._access_counter += 1
        self._lru[(index, way)] = self._access_counter

    def format_status(self) -> str:
        lines = [
            f"{self.config.name} ({self.config.organization.value}, "
            f"{self.config.replacement.value})",
            f"  Hits: {self.stats.hits}  Misses: {self.stats.misses}  "
            f"Hit rate: {self.stats.hit_rate * 100:.1f}%  "
            f"Replacements: {self.stats.replacements}",
        ]
        return "\n".join(lines)


class CacheHierarchy:
    """Instruction and data caches."""

    def __init__(
        self,
        instruction_memory: Memory,
        data_memory: Memory,
        icache_config: Optional[CacheConfig] = None,
        dcache_config: Optional[CacheConfig] = None,
    ) -> None:
        icfg = icache_config or CacheConfig(
            name="I-Cache",
            total_size=256,
            block_size=16,
            organization=CacheOrganization.DIRECT_MAPPED,
        )
        dcfg = dcache_config or CacheConfig(
            name="D-Cache",
            total_size=256,
            block_size=16,
            organization=CacheOrganization.SET_ASSOCIATIVE,
            associativity=2,
        )
        self.icache = Cache(instruction_memory, icfg)
        self.dcache = Cache(data_memory, dcfg)

    def reset(self) -> None:
        self.icache.reset()
        self.dcache.reset()

    def fetch_instruction(self, address: int) -> int:
        """Fetch instruction word through instruction cache."""
        return self.icache.access(address, is_write=False)

    def load_word(self, address: int) -> int:
        """Load data word through data cache."""
        return self.dcache.access(address, is_write=False)

    def store_word(self, address: int, value: int) -> None:
        """Store data word through data cache."""
        self.dcache.access(address, is_write=True, write_data=value)
