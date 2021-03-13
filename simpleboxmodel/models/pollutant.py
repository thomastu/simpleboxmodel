from pydantic.dataclasses import dataclass


@dataclass
class Pollutant:

    concentration: float  # ppm
