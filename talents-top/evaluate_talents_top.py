"""Compare selected talents-top builds across available fight types.

Default behavior:
- Picks baselines per hero from top results, config.yml, or explicit inputs.
- Adds any custom builds passed via --custom-builds.
- Writes a markdown report to talents-top/results.

Usage:
- Default run:
    python talents-top/evaluate_talents_top.py
- With custom builds and custom output file:
    python talents-top/evaluate_talents_top.py --custom-builds BUILD_A BUILD_B --output Build_Comparison_Custom.md
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
from dataclasses import dataclass
from pathlib import Path

import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_RESULTS_DIR = SCRIPT_DIR / "results"
HERO_PREFIXES = {"Archon": "AR_", "Voidweaver": "VW_"}
CONFIG_PATH = SCRIPT_DIR.parent / "config.yml"


@dataclass
class Row:
    actor: str
    dps: float
    rank: int


@dataclass
class HeroBaselines:
    dungeon: str | None
    t8: str | None
    source: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate talents-top builds across all available fight result files."
    )
    parser.add_argument(
        "--results-dir",
        default="results",
        help="Directory containing Results_*.csv files. Relative paths are resolved from talents-top/.",
    )
    parser.add_argument(
        "--custom-builds",
        nargs="*",
        default=[],
        help="Custom build names to include in the comparison.",
    )
    parser.add_argument(
        "--output",
        default="Build_Comparison_DungeonFocus.md",
        help="Output markdown filename (written under results-dir unless absolute path).",
    )
    parser.add_argument(
        "--high-key-dungeon-drop-threshold",
        type=float,
        default=5.0,
        help="If 8T winner loses more than this %% on dungeon profile, flag as high-key-only.",
    )
    parser.add_argument(
        "--baseline-mode",
        choices=["top", "config", "explicit"],
        default="top",
        help="How to choose per-hero baselines: top results, config.yml, or explicit args.",
    )
    parser.add_argument(
        "--preset",
        choices=["general-review", "high-key-review", "custom-only"],
        default="general-review",
        help="Controls which non-custom candidates are added per hero.",
    )
    parser.add_argument("--archon-dungeon-baseline", default=None)
    parser.add_argument("--archon-8t-baseline", default=None)
    parser.add_argument("--voidweaver-dungeon-baseline", default=None)
    parser.add_argument("--voidweaver-8t-baseline", default=None)
    return parser.parse_args()


def resolve_results_dir(results_dir_arg: str) -> Path:
    path = Path(results_dir_arg)
    if path.is_absolute():
        return path
    return SCRIPT_DIR / path


def load_config() -> dict:
    with CONFIG_PATH.open("r", encoding="utf8") as handle:
        return yaml.load(handle, Loader=yaml.FullLoader)


def load_config_recommendations(config: dict) -> dict[str, dict[str, str | None]]:
    return {
        "Archon": {
            "dungeon": config.get("builds", {})
            .get("archon", {})
            .get("talents", {})
            .get("dungeons", {})
            .get("name"),
            "8t": config.get("builds", {})
            .get("archon", {})
            .get("talents", {})
            .get("8t", {})
            .get("name"),
        },
        "Voidweaver": {
            "dungeon": config.get("builds", {})
            .get("voidweaver", {})
            .get("talents", {})
            .get("dungeons", {})
            .get("name"),
            "8t": config.get("builds", {})
            .get("voidweaver", {})
            .get("talents", {})
            .get("8t", {})
            .get("name"),
        },
    }


def load_results(results_dir: Path) -> dict[str, list[Row]]:
    data: dict[str, list[Row]] = {}
    for csv_path in sorted(results_dir.glob("Results_*.csv")):
        fight = csv_path.stem.replace("Results_", "")
        rows: list[Row] = []
        with csv_path.open("r", encoding="utf8", newline="") as handle:
            reader = csv.DictReader(handle)
            for i, row in enumerate(reader, start=1):
                actor = (row.get("actor") or "").strip()
                dps_raw = (row.get("DPS") or "0").replace(",", "")
                if not actor:
                    continue
                rows.append(Row(actor=actor, dps=float(dps_raw), rank=i))
        if rows:
            data[fight] = rows
    return data


def find_dungeon_fight(data: dict[str, list[Row]]) -> str:
    preferred = ["Dungeons-Slice", "Dungeons-Route"]
    for fight in preferred:
        if fight in data:
            return fight

    dungeon_like = sorted([name for name in data if name.startswith("Dungeons-")])
    if dungeon_like:
        return dungeon_like[0]

    raise ValueError(
        "No dungeon results file found. Expected Results_Dungeons-Slice.csv or Results_Dungeons-Route.csv."
    )


def get_top_actor(data: dict[str, list[Row]], fight: str) -> str | None:
    rows = data.get(fight, [])
    if not rows:
        return None
    return rows[0].actor


def get_top_actor_for_prefix(
    data: dict[str, list[Row]], fight: str, hero_prefix: str
) -> str | None:
    rows = data.get(fight, [])
    for row in rows:
        if row.actor.startswith(hero_prefix):
            return row.actor
    return None


def get_top_n_actors_for_prefix(
    data: dict[str, list[Row]],
    fight: str,
    hero_prefix: str,
    n: int = 1,
) -> list[str]:
    rows = data.get(fight, [])
    out: list[str] = []
    for row in rows:
        if row.actor.startswith(hero_prefix):
            out.append(row.actor)
            if len(out) >= n:
                break
    return out


def build_index(data: dict[str, list[Row]]) -> dict[str, dict[str, Row]]:
    by_actor_by_fight: dict[str, dict[str, Row]] = {}
    for fight, rows in data.items():
        for row in rows:
            by_actor_by_fight.setdefault(row.actor, {})[fight] = row
    return by_actor_by_fight


def build_hero_rank_index(
    data: dict[str, list[Row]],
    hero_prefix: str,
) -> dict[str, dict[str, int]]:
    out: dict[str, dict[str, int]] = {}
    for fight, rows in data.items():
        hero_rows = [row for row in rows if row.actor.startswith(hero_prefix)]
        hero_total = len(hero_rows)
        fight_rank: dict[str, int] = {}
        for hero_rank, row in enumerate(hero_rows, start=1):
            fight_rank[row.actor] = hero_rank
        fight_rank["__total__"] = hero_total
        out[fight] = fight_rank
    return out


def ordered_unique(items: list[str]) -> list[str]:
    seen = set()
    out: list[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            out.append(item)
    return out


def get_fight_order(data: dict[str, list[Row]], dungeon_fight: str) -> list[str]:
    preferred = [dungeon_fight, "8T", "3T", "2T", "Single", "Composite"]
    ordered = [fight for fight in preferred if fight in data]
    remaining = sorted([fight for fight in data if fight not in ordered])
    ordered.extend(remaining)
    return ordered


def fmt_cell(
    actor_data: dict[str, Row],
    fight: str,
    top_dps: float,
    hero_rank_index: dict[str, dict[str, int]],
    actor: str,
) -> str:
    row = actor_data.get(fight)
    if not row:
        return "N/A"
    pct_vs_top = ((row.dps / top_dps) - 1.0) * 100.0
    hero_total = hero_rank_index.get(fight, {}).get("__total__", 0)
    hero_rank = hero_rank_index.get(fight, {}).get(actor)
    if hero_rank and hero_total:
        return f"{row.dps:,.0f} (#{hero_rank}/{hero_total}, {pct_vs_top:+.2f}%)"
    return f"{row.dps:,.0f} (N/A, {pct_vs_top:+.2f}%)"


def pct_delta(new: float, base: float) -> float:
    return ((new / base) - 1.0) * 100.0


def recommend_builds(
    selected_builds: list[str],
    index: dict[str, dict[str, Row]],
    dungeon_fight: str,
    high_key_drop_threshold: float,
) -> dict[str, str]:
    dungeon_candidates = [
        b for b in selected_builds if b in index and dungeon_fight in index[b]
    ]
    t8_candidates = [b for b in selected_builds if b in index and "8T" in index[b]]

    if not dungeon_candidates:
        raise ValueError("None of the selected builds exist in dungeon fight results.")

    general = max(dungeon_candidates, key=lambda b: index[b][dungeon_fight].dps)

    if not t8_candidates:
        return {
            "general": general,
            "high_key": "",
            "note": "No 8T results available; high-key recommendation not generated.",
        }

    high_key = max(t8_candidates, key=lambda b: index[b]["8T"].dps)

    if high_key == general:
        return {
            "general": general,
            "high_key": "",
            "note": "Same build wins both dungeon baseline and 8T.",
        }

    general_dungeon = index[general][dungeon_fight].dps
    high_key_dungeon = index[high_key].get(dungeon_fight)
    high_key_8t = index[high_key]["8T"].dps
    general_8t = index[general].get("8T")

    drop_text = "unknown"
    if high_key_dungeon:
        drop = pct_delta(high_key_dungeon.dps, general_dungeon)
        drop_text = f"{drop:+.2f}%"

    gain_text = "unknown"
    if general_8t:
        gain = pct_delta(high_key_8t, general_8t.dps)
        gain_text = f"{gain:+.2f}%"

    usage_note = ""
    if high_key_dungeon:
        drop = pct_delta(high_key_dungeon.dps, general_dungeon)
        if drop <= -abs(high_key_drop_threshold):
            usage_note = (
                "Use as high-key/trash-heavy optional build only; dungeon baseline loss is severe."
            )
        elif drop < 0:
            usage_note = "Use as optional build when AoE is prioritized."
        else:
            usage_note = "Safe to use broadly; no dungeon baseline penalty detected."

    note = (
        f"8T swing vs general: {gain_text}; {dungeon_fight} swing vs general: {drop_text}. "
        f"{usage_note}".strip()
    )

    return {"general": general, "high_key": high_key, "note": note}


def get_explicit_baselines(args: argparse.Namespace, hero_name: str) -> HeroBaselines:
    if hero_name == "Archon":
        return HeroBaselines(
            dungeon=args.archon_dungeon_baseline,
            t8=args.archon_8t_baseline,
            source="explicit",
        )
    return HeroBaselines(
        dungeon=args.voidweaver_dungeon_baseline,
        t8=args.voidweaver_8t_baseline,
        source="explicit",
    )


def choose_hero_baselines(
    hero_name: str,
    hero_prefix: str,
    args: argparse.Namespace,
    data: dict[str, list[Row]],
    dungeon_fight: str,
    config_recs: dict[str, dict[str, str | None]],
    index: dict[str, dict[str, Row]],
) -> tuple[HeroBaselines, list[str]]:
    notes: list[str] = []

    top_baselines = HeroBaselines(
        dungeon=get_top_actor_for_prefix(data, dungeon_fight, hero_prefix),
        t8=get_top_actor_for_prefix(data, "8T", hero_prefix),
        source="top",
    )
    config_baselines = HeroBaselines(
        dungeon=config_recs.get(hero_name, {}).get("dungeon"),
        t8=config_recs.get(hero_name, {}).get("8t"),
        source="config",
    )
    explicit_baselines = get_explicit_baselines(args, hero_name)

    if args.baseline_mode == "top":
        chosen = top_baselines
    elif args.baseline_mode == "config":
        chosen = HeroBaselines(
            dungeon=config_baselines.dungeon or top_baselines.dungeon,
            t8=config_baselines.t8 or top_baselines.t8,
            source="config",
        )
        if not config_baselines.dungeon:
            notes.append("Config dungeon baseline missing; fell back to top dungeon baseline.")
        if not config_baselines.t8:
            notes.append("Config 8T baseline missing; fell back to top 8T baseline.")
    else:
        chosen = HeroBaselines(
            dungeon=explicit_baselines.dungeon or config_baselines.dungeon or top_baselines.dungeon,
            t8=explicit_baselines.t8 or config_baselines.t8 or top_baselines.t8,
            source="explicit",
        )
        if not explicit_baselines.dungeon:
            notes.append("Explicit dungeon baseline not provided; fell back to config/top.")
        if not explicit_baselines.t8:
            notes.append("Explicit 8T baseline not provided; fell back to config/top.")

    if chosen.dungeon and chosen.dungeon not in index:
        notes.append(f"Selected dungeon baseline not found in results: {chosen.dungeon}")
    if chosen.t8 and chosen.t8 not in index:
        notes.append(f"Selected 8T baseline not found in results: {chosen.t8}")

    return chosen, notes


def get_preset_candidates(
    preset: str,
    data: dict[str, list[Row]],
    hero_prefix: str,
    dungeon_fight: str,
) -> list[str]:
    if preset == "custom-only":
        return []
    if preset == "high-key-review":
        candidates: list[str] = []
        candidates.extend(get_top_n_actors_for_prefix(data, "8T", hero_prefix, n=2))
        candidates.extend(get_top_n_actors_for_prefix(data, "3T", hero_prefix, n=2))
        candidates.extend(get_top_n_actors_for_prefix(data, "2T", hero_prefix, n=2))
        candidates.extend(get_top_n_actors_for_prefix(data, dungeon_fight, hero_prefix, n=1))
        return ordered_unique(candidates)

    # general-review
    candidates = []
    candidates.extend(get_top_n_actors_for_prefix(data, dungeon_fight, hero_prefix, n=1))
    candidates.extend(get_top_n_actors_for_prefix(data, "8T", hero_prefix, n=1))
    return ordered_unique(candidates)


def build_delta_text(
    candidate_build: str,
    base_build: str,
    fights: list[str],
    index: dict[str, dict[str, Row]],
) -> str:
    segments: list[str] = []
    for fight in fights:
        candidate_row = index.get(candidate_build, {}).get(fight)
        base_row = index.get(base_build, {}).get(fight)
        if not candidate_row or not base_row:
            continue
        delta = pct_delta(candidate_row.dps, base_row.dps)
        segments.append(f"{fight} {delta:+.2f}%")
    if not segments:
        return "No overlap with baseline fights."
    return ", ".join(segments)


def render_report(
    output_path: Path,
    data: dict[str, list[Row]],
    custom_builds: list[str],
    dungeon_fight: str,
    high_key_drop_threshold: float,
    args: argparse.Namespace,
    config_recs: dict[str, dict[str, str | None]],
) -> None:
    index = build_index(data)
    fights = get_fight_order(data, dungeon_fight)
    custom_found = [build for build in custom_builds if build in index]
    custom_missing = [build for build in custom_builds if build not in index]
    custom_unknown_prefix = [
        build
        for build in custom_builds
        if not any(build.startswith(prefix) for prefix in HERO_PREFIXES.values())
    ]

    lines: list[str] = []
    lines.append("# Talents-Top Build Comparison")
    lines.append("")
    lines.append(f"Generated: {dt.datetime.now(tz=dt.UTC).date().isoformat()}")
    lines.append(f"Results directory: {output_path.parent}")
    lines.append("")
    lines.append("## Selection Logic")
    lines.append(f"- Dungeon baseline fight: {dungeon_fight}")
    lines.append(f"- Baseline mode: {args.baseline_mode}")
    lines.append(f"- Candidate preset: {args.preset}")
    lines.append("- Recommendations are evaluated among selected builds per hero (not all builds).")
    if custom_builds:
        lines.append("- Custom builds included:")
        for build in custom_builds:
            lines.append(f"  - {build}")
    else:
        lines.append("- Custom builds included: none")
    lines.append("")

    lines.append("## Diagnostics")
    lines.append(f"- Custom builds found in results: {len(custom_found)}")
    lines.append(f"- Custom builds missing from results: {len(custom_missing)}")
    lines.append(f"- Custom builds with unknown hero prefix: {len(custom_unknown_prefix)}")
    if custom_missing:
        lines.append("- Missing custom builds:")
        for build in custom_missing:
            lines.append(f"  - {build}")
    if custom_unknown_prefix:
        lines.append("- Unknown-prefix custom builds:")
        for build in custom_unknown_prefix:
            lines.append(f"  - {build}")
    lines.append("")

    for hero_name, hero_prefix in HERO_PREFIXES.items():
        hero_rank_index = build_hero_rank_index(data, hero_prefix)
        hero_baselines, baseline_notes = choose_hero_baselines(
            hero_name,
            hero_prefix,
            args,
            data,
            dungeon_fight,
            config_recs,
            index,
        )

        hero_custom_builds = [
            build for build in custom_builds if build.startswith(hero_prefix)
        ]
        preset_candidates = get_preset_candidates(
            args.preset, data, hero_prefix, dungeon_fight
        )
        selected_builds = ordered_unique(
            [hero_baselines.dungeon or "", hero_baselines.t8 or ""]
            + preset_candidates
            + hero_custom_builds
        )
        selected_builds = [build for build in selected_builds if build in index]

        if not selected_builds:
            lines.append(f"## {hero_name}")
            lines.append("- No builds found for this hero in the current result files.")
            lines.append("")
            continue

        recommendation = recommend_builds(
            selected_builds,
            index,
            dungeon_fight,
            high_key_drop_threshold,
        )

        lines.append(f"## {hero_name}")
        lines.append(f"- Baseline source: {hero_baselines.source}")
        lines.append(f"- Selected dungeon baseline: {hero_baselines.dungeon or 'not found'}")
        lines.append(f"- Selected 8T baseline: {hero_baselines.t8 or 'not found'}")
        if baseline_notes:
            lines.append("- Baseline notes:")
            for note in baseline_notes:
                lines.append(f"  - {note}")

        lines.append("- Compared builds:")
        for build in selected_builds:
            lines.append(f"  - {build}")
        lines.append("")

        header = "| Build | " + " | ".join(fights) + " |"
        divider = "|---|" + "|".join(["---:" for _ in fights]) + "|"
        lines.append("### Cross-Fight Results")
        lines.append(
            "Cell format: DPS (#hero_rank/hero_total, % vs top build for this hero/fight)"
        )
        lines.append("")
        lines.append(header)
        lines.append(divider)

        for build in selected_builds:
            actor_data = index.get(build, {})
            cells: list[str] = []
            for fight in fights:
                fight_rows = data[fight]
                top_hero_dps = next(
                    (
                        row.dps
                        for row in fight_rows
                        if row.actor.startswith(hero_prefix)
                    ),
                    fight_rows[0].dps,
                )
                cells.append(
                    fmt_cell(
                        actor_data,
                        fight,
                        top_hero_dps,
                        hero_rank_index,
                        build,
                    )
                )
            lines.append(f"| {build} | " + " | ".join(cells) + " |")

        lines.append("")
        current_recommendation = config_recs.get(hero_name, {}).get("dungeon")
        lines.append("### Delta vs Current Recommendation (config.yml)")
        lines.append(
            f"- Current recommendation baseline: {current_recommendation or 'not found'}"
        )
        if current_recommendation and current_recommendation in index:
            for build in selected_builds:
                if build == current_recommendation:
                    continue
                delta_text = build_delta_text(
                    build,
                    current_recommendation,
                    fights,
                    index,
                )
                lines.append(f"- {build}: {delta_text}")
        else:
            lines.append("- Unable to compute deltas because current recommendation is missing in results.")

        lines.append("")
        lines.append("### Recommendation")
        lines.append("- Scope: evaluated among selected builds for this hero.")
        lines.append(f"- General dungeon build: {recommendation['general']}")
        if recommendation.get("high_key"):
            lines.append(f"- High-key optional build: {recommendation['high_key']}")
        lines.append(f"- Reasoning: {recommendation['note']}")
        lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf8")


def main() -> None:
    args = parse_args()
    config = load_config()
    config_recs = load_config_recommendations(config)
    results_dir = resolve_results_dir(args.results_dir)

    if not results_dir.exists():
        raise FileNotFoundError(f"Results directory not found: {results_dir}")

    data = load_results(results_dir)
    if not data:
        raise ValueError(f"No Results_*.csv files found in {results_dir}")

    dungeon_fight = find_dungeon_fight(data)
    output_arg = Path(args.output)
    if output_arg.is_absolute():
        output_path = output_arg
    else:
        output_path = results_dir / output_arg

    render_report(
        output_path=output_path,
        data=data,
        custom_builds=args.custom_builds,
        dungeon_fight=dungeon_fight,
        high_key_drop_threshold=args.high_key_dungeon_drop_threshold,
        args=args,
        config_recs=config_recs,
    )

    print(f"Wrote report to {output_path}")


if __name__ == "__main__":
    main()