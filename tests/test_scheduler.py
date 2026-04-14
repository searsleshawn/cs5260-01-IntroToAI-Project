from __future__ import annotations

import csv
from pathlib import Path

from source.world_state import WorldState, CountryState, ResourceWeights
from source.operators import Transform
from source.scheduler import country_scheduler


def parse_template_file(template_path: str) -> list[Transform]:
    """
    Parse the provided template.txt format into Transform objects.

    Expected format:

    (TRANSFORM BUILD_HOUSING
      (INPUTS
        (Population 5)
        ...)
      (OUTPUTS
        (Housing 1)
        ...))
    """
    lines = Path(template_path).read_text(encoding="utf-8").splitlines()

    transforms: list[Transform] = []
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        if line.startswith("(TRANSFORM "):
            parts = line.replace("(", "").split()
            if len(parts) < 2:
                raise ValueError(f"Bad transform header: {line}")

            name = parts[1]
            inputs: dict[str, float] = {}
            outputs: dict[str, float] = {}

            i += 1
            section = None

            while i < len(lines):
                current = lines[i].strip()

                if current.startswith("(INPUTS"):
                    section = "inputs"
                    i += 1
                    continue

                if current.startswith("(OUTPUTS"):
                    section = "outputs"
                    i += 1
                    continue

                if current.startswith("(") and not current.startswith("(TRANSFORM"):
                    # resource line like: (Population 5)
                    cleaned = current.strip("()")
                    pieces = cleaned.split()

                    if len(pieces) == 2:
                        resource, amount = pieces[0], float(pieces[1])
                        if section == "inputs":
                            inputs[resource] = amount
                        elif section == "outputs":
                            outputs[resource] = amount

                if current.endswith("))") or current == ")":
                    # do not break yet unless this closes the transform block
                    # The transform usually ends with the last output line having '))'
                    if section == "outputs" and current.endswith("))"):
                        break

                i += 1

            transforms.append(Transform(name=name, inputs=inputs, outputs=outputs))

        i += 1

    return transforms


def parse_resources_csv(resources_path: str) -> ResourceWeights:
    weights = ResourceWeights()

    with open(resources_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            resource = (row.get("Resource") or "").strip()
            weight_raw = (row.get("Weight") or "").strip()

            if not resource:
                continue

            weights.weights[resource] = float(weight_raw) if weight_raw else 0.0

    return weights


def parse_world_csv(world_path: str) -> WorldState:
    world = WorldState()

    with open(world_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError("init_world.csv missing header row")

        for row in reader:
            country = (row.get("Country") or "").strip()
            if not country:
                continue

            resources: dict[str, float] = {}
            for key, value in row.items():
                if key == "Country":
                    continue
                resources[key] = float(value) if value and value.strip() else 0.0

            world.countries[country] = CountryState(name=country, resources=resources)

    return world


def test_scheduler_runs_with_given_files() -> None:
    base = Path(__file__).resolve().parent

    template_path = base / "../template.txt"
    resources_path = base / "../resources.csv"
    world_path = base / "../init_world.csv"
    output_path = base / "test_output_schedules.txt"

    transforms = parse_template_file(str(template_path))
    weights = parse_resources_csv(str(resources_path))
    world = parse_world_csv(str(world_path))

    schedules = country_scheduler(
        your_country_name="Valmorika",
        resources_filename=str(resources_path),
        initial_state_filename=str(world_path),
        output_schedule_filename=str(output_path),
        num_output_schedules=5,
        depth_bound=3,
        frontier_max_size=50,
        world_start=world,
        weights=weights,
        transforms=transforms,
        gamma=0.9,
        k=1.0,
        x0=0.0,
        C=-1.0,
        transfer_resources=[
            "MetallicElements",
            "Timber",
            "MetallicAlloys",
            "Electronics",
            "Housing",
        ],
        transfer_amounts=(1.0, 2.0, 3.0),
    )

    assert isinstance(schedules, list)

    # With your current init_world.csv, all actionable resources are zero,
    # so it is possible the scheduler finds no valid successors and returns [].
    # That is acceptable for this first test.
    if schedules:
        first = schedules[0]
        assert hasattr(first, "actions")
        assert hasattr(first, "eu")
        assert output_path.exists()


if __name__ == "__main__":
    test_scheduler_runs_with_given_files()
    print("test_scheduler_runs_with_given_files completed")