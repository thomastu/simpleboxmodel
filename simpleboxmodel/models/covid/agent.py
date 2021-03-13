import dataclasses

from pydantic import root_validator
from pydantic.dataclasses import dataclass

from .population import Population
from functools import reduce


@dataclass
class Agent:

    population: Population
    hospitalization_risk: float
    exhale_efficiency: float
    inhale_efficiency: float
    infective: bool = False
    infective_doses_per_h: float = 0  # infectous doses per hour
    co2_emission_rate: float = 0.005  # L/s @ 273K, 1atm
    breathing_rate_multiplier: float = 1  # activity dependent

    @root_validator
    def validate_infective(cls, values):
        if values.get("infective") and values.get("infective_doses_per_h") <= 0:
            raise ValueError("Infective agents must exhale some infective doses.")
        return values
