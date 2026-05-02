"""Race design data models."""

from enum import StrEnum

from pydantic import BaseModel, Field, model_validator

from openstars.engine.research.costs import FIELDS


class PRT(StrEnum):
    HYPER_EXPANSION = "HE"
    SUPER_STEALTH = "SS"
    WAR_MONGER = "WM"
    CLAIM_ADJUSTER = "CA"
    INNER_STRENGTH = "IS"
    SPACE_DEMOLITION = "SD"
    PACKET_PHYSICS = "PP"
    INTERSTELLAR_TRAVELLER = "IT"
    ALTERNATE_REALITY = "AR"
    JACK_OF_ALL_TRADES = "JOAT"


class LRT(StrEnum):
    IMPROVED_FUEL_EFFICIENCY = "IFE"
    TOTAL_TERRAFORMING = "TT"
    ADVANCED_REMOTE_MINING = "ARM"
    IMPROVED_STARBASES = "ISB"
    GENERALIZED_RESEARCH = "GR"
    ULTIMATE_RECYCLING = "UR"
    MINERAL_ALCHEMY = "MA"
    NO_RAMSCOOP_ENGINES = "NRSE"
    CHEAP_ENGINES = "CE"
    ONLY_BASIC_REMOTE_MINING = "OBRM"
    NO_ADVANCED_SCANNERS = "NAS"
    LOW_STARTING_POPULATION = "LSP"
    BLEEDING_EDGE_TECHNOLOGY = "BET"
    REGENERATING_SHIELDS = "RS"


class ResearchCostProfile(StrEnum):
    CHEAP = "cheap"
    STANDARD = "standard"
    EXPENSIVE = "expensive"


class LeftoverBonusKind(StrEnum):
    SURFACE_MINERALS = "surface_minerals"
    MINES = "mines"
    FACTORIES = "factories"
    DEFENCES = "defenses"
    CONCENTRATIONS = "concentrations"


class RaceHabitabilityFactor(BaseModel):
    immune: bool = False
    range: tuple[int, int] = (15, 85)

    @model_validator(mode="after")
    def validate_range(self) -> "RaceHabitabilityFactor":
        low, high = self.range
        if low < 0 or high < 0 or low > 100 or high > 100:
            raise ValueError("habitability range values must be in range 0..100")
        if low > high:
            raise ValueError("habitability range low value must be <= high value")
        return self


class RaceHabitability(BaseModel):
    gravity: RaceHabitabilityFactor
    temperature: RaceHabitabilityFactor
    radiation: RaceHabitabilityFactor


class RaceEconomy(BaseModel):
    colonists_per_resource: int = Field(default=1000, ge=700, le=2500)
    factory_output_per_10: int = Field(default=10, ge=5, le=15)
    factory_cost_resources: int = Field(default=10, ge=5, le=25)
    factories_per_10k_colonists: int = Field(default=10, ge=5, le=25)
    factories_save_germanium: bool = False
    mine_output_per_10: int = Field(default=10, ge=5, le=25)
    mine_cost_resources: int = Field(default=5, ge=2, le=15)
    mines_per_10k_colonists: int = Field(default=10, ge=5, le=25)
    ar_resource_divisor: int = Field(default=10, ge=5, le=25)


def _standard_research_profile() -> dict[str, ResearchCostProfile]:
    return {field: ResearchCostProfile.STANDARD for field in FIELDS}


class RaceResearch(BaseModel):
    field_profile: dict[str, ResearchCostProfile] = Field(
        default_factory=_standard_research_profile
    )
    start_at_tech_3: bool = False

    @model_validator(mode="after")
    def validate_field_profile(self) -> "RaceResearch":
        expected_fields = set(FIELDS)
        if set(self.field_profile.keys()) != expected_fields:
            raise ValueError("field_profile must include exactly the six canonical research fields")
        return self


class LeftoverBonus(BaseModel):
    kind: LeftoverBonusKind
    points: int = Field(ge=1, le=50)


class Race(BaseModel):
    name: str = Field(min_length=1, max_length=32)
    plural_name: str = Field(min_length=1, max_length=32)
    emblem: int = Field(ge=0, le=31)
    prt: PRT
    lrts: frozenset[LRT] = Field(default_factory=frozenset)
    habitability: RaceHabitability
    max_growth_rate: int = Field(default=15, ge=1, le=20)
    economy: RaceEconomy = Field(default_factory=RaceEconomy)
    research: RaceResearch = Field(default_factory=RaceResearch)
    leftover_bonus: LeftoverBonus | None = None
