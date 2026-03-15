from dataclasses import dataclass
import bw2data as bd

@dataclass
class AggregateData:
    production: int = 0
    hours_of_tractor_use: int=0
    nitrogen: int = 0
    herbicide: int = 0
    insecticide: int = 0
    eco4: int = 0
    sra19: int = 0
    sra20: int = 0
    sra19plus20: int = 0



