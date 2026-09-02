"""
Main entry point for the RISC Pipeline Simulator.

Parses command-line arguments, loads instruction programs, initializes the CPU,
and runs the simulation loop (CLI or GUI mode).
"""

import argparse
import sys
from pathlib import Path

from gui import main as gui_main
from pipeline import FiveStagePipeline
from parser import parse_program
from statistics import PerformanceStatistics


def run_cli_mode(program_path: str, verbose: bool = False) -> None:
    """Run the simulator in command-line mode."""
    pipeline = FiveStagePipeline()
    
    try:
        count = pipeline.load_program_from_file(program_path)
        print(f"Loaded {count} instructions from {program_path}")
    except Exception as e:
        print(f"Error loading program: {e}")
        sys.exit(1)
    
    print("\nStarting simulation...")
    print("=" * 60)
    
    pipeline.run_until_halt()
    
    print("\n" + pipeline.stats.format_report())
    
    if verbose:
        print("\nFinal Pipeline State:")
        print(f"PC: 0x{pipeline.cpu.pc:08X}")
        print("\nRegister File:")
        print(pipeline.cpu.registers.display())


def main() -> int:
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="RISC Pipeline Simulator - A cycle-accurate 5-stage pipelined processor simulator"
    )
    parser.add_argument(
        "program",
        nargs="?",
        help="Assembly program file to execute (for CLI mode)"
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Launch graphical user interface"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output (CLI mode only)"
    )
    
    args = parser.parse_args()
    
    # GUI mode
    if args.gui:
        return gui_main()
    
    # CLI mode with program file
    if args.program:
        run_cli_mode(args.program, args.verbose)
        return 0
    
    # No arguments - show help and launch GUI by default
    print("No program file specified. Launching GUI mode...")
    print("Use --help for command-line options.")
    return gui_main()


if __name__ == "__main__":
    sys.exit(main())
