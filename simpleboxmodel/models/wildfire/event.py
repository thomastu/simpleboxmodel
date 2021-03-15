"""
Use the box model to estimate the concentration of CO2 in the room from people breathing, with different numbers of people and different types of activity. Compare your results to the results from last week using the COVID-19 model. Find the CO2 level that is associated with meeting basic minimum ventilation requirements (15 CFM per person). Use the box model to estimate the concentration of particulate matter indoors during a wildfire smoke event with various infiltration, ventilation and filtration rates.Find combinations that are consistent with meeting minimum ventilation requirements and maintaining healthy air. 
"""
import pandas as pd

from pydantic.dataclasses import dataclass

from functools import cached_property
from simpleboxmodel.models.room import Room


CuFt_to_m3 = 0.0283168
ppm_to_unitary = 1.0 / 1e6
unitary_to_ppm = 1e6
L_to_m3 = 0.001
min_to_second = 60


def main(
    volume,
    population,
    infiltration,  # ACH
    ventilation,  # m^3 / minute
    filtration,  # m^3 / minute
    co2_indoor_starting_concentration=415,  # ppm
    co2_outdoor_starting_concentration=450,  # ppm
    co2_exhalation_rate=0.0035,  # L/s
):
    pass


def ach_to_m3_min(ach, volume):
    return ach * volume / 60


def m3_min_to_ach(m3_min, volume):
    return m3_min * 60 / volume


@dataclass
class WildfireEvent:
    """Since the"""

    volume: float  # m^3
    population: int  # Count
    co2_exhalation_rate: float  # L/s

    ventilation: float  # m^3 / minute
    filtration: float  # m^3  / minute
    filtration_efficiency: float  # %
    infiltration: float  # m^3 / minute

    outdoor_co2: float  # ppm
    outdoor_pm2: float  # microgram per m^3

    starting_co2: float = 415  # ppm
    starting_pm2: float = 0  # microgram per m^3

    @cached_property
    def mechanical_ventilation_per_person(self):
        return self.ventilation / self.population

    @cached_property
    def outdoor_air_flowrate(self):
        """Outdoor air flow-rate in m^3/minute"""
        return self.ventilation + self.infiltration

    @cached_property
    def co2_exhaled(self):
        """CO2 Exhaled per minute in m^3/minute"""

        return self.co2_exhalation_rate * self.population * min_to_second * L_to_m3

    def calculate_co2_change(self, co2_ppm, duration: float):
        """Calculate CO2 change at a single timestep.

        Duration should be in minutes.
        """
        # Calculate sources of CO2 from people in the room
        exhalation = self.co2_exhaled * duration  # m^3

        # Calculate sources from outdoor connections
        # Note that the difference between the starting
        # concentration and outdoor concentration * flow rate gives co2 difference
        outdoor_exchange = (
            self.outdoor_air_flowrate * (self.outdoor_co2 - co2_ppm) * duration
        )  # m^3*ppm
        outdoor_exchange = outdoor_exchange * ppm_to_unitary  #  Convert to m^3
        return exhalation + outdoor_exchange

    def calculate_co2(self, num_timesteps, duration=10):
        """
        Args:
            duration (float): duration of each timestep in minutes.
        """
        co2_ic = self.starting_co2
        co2_change = 0
        series = [
            {
                "timestep": 0,
                "co2_change": co2_change,
                "co2": co2_ic,
                "duration": duration,
            }
        ]
        for timestep in range(num_timesteps):

            co2_change = self.calculate_co2_change(co2_ic, duration)

            # Calculate change in CO2
            co2_new = co2_ic + (co2_change / self.volume) * unitary_to_ppm

            # Append results
            series.append(
                {
                    "timestep": (timestep + 1) * duration,
                    "co2_change": co2_change,
                    "co2": co2_new,
                    "duration": duration,
                }
            )

            # Set the new initial condition for the next iteration
            co2_ic = co2_new
        return pd.DataFrame(series)

    def calculate_pm2_change(self, pm2, duration):
        """This assumes the only PM2.5 sources come from the ambient atmosphere."""

        outdoor_exchange = (
            self.outdoor_air_flowrate * (self.outdoor_pm2 - pm2) * duration
        )
        return outdoor_exchange * ppm_to_unitary

    def calculate_pm2(self, num_timesteps, duration=10):
        pm2_ic = self.starting_pm2
        pm2_change = 0
        series = [
            {
                "timestep": 0,
                "pm2_change": pm2_change,
                "pm2": pm2_ic,
                "duration": duration,
            }
        ]
        for timestep in range(num_timesteps):
            pm2_change = self.calculate_pm2_change(pm2_ic, duration)

            # Find mass of air removed in units of mass - note you can only remove as much particulate matter as there exists
            pm2_removed = (
                self.filtration * duration * pm2_ic * self.filtration_efficiency
            )

            pm2_new = (
                pm2_ic
                - (pm2_removed / self.volume)
                + (pm2_change / self.volume) * unitary_to_ppm
            )
            # If we are removing more particulate matter than is being replenished
            # we can have at most no PM2 left
            pm2_new = max(0, pm2_new)

            series.append(
                {
                    "timestep": (timestep + 1) * duration,
                    "pm2_change": pm2_change,
                    "pm2": pm2_new,
                    "duration": duration,
                }
            )
            pm2_ic = pm2_new
        return pd.DataFrame(series)