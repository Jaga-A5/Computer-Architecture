# RISC Pipeline Simulator

A cycle-accurate 5-stage pipelined RISC processor simulator with cache memory and hazard detection, designed for educational purposes and computer architecture demonstrations.

## Features

- **5-Stage Pipeline**: IF (Instruction Fetch), ID (Instruction Decode), EX (Execute), MEM (Memory Access), WB (Write Back)
- **Hazard Detection**: Data hazards (RAW, WAR, WAW), control hazards, and structural hazards
- **Data Forwarding**: Eliminates most stalls by forwarding results from later pipeline stages
- **Cache Memory**: Separate instruction and data caches with configurable organizations
- **Branch Prediction**: Static and dynamic branch prediction strategies
- **Interactive GUI**: Real-time pipeline visualization with PyQt6
- **ALU Calculator**: Interactive calculator for basic arithmetic operations
- **Performance Statistics**: Comprehensive metrics including CPI, IPC, cache hit rates, and hazard analysis

## Architecture

### Instruction Set Architecture (ISA)

**R-Type Instructions:**
- `ADD Rdest,Rsrc1,Rsrc2` - Addition
- `SUB Rdest,Rsrc1,Rsrc2` - Subtraction  
- `MUL Rdest,Rsrc1,Rsrc2` - Multiplication

**I-Type Instructions:**
- `LW Rdest,offset(Rsrc)` - Load word
- `SW Rsrc,offset(Rdest)` - Store word
- `BEQ Rsrc1,Rsrc2,offset` - Branch if equal
- `BNE Rsrc1,Rsrc2,offset` - Branch if not equal

**J-Type Instructions:**
- `JUMP target` - Unconditional jump

**Special Instructions:**
- `NOP` - No operation
- `HALT` - Stop processor

## Installation

### Prerequisites

- Python 3.8 or higher
- PyQt6 for GUI functionality

### Setup

1. Clone or download the repository
2. Install dependencies:
```bash
pip install PyQt6 pytest
```

## Usage

### GUI Mode (Recommended)

Launch the graphical interface:

```bash
python src/gui.py
```

Or via the main entry point:

```bash
python src/main.py --gui
```

The GUI provides:
- **Pipeline Simulation Tab**: Full pipeline visualization with instruction editor
- **ALU Calculator Tab**: Interactive calculator for immediate operations

### CLI Mode

Run programs from command line:

```bash
python src/main.py instructions/program.txt
```

Enable verbose output:

```bash
python src/main.py instructions/program.txt --verbose
```

## Project Structure

```
RISC_Pipeline_Simulator/
├── src/                    # Source code
│   ├── alu.py             # Arithmetic Logic Unit
│   ├── cache.py           # Cache memory hierarchy
│   ├── cpu.py             # CPU core and control unit
│   ├── forwarding.py      # Data forwarding unit
│   ├── gui.py             # Graphical user interface
│   ├── hazard.py          # Hazard detection unit
│   ├── instruction.py     # ISA definition and encoding
│   ├── main.py            # Main entry point
│   ├── memory.py          # Memory system
│   ├── parser.py          # Assembly parser
│   ├── pipeline.py        # Pipeline orchestration
│   ├── registers.py       # Register file
│   ├── statistics.py      # Performance metrics
│   └── branch_predictor.py # Branch prediction
├── tests/                 # Unit tests
│   ├── test_alu.py
│   ├── test_memory.py
│   ├── test_parser.py
│   └── test_registers.py
├── instructions/          # Example programs
│   └── program.txt
├── docs/                  # Documentation
└── outputs/               # Simulation outputs
```

## Example Program

```assembly
ADD R1,R0,R0          # R1 <- 0 (clear)
LW R1,0(R0)           # load word at address 0
LW R2,4(R0)           # load word at address 4
ADD R3,R1,R2          # R3 = R1 + R2
SW R3,8(R0)           # store sum at address 8
HALT
```

## Testing

Run the test suite:

```bash
pytest tests/
```

Run with verbose output:

```bash
pytest tests/ -v
```

## Performance Metrics

The simulator tracks and reports:

- **CPI** (Cycles Per Instruction)
- **IPC** (Instructions Per Cycle)
- **Pipeline stalls and flushes**
- **Cache hit rates** (instruction and data)
- **Branch prediction accuracy**
- **Forwarding utilization**
- **Hazard analysis**

## Educational Use

This simulator is designed for:
- **Computer Architecture Courses**: Demonstrate pipelining concepts
- **Processor Design**: Understanding pipeline hazards and forwarding
- **Cache Performance**: Analyzing memory hierarchy behavior
- **Assembly Programming**: Learning RISC instruction sets

## Key Concepts Demonstrated

1. **Pipeline Stages**: How instructions flow through IF, ID, EX, MEM, WB
2. **Pipeline Hazards**: RAW, WAR, WAW hazards and their resolution
3. **Data Forwarding**: Eliminating stalls through result forwarding
4. **Cache Memory**: Hit/miss behavior and replacement policies
5. **Branch Prediction**: Static vs dynamic prediction strategies
6. **Performance Analysis**: CPI, IPC, and their relationship to pipeline efficiency

## License

This project is provided for educational purposes.

## Contributing

Contributions are welcome, especially for:
- Additional instruction set extensions
- Enhanced cache configurations
- Improved branch prediction algorithms
- Additional test cases and example programs

## Author

Created as a B.Tech project for "Design and Implementation of a Cycle-Accurate 5-Stage Pipelined RISC Processor Simulator with Cache Memory and Hazard Detection"
