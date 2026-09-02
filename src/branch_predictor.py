"""
Branch prediction module.

Implements static and dynamic branch prediction strategies to reduce
control hazards and improve pipeline performance.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional


class PredictionStrategy(str, Enum):
    """Branch prediction strategies."""

    ALWAYS_NOT_TAKEN = "always_not_taken"
    ALWAYS_TAKEN = "always_taken"
    ALTERNATING = "alternating"
    BIMODAL = "bimodal"


@dataclass
class BranchPredictor:
    """Static branch predictor using configurable strategies."""

    strategy: PredictionStrategy = PredictionStrategy.ALWAYS_NOT_TAKEN
    correct_predictions: int = 0
    incorrect_predictions: int = 0
    total_branches: int = 0

    # For alternating strategy
    last_prediction: bool = False

    # For bimodal strategy (simple 2-bit counter)
    prediction_table: Dict[int, int] = None

    def __post_init__(self) -> None:
        if self.strategy == PredictionStrategy.BIMODAL:
            self.prediction_table = {}

    def predict(self, address: int) -> bool:
        """
        Predict branch direction.

        Args:
            address: Branch instruction address.

        Returns:
            True if predicted taken, False if predicted not taken.
        """
        self.total_branches += 1

        if self.strategy == PredictionStrategy.ALWAYS_NOT_TAKEN:
            return False
        elif self.strategy == PredictionStrategy.ALWAYS_TAKEN:
            return True
        elif self.strategy == PredictionStrategy.ALTERNATING:
            self.last_prediction = not self.last_prediction
            return self.last_prediction
        elif self.strategy == PredictionStrategy.BIMODAL:
            # Simple bimodal prediction using 2-bit counter
            table_index = address & 0xFF  # Use lower 8 bits as index
            counter = self.prediction_table.get(table_index, 1)  # Start with weakly not taken
            prediction = counter >= 2
            return prediction
        else:
            return False

    def update(self, address: int, actually_taken: bool, predicted_taken: bool) -> None:
        """
        Update predictor based on actual branch outcome.

        Args:
            address: Branch instruction address.
            actually_taken: Whether branch was actually taken.
            predicted_taken: Whether branch was predicted taken.
        """
        if actually_taken == predicted_taken:
            self.correct_predictions += 1
        else:
            self.incorrect_predictions += 1

        if self.strategy == PredictionStrategy.BIMODAL:
            table_index = address & 0xFF
            counter = self.prediction_table.get(table_index, 1)
            
            if actually_taken:
                # Increment counter (max 3)
                counter = min(3, counter + 1)
            else:
                # Decrement counter (min 0)
                counter = max(0, counter - 1)
            
            self.prediction_table[table_index] = counter

    @property
    def accuracy(self) -> float:
        """Prediction accuracy as percentage."""
        if self.total_branches == 0:
            return 0.0
        return (self.correct_predictions / self.total_branches) * 100

    def reset(self) -> None:
        """Reset predictor state."""
        self.correct_predictions = 0
        self.incorrect_predictions = 0
        self.total_branches = 0
        self.last_prediction = False
        if self.strategy == PredictionStrategy.BIMODAL:
            self.prediction_table = {}
