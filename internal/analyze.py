"""creates results files from sim results"""

import json
import operator
import os
import re
import time

import pandas
import yaml

from internal import utils
from internal.spell_ids import find_ids
from internal.weights import find_weights

with open("config.yml", "r", encoding="utf8") as ymlfile:
    config = yaml.load(ymlfile, Loader=yaml.FullLoader)


def discover_step_suffixes(results):
    """Discover numeric step suffixes from actor names like Name_285."""
    discovered = set()
    for actor_name in results:
        match = re.search(r"_(\d+)$", str(actor_name))
        if match:
            discovered.add(int(match.group(1)))
    return sorted(discovered)


def resolve_sim_steps(directory, results):
    """Resolve configured steps, with auto-discovery support for trinkets."""
    sim_name = directory[:-1]
    configured_steps = config["sims"][sim_name].get("steps", [])

    # Trinkets can mix multiple item level pools (raid/dungeons/other).
    # Discovering from actual result actor names removes the need to hardcode steps.
    if sim_name == "trinkets":
        discovered_steps = discover_step_suffixes(results)
        if discovered_steps:
            return discovered_steps

        # No numeric suffixes means single-step labels (e.g. plain actor names).
        # Keep this path working even when trinket steps are removed from config.
        if not configured_steps:
            return ["DPS"]

    return configured_steps


def assure_path_exists(path):
    """Make sure the path exists and contains a folder"""
    dir_name = os.path.dirname(path)
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)


def build_output_string(sim_type, talent_string, file_type, dungeons):
    """creates output string for the results file"""
    output_dir = "results/"
    if dungeons:
        output_dir += "dungeons/"
        if "standard" in sim_type:
            output_dir += "standard/"
        elif "push" in sim_type:
            output_dir += "push/"
    assure_path_exists(output_dir)
    output_string = f"{output_dir}Results_{sim_type}{talent_string}.{file_type}"
    return output_string


def get_change(current, previous):
    """gets the percent change between two numbers"""
    negative = 0
    if current < previous:
        negative = True
    try:
        value = (abs(current - previous) / previous) * 100.0
        value = round(value, 2)
        if value >= 0.01 and negative:
            value = value * -1
        return value
    except ZeroDivisionError:
        return 0


def find_weight(sim_type, profile_name, dungeons):
    """looks up the weight based on the sim type"""
    weight_type = ""
    if sim_type == "Composite":
        weight_type = "compositeWeights"
    elif sim_type == "Single":
        weight_type = "singleTargetWeights"
    elif sim_type == "2T":
        weight_type = "twoTargetWeights"
    elif sim_type == "3T":
        weight_type = "threeTargetWeights"
    elif sim_type == "4T":
        weight_type = "fourTargetWeights"
    elif sim_type == "8T":
        weight_type = "eightTargetWeights"
    elif sim_type == "Dungeons-Standard":
        weight_type = "dungeonStandardWeights"
    elif sim_type == "Dungeons-Push" or sim_type == "Dungeons-Route":
        weight_type = "dungeonPushWeights"
    elif sim_type == "Dungeons-Slice":
        weight = 1
        return weight
    elif dungeons:
        if sim_type == profile_name:
            weight = 1
        else:
            weight = 0
        return weight
    if weight_type == "":
        print(f"error: no weight type. {sim_type}, {profile_name}, {dungeons}")
    weight = find_weights(config[weight_type]).get(profile_name)
    if not weight:
        return 0
    return weight


def get_number_of_profiles(dir_name):
    """support talents having a dynamic number of base profiles"""
    if dir_name == "talents":
        return len(os.listdir("builds/"))
    else:
        return len(config["sims"][dir_name]["files"])


def build_results(data, weights, sim_type, directory, dungeons):
    """create results dict from sim data"""
    results = {}
    for value in data.iterrows():
        actor = value[1].actor
        # APL sims can emit a lowercase baseline actor name.
        if str(actor).lower() == "base":
            actor = "Base"
        if "Dungeons" in sim_type or dungeons:
            fight_style = value[1].profile.split("_")[-1]
        else:
            fight_style = re.search(
                "((hm|lm|pw).*|dungeons$)", value[1].profile
            ).group()
        weight = find_weight(sim_type, fight_style, dungeons)
        weighted_dps = value[1].DPS * weight
        if weights:
            intellect = value[1].int
            haste = value[1].haste / intellect * weight
            crit = value[1].crit / intellect * weight
            mastery = value[1].mastery / intellect * weight
            vers = value[1].vers / intellect * weight
            wdps = 1 / intellect * weight
            existing = results.get(actor, {})
            results[actor] = {
                "dps": existing.get("dps", 0) + weighted_dps,
                "intellect": existing.get("intellect", 0) + weight,
                "haste": existing.get("haste", 0) + haste,
                "crit": existing.get("crit", 0) + crit,
                "mastery": existing.get("mastery", 0) + mastery,
                "vers": existing.get("vers", 0) + vers,
                "wdps": existing.get("wdps", 0) + wdps,
            }
        else:
            results[actor] = results.get(actor, 0) + weighted_dps
    # Each profile sims "Base" again so we need to divide that to get the real average
    number_of_profiles = get_number_of_profiles(directory[:-1])
    base_actor = results.get("Base")
    if base_actor is None:
        if weights:
            base_actor = {
                "dps": 0,
                "intellect": 0,
                "haste": 0,
                "crit": 0,
                "mastery": 0,
                "vers": 0,
                "wdps": 0,
            }
        else:
            base_actor = 0
    if weights:
        base_dps = {}
        for key, value in base_actor.items():
            base_dps[key] = value / number_of_profiles
    else:
        base_dps = base_actor / number_of_profiles
    results["Base"] = base_dps
    return results


def generate_report_name(sim_type, talent_string):
    """create report name based on talents"""
    stripped_talents = talent_string.strip("_")
    talents = f" - {stripped_talents}" if talent_string else ""
    return f"{sim_type}{talents}"


def build_markdown(sim_type, talent_string, results, weights, base_dps, dungeons):
    """converts result data into markdown files"""
    output_file = build_output_string(sim_type, talent_string, "md", dungeons)
    report_name = generate_report_name(sim_type, talent_string)
    with open(output_file, "w+", encoding="utf8") as results_md:
        if weights:
            results_md.write(
                f"# {report_name}\n| Actor | DPS | Int | Haste | Crit | Mastery | Vers | DPS Weight "
                "|\n|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|\n"
            )
            # Take the dict of dicts and created a new dict to be able to sort our keys
            actor_dps = {}
            for key, value in results.items():
                actor_dps[key] = value.get("dps")
            # sort the keys in the actor_dps dict by the dps value
            # use that key to lookup the actual dict of values
            for key, value in sorted(
                actor_dps.items(), key=operator.itemgetter(1), reverse=True
            ):
                results_md.write(
                    f"|{key}|{results[key].get('dps'):.0f}|"
                    f"{results[key].get('intellect'):.2f}|"
                    f"{results[key].get('haste'):.2f}|"
                    f"{results[key].get('crit'):.2f}|"
                    f"{results[key].get('mastery'):.2f}|"
                    f"{results[key].get('vers'):.2f}|"
                    f"{results[key].get('wdps'):.2f}|\n"
                )
        else:
            results_md.write(
                f"# {report_name}\n| Actor | DPS | Increase |\n|---|:---:|:---:|\n"
            )
            for key, value in sorted(
                results.items(), key=operator.itemgetter(1), reverse=True
            ):
                results_md.write(f"|{key}|{value:.0f}|{get_change(value, base_dps):.2f}%|\n")


def build_csv(sim_type, talent_string, results, weights, base_dps, dungeons):
    """build csv from results dict"""
    output_file = build_output_string(sim_type, talent_string, "csv", dungeons)
    with open(output_file, "w", encoding="utf8") as results_csv:
        if weights:
            results_csv.write("profile,actor,DPS,int,haste,crit,mastery,vers,dpsW,\n")
            # Take the dict of dicts and created a new dict to be able to sort our keys
            actor_dps = {}
            for key, value in results.items():
                actor_dps[key] = value.get("dps")
            # sort the keys in the actor_dps dict by the dps value
            # use that key to lookup the actual dict of values
            for key, value in sorted(
                actor_dps.items(), key=operator.itemgetter(1), reverse=True
            ):
                results_csv.write(
                    f"{sim_type},{key},{results[key].get('dps'):.0f},"
                    f"{results[key].get('intellect'):.2f},"
                    f"{results[key].get('haste'):.2f},"
                    f"{results[key].get('crit'):.2f},"
                    f"{results[key].get('mastery'):.2f},"
                    f"{results[key].get('vers'):.2f},"
                    f"{results[key].get('wdps'):.2f},\n"
                )
        else:
            results_csv.write("profile,actor,DPS,increase,\n")
            for key, value in sorted(
                results.items(), key=operator.itemgetter(1), reverse=True
            ):
                results_csv.write(
                    f"{sim_type},{key},{value:.0f},{get_change(value, base_dps):.2f}%,\n"
                )


def lookup_id(name, directory):
    """lookup the spell or item id of an item name"""
    lookup_type = config["sims"][directory[:-1]]["lookupType"]
    if lookup_type == "spell":
        return lookup_spell_id(name, directory)
    if lookup_type == "item":
        return lookup_item_id(name, directory)
    if lookup_type == "none":
        return None
    print(f"Could not find id for {name}")
    return None


def lookup_spell_id(spell_name, directory):
    """lookup a spell name from the ids dict"""
    if directory == "special-gear/":
        spell_name = re.sub(r"_\d+$", "", spell_name)
    ids = find_ids(directory[:-1])
    if ids:
        return ids.get(spell_name)
    print(f"Could not find spell id for {spell_name}")
    return None


# TODO: this will break on talents/ having dynamic files
def lookup_item_id(item_name, directory):
    """
    get the list of sim files from config
    loop over them and search for the item name line by line
    """
    for sim_file in config["sims"][directory[:-1]]["files"]:
        with open(sim_file, "r", encoding="utf8") as file:
            for line in file:
                if item_name in line and "id=" in line:
                    # find ,id= -> take 2nd half ->
                    # find , -> take 1st half
                    return int(line.split(",id=")[1].split(",")[0])
    return None


def build_json(sim_type, talent_string, results, directory, timestamp, dungeons):
    """build json from results"""
    output_file = build_output_string(sim_type, talent_string, "json", dungeons)
    human_date = time.strftime("%Y-%m-%d", time.localtime(timestamp))
    chart_data = {
        "name": generate_report_name(sim_type, talent_string),
        "data": {},
        "ids": {},
        "simulated_steps": [],
        "sorted_data_keys": [],
        "last_updated": human_date,
    }
    # check steps in config
    # for each profile, try to find every step
    # if found put in unique dict
    steps = resolve_sim_steps(directory, results)
    number_of_steps = len(steps)

    # If we're analyzing the trinket-combos directory, populate ids
    # directly from trinkets.yml so charts can reference item ids.
    if directory[:-1] == "trinket-combos":
        try:
            with open("trinkets.yml", "r", encoding="utf8") as fh:
                tdata = yaml.safe_load(fh) or {}
                tcombos = tdata.get("combos", {})
                for tname, tspec in tcombos.items():
                    # structured spec: { id: <num>, ilevels: [..] }
                    if isinstance(tspec, dict):
                        tid = tspec.get("id")
                        # Store id by base trinket name (ignore ilevels)
                        if tid is not None:
                            chart_data["ids"][tname] = int(tid)
                    else:
                        # legacy flat mapping: value is simc string containing id
                        try:
                            tid = int(str(tspec).split(",id=")[1].split(",")[0])
                            chart_data["ids"][tname] = tid
                        except (TypeError, ValueError, IndexError):
                            # ignore parse errors
                            pass
        except FileNotFoundError:
            # no trinkets.yml present; skip
            pass

    # if there is only 1 step, we can just go right to iterating
    if number_of_steps == 1:
        chart_data["simulated_steps"] = ["DPS"]
        for key, value in sorted(
            results.items(), key=operator.itemgetter(1), reverse=True
        ):
            chart_data["data"][key] = {"DPS": int(round(value, 0))}
            if key != "Base":
                chart_data["sorted_data_keys"].append(key)
                chart_data["ids"][key] = lookup_id(key, directory)
    else:
        unique_profiles = []
        chart_data["simulated_steps"] = steps
        # iterate over results and build a list of unique profiles
        # trim off everything after last _
        for key, value in sorted(
            results.items(), key=operator.itemgetter(1), reverse=True
        ):
            unique_key = "_".join(key.split("_")[:-1])
            if (
                unique_key not in unique_profiles
                and unique_key != "Base"
                and unique_key != ""
            ):
                unique_profiles.append(unique_key)
                chart_data["sorted_data_keys"].append(unique_key)
                chart_data["ids"][unique_key] = lookup_id(unique_key, directory)
        for profile in unique_profiles:
            chart_data["data"][profile] = {}
            steps.sort(reverse=True)
            # Make sure that the steps in the json are from highest to lowest
            for step in steps:
                for key, value in sorted(
                    results.items(), key=operator.itemgetter(1), reverse=True
                ):
                    # split off the key to get the step
                    # key: Trinket_415 would turn into 415
                    key_step = key.split("_")[len(key.split("_")) - 1]
                    # trim off _415 which is key_step + 1 char for the _
                    offset = (len(key_step) + 1) * -1
                    key_name = key[:offset]
                    if profile == key_name and str(key_step) == str(step):
                        chart_data["data"][profile][step] = int(round(value, 0))
        # Base isn't in unique_profiles so we handle that explicitly
        chart_data["data"]["Base"] = {}
        chart_data["data"]["Base"]["DPS"] = int(round(results.get("Base"), 0))
    json_data = json.dumps(chart_data)
    with open(output_file, "w", encoding="utf8") as results_json:
        results_json.write(json_data)


def convert_increase_to_double(increase):
    """convert string increase to double"""
    increase = increase.strip("%")
    increase = round(float(increase), 4)
    if increase:
        increase = round(increase / 100, 4)
    return increase


def not_dungeon_fight(fight_type):
    """checks if fight_type is a specific dungeon one"""
    non_dungeon_fights = [
        "Composite",
        "Single",
        "Dungeons-Push",
        "Dungeons-Standard",
        "Dungeons-Route",
        "Dungeons-Slice",
        "2T",
        "3T",
        "4T",
        "8T",
    ]
    return fight_type in non_dungeon_fights


def clear_dir(path, talent_string, fight_types):
    """clear out unused files that are not in the current run"""
    if not os.path.isdir(path):
        return
    for file in os.listdir(path):
        # ignore the sub-folders
        if file == "dungeons" or file == "push" or file == "standard":
            continue
        file_to_delete = path + "/" + file
        output_files = []
        if talent_string:
            for talent in config["builds"]:
                for fight_type in fight_types:
                    dungeonChartsGen = config["analyze"][
                        "dungeonCharts"
                    ] or not_dungeon_fight(fight_type)
                    if config["analyze"]["markdown"]:
                        output_files.append(f"{path}/Results_{fight_type}_{talent}.md")
                    if config["analyze"]["csv"] and (
                        dungeonChartsGen or path == "talents/"
                    ):
                        output_files.append(f"{path}/Results_{fight_type}_{talent}.csv")
                    if config["analyze"]["json"] and dungeonChartsGen:
                        output_files.append(
                            f"{path}/Results_{fight_type}_{talent}.json"
                        )
        else:
            for fight_type in fight_types:
                if config["analyze"]["markdown"]:
                    output_files.append(f"{path}/Results_{fight_type}.md")
                if config["analyze"]["csv"]:
                    output_files.append(f"{path}/Results_{fight_type}.csv")
                if config["analyze"]["json"]:
                    output_files.append(f"{path}/Results_{fight_type}.json")
        if file_to_delete not in output_files and os.path.exists(file_to_delete):
            os.remove(file_to_delete)


def clear_output_files(talent_string):
    """after all results are built clear out unused files"""
    dungeon_fights = utils.get_dungeon_combos()

    clear_dir(
        "results",
        talent_string,
        utils.get_sim_types(),
    )
    # Check if this needs to be adjusted to clear out the Slice fights
    clear_dir("results/dungeons/push", talent_string, dungeon_fights)
    clear_dir("results/dungeons/standard", talent_string, dungeon_fights)
    clear_dir("results/dungeons", talent_string, dungeon_fights)


def generate_result_name(result, talent):
    """takes a full result file path and generate a readable name from it"""
    fight_types = ["Composite", "Single", "Dungeons", "2T", "8T"]
    fight_types.append(str(config["councilTargets"]) + "T")
    for fight_type in fight_types:
        if fight_type in result:
            return f"{fight_type} - {talent.upper()}"
    return talent


def build_readme_md(directory, talent_string):
    """builds README.md in for each set of results"""
    with open("README.md", "w+", encoding="utf8") as readme:
        readme.write(f"# {directory[:-1]} Results\n")
        if talent_string:
            for talent in config["builds"]:
                readme.write(f"## {talent.upper()}\n")
                file_list = []
                for fight_type in utils.get_sim_types():
                    file_list.append(f"results/Results_{fight_type}_{talent}.md")
                for result in file_list:
                    result_name = generate_result_name(result, talent)
                    readme.write(f"- [{result_name}]({result})\n")
        else:
            file_list = []
            for fight_type in utils.get_sim_types():
                file_list.append(f"results/Results_{fight_type}.md")
            for result in file_list:
                readme.write(f"- [{result[16:-3]}]({result})\n")


def analyze(talents, directory, dungeons, weights, timestamp):
    """main analyze function"""
    foldername = os.path.basename(os.getcwd())
    # Move to correct outer folder
    while foldername != directory[:-1]:
        os.chdir("..")
        foldername = os.path.basename(os.getcwd())
    csv = f"{utils.get_simc_dir(talents, 'output', dungeons)}statweights.csv"

    if weights:
        data = pandas.read_csv(
            csv,
            usecols=[
                "profile",
                "actor",
                "DD",
                "DPS",
                "int",
                "haste",
                "crit",
                "mastery",
                "vers",
            ],
        )
    else:
        data = pandas.read_csv(csv, usecols=["profile", "actor", "DD", "DPS"])

    fights = ["Composite", "Single", "2T", "8T"]
    fights.append(str(config["councilTargets"]) + "T")

    talent_string = f"_{talents}" if talents else ""
    if config["dungeonType"] == "route":
        dungeon_list = ["Dungeons-Route"]
    elif config["dungeonType"] == "slice":
        dungeon_list = ["Dungeons-Slice"]
    sim_types = dungeon_list if dungeons else fights

    # Main Composites
    for sim_type in sim_types:
        results = build_results(data, weights, sim_type, directory, False)
        base_dps = results.get("Base")
        if config["analyze"]["markdown"]:
            build_markdown(sim_type, talent_string, results, weights, base_dps, False)
        if config["analyze"]["csv"]:
            build_csv(sim_type, talent_string, results, weights, base_dps, False)
        if config["analyze"]["json"] and not weights:
            build_json(sim_type, talent_string, results, directory, timestamp, False)

    # Individual Dungeons
    if dungeons:
        combinations = utils.get_dungeon_combos()

        for combo in combinations:
            results = build_results(data, weights, combo, directory, True)
            base_dps = results.get("Base")
            if config["analyze"]["markdown"]:
                build_markdown(combo, talent_string, results, weights, base_dps, True)
            # always build talent csv for top.py
            if config["analyze"]["csv"] and (
                config["analyze"]["dungeonCharts"] or directory == "talents/"
            ):
                build_csv(combo, talent_string, results, weights, base_dps, True)
            if (
                config["analyze"]["json"]
                and config["analyze"]["dungeonCharts"]
                and not weights
            ):
                build_json(combo, talent_string, results, directory, timestamp, True)

    clear_output_files(talent_string)
    build_readme_md(directory, talent_string)
    os.chdir("..")
