# Hazard Detection and Data Forwarding Unit

## 1. Pipeline Hazards Overview

In a pipelined CPU, hazards prevent the next instruction in the instruction stream from executing in its designated clock cycle. This simulator detects three primary types of hazards:

### A. Data Hazards (RAW - Read After Write)
Occurs when an instruction depends on the result of a previous instruction that is still in the pipeline.

- **EX Hazard**: Result generated in `EX` stage by instruction $I_1$ is needed by $I_2$ in `EX` stage.
- **MEM Hazard**: Result in `MEM` stage (or `WB` stage) needed by an instruction entering `EX`.

#### Forwarding Solution:
Instead of stalling the pipeline, the **Forwarding Unit** ([`forwarding.py`](file:///d:/CA/RISC_Pipeline_Simulator/src/forwarding.py)) routes the computed value directly from `EX/MEM` or `MEM/WB` pipeline registers to the input multiplexers of the ALU.

---

### B. Load-Use Hazard
Special case of RAW data hazard involving a Load Word (`LW`) instruction:
- `LW R1, 0(R0)` is in `ID/EX` stage.
- Next instruction `ADD R2, R1, R3` is in `IF/ID` stage.

#### Stall Solution:
Since memory read data is only available at the end of the `MEM` stage, forwarding directly to the next instruction's `EX` stage is physically impossible. The **Hazard Detection Unit** ([`hazard.py`](file:///d:/CA/RISC_Pipeline_Simulator/src/hazard.py)) handles this by:
1. Freezing `PC` update.
2. Freezing `IF/ID` register.
3. Insering a **NOP Bubble** into `ID/EX` register for 1 clock cycle.

---

### C. Control Hazards (Branch & Jump Penalty)
Occurs when conditional branch (`BEQ`, `BNE`) or unconditional `JUMP` instructions alter the execution flow.

- Branch outcome and target address are resolved in the **EX stage**.
- Instructions fetched during `IF` and `ID` stages while the branch was resolving are speculative.
- If the branch is **taken**, the pipeline flushes `IF/ID` and `ID/EX` registers (2-cycle branch penalty) and updates `PC` to the branch target.
