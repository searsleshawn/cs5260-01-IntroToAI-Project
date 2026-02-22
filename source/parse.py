from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Optional, Tuple

from source.world_state import WorldState, CountryState, ResourceWeights, Number


# Required (*) resources from the project spec.
# (You can expand this list later if you include more resources like Water/AvailableLand.)
REQUIRED_RESOURCES = {
    "Population",
    "MetallicElements",
    "Timber",
    "MetallicAlloys",
    "MetallicAlloysWaste",
    "Electronics",
    "ElectronicsWaste",
    "Housing",
    "HousingWaste",
}


def _to_number(s: str) -> Number:
    """
    Convert CSV cell to float. Treat empty as 0.
    Accepts ints/floats and strings like '  3.0 '.
    """
    if s is None:
        return 0.0
    s = str(s).strip()
    if s == "":
        return 0.0
    # ignore commas
    s = s.replace(",", "")
    return float(s)


def _normalize_header(h: str) -> str:
    return (h or "").strip()


def parse_world_and_weights_csv(
    csv_path: str | Path,
    *,
    required_resources: Optional[Iterable[str]] = None,
    weights_row_names: Iterable[str] = ("WEIGHTS", "Weights", "weights"),
) -> Tuple[WorldState, ResourceWeights]:
    """
    Parse a CSV into (WorldState, ResourceWeights).

    Supports two layouts:

    A) WIDE format:
       Country, Population, MetallicElements, Timber, ..., HousingWaste, (optional Weight columns)
       plus optionally a special row where Country is WEIGHTS that provides weights per resource.

       Example:
       Country,Population,Timber,Housing,HousingWaste
       Atlantis,100,25,0,0
       WEIGHTS,0.2,0.1,2,-2

    B) LONG format:
       Country, Resource, Amount, Weight
       Atlantis, Population, 100, 0.2
       Atlantis, Timber, 25, 0.1
       (Weight may be blank; weights are global and last non-blank wins)

    Notes:
    - Missing resources default to 0.
    - Weights default to 0 if not provided.
    """
    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(csv_path)

    req = set(required_resources) if required_resources is not None else set(REQUIRED_RESOURCES)

    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError("CSV has no header row / fieldnames.")

        headers = [_normalize_header(h) for h in reader.fieldnames]
        header_set = {h.lower() for h in headers}

        # Detect LONG format if it has a Resource column (common names)
        long_resource_keys = {"resource", "resourcename", "resource_name"}
        long_country_keys = {"country", "countryname", "country_name"}
        long_amount_keys = {"amount", "qty", "quantity", "value"}
        long_weight_keys = {"weight", "w"}

        is_long = (header_set & long_resource_keys) and (header_set & long_country_keys) and (header_set & long_amount_keys)

        world = WorldState()
        weights = ResourceWeights()

        if is_long:
            # Map actual key names used in the CSV
            def pick_key(candidates: set[str]) -> str:
                for h in headers:
                    if h.lower() in candidates:
                        return h
                raise ValueError(f"Missing expected column from {candidates} in LONG format CSV.")

            k_country = pick_key(long_country_keys)
            k_resource = pick_key(long_resource_keys)
            k_amount = pick_key(long_amount_keys)
            k_weight = None
            for h in headers:
                if h.lower() in long_weight_keys:
                    k_weight = h
                    break

            for row in reader:
                country = (row.get(k_country) or "").strip()
                resource = (row.get(k_resource) or "").strip()
                if not country or not resource:
                    continue

                amount = _to_number(row.get(k_amount, "0"))
                # Create/get country
                if country not in world.countries:
                    world.countries[country] = CountryState(country, {})
                world.countries[country].resources[resource] = amount

                # Weights are global; if present, take last non-empty
                if k_weight is not None:
                    w_raw = (row.get(k_weight) or "").strip()
                    if w_raw != "":
                        weights.weights[resource] = _to_number(w_raw)

        else:
            # WIDE format: first column should be Country (or similar).
            # We’ll look for a country-like column; else assume first header is the country id.
            country_col = None
            for h in headers:
                if h.lower() in ("country", "countryname", "country_name", "name"):
                    country_col = h
                    break
            if country_col is None:
                country_col = headers[0]  # fallback

            # Resource columns are everything except the country column
            resource_cols = [h for h in headers if h != country_col]

            for row in reader:
                country = (row.get(country_col) or "").strip()
                if not country:
                    continue

                # Special weights row
                if country in weights_row_names:
                    for r in resource_cols:
                        cell = (row.get(r) or "").strip()
                        if cell != "":
                            weights.weights[r] = _to_number(cell)
                    continue

                inv: Dict[str, Number] = {}
                for r in resource_cols:
                    inv[r] = _to_number(row.get(r, "0"))

                world.countries[country] = CountryState(country, inv)

        # Ensure required resources exist (at least as 0) in every country
        for c in world.countries.values():
            for r in req:
                c.resources.setdefault(r, 0.0)

        # Ensure required resources exist in weights (default 0)
        for r in req:
            weights.weights.setdefault(r, 0.0)

        return world, weights