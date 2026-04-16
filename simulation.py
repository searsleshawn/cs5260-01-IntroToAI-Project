from __future__ import annotations

import csv
import time
from pathlib import Path

from source.world_state import WorldState, CountryState, ResourceWeights
from source.operators import Transform
from source.scheduler import country_scheduler


def parse_template_file(template_path: str) -> list[Transform]:
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
                    cleaned = current.strip("()")
                    pieces = cleaned.split()

                    if len(pieces) == 2:
                        resource, amount = pieces[0], float(pieces[1])
                        if section == "inputs":
                            inputs[resource] = amount
                        elif section == "outputs":
                            outputs[resource] = amount

                if current.endswith("))") or current == ")":
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


def summarize_schedule(schedule) -> dict[str, object]:
    action_labels = [step.label for step in schedule.actions]
    num_transforms = sum(1 for label in action_labels if label.startswith("(TRANSFORM"))
    num_transfers = sum(1 for label in action_labels if label.startswith("(TRANSFER"))

    return {
        "final_eu": schedule.eu,
        "discovery_order": schedule.discovery_order,
        "num_actions": len(action_labels),
        "num_transforms": num_transforms,
        "num_transfers": num_transfers,
        "participants": ",".join(schedule.participant_countries),
        "schedule_text": " | ".join(action_labels),
    }


def main() -> None:
    base = Path(__file__).resolve().parent
    template_path = base / "template.txt"
    resources_path = base / "resources.csv"
    world_path = base / "init_world.csv"

    output_dir = base / "simulation_outputs"
    output_dir.mkdir(exist_ok=True)

    transforms = parse_template_file(str(template_path))
    weights = parse_resources_csv(str(resources_path))
    world = parse_world_csv(str(world_path))

    simulation_configs = [
        {
            "run_name": "depth3_frontier50",
            "depth_bound": 3,
            "frontier_max_size": 50,
            "gamma": 0.9,
            "k": 1.0,
            "x0": 0.0,
            "C": -1.0,
            "transfer_amounts": (1.0, 2.0, 3.0),
        },
        {
            "run_name": "depth4_frontier50",
            "depth_bound": 4,
            "frontier_max_size": 50,
            "gamma": 0.9,
            "k": 1.0,
            "x0": 0.0,
            "C": -1.0,
            "transfer_amounts": (1.0, 2.0, 3.0),
        },
        {
            "run_name": "depth5_frontier50",
            "depth_bound": 5,
            "frontier_max_size": 50,
            "gamma": 0.9,
            "k": 1.0,
            "x0": 0.0,
            "C": -1.0,
            "transfer_amounts": (1.0, 2.0, 3.0),
        },
        {
            "run_name": "depth4_frontier100",
            "depth_bound": 4,
            "frontier_max_size": 100,
            "gamma": 0.9,
            "k": 1.0,
            "x0": 0.0,
            "C": -1.0,
            "transfer_amounts": (1.0, 2.0, 3.0),
        },
        {
            "run_name": "depth4_low_failure_penalty",
            "depth_bound": 4,
            "frontier_max_size": 50,
            "gamma": 0.9,
            "k": 1.0,
            "x0": 0.0,
            "C": -0.25,
            "transfer_amounts": (1.0, 2.0, 3.0),
        },
        {
            "run_name": "depth4_high_failure_penalty",
            "depth_bound": 4,
            "frontier_max_size": 50,
            "gamma": 0.9,
            "k": 1.0,
            "x0": 0.0,
            "C": -2.0,
            "transfer_amounts": (1.0, 2.0, 3.0),
        },
    ]

    transfer_resources = [
        "MetallicElements",
        "Timber",
        "MetallicAlloys",
        "Electronics",
        "Housing",
    ]

    summary_rows: list[dict[str, object]] = []

    for config in simulation_configs:
        run_name = config["run_name"]
        output_file = output_dir / f"{run_name}_schedules.txt"

    for country_name in world.country_names():
        start = time.perf_counter()

        schedules = country_scheduler(
            your_country_name=country_name,
            resources_filename=str(resources_path),
            initial_state_filename=str(world_path),
            output_schedule_filename="temp_unused_output.txt",
            num_output_schedules=5,
            depth_bound=config["depth_bound"],
            frontier_max_size=config["frontier_max_size"],
            world_start=world,
            weights=weights,
            transforms=transforms,
            gamma=config["gamma"],
            k=config["k"],
            x0=config["x0"],
            C=config["C"],
            transfer_resources=config.get("transfer_resources", ["MetallicElements", "Timber", "MetallicAlloys", "Housing", "Electronics"]),
            transfer_amounts=config.get("transfer_amounts", (1.0, 2.0, 3.0)),
        )

        elapsed = time.perf_counter() - start

        if not schedules:
            summary_rows.append({
                "country": country_name,
                "run_name": run_name,
                "depth_bound": config["depth_bound"],
                "frontier_max_size": config["frontier_max_size"],
                "gamma": config["gamma"],
                "k": config["k"],
                "x0": config["x0"],
                "C": config["C"],
                "transfer_amounts": ",".join(str(x) for x in config["transfer_amounts"]),
                "runtime_seconds": f"{elapsed:.6f}",
                "num_schedules_returned": 0,
                "best_final_eu": "",
                "best_discovery_order": "",
                "best_num_actions": "",
                "best_num_transforms": "",
                "best_num_transfers": "",
                "best_participants": "",
                "best_schedule_text": "",
                "output_file": str(output_file),
            })
            continue

        best = schedules[0]
        best_summary = summarize_schedule(best)

        summary_rows.append({
            "country": country_name,
            "run_name": run_name,
            "depth_bound": config["depth_bound"],
            "frontier_max_size": config["frontier_max_size"],
            "gamma": config["gamma"],
            "k": config["k"],
            "x0": config["x0"],
            "C": config["C"],
            "transfer_amounts": ",".join(str(x) for x in config["transfer_amounts"]),
            "runtime_seconds": f"{elapsed:.6f}",
            "num_schedules_returned": len(schedules),
            "best_final_eu": f"{best_summary['final_eu']:.6f}",
            "best_discovery_order": best_summary["discovery_order"],
            "best_num_actions": best_summary["num_actions"],
            "best_num_transforms": best_summary["num_transforms"],
            "best_num_transfers": best_summary["num_transfers"],
            "best_participants": best_summary["participants"],
            "best_schedule_text": best_summary["schedule_text"],
            "output_file": str(output_file),
        })

    summary_path = output_dir / "simulation_summary.csv"
    fieldnames = [
        "country",
        "run_name",
        "depth_bound",
        "frontier_max_size",
        "gamma",
        "k",
        "x0",
        "C",
        "transfer_amounts",
        "runtime_seconds",
        "num_schedules_returned",
        "best_final_eu",
        "best_discovery_order",
        "best_num_actions",
        "best_num_transforms",
        "best_num_transfers",
        "best_participants",
        "best_schedule_text",
        "output_file",
    ]

    with open(summary_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summary_rows)

    print(f"Wrote summary to: {summary_path}")
    print(f"Wrote detailed schedules to: {output_dir}")


if __name__ == "__main__":
    main()