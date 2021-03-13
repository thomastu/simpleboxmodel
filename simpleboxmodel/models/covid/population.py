from pydantic.dataclasses import dataclass


@dataclass
class Population:
    """A representation of a population with IAQ characteristics of interest."""

    pct_immune: float
    pct_spread: float
