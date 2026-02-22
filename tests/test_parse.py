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