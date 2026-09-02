"""
Graphical user interface module.

Provides a visual interface for running simulations, viewing pipeline state,
register values, memory contents, and performance statistics.
"""

from __future__ import annotations

import sys
from typing import Optional

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QTextEdit,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QGroupBox,
    QSplitter,
    QFrame,
    QHeaderView,
    QTabWidget,
    QMessageBox,
    QLineEdit,
    QComboBox,
    QSpinBox,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPalette

from pipeline import FiveStagePipeline
from parser import InstructionParser
from alu import ALU, ALUOperation
from forwarding import ForwardSource


class ALUCalculator(QWidget):
    """Interactive ALU calculator like gnusim - for basic operations."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.alu = ALU()
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        
        label = QLabel("ALU Calculator (Interactive Mode):")
        label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        layout.addWidget(label)
        
        # Operation selection
        op_layout = QHBoxLayout()
        op_layout.addWidget(QLabel("Operation:"))
        self.operation_combo = QComboBox()
        self.operation_combo.addItems([
            "ADD", "SUB", "MUL", "AND", "OR", "XOR", "NOT", 
            "SLL", "SRL", "SRA", "CMP (Equal)", "CMP (Less Than)"
        ])
        op_layout.addWidget(self.operation_combo)
        layout.addLayout(op_layout)
        
        # Input fields
        input_layout = QGridLayout()
        
        input_layout.addWidget(QLabel("Operand 1:"), 0, 0)
        self.operand1_input = QLineEdit()
        self.operand1_input.setPlaceholderText("Enter decimal or hex (0x...)")
        input_layout.addWidget(self.operand1_input, 0, 1)
        
        input_layout.addWidget(QLabel("Operand 2:"), 1, 0)
        self.operand2_input = QLineEdit()
        self.operand2_input.setPlaceholderText("Enter decimal or hex (0x...)")
        input_layout.addWidget(self.operand2_input, 1, 1)
        
        layout.addLayout(input_layout)
        
        # Calculate button
        self.calculate_button = QPushButton("Calculate")
        self.calculate_button.setMinimumHeight(35)
        self.calculate_button.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        self.calculate_button.clicked.connect(self._on_calculate)
        layout.addWidget(self.calculate_button)
        
        # Result display
        result_group = QGroupBox("Result")
        result_layout = QVBoxLayout(result_group)
        
        self.result_decimal = QLabel("Decimal: 0")
        self.result_hex = QLabel("Hex: 0x00000000")
        self.result_binary = QLabel("Binary: 00000000000000000000000000000000")
        self.result_flags = QLabel("Flags: Z=0 N=0 C=0 V=0")
        
        result_layout.addWidget(self.result_decimal)
        result_layout.addWidget(self.result_hex)
        result_layout.addWidget(self.result_binary)
        result_layout.addWidget(self.result_flags)
        
        layout.addWidget(result_group)
        
        # Store to register option
        store_layout = QHBoxLayout()
        store_layout.addWidget(QLabel("Store result to register:"))
        self.register_spin = QSpinBox()
        self.register_spin.setRange(0, 31)
        store_layout.addWidget(self.register_spin)
        
        self.store_button = QPushButton("Store to Register")
        self.store_button.clicked.connect(self._on_store_to_register)
        store_layout.addWidget(self.store_button)
        
        layout.addLayout(store_layout)
        
        layout.addStretch()

    def _parse_value(self, text: str) -> int:
        """Parse decimal or hex value."""
        text = text.strip()
        if not text:
            return 0
        try:
            if text.startswith("0x") or text.startswith("0X"):
                return int(text, 16)
            return int(text)
        except ValueError:
            QMessageBox.warning(self, "Input Error", f"Invalid value: {text}")
            return 0

    def _on_calculate(self) -> None:
        """Perform ALU operation."""
        op_text = self.operation_combo.currentText()
        op1 = self._parse_value(self.operand1_input.text())
        op2 = self._parse_value(self.operand2_input.text())
        
        # Map operation names to ALU operations
        op_map = {
            "ADD": ALUOperation.ADD,
            "SUB": ALUOperation.SUB,
            "MUL": ALUOperation.MUL,
            "AND": ALUOperation.AND,
            "OR": ALUOperation.OR,
            "XOR": ALUOperation.XOR,
            "NOT": ALUOperation.NOT,
            "SLL": ALUOperation.SLL,
            "SRL": ALUOperation.SRL,
            "SRA": ALUOperation.SRA,
            "CMP (Equal)": ALUOperation.EQUAL,
            "CMP (Less Than)": ALUOperation.LESS_THAN,
        }
        
        alu_op = op_map.get(op_text, ALUOperation.ADD)
        
        try:
            result = self.alu.execute(alu_op, op1, op2)
            
            # Update result display
            self.result_decimal.setText(f"Decimal: {result.result}")
            self.result_hex.setText(f"Hex: 0x{result.result:08X}")
            self.result_binary.setText(f"Binary: {result.result:032b}")
            
            # Display flags
            flags = f"Flags: Z={int(result.zero)} N={int(result.negative)} C={int(result.carry)} V={int(result.overflow)}"
            self.result_flags.setText(flags)
            
            # Store for potential register write
            self.last_result = result.result
            
        except Exception as e:
            QMessageBox.critical(self, "Calculation Error", f"Error: {str(e)}")

    def _on_store_to_register(self) -> None:
        """Store the last calculated result to a register."""
        if not hasattr(self, 'last_result'):
            QMessageBox.warning(self, "No Result", "Calculate a result first.")
            return
        
        reg = self.register_spin.value()
        # This would need access to the pipeline's register file
        # For now, just show what would happen
        QMessageBox.information(
            self, 
            "Store Operation", 
            f"Would store 0x{self.last_result:08X} to R{reg}"
        )


class InstructionEditor(QWidget):
    """Text editor for entering assembly instructions with preset options."""

    code_changed = pyqtSignal(str)

    DEFAULT_PROGRAM = (
        "# Basic Example Program\n"
        "# R1 = mem[0], R2 = mem[4], R3 = R1 + R2, store sum at mem[8]\n"
        "ADD R1, R0, R0\n"
        "LW R1, 0(R0)\n"
        "LW R2, 4(R0)\n"
        "ADD R3, R1, R2\n"
        "SW R3, 8(R0)\n"
        "HALT"
    )

    HAZARD_DEMO = (
        "# Data Hazard & Load-Use Demo\n"
        "ADD R1, R0, R0\n"
        "LW R1, 0(R0)\n"
        "LW R2, 4(R0)\n"
        "ADD R3, R1, R2        # RAW Hazard -> Forwarded from EX/MEM\n"
        "SW R3, 8(R0)\n"
        "LW R4, 8(R0)\n"
        "ADD R5, R4, R1        # Load-Use Hazard on R4 -> Stalls 1 cycle\n"
        "HALT"
    )

    BRANCH_DEMO = (
        "# Control Hazard & Branch Penalty Demo\n"
        "ADD R1, R0, R0\n"
        "LW R1, 0(R0)\n"
        "LW R2, 0(R0)          # R1 == R2\n"
        "BEQ R1, R2, 2         # Branch Taken! Flushes IF/ID & ID/EX\n"
        "ADD R3, R0, R0        # Skipped (Flushed)\n"
        "ADD R4, R0, R0        # Skipped (Flushed)\n"
        "ADD R5, R1, R2        # Target of branch\n"
        "HALT"
    )

    CACHE_DEMO = (
        "# Cache Locality Demo\n"
        "ADD R1, R0, R0\n"
        "LW R1, 0(R0)          # Address 0: D-Cache Miss (Cold)\n"
        "LW R2, 4(R0)          # Address 4: D-Cache Hit (Same block)\n"
        "LW R3, 8(R0)          # Address 8: D-Cache Hit (Same block)\n"
        "LW R4, 12(R0)         # Address 12: D-Cache Hit (Same block)\n"
        "SW R1, 0(R0)          # Address 0: D-Cache Hit\n"
        "HALT"
    )

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        
        label = QLabel("Assembly Program")
        label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        layout.addWidget(label)

        sub_label = QLabel("Enter one instruction per line.")
        sub_label.setFont(QFont("Arial", 9))
        sub_label.setStyleSheet("color: #AAAAAA;")
        layout.addWidget(sub_label)

        # Preset selection buttons
        preset_layout = QHBoxLayout()
        preset_label = QLabel("Presets:")
        preset_layout.addWidget(preset_label)

        self.preset_combo = QComboBox()
        self.preset_combo.addItems([
            "Default Program",
            "Hazard & Forwarding Demo",
            "Branch Penalty Demo",
            "Cache Locality Demo"
        ])
        self.preset_combo.currentIndexChanged.connect(self._on_preset_changed)
        preset_layout.addWidget(self.preset_combo)
        layout.addLayout(preset_layout)
        
        self.editor = QTextEdit()
        self.editor.setPlaceholderText("Type your custom assembly code here...")
        self.editor.setFont(QFont("Consolas", 10))
        self.editor.setPlainText(self.DEFAULT_PROGRAM)
        self.editor.textChanged.connect(self._on_text_changed)
        layout.addWidget(self.editor)

    def _on_preset_changed(self, index: int) -> None:
        presets = [
            self.DEFAULT_PROGRAM,
            self.HAZARD_DEMO,
            self.BRANCH_DEMO,
            self.CACHE_DEMO
        ]
        if 0 <= index < len(presets):
            self.editor.setPlainText(presets[index])

    def _on_text_changed(self) -> None:
        self.code_changed.emit(self.editor.toPlainText())

    def get_text(self) -> str:
        return self.editor.toPlainText()

    def set_text(self, text: str) -> None:
        self.editor.setPlainText(text)

    def clear(self) -> None:
        self.editor.clear()


class PipelineViewer(QWidget):
    """Visual representation of the 5-stage pipeline."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        
        self.stages_table = QTableWidget(5, 3)
        self.stages_table.setHorizontalHeaderLabels(["Stage", "Instruction", "Status"])
        self.stages_table.setVerticalHeaderLabels(["Fetch", "Decode", "Execute", "Memory", "Write-back"])
        self.stages_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.stages_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.stages_table.setFont(QFont("Consolas", 10))
        layout.addWidget(self.stages_table)

        # PC display
        self.pc_label = QLabel("PC: 0x00000000")
        self.pc_label.setFont(QFont("Consolas", 10, QFont.Weight.Bold))
        layout.addWidget(self.pc_label)

    def update_pipeline(self, pipeline: FiveStagePipeline) -> None:
        """Update pipeline visualization from pipeline state."""
        stages = [
            ("Fetch", pipeline.if_id),
            ("Decode", pipeline.id_ex),
            ("Execute", pipeline.ex_mem),
            ("Memory", pipeline.mem_wb),
            ("Write-back", pipeline.mem_wb),
        ]

        last_hazard = pipeline.last_hazard

        for row, (stage_name, reg) in enumerate(stages):
            # Column 0: Stage name
            self.stages_table.setItem(row, 0, QTableWidgetItem(stage_name))
            
            # Column 1: Instruction
            if reg.instruction and not reg.is_bubble:
                instr_text = str(reg.instruction.mnemonic.value)
                if reg.instruction.opcode.value in [0x23, 0x2B, 0x04, 0x05]:  # LW, SW, BEQ, BNE
                    instr_text += f" R{reg.instruction.rt}, {reg.instruction.immediate}(R{reg.instruction.rs})"
                elif reg.instruction.opcode.value == 0x00:  # R-type
                    instr_text += f" R{reg.instruction.rd}, R{reg.instruction.rs}, R{reg.instruction.rt}"
            elif reg.is_bubble:
                instr_text = "Bubble"
            else:
                instr_text = "Empty"
            
            instr_item = QTableWidgetItem(instr_text)
            if reg.is_bubble:
                instr_item.setBackground(QColor(80, 40, 40))
                instr_item.setForeground(QColor(255, 200, 200))
            elif reg.valid:
                instr_item.setBackground(QColor(40, 80, 40))
                instr_item.setForeground(QColor(200, 255, 200))
            self.stages_table.setItem(row, 1, instr_item)
            
            # Column 2: Status
            status = "Stalled" if (stage_name in ["Fetch", "Decode"] and last_hazard.stall_id) else ("Bubble" if reg.is_bubble else ("Valid" if reg.valid else "Empty"))
            status_item = QTableWidgetItem(status)
            if status == "Stalled" or status == "Bubble":
                status_item.setBackground(QColor(80, 40, 40))
                status_item.setForeground(QColor(255, 200, 200))
            elif status == "Valid":
                status_item.setBackground(QColor(40, 80, 40))
                status_item.setForeground(QColor(200, 255, 200))
            self.stages_table.setItem(row, 2, status_item)

        # Update PC
        self.pc_label.setText(f"PC: 0x{pipeline.cpu.pc:08X}")


class HazardViewer(QWidget):
    """Dedicated visual panel for detecting and reporting active Hazards & Forwarding events."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        
        label = QLabel("Hazard & Forwarding Detection:")
        label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        layout.addWidget(label)
        
        self.table = QTableWidget(4, 3)
        self.table.setHorizontalHeaderLabels(["Hazard Type", "Stage", "Hardware Action / Details"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setFont(QFont("Consolas", 9))
        layout.addWidget(self.table)

    def update_hazards(self, pipeline: FiveStagePipeline) -> None:
        """Update hazard detection panel from pipeline state."""
        last_hazard = pipeline.last_hazard
        last_forward = pipeline.last_forward

        events = []

        # Check Data Hazard (Load-Use Stall)
        if last_hazard.stall_id:
            events.append(("DATA HAZARD", "ID/EX Stage", "Stall: Load-Use Hazard (1-Cycle NOP Bubble Injected)"))

        # Check Data Hazard (Forwarding)
        fwd_sources = []
        if last_forward.rs_source not in (ForwardSource.NONE, ForwardSource.ID_EX):
            fwd_sources.append(f"Reg1<-{last_forward.rs_source.value}")
        if last_forward.rt_source not in (ForwardSource.NONE, ForwardSource.ID_EX):
            fwd_sources.append(f"Reg2<-{last_forward.rt_source.value}")
        if fwd_sources:
            events.append(("DATA HAZARD", "EX Stage", f"Forwarding Active ({', '.join(fwd_sources)})"))

        # Check Control Hazard (Branch Taken)
        if pipeline.ex_mem.branch_taken:
            events.append(("CONTROL HAZARD", "EX Stage", "Branch Taken: Flushed Speculative IF/ID & ID/EX"))

        # Check Structural Hazard (Simultaneous IF & MEM memory access)
        if pipeline.ex_mem.valid and not pipeline.ex_mem.is_bubble and (pipeline.ex_mem.control.mem_read or pipeline.ex_mem.control.mem_write):
            if pipeline.if_id.valid and not pipeline.if_id.is_bubble:
                events.append(("STRUCTURAL HAZARD", "IF & MEM", "Simultaneous Fetch & Data Access (Handled by Split Cache)"))

        if not events:
            events.append(("NONE", "All Stages", "Normal Execution (No Hazards Detected)"))

        self.table.setRowCount(len(events))
        for row, (h_type, stage, detail) in enumerate(events):
            # Hazard Type
            type_item = QTableWidgetItem(h_type)
            if h_type == "DATA HAZARD":
                type_item.setBackground(QColor(255, 230, 230))
                type_item.setForeground(QColor(180, 0, 0))
            elif h_type == "CONTROL HAZARD":
                type_item.setBackground(QColor(255, 240, 200))
                type_item.setForeground(QColor(180, 100, 0))
            elif h_type == "STRUCTURAL HAZARD":
                type_item.setBackground(QColor(240, 230, 255))
                type_item.setForeground(QColor(100, 0, 180))
            else:
                type_item.setBackground(QColor(220, 255, 220))
                type_item.setForeground(QColor(0, 120, 0))
            self.table.setItem(row, 0, type_item)

            # Stage
            self.table.setItem(row, 1, QTableWidgetItem(stage))

            # Details
            detail_item = QTableWidgetItem(detail)
            if "Forwarding" in detail:
                detail_item.setBackground(QColor(220, 235, 255))
                detail_item.setForeground(QColor(0, 80, 180))
            elif "Stall" in detail or "Bubble" in detail:
                detail_item.setBackground(QColor(255, 230, 230))
                detail_item.setForeground(QColor(180, 0, 0))
            self.table.setItem(row, 2, detail_item)


class RegisterViewer(QWidget):
    """Table view of register file contents."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        
        label = QLabel("Register File:")
        label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        layout.addWidget(label)
        
        self.table = QTableWidget(32, 4)
        self.table.setHorizontalHeaderLabels(["Register", "Hex", "Decimal", "Binary"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setFont(QFont("Consolas", 9))
        layout.addWidget(self.table)

    def update_registers(self, pipeline: FiveStagePipeline) -> None:
        """Update register display from pipeline state."""
        registers = pipeline.cpu.registers.get_all()
        
        for reg_idx in range(32):
            value = registers.get(reg_idx, 0)
            
            # Register name
            self.table.setItem(reg_idx, 0, QTableWidgetItem(f"R{reg_idx}"))
            # Hex
            self.table.setItem(reg_idx, 1, QTableWidgetItem(f"0x{value:08X}"))
            # Decimal
            self.table.setItem(reg_idx, 2, QTableWidgetItem(str(value)))
            # Binary
            self.table.setItem(reg_idx, 3, QTableWidgetItem(f"{value:032b}"))


class MemoryViewer(QWidget):
    """Table view of data memory contents."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._setup_ui()
        self.start_address = 0

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        
        label = QLabel("Data Memory:")
        label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        layout.addWidget(label)
        
        # Address controls
        addr_layout = QHBoxLayout()
        addr_layout.addWidget(QLabel("Start Address:"))
        self.address_input = QLineEdit()
        self.address_input.setMaximumHeight(25)
        self.address_input.setPlaceholderText("0")
        self.address_input.setText("0")
        self.address_input.textChanged.connect(self._on_address_changed)
        addr_layout.addWidget(self.address_input)
        layout.addLayout(addr_layout)
        
        self.table = QTableWidget(16, 2)
        self.table.setHorizontalHeaderLabels(["Address", "Data"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setFont(QFont("Consolas", 9))
        layout.addWidget(self.table)

    def _on_address_changed(self) -> None:
        try:
            text = self.address_input.toPlainText().strip()
            self.start_address = int(text, 0) if text else 0
        except ValueError:
            self.start_address = 0

    def update_memory(self, pipeline: FiveStagePipeline) -> None:
        """Update memory display from pipeline state."""
        memory = pipeline.cpu.memory.data_memory
        
        for row in range(16):
            addr = self.start_address + row * 4
            try:
                value = memory.read(addr)
            except:
                value = 0
            
            self.table.setItem(row, 0, QTableWidgetItem(f"0x{addr:08X}"))
            self.table.setItem(row, 1, QTableWidgetItem(f"0x{value:08X}"))


class CacheViewer(QWidget):
    """Tabbed view of instruction and data cache state."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        
        label = QLabel("Cache Hierarchy:")
        label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        layout.addWidget(label)
        
        self.tabs = QTabWidget()
        
        # Instruction cache tab
        self.icache_table = QTableWidget()
        self.icache_table.setColumnCount(4)
        self.icache_table.setHorizontalHeaderLabels(["Set", "Way", "Tag", "Valid"])
        self.icache_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.icache_table.setFont(QFont("Consolas", 9))
        self.tabs.addTab(self.icache_table, "I-Cache")
        
        # Data cache tab
        self.dcache_table = QTableWidget()
        self.dcache_table.setColumnCount(4)
        self.dcache_table.setHorizontalHeaderLabels(["Set", "Way", "Tag", "Valid"])
        self.dcache_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.dcache_table.setFont(QFont("Consolas", 9))
        self.tabs.addTab(self.dcache_table, "D-Cache")
        
        layout.addWidget(self.tabs)
        
        # Cache statistics
        self.cache_stats_label = QLabel()
        self.cache_stats_label.setFont(QFont("Consolas", 9))
        layout.addWidget(self.cache_stats_label)

    def update_cache(self, pipeline: FiveStagePipeline) -> None:
        """Update cache display from pipeline state."""
        # Update instruction cache
        icache = pipeline.caches.icache
        self.icache_table.setRowCount(len(icache._lines) * icache.config.associativity)
        
        row = 0
        for set_idx, ways in enumerate(icache._lines):
            for way_idx, line in enumerate(ways):
                self.icache_table.setItem(row, 0, QTableWidgetItem(str(set_idx)))
                self.icache_table.setItem(row, 1, QTableWidgetItem(str(way_idx)))
                self.icache_table.setItem(row, 2, QTableWidgetItem(f"0x{line.tag:X}" if line.tag >= 0 else "-"))
                valid_item = QTableWidgetItem("Yes" if line.valid else "No")
                valid_item.setBackground(QColor(200, 255, 200) if line.valid else QColor(255, 200, 200))
                self.icache_table.setItem(row, 3, valid_item)
                row += 1
        
        # Update data cache
        dcache = pipeline.caches.dcache
        self.dcache_table.setRowCount(len(dcache._lines) * dcache.config.associativity)
        
        row = 0
        for set_idx, ways in enumerate(dcache._lines):
            for way_idx, line in enumerate(ways):
                self.dcache_table.setItem(row, 0, QTableWidgetItem(str(set_idx)))
                self.dcache_table.setItem(row, 1, QTableWidgetItem(str(way_idx)))
                self.dcache_table.setItem(row, 2, QTableWidgetItem(f"0x{line.tag:X}" if line.tag >= 0 else "-"))
                valid_item = QTableWidgetItem("Yes" if line.valid else "No")
                valid_item.setBackground(QColor(200, 255, 200) if line.valid else QColor(255, 200, 200))
                self.dcache_table.setItem(row, 3, valid_item)
                row += 1
        
        # Update statistics
        stats_text = (
            f"I-Cache: {icache.stats.hits} hits, {icache.stats.misses} misses "
            f"({icache.stats.hit_rate*100:.1f}% hit rate)\n"
            f"D-Cache: {dcache.stats.hits} hits, {dcache.stats.misses} misses "
            f"({dcache.stats.hit_rate*100:.1f}% hit rate)"
        )
        self.cache_stats_label.setText(stats_text)


class StatisticsDashboard(QWidget):
    """Display of performance statistics and metrics."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        
        label = QLabel("Performance Statistics:")
        label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        layout.addWidget(label)
        
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setFont(QFont("Consolas", 9))
        layout.addWidget(self.stats_text)

    def update_statistics(self, pipeline: FiveStagePipeline) -> None:
        """Update statistics display from pipeline state."""
        stats = pipeline.stats
        report = stats.format_report()
        self.stats_text.setPlainText(report)


class ControlPanel(QWidget):
    """Control buttons for simulation execution."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        
        self.run_button = QPushButton("Run")
        self.run_button.setMinimumHeight(40)
        self.run_button.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        layout.addWidget(self.run_button)
        
        self.step_button = QPushButton("Step")
        self.step_button.setMinimumHeight(40)
        self.step_button.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        layout.addWidget(self.step_button)
        
        self.pause_button = QPushButton("Pause")
        self.pause_button.setMinimumHeight(40)
        self.pause_button.setStyleSheet("background-color: #FF9800; color: white; font-weight: bold;")
        self.pause_button.setEnabled(False)
        layout.addWidget(self.pause_button)
        
        self.reset_button = QPushButton("Reset")
        self.reset_button.setMinimumHeight(40)
        self.reset_button.setStyleSheet("background-color: #f44336; color: white; font-weight: bold;")
        layout.addWidget(self.reset_button)
        
        layout.addStretch()

    def set_running_state(self, is_running: bool) -> None:
        """Update button states based on execution state."""
        self.run_button.setEnabled(not is_running)
        self.step_button.setEnabled(not is_running)
        self.pause_button.setEnabled(is_running)
        self.reset_button.setEnabled(not is_running)


class MainWindow(QMainWindow):
    """Main application window for the RISC Pipeline Simulator."""

    def __init__(self) -> None:
        super().__init__()
        self.pipeline = FiveStagePipeline()
        self.run_timer = QTimer()
        self.run_timer.timeout.connect(self._on_run_step)
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        self.setWindowTitle("RISC Pipeline Simulator")
        self.setGeometry(100, 100, 1600, 950)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Top Header Title Banner
        title_label = QLabel("5-Stage RISC Pipeline Simulator")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Control Panel (Top-left aligned buttons)
        self.control_panel = ControlPanel()
        main_layout.addWidget(self.control_panel)
        
        # Main splitter dividing Program (Left) and Simulator View (Right)
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left Panel: Program Group Box
        program_group = QGroupBox("Program")
        program_group.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        program_layout = QVBoxLayout(program_group)
        
        self.instruction_editor = InstructionEditor()
        program_layout.addWidget(self.instruction_editor)
        
        # Load Program button
        self.load_button = QPushButton("Load Program")
        self.load_button.setMinimumHeight(35)
        self.load_button.setStyleSheet("background-color: #444444; color: white; font-weight: bold; border-radius: 4px;")
        program_layout.addWidget(self.load_button)
        
        content_splitter.addWidget(program_group)
        
        # Right Panel: Simulator View Group Box with Tabs
        sim_group = QGroupBox("Simulator View")
        sim_group.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        sim_layout = QVBoxLayout(sim_group)
        
        self.tabs = QTabWidget()
        self.tabs.setFont(QFont("Arial", 9))
        
        # 1. Pipeline Tab
        self.pipeline_viewer = PipelineViewer()
        self.tabs.addTab(self.pipeline_viewer, "Pipeline")
        
        # 2. Registers Tab
        self.register_viewer = RegisterViewer()
        self.tabs.addTab(self.register_viewer, "Registers")
        
        # 3. Memory Tab
        self.memory_viewer = MemoryViewer()
        self.tabs.addTab(self.memory_viewer, "Memory")
        
        # 4. Cache Tab
        self.cache_viewer = CacheViewer()
        self.tabs.addTab(self.cache_viewer, "Cache")
        
        # 5. Performance Tab
        self.statistics_dashboard = StatisticsDashboard()
        self.tabs.addTab(self.statistics_dashboard, "Performance")
        
        # 6. Hazards Tab
        self.hazard_viewer = HazardViewer()
        self.tabs.addTab(self.hazard_viewer, "Hazards")
        
        sim_layout.addWidget(self.tabs)
        content_splitter.addWidget(sim_group)
        
        # Set splitter proportions (Left 35%, Right 65%)
        content_splitter.setStretchFactor(0, 35)
        content_splitter.setStretchFactor(1, 65)
        
        main_layout.addWidget(content_splitter, 1)
        
        # Status bar
        self.status_label = QLabel("Ready - Enter a program and click Load Program")
        self.statusBar().addWidget(self.status_label)

    def _connect_signals(self) -> None:
        """Connect signals and slots."""
        self.control_panel.run_button.clicked.connect(self._on_run)
        self.control_panel.step_button.clicked.connect(self._on_step)
        self.control_panel.pause_button.clicked.connect(self._on_pause)
        self.control_panel.reset_button.clicked.connect(self._on_reset)
        self.load_button.clicked.connect(self._on_load_program)

    def _on_load_program(self) -> None:
        """Load program from instruction editor."""
        try:
            text = self.instruction_editor.get_text()
            if not text.strip():
                QMessageBox.warning(self, "Warning", "No instructions to load.")
                return
            
            self.pipeline.reset()
            count = self.pipeline.load_program_text(text)
            self.status_label.setText(f"Loaded {count} instructions from GUI editor")
            self._update_all_viewers()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load program: {str(e)}")

    def _on_run(self) -> None:
        """Start continuous execution."""
        if self.pipeline.halted:
            QMessageBox.information(self, "Info", "Program has halted. Reset to run again.")
            return
        
        if not self.pipeline.if_id.valid and not self.pipeline.id_ex.valid:
            if not self.instruction_editor.get_text().strip():
                QMessageBox.warning(self, "Warning", "Load a program first.")
                return
            self._on_load_program()
        
        self.pipeline.running = True
        self.pipeline.paused = False
        self.control_panel.set_running_state(True)
        self.run_timer.start(100)  # 100ms per step
        self.status_label.setText("Running...")

    def _on_run_step(self) -> None:
        """Execute one step during run mode."""
        if self.pipeline.halted:
            self._on_pause()
            self.status_label.setText("Program halted")
            QMessageBox.information(self, "Info", "Program execution completed.")
            return
        
        self.pipeline.step()
        self._update_all_viewers()

    def _on_step(self) -> None:
        """Execute single step."""
        if self.pipeline.halted:
            QMessageBox.information(self, "Info", "Program has halted. Reset to run again.")
            return
        
        if not self.pipeline.if_id.valid and not self.pipeline.id_ex.valid:
            if not self.instruction_editor.get_text().strip():
                QMessageBox.warning(self, "Warning", "Load a program first.")
                return
            self._on_load_program()
        
        success = self.pipeline.step()
        self._update_all_viewers()
        
        if not success:
            self.status_label.setText("Program halted")
        else:
            self.status_label.setText(f"Step executed. Cycle: {self.pipeline.stats.total_cycles}")

    def _on_pause(self) -> None:
        """Pause execution."""
        self.pipeline.paused = True
        self.pipeline.running = False
        self.run_timer.stop()
        self.control_panel.set_running_state(False)
        self.status_label.setText("Paused")

    def _on_reset(self) -> None:
        """Reset the pipeline and all state."""
        self.run_timer.stop()
        self.pipeline.reset()
        self.control_panel.set_running_state(False)
        self._update_all_viewers()
        self.status_label.setText("Reset")

    def _update_all_viewers(self) -> None:
        """Update all viewer components."""
        self.pipeline_viewer.update_pipeline(self.pipeline)
        self.register_viewer.update_registers(self.pipeline)
        self.memory_viewer.update_memory(self.pipeline)
        self.hazard_viewer.update_hazards(self.pipeline)
        self.cache_viewer.update_cache(self.pipeline)
        self.statistics_dashboard.update_statistics(self.pipeline)


def main() -> int:
    """Main entry point for the GUI application."""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # Set dark theme matching exact screenshot
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(40, 40, 40))
    palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(45, 45, 45))
    palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Button, QColor(50, 50, 50))
    palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
    palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(60, 60, 60))
    palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)
    app.setPalette(palette)
    
    window = MainWindow()
    window.show()
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
