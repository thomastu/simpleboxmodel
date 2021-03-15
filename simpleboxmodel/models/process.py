from typing import Dict
from pydantic.dataclasses import dataclass

from .pollutant import Pollutant


@dataclass
class Source:
    """A ventilation source (or sink.)"""

    name: str
    flow_rate: float  # cu. meter / minute
    pollutants: Dict[str, Pollutant]  # pollutant name: value

    def calculate_ach(self, volume):
        """Given a flow rate for this source, calculate air changes per hour"""
        return (self.flow_rate / volume) * 60
