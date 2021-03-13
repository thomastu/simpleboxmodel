import dataclasses
import numpy as np

from functools import cached_property

from pydantic import validator
from pydantic.dataclasses import dataclass
from typing import List


from simpleboxmodel.models.room import Room
from .agent import Agent


@dataclass
class Activity:
    """An activity is a process by which agents interact - in the COVID case, this calculates probabilities of infection."""

    default_breathing_rate: float
    room: Room
    agents: List[Agent] = dataclasses.field(default_factory=list)

    @validator("agents", pre=True, each_item=True, always=True)
    def validate_agent(cls, value):
        assert isinstance(value, Agent), f"{value} must be an {Agent.__class__}"
        return value

    def add_agent(self, agent):
        agent = self.validate_agent(agent)
        self.agents.append(agent)

    @cached_property
    def num_agents(self):
        return len(self.agents)

    @cached_property
    def num_infected(self):
        return len(list(filter(lambda x: x.infective, self.agents)))

    @cached_property
    def ventilation_rate_per_person(self):
        return self.room.ventilation_rate_per_second / self.num_agents

    @cached_property
    def num_susceptible(self):
        n = 0
        for agent in self.agents:
            n += (not agent.infective) * (1 - agent.population.pct_immune)
        return n

    @cached_property
    def floorspace_per_agent(self):
        return self.room.length * self.room.width / self.num_agents

    @cached_property
    def agents_per_floorspace(self):
        return self.num_agents / self.room.floorspace

    @cached_property
    def volume_per_person(self):
        return self.room.volume / self.num_agents

    @cached_property
    def co2_emission_rate(self):
        """"""
        co2_rate = 0
        for agent in self.agents:
            co2_rate += (
                agent.co2_emission_rate
                * (1 / self.room.pressure)
                * (273.15 + self.room.temperature)
                / 273.15
            )
        return co2_rate

    def avg_co2_mixing_ratio(self, duration):
        outdoor_air_ventilation = self.room.outdoor_air_ventilation
        volume = self.room.volume
        return (
            self.co2_emission_rate
            * 3.6
            / outdoor_air_ventilation
            / volume
            * (
                1
                - (1 / outdoor_air_ventilation / duration)
                * (1 - np.exp(-outdoor_air_ventilation * duration))
            )
            * 1000000
            + 400
        )

    @cached_property
    def infective_doses_per_h(self):
        p = 0
        for agent in self.agents:
            p += (
                agent.infective
                * agent.infective_doses_per_h
                * (1 - agent.exhale_efficiency)
            )
        return p

    # Conditional Results for One Event
    def calc_avg_quanta_concentration(self, duration: float):
        """
        Args:
            duration (float): Duration of event in hours
        """
        concentration = (
            self.infective_doses_per_h / self.room.viral_loss_rate / self.room.volume
        )
        return concentration * (
            1
            - (1 / self.room.viral_loss_rate / duration)
            * (1 - np.exp(-self.room.viral_loss_rate * duration))
        )

    def calc_avg_quanta_inhaled_per_person(self, duration):
        """Average quanta inhaled per person."""
        q = 0
        for agent in self.agents:
            q += self.calc_agent_quanta_inhaled(agent, duration)
        return q / self.num_agents

    def calc_prob_infection(self, duration):
        """"""
        return 1 - np.exp(-self.calc_avg_quanta_inhaled_per_person(duration))

    def calc_avg_probability_hospitalization(self, duration):
        p = 0
        for agent in self.agents:
            p += self.calc_agent_hospitalization_prob(agent, duration)
        return p / self.num_agents

    def calc_agent_quanta_inhaled(self, agent, duration):
        """Calculate the quanta inhaled for a single agent."""
        return (
            self.calc_avg_quanta_concentration(duration)
            * (agent.breathing_rate_multiplier * self.default_breathing_rate)
            * duration
            * (1 - agent.inhale_efficiency)
        )

    def calc_agent_prob_infection(self, agent, duration):
        return 1 - np.exp(-self.calc_agent_quanta_inhaled(agent, duration))

    def calc_agent_hospitalization_prob(self, agent, duration):
        return (
            self.calc_agent_prob_infection(agent, duration)
            * agent.hospitalization_risk
            * (1 - agent.population.pct_immune)
        )

    def calc_new_cases(self, duration):
        return self.calc_prob_infection(duration) * self.num_susceptible

    def calc_new_hospitalizations(self, duration):
        n = 0
        for agent in self.agents:
            n += (not agent.infective) * self.calc_agent_hospitalization_prob(
                agent, duration
            )
        return n
