"""Search criteria normalization and validation."""

from dataclasses import dataclass, field
from typing import Optional

from .config import DEAL_TYPE_MAP


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
        """Convert criteria to URL query parameters."""
        params = {
            "act": "search.simple",
            "deal_type": DEAL_TYPE_MAP.get(self.deal_type, "1"),
            "page": str(self.page),
        }

        if self.county:
            params["county"] = self.county
        if self.parish:
            params["parish"] = self.parish
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
        if self.keyword:
            params["keyword"] = self.keyword
        if self.page_size is not None:
            params["page_size"] = str(self.page_size)

        return params


def parse_criteria_from_args(
    deal_type: str = "sale",
    county: Optional[str] = None,
    price_min: Optional[int] = None,
    price_max: Optional[int] = None,
    rooms_min: Optional[int] = None,
    rooms_max: Optional[int] = None,
    area_min: Optional[int] = None,
    area_max: Optional[int] = None,
    keyword: Optional[str] = None,
) -> SearchCriteria:
    """Create SearchCriteria from CLI arguments."""
    return SearchCriteria(
        deal_type=deal_type,
        county=county,
        price_min=price_min,
        price_max=price_max,
        rooms_min=rooms_min,
        rooms_max=rooms_max,
        area_min=area_min,
        area_max=area_max,
        keyword=keyword,
    )
