# Theory vs. Simulator Implementation: Academic & Viva Guide

## Key Differences Summary

This document explains the technical distinction between **Classroom Textbook Theory** and this **Cycle-Accurate Processor Simulator** for presentation / viva defense.

---

### 1. Paper Calculations vs. Cycle-Accurate Execution
* **Textbook Theory**: Pipeline execution is demonstrated manually using static grid diagrams for 3–4 instructions.
* **Simulator**: A clock-driven state machine (`pipeline.step()`). On every clock tick, 5 independent functions represent 5 concurrent hardware stages operating simultaneously in parallel.

---

### 2. Microarchitectural State Registers
* **Textbook Theory**: Stage boundaries (`IF/ID`, `ID/EX`, `EX/MEM`, `MEM/WB`) are drawn as vertical lines on paper.
* **Simulator**: Implemented as explicit state structures latched at cycle boundaries. Control signals (`reg_write`, `mem_read`, `branch`) travel along with instruction data through pipeline registers.

---

### 3. Integrated Memory & Cache Behavior
* **Textbook Theory**: Cache hit/miss rates are calculated in isolation using probability questions.
* **Simulator**: Cache access is tied directly to the pipeline. Every instruction fetch in `IF` queries the `I-Cache`, and every `LW`/`SW` in `MEM` queries the `D-Cache`. Cold misses and spatial locality affect pipeline progress live.

---

### 4. Dynamic Performance Metrics
* **Textbook Theory**: CPI is given as a theoretical constant.
* **Simulator**: CPI, IPC, hazard frequencies, stall cycles, and forwarding counts are computed dynamically:
$$\text{CPI} = \frac{\text{Total Clock Cycles}}{\text{Executed Instructions}}$$

---

## Sample Viva Questions & Answers

**Q1: Is this just a Python code interpreter executing commands sequentially?**
> *Answer:* No. An interpreter executes code line-by-line sequentially. This simulator is a **cycle-accurate microarchitectural model**. Every cycle, all 5 pipeline stages run concurrently, processing different instructions in flight, checking hazard conditions, and updating pipeline registers.

**Q2: How does your project handle Load-Use hazards?**
> *Answer:* When a `LW` instruction is in `ID/EX` and its destination register matches a source register of an instruction in `IF/ID`, data forwarding cannot resolve it because memory read data isn't ready. The `HazardDetectionUnit` detects this, stalls `PC` and `IF/ID` for 1 cycle, and inserts a NOP bubble into `ID/EX`.

**Q3: How are preset example programs loaded from the GUI?**
> *Answer:* The GUI provides a live text editor and preset load buttons ("Load Hazard Demo", "Load Branch Demo", "Load Cache Demo"). When clicked, the text is parsed directly from the editor string using `InstructionParser`, converted to machine instruction words, and loaded into instruction memory.
