"""
builds trinket strings
python build_combos.py
"""

import os
from itertools import combinations

# Load combos from trinkets.yml (simple mapping under 'combos').
# Try PyYAML then fallback to a minimal parser for this simple format.
combos = {}
cfg_path = os.path.join(os.path.dirname(__file__), "trinkets.yml")
raw_combos = {}
if os.path.exists(cfg_path):
    yaml_module = None
    try:
        import yaml as yaml_module
    except ImportError:
        yaml_module = None

    if yaml_module is not None:
        try:
            with open(cfg_path, "r", encoding="utf8") as fh:
                data = yaml_module.safe_load(fh)
                if isinstance(data, dict) and "combos" in data:
                    raw_combos = data["combos"] or {}
        except yaml_module.YAMLError:
            raw_combos = {}

    if not raw_combos:
        # Minimal fallback parser: lines with `key: "value"` under `combos:` -> raw mapping
        with open(cfg_path, "r", encoding="utf8") as fh:
            in_combos = False
            for line in fh:
                s = line.strip()
                if not s or s.startswith("#"):
                    continue
                if s.startswith("combos:"):
                    in_combos = True
                    continue
                if in_combos and ":" in s:
                    key, val = s.split(":", 1)
                    key = key.strip()
                    val = val.strip()
                    # remove surrounding quotes if present
                    if (val.startswith('"') and val.endswith('"')) or (
                        val.startswith("'") and val.endswith("'")
                    ):
                        val = val[1:-1]
                    raw_combos[key] = val

# Expand structured entries into flattened combos mapping expected by the rest of the script
for name, spec in raw_combos.items():
    # If the value is a mapping with id + ilevels, expand into per-ilevel entries
    if isinstance(spec, dict):
        item_id_val = spec.get("id")
        ilevels = spec.get("ilevels", []) or []
        for ilevel in ilevels:
            key = f"{name}_{ilevel}"
            # trinket names must not contain hyphens; fail early so charts stay valid
            if "-" in name:
                raise ValueError(
                    f"Invalid trinket name '{name}': hyphens are not allowed in trinket keys"
                )
            # build the simc base name: spaces -> underscore (do not alter hyphens here)
            simc_name = name.lower().replace(" ", "_")
            combos[key] = f"{simc_name},id={item_id_val},ilevel={ilevel}"
    else:
        # legacy/raw string; keep as-is
        combos[name] = spec


def item_id(trinket):
    """given a comma-separated definition for a trinket, returns just the id"""
    i = trinket.split(",")[1]
    return i[3:]


def build_combos():
    """generates the combination list with unique equipped trinkets only"""
    trinkets = combinations(combos.keys(), 2)
    unique_trinkets = []
    for pair in trinkets:
        # check if item id matches, trinkets are unique
        if item_id(combos[pair[0]]) != item_id(combos[pair[1]]):
            unique_trinkets.append(pair)
    print(f"Generated {len(unique_trinkets)} combinations.")
    return unique_trinkets


def build_simc_string(trinkets):
    """build profileset for each trinket combination"""
    result = ""
    for combo in trinkets:
        for trinket in combo:
            trinket_one = combo[0]
            trinket_two = combo[1]
            trinket_one_value = combos[trinket_one]
            trinket_two_value = combos[trinket_two]
            profileset_name = f"{trinket_one}-{trinket_two}"
            # TWW S3 Options
            if "Soleahs_Secret_Technique" in trinket:
                stat_type = trinket.split("_")[3].lower()
                result += f'profileset."{profileset_name}"+=shadowlands.soleahs_secret_technique_type={stat_type}\n'
            if "Astral_Antenna" in trinket:
                result += f'profileset."{profileset_name}"+=thewarwithin.astral_antenna_miss_chance=0.10\n'
            # TWW S2 Options
            if "Synergistic_Brewterializer" in trinket:
                result += f'profileset."{profileset_name}"+=priest.synergistic_brewterializer_tof_chance=0.90\n'
                result += f'profileset."{profileset_name}"+=priest.synergistic_brewterializer_barrel_hit_chance=0.75\n'
            # TWW S1 Options
            if "Unbound_Changeling" in trinket:
                stat_type = trinket.split("_")[2].lower()
                result += f'profileset."{profileset_name}"+=shadowlands.unbound_changeling_stat_type={stat_type}\n'
        result += f'profileset."{profileset_name}"+=trinket1={trinket_one_value}\n'
        result += f'profileset."{profileset_name}"+=trinket2={trinket_two_value}\n\n'
    return result


def generate_sim_file(input_string):
    """reads in the base simc file and creates the generated.simc file"""
    with open("base.simc", "r", encoding="utf8") as file:
        data = file.read()
        file.close()
    with open("generated.simc", "w+", encoding="utf8") as file:
        file.writelines(data)
        file.writelines(input_string)


if __name__ == "__main__":
    trinket_combos = build_combos()
    SIMC_STRING = build_simc_string(trinket_combos)
    generate_sim_file(SIMC_STRING)
