"""Search criteria normalization and validation."""

from dataclasses import dataclass, field
from typing import Optional

from .config import DEAL_TYPE_MAP

# kv.ee building material codes (structure[] parameter)
BUILDING_MATERIAL_MAP = {
    "stone": "9",
    "wood": "10",
    "wooden": "10",
    "panel": "11",
    "log": "68",
}

# kv.ee condition codes (c[] parameter)
CONDITION_MAP = {
    "new": "38",
    "all brand-new": "38",
    "good": "104",
    "good condition": "104",
    "renovated": "39",
    "satisfactory": "41",
    "needs renovation": "51",
}

# kv.ee county codes
COUNTY_MAP = {
    "harjumaa": "1",
    "hiiumaa": "2",
    "ida-virumaa": "3",
    "jõgevamaa": "4",
    "järvamaa": "5",
    "läänemaa": "6",
    "lääne-virumaa": "7",
    "põlvamaa": "8",
    "pärnumaa": "9",
    "raplamaa": "10",
    "saaremaa": "11",
    "tartumaa": "12",
    "valgamaa": "13",
    "viljandimaa": "14",
    "võrumaa": "15",
    # Major cities as shortcuts (these are actually parish codes)
    "tallinn": "1061",
    "tartu": "1063",
    "pärnu": "1045",
}

# kv.ee parish codes (Harjumaa parishes)
PARISH_MAP = {
    # Harjumaa
    "tallinn": "1061",
    "aegviidu vald": "1",
    "anija vald": "2",
    "harku vald": "3",
    "jõelähtme vald": "4",
    "keila": "416",
    "keila vald": "5",
    "kernu vald": "6",
    "kiili vald": "7",
    "kose vald": "8",
    "kuusalu vald": "9",
    "loksa": "417",
    "maardu": "418",
    "nissi vald": "12",
    "padise vald": "13",
    "paldiski": "419",
    "raasiku vald": "14",
    "rae vald": "15",
    "saku vald": "16",
    "saue": "420",
    "saue vald": "17",
    "vasalemma vald": "18",
    "viimsi vald": "19",
}

# kv.ee city/district codes (Tallinn districts)
CITY_MAP = {
    # Tallinn districts
    "haabersti": "1001",
    "kadriorg": "5701",
    "kesklinn": "1003",
    "kristiine": "1004",
    "lasnamäe": "1006",
    "mustamäe": "1007",
    "nõmme": "1008",
    "pirita": "1010",
    "põhja-tallinn": "1011",
    "vanalinn": "5700",
}


@dataclass
class SearchCriteria:
    """Search criteria for kv.ee listings."""

    deal_type: str = "sale"  # "sale" or "rent"
    county: Optional[str] = None
    parish: Optional[str] = None
    city: Optional[str] = None
    price_min: Optional[int] = None
    price_max: Optional[int] = None
    rooms_min: Optional[int] = None
    rooms_max: Optional[int] = None
    area_min: Optional[int] = None
    area_max: Optional[int] = None
    floor_min: Optional[int] = None
    floor_max: Optional[int] = None
    build_year_min: Optional[int] = None
    build_year_max: Optional[int] = None
    condition: Optional[str] = None  # "new", "renovated", "good", etc.
    building_material: Optional[str] = None  # "stone", "panel", "wood", etc.
    energy_certificate: Optional[str] = None  # "A", "B", "C", etc.
    keyword: Optional[str] = None
    page: int = 1
    page_size: Optional[int] = None

    def validate(self) -> list[str]:
        """Validate criteria and return list of errors."""
        errors = []

        if self.deal_type not in DEAL_TYPE_MAP:
            errors.append(f"Invalid deal_type: {self.deal_type}. Must be 'sale' or 'rent'.")

        if self.price_min is not None and self.price_max is not None:
            if self.price_min > self.price_max:
                errors.append("price_min cannot be greater than price_max")

        if self.rooms_min is not None and self.rooms_max is not None:
            if self.rooms_min > self.rooms_max:
                errors.append("rooms_min cannot be greater than rooms_max")

        if self.area_min is not None and self.area_max is not None:
            if self.area_min > self.area_max:
                errors.append("area_min cannot be greater than area_max")

        if self.page < 1:
            errors.append("page must be >= 1")

        return errors

    def to_query_params(self) -> dict[str, str]:
        """Convert criteria to URL query parameters.

        Uses kv.ee's actual parameter names and value codes.
        """
        params = {
            "act": "search.simple",
            "deal_type": DEAL_TYPE_MAP.get(self.deal_type, "1"),
            "page": str(self.page),
        }

        # County - convert name to code if needed
        if self.county:
            county_lower = self.county.lower()
            county_code = COUNTY_MAP.get(county_lower, self.county)
            params["county"] = county_code

        # Parish - convert name to code if needed
        if self.parish:
            parish_lower = self.parish.lower()
            parish_code = PARISH_MAP.get(parish_lower, self.parish)
            params["parish"] = parish_code

        # City - convert name to code, uses array syntax city[0]
        if self.city:
            city_lower = self.city.lower()
            city_code = CITY_MAP.get(city_lower, self.city)
            params["city[0]"] = city_code

        if self.price_min is not None:
            params["price_min"] = str(self.price_min)
        if self.price_max is not None:
            params["price_max"] = str(self.price_max)
        if self.rooms_min is not None:
            params["rooms_min"] = str(self.rooms_min)
        if self.rooms_max is not None:
            params["rooms_max"] = str(self.rooms_max)
        if self.area_min is not None:
            params["area_min"] = str(self.area_min)
        if self.area_max is not None:
            params["area_max"] = str(self.area_max)
        if self.floor_min is not None:
            params["floor_min"] = str(self.floor_min)
        if self.floor_max is not None:
            params["floor_max"] = str(self.floor_max)
        if self.build_year_min is not None:
            params["construction_year_min"] = str(self.build_year_min)
        if self.build_year_max is not None:
            params["construction_year_max"] = str(self.build_year_max)

        # Condition - convert to kv.ee code, uses c[0] parameter
        if self.condition:
            cond_lower = self.condition.lower()
            cond_code = CONDITION_MAP.get(cond_lower, self.condition)
            params["c[0]"] = cond_code

        # Building material - convert to kv.ee code, uses structure[0] parameter
        if self.building_material:
            mat_lower = self.building_material.lower()
            mat_code = BUILDING_MATERIAL_MAP.get(mat_lower, self.building_material)
            params["structure[0]"] = mat_code

        # Energy certificate - comma-separated list (e.g., "B,C,D")
        if self.energy_certificate:
            params["energy_certs"] = self.energy_certificate.upper()

        if self.keyword:
            params["keyword"] = self.keyword
        if self.page_size is not None:
            params["page_size"] = str(self.page_size)

        return params


def parse_criteria_from_args(
    deal_type: str = "sale",
    county: Optional[str] = None,
    parish: Optional[str] = None,
    city: Optional[str] = None,
    price_min: Optional[int] = None,
    price_max: Optional[int] = None,
    rooms_min: Optional[int] = None,
    rooms_max: Optional[int] = None,
    area_min: Optional[int] = None,
    area_max: Optional[int] = None,
    build_year_min: Optional[int] = None,
    build_year_max: Optional[int] = None,
    condition: Optional[str] = None,
    building_material: Optional[str] = None,
    energy_certificate: Optional[str] = None,
    keyword: Optional[str] = None,
) -> SearchCriteria:
    """Create SearchCriteria from CLI arguments."""
    return SearchCriteria(
        deal_type=deal_type,
        county=county,
        parish=parish,
        city=city,
        price_min=price_min,
        price_max=price_max,
        rooms_min=rooms_min,
        rooms_max=rooms_max,
        area_min=area_min,
        area_max=area_max,
        build_year_min=build_year_min,
        build_year_max=build_year_max,
        condition=condition,
        building_material=building_material,
        energy_certificate=energy_certificate,
        keyword=keyword,
    )
