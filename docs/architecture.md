# 5-Stage RISC Pipeline Architecture

## Overview

The processor modeled in this simulator is a **32-bit cycle-accurate 5-stage pipelined RISC architecture** modeled after classical MIPS / RISC-I microarchitectures. 

The five pipeline stages execute concurrently during each clock cycle:

1. **IF (Instruction Fetch)**: Fetches 32-bit instruction word from Instruction Cache / Memory at `PC`.
2. **ID (Instruction Decode)**: Decodes instruction opcode, extracts register indices (`rs`, `rt`, `rd`), reads register operands from Register File, and generates control signals.
3. **EX (Execute / Address Calculation)**: Computes arithmetic/logic operations in the ALU, evaluates branch conditions (`BEQ`, `BNE`), or calculates memory effective addresses (`base + offset`).
4. **MEM (Memory Access)**: Reads from or writes to Data Cache / Data Memory (`LW`, `SW`).
5. **WB (Write Back)**: Writes result (`ALU` output or `Memory` loaded data) back to the target register in Register File.

---

## Inter-Stage Pipeline Registers

Data and control signals are latched into state registers between stages at every clock edge:

- **IF/ID Register** (`IF_IDRegister`): Latching `PC` and fetched `instruction_word`.
- **ID/EX Register** (`ID_EXRegister`): Latching `pc`, decoded `Instruction`, `ControlSignals`, `rs`/`rt` indices, and `rs_value`/`rt_value`.
- **EX/MEM Register** (`EX_MEMRegister`): Latching `alu_result`, `rt_value`, `reg_write` controls, branch target address, and branch evaluation results.
- **MEM/WB Register** (`MEM_WBRegister`): Latching `alu_result`, `mem_data`, destination register index `write_reg`, and write-back control flags.

---

## Registers & Memory

- **Register File**: 32 general-purpose registers (`R0` through `R31`). `R0` is hardwired to constant `0`.
- **Instruction Memory**: Word-aligned memory storing 32-bit instructions.
- **Data Memory**: Byte-addressable / Word-aligned data memory.
