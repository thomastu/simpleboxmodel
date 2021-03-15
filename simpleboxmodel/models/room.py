from pydantic.dataclasses import dataclass
from typing import List
from functools import cached_property
from dataclasses import field
from simpleboxmodel.models.process import Source

FT_TO_METERS = 0.3048


@dataclass
class Room:

    # Physical dimensions
    length: float  # meters
    width: float  # meters
    height: float  # meters

    # Room Characteristics
    outdoor_air_ventilation: float  # ach

    # Environment Characteristics
    pressure: float = 0.95  # atmospheres
    temperature: float = 20  # Celcius
    relative_humidity: float = 0.5  # pct
    background_co2: float = 415  # ppm
    uv_index: float = 0

    # Air Control Measures
    air_quality_measures: List[Source] = field(default_factory=list)
    viral_surface_deposition: float = 0.3  # ach

    @cached_property
    def volume(self):
        return self.length * self.width * self.height

    @property
    def ventilation_rate_per_second(self):
        """
        Return ventilation rate in Litres/s == 1000 m^3/s
        """
        return self.volume * self.outdoor_air_ventilation * 1000 / 3600

    @cached_property
    def viral_decay_rate(self):
        """
        TODO: Citation!
        """
        return (
            7.56923714795655
            + 1.41125518824508 * (self.temperature - 20.54) / 10.66
            + 0.02175703466389 * (self.relative_humidity * 100 - 45.235) / 28.665
            + 7.55272292970083 * ((self.uv_index * 0.185) - 50) / 50
            + (self.temperature - 20.54)
            / 10.66
            * (self.uv_index * 0.185 - 50)
            / 50
            * 1.3973422174602
        ) * 60

    @property
    def ventilation_rate(self):
        """Sum up total air exchanges per hour based on all AQ measures."""
        # TODO: calculate based on MERV ratings/efficiency/power/etc.
        return (
            sum(v.calculate_ach(self.volume) for v in self.air_quality_measures)
            + self.outdoor_air_ventilation
        )

    @property
    def viral_loss_rate(self):
        """Rate of virus loss per hour"""
        return (
            self.viral_decay_rate
            + self.ventilation_rate
            + self.viral_surface_deposition
        )