from enum import Enum


class Agregator(str, Enum):
    mean = "mean"
    weighted_mean = "weighted_mean"
