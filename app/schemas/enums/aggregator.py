from enum import Enum


class Aggregator(str, Enum):
    mean = "mean"
    weighted_mean = "weighted_mean"
