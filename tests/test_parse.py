# from pathlib import Path
# import pytest

# from source.parse import parse_world_and_weights_csv, REQUIRED_RESOURCES


# def _write(tmp_path: Path, name: str, text: str) -> Path:
#     p = tmp_path / name
#     p.write_text(text.strip() + "\n", encoding="utf-8")
#     return p


# def test_parse_wide_with_weights_row(tmp_path: Path):
#     # WIDE format with a WEIGHTS row
#     csv_text = """
# Country,Population,MetallicElements,Timber,Housing,HousingWaste
# Atlantis,100,5,10,1,0
# Carpania,50,0,0,0,0
# WEIGHTS,0.2,0.5,1.0,2.0,-2.0
# """
#     p = _write(tmp_path, "wide.csv", csv_text)
#     world, weights = parse_world_and_weights_csv(p)

#     # Countries loaded
#     assert "Atlantis" in world.countries
#     assert "Carpania" in world.countries

#     # Values loaded
#     assert world.get_country("Atlantis").get("Population") == 100.0
#     assert world.get_country("Atlantis").get("Timber") == 10.0
#     assert world.get_country("Carpania").get("Population") == 50.0

#     # Missing resources default to 0
#     assert world.get_country("Carpania").get("Timber") == 0.0

#     # WEIGHTS row parsed
#     assert weights.get("Population") == 0.2
#     assert weights.get("Housing") == 2.0
#     assert weights.get("HousingWaste") == -2.0

#     # Required resources enforced (present with default 0 if missing)
#     for r in REQUIRED_RESOURCES:
#         assert world.get_country("Atlantis").get(r) >= 0.0
#         assert weights.get(r) == weights.get(r)  # exists and is numeric


# def test_parse_long_last_weight_wins(tmp_path: Path):
#     # LONG format: Country,Resource,Amount,Weight
#     # last non-empty Weight for a resource should win
#     csv_text = """
# Country,Resource,Amount,Weight
# Atlantis,Population,100,0.2
# Atlantis,Timber,10,1.0
# Carpania,Population,50,
# Carpania,Timber,5,2.0
# Carpania,Timber,6,
# """
#     p = _write(tmp_path, "long.csv", csv_text)
#     world, weights = parse_world_and_weights_csv(p)

#     # Values loaded per country
#     assert world.get_country("Atlantis").get("Population") == 100.0
#     assert world.get_country("Atlantis").get("Timber") == 10.0

#     assert world.get_country("Carpania").get("Population") == 50.0
#     # Last Timber amount for Carpania should be 6 (row overwrites)
#     assert world.get_country("Carpania").get("Timber") == 6.0

#     # Weights are global; last non-empty wins per resource
#     # Timber weight appears as 1.0 then 2.0 then blank => should remain 2.0
#     assert weights.get("Timber") == 2.0
#     assert weights.get("Population") == 0.2

#     # Required resources enforced (world + weights)
#     for r in REQUIRED_RESOURCES:
#         assert world.get_country("Atlantis").get(r) >= 0.0
#         assert weights.get(r) == weights.get(r)


# def test_parse_missing_file_raises():
#     with pytest.raises(FileNotFoundError):
#         parse_world_and_weights_csv("does_not_exist.csv")



from pathlib import Path
import pytest

from source.parse import parse_world_and_weights_csv, REQUIRED_RESOURCES


def _write(tmp_path: Path, name: str, text: str) -> Path:
    p = tmp_path / name
    p.write_text(text.strip() + "\n", encoding="utf-8")
    return p


def _summarize(world, weights) -> str:
    lines = []
    lines.append("World:")
    for cname in sorted(world.countries.keys()):
        c = world.get_country(cname)
        # show a small, stable subset so output doesn't explode
        lines.append(
            f"  {cname}: Pop={c.get('Population')}, Timber={c.get('Timber')}, "
            f"Housing={c.get('Housing')}, HousingWaste={c.get('HousingWaste')}"
        )
    lines.append("Weights:")
    for r in ["Population", "Timber", "Housing", "HousingWaste"]:
        lines.append(f"  {r}: {weights.get(r)}")
    return "\n".join(lines)


def test_parse_wide_with_weights_row(tmp_path: Path):
    csv_text = """
Country,Population,MetallicElements,Timber,Housing,HousingWaste
Atlantis,100,5,10,1,0
Carpania,50,0,0,0,0
WEIGHTS,0.2,0.5,1.0,2.0,-2.0
"""
    p = _write(tmp_path, "wide.csv", csv_text)
    world, weights = parse_world_and_weights_csv(p)

    # Visual summary (shown only if you run pytest -s)
    print("\n[WIDE PARSE OUTPUT]\n" + _summarize(world, weights))

    assert "Atlantis" in world.countries
    assert "Carpania" in world.countries
    assert world.get_country("Atlantis").get("Population") == 100.0
    assert world.get_country("Atlantis").get("Timber") == 10.0
    assert world.get_country("Carpania").get("Population") == 50.0
    assert world.get_country("Carpania").get("Timber") == 0.0

    assert weights.get("Population") == 0.2
    assert weights.get("Housing") == 2.0
    assert weights.get("HousingWaste") == -2.0

    for r in REQUIRED_RESOURCES:
        assert world.get_country("Atlantis").get(r) >= 0.0
        assert isinstance(weights.get(r), float)


def test_parse_long_last_weight_wins(tmp_path: Path):
    csv_text = """
Country,Resource,Amount,Weight
Atlantis,Population,100,0.2
Atlantis,Timber,10,1.0
Carpania,Population,50,
Carpania,Timber,5,2.0
Carpania,Timber,6,
"""
    p = _write(tmp_path, "long.csv", csv_text)
    world, weights = parse_world_and_weights_csv(p)

    print("\n[LONG PARSE OUTPUT]\n" + _summarize(world, weights))

    assert world.get_country("Atlantis").get("Population") == 100.0
    assert world.get_country("Atlantis").get("Timber") == 10.0
    assert world.get_country("Carpania").get("Population") == 50.0
    assert world.get_country("Carpania").get("Timber") == 6.0

    assert weights.get("Timber") == 2.0
    assert weights.get("Population") == 0.2

    for r in REQUIRED_RESOURCES:
        assert world.get_country("Atlantis").get(r) >= 0.0
        assert isinstance(weights.get(r), float)


def test_parse_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        parse_world_and_weights_csv("does_not_exist.csv")