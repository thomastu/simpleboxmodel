from simpleboxmodel.models.covid import Population, Agent, Activity
from simpleboxmodel.room import Room


def run_simulation(
    pct_immune,
    pct_spread,
    num_infective,
    room,
    breathing_rate,
):
    population = Population(pct_immune=pct_immune, pct_spread=pct_spread)
    activity = Activity(
        default_breathing_rate=breathing_rate,
        room=room,
        agents=agents,
    )
