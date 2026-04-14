from __future__ import annotations

from dataclasses import dataclass, field
from heapq import heappop, heappush
from typing import Iterable, Sequence

from source.expected_utility import expected_utility
from source.world_state import WorldState, ResourceWeights
from source.operators import Transform, apply_transform, apply_transfer, growth


@dataclass(slots=True)
class ScheduledAction:
    """
    One action and the EU of the partial schedule after that action is applied.
    """
    label: str
    eu: float


@dataclass(slots=True)
class SearchNode:
    """
    One node in the forward search tree.
    """
    world: WorldState
    actions: list[ScheduledAction] = field(default_factory=list)
    participant_countries: set[str] = field(default_factory=set)
    depth: int = 0
    eu: float = 0.0


@dataclass(slots=True)
class CompletedSchedule:
    """
    A completed schedule found at the depth bound.
    """
    actions: list[ScheduledAction]
    final_world: WorldState
    participant_countries: list[str]
    eu: float
    discovery_order: int


def _format_transform_action(country: str, transform: Transform) -> str:
    return f"(TRANSFORM {country} {transform.name})"


def _format_transfer_action(src: str, dst: str, resource: str, amount: float) -> str:
    amount_text = int(amount) if float(amount).is_integer() else amount
    return f"(TRANSFER {src} {dst} (({resource} {amount_text})))"


def _score_node(
    *,
    world_start: WorldState,
    node_world: WorldState,
    self_country: str,
    participant_countries: Iterable[str],
    weights: ResourceWeights,
    gamma: float,
    depth: int,
    k: float,
    x0: float,
    C: float,
) -> float:
    participants = sorted(set(participant_countries) | {self_country})
    return expected_utility(
        world_start,
        node_world,
        self_country=self_country,
        participant_countries=participants,
        weights=weights,
        gamma=gamma,
        N=depth,
        k=k,
        x0=x0,
        C=C,
    )


def generate_successors(
    world: WorldState,
    self_country: str,
    transforms: Sequence[Transform],
    *,
    transfer_resources: Sequence[str] | None = None,
    transfer_amounts: Sequence[float] = (1.0,),
) -> list[tuple[str, WorldState, set[str]]]:
    """
    Generate valid one-step successors involving self_country.

    Returns:
        list of (action_label, successor_world, participant_countries)
    """
    successors: list[tuple[str, WorldState, set[str]]] = []

    grown_world = growth(world)

    # Transforms for self only.
    for transform in transforms:
        try:
            next_world = apply_transform(grown_world, self_country, transform)
        except ValueError:
            continue

        label = _format_transform_action(self_country, transform)
        successors.append((label, next_world, {self_country}))

    # Transfers involving self and one other country.
    if transfer_resources is None:
        transfer_resources = []

    for other_country in grown_world.country_names():
        if other_country == self_country:
            continue

        for resource in transfer_resources:
            for amount in transfer_amounts:
                try:
                    next_world = apply_transfer(grown_world, self_country, other_country, resource, amount)
                    label = _format_transfer_action(self_country, other_country, resource, amount)
                    successors.append((label, next_world, {self_country, other_country}))
                except ValueError:
                    pass

                try:
                    next_world = apply_transfer(grown_world, other_country, self_country, resource, amount)
                    label = _format_transfer_action(other_country, self_country, resource, amount)
                    successors.append((label, next_world, {self_country, other_country}))
                except ValueError:
                    pass

    return successors


def _serialize_schedule(schedule: CompletedSchedule) -> str:
    lines = ["["]
    for step in schedule.actions:
        lines.append(f"  {step.label} EU: {step.eu:.6f}")
    lines.append("]")
    return "\n".join(lines)


def write_schedules(output_schedule_filename: str, schedules: Sequence[CompletedSchedule]) -> None:
    with open(output_schedule_filename, "w", encoding="utf-8") as f:
        for idx, schedule in enumerate(schedules, start=1):
            f.write(
                f"Schedule {idx} | Final EU: {schedule.eu:.6f} | "
                f"Discovery Order: {schedule.discovery_order}\n"
            )
            f.write(_serialize_schedule(schedule))
            f.write("\n\n")


def _trim_frontier(frontier: list[tuple[float, int, SearchNode]], frontier_max_size: int) -> None:
    """
    Keep only the best frontier_max_size nodes by EU.
    Frontier items are stored as (-eu, tie_break, node).
    Lower tuple values are better because EU is negated.
    """
    if frontier_max_size <= 0:
        raise ValueError("frontier_max_size must be > 0")

    if len(frontier) <= frontier_max_size:
        return

    frontier.sort(key=lambda item: item[0])
    del frontier[frontier_max_size:]


def country_scheduler(
    your_country_name: str,
    resources_filename: str,
    initial_state_filename: str,
    output_schedule_filename: str,
    num_output_schedules: int,
    depth_bound: int,
    frontier_max_size: int,
    *,
    world_start: WorldState,
    weights: ResourceWeights,
    transforms: Sequence[Transform],
    gamma: float,
    k: float,
    x0: float,
    C: float,
    transfer_resources: Sequence[str] | None = None,
    transfer_amounts: Sequence[float] = (1.0,),
) -> list[CompletedSchedule]:
    """
    Anytime, forward-searching, depth-bounded, utility-driven scheduler.

    Notes:
    - resources_filename and initial_state_filename are kept to preserve the project prototype.
    - This scheduler uses the provided world_start and weights directly.
    - Input loading should be handled by the existing parse layer before calling this function.
    """
    if num_output_schedules <= 0:
        raise ValueError("num_output_schedules must be > 0")
    if depth_bound < 0:
        raise ValueError("depth_bound must be >= 0")
    if frontier_max_size <= 0:
        raise ValueError("frontier_max_size must be > 0")
    if your_country_name not in world_start.countries:
        raise KeyError(f"Unknown self country: {your_country_name}")

    initial_eu = _score_node(
        world_start=world_start,
        node_world=world_start,
        self_country=your_country_name,
        participant_countries={your_country_name},
        weights=weights,
        gamma=gamma,
        depth=0,
        k=k,
        x0=x0,
        C=C,
    )

    root = SearchNode(
        world=world_start,
        actions=[],
        participant_countries={your_country_name},
        depth=0,
        eu=initial_eu,
    )

    frontier: list[tuple[float, int, SearchNode]] = []
    tie_break = 0
    heappush(frontier, (-root.eu, tie_break, root))
    tie_break += 1

    completed: list[CompletedSchedule] = []
    discovery_order = 0

    while frontier:
        _, _, current = heappop(frontier)

        if current.depth == depth_bound:
            discovery_order += 1
            completed.append(
                CompletedSchedule(
                    actions=current.actions.copy(),
                    final_world=current.world,
                    participant_countries=sorted(current.participant_countries),
                    eu=current.eu,
                    discovery_order=discovery_order,
                )
            )
            continue

        successors = generate_successors(
            current.world,
            your_country_name,
            transforms,
            transfer_resources=transfer_resources,
            transfer_amounts=transfer_amounts,
        )

        if not successors:
            # Dead-end path before depth bound: skip, unless you later decide
            # you want these retained as incomplete schedules.
            continue

        for action_label, next_world, new_participants in successors:
            next_depth = current.depth + 1
            participants = set(current.participant_countries) | set(new_participants)

            next_eu = _score_node(
                world_start=world_start,
                node_world=next_world,
                self_country=your_country_name,
                participant_countries=participants,
                weights=weights,
                gamma=gamma,
                depth=next_depth,
                k=k,
                x0=x0,
                C=C,
            )

            next_actions = current.actions + [ScheduledAction(label=action_label, eu=next_eu)]

            next_node = SearchNode(
                world=next_world,
                actions=next_actions,
                participant_countries=participants,
                depth=next_depth,
                eu=next_eu,
            )

            heappush(frontier, (-next_node.eu, tie_break, next_node))
            tie_break += 1

        _trim_frontier(frontier, frontier_max_size)

    completed.sort(key=lambda s: s.eu, reverse=True)
    best = completed[:num_output_schedules]
    write_schedules(output_schedule_filename, best)
    return best