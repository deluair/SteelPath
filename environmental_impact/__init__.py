"""
Environmental Impact Module for SteelPath.

Focuses on calculating and assessing environmental footprints, primarily CO2 emissions.
"""

from .emission_calculator import EmissionCalculator, EmissionFactors

__all__ = [
    "EmissionCalculator",
    "EmissionFactors"
]
