# Cache Memory Hierarchy

## Overview

The simulator incorporates a **split 2-level cache hierarchy** (Separate **I-Cache** for Instruction Fetch and **D-Cache** for Data Access) backed by main memory.

---

## 1. Cache Organization Parameters

Each cache is defined by a `CacheConfig` object:
- **Total Size**: Default 256 Bytes per cache.
- **Block Size (Line Size)**: Default 16 Bytes (4 words per block).
- **Associativity**:
  - **Direct Mapped** (1-way associative): Each block maps to exactly one set index.
  - **Set Associative** (N-way associative): Each block maps to a set with N lines (default 2-way for D-Cache).
  - **Fully Associative**: Any block can reside anywhere in the cache.

---

## 2. Address Decomposition

A 32-bit byte address is decomposed into:
```
+------------------+------------------+-------------------+
|    Tag Bits      |    Index Bits    |    Offset Bits    |
+------------------+------------------+-------------------+
```
- **Offset Bits**: $\log_2(\text{Block Size})$ (e.g., 4 bits for 16-byte blocks).
- **Index Bits**: $\log_2(\text{Number of Sets})$.
- **Tag Bits**: Remaining upper bits.

---

## 3. Replacement Policies & Hit/Miss Accounting

- **Hit**: Requested word address is present in valid line with matching Tag. `hits` counter incremented.
- **Miss**: Requested block is fetched from Main Memory into Cache. `misses` counter incremented.
- **Replacement Policy**:
  - **LRU (Least Recently Used)**: Evicts block accessed furthest in the past.
  - **FIFO (First In First Out)**: Evicts oldest allocated block.
