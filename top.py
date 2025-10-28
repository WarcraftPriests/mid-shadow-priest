"""finds top talent builds"""
# python top.py [--analyze_only False, --top_matches 5, --match_jitter 2]

import argparse
import csv
import math
import os
import json
import yaml

from internal import utils
from internal.api import raidbots
from api_secrets import api_key

with open("config.yml", "r", encoding="utf8") as ymlfile:
    config = yaml.load(ymlfile, Loader=yaml.FullLoader)


def get_top_talents(results, combos, directory, matches, jitter):
    talent_names = []
    st_crash_builds = []
    for result in results:
        builds = []
        with open(f"{directory}/Results_{result}.csv", "r", encoding="utf8") as file:
            reader = csv.reader(file, delimiter=",")
            for row in reader:
                builds.append(row[1])
        file.close()
        # st + crash
        if result == "Single":
            for combo in combos:
                count = 0
                for build in builds:
                    filler = ""
                    fillers = ["_ME", "_DR"]
                    for name in fillers:
                        if name in build:
                            filler = name
                    if combo[0] in build and filler == combo[1] and "_SC" in build:
                        st_crash_builds.append(build)
                        talent_names.append(build)
                        count = count + 1
                        # add a buffer to get more diversity
                        if count >= jitter:
                            break
        # get top x builds
        talent_names.extend(builds[1 : matches + 1])
        for combo in combos:
            count = 0
            for build in builds:
                filler = ""
                fillers = ["_ME", "_DR"]
                for name in fillers:
                    if name in build:
                        filler = name
                if combo[0] in build and filler == combo[1]:
                    talent_names.append(build)
                    count = count + 1
                    # add a buffer to get more diversity
                    if count >= jitter:
                        break
    if len(st_crash_builds) > 0:
        print(f"Found ST + Crash builds: {st_crash_builds}")
    return list(set(talent_names))


def get_hero_builds(ht, cds, idols):
    # overwriting this for now to limit combos
    hero_talent_combos = list(config["hero"][ht].keys())
    if ht == "AR":
        hero_talent_combos = ["AR_EC", "AR_SP"]
    if ht =="VW":
        hero_talent_combos = ["VW_VE_DoS", "VW_DH_DoS", "VW_DH_VW", "VW_DH_VW"]
    return [
        f"{ht}_{cd}_{idol}" for ht in hero_talent_combos for cd in cds for idol in idols
    ]


def get_builds():
    combos = []
    ar_cds = ["VF"]
    vw_cds = ["DA"]
    # Archon and Voidweaver can have different Idol options, manually splitting
    ar_idols = [
        "nzoth_cthun",
        "nzoth_yogg_cthun",
    ]
    combos.extend(get_hero_builds("AR", ar_cds, ar_idols))
    ## Voidweaver
    vw_idols = [
        "nzoth_cthun",
        "yshaarj_nzoth_cthun",
        "nzoth_yogg_cthun"
    ]
    combos.extend(get_hero_builds("VW", vw_cds, vw_idols))
    return combos


class Talents:
    def __init__(self, st, ct, ht):
        self.st = st
        self.ct = ct
        self.ht = ht


def find_talents(talent):
    spec_talents = "not_found"
    class_talents = "not_found"
    hero_talents = "not_found"
    hero_specs = ["AR", "VW"]
    for hero_talent in hero_specs:
        with open(
            f"talents/hero_{hero_talent}_duplicated.simc", "r", encoding="utf8"
        ) as file:
            for line in file:
                if talent in line:
                    if "spec_talents" in line:
                        spec_talents = (
                            line.split("+=")[1].replace('"', "").replace("\n", "")
                        )
                    if "class_talents" in line:
                        class_talents = (
                            line.split("+=", 1)[1].replace('"', "").replace("\n", "")
                        )
                    if "hero_talents" in line:
                        hero_talents = (
                            line.split("+=")[1].replace('"', "").replace("\n", "")
                        )

                    if (
                        spec_talents != "not_found"
                        and class_talents != "not_found"
                        and hero_talents != "not_found"
                    ):
                        break
        file.close()
    if spec_talents == "not_found":
        print(f"{talent} not found")
        exit()
    return Talents(spec_talents, class_talents, hero_talents)


def get_base_actor():
    file_name = os.listdir("talents/profiles/")[0]
    with open(f"talents/profiles/{file_name}", "r", encoding="utf8") as file:
        ending_line = 27
        for num, line in enumerate(file, 1):
            if "main_hand" in line:
                ending_line = num
    file.close()
    with open(f"talents/profiles/{file_name}", "r", encoding="utf8") as file:
        head = [next(file) for _ in range(ending_line)]
    file.close()
    head.extend("\n")
    return head


def create_sim_file(base, talent_dictionary, batches):
    items = list(talent_dictionary.items())
    # clear out existing build files
    for filename in os.listdir("talents/top/"):
        if os.path.isfile(os.path.join("talents/top/", filename)):
            os.remove(os.path.join("talents/top/", filename))
    # raidbots limits us to 200 actors per sim
    for batch in range(batches):
        start = 0 + (199 * batch)
        end = 199 + (199 * batch)
        with open(
            f"talents/top/top_talents_{batch}.simc", "w", encoding="utf8"
        ) as file:
            file.writelines(base)
            for actor in items[start:end]:
                name = actor[0]
                talents = actor[1]
                file.writelines([f'copy="{name}","Base"\n'])
                if talents.st != "not_found":
                    file.writelines(f"{talents.st}\n")
                if talents.ct != "not_found":
                    file.writelines(f"{talents.ct}\n")
                if talents.ht != "not_found":
                    file.writelines(f"{talents.ht}\n")
            file.write("iterations=1")
        file.close()


def populate_talent_strings(name):
    talent_string_dictionary = {}
    f = open(f"{name}.json")
    data = json.load(f)
    f.close()
    for player in data["sim"]["players"]:
        if player["name"] != "Base":
            talent_string_dictionary[player["name"]] = player["talents"]
    return talent_string_dictionary


def populate_talents(talent_string_dictionary):
    with open("internal/talents.yml", "r") as file:
        talents = yaml.safe_load(file)
        custom_builds = talents["builds"]
        full_yaml = {"builds": custom_builds, "generated": talent_string_dictionary}
    file.close()
    with open("internal/talents.yml", "w") as file:
        yaml.dump(full_yaml, file)
    file.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--top_matches", nargs="?", default=5, type=int)
    parser.add_argument("--match_jitter", nargs="?", default=3, type=int)
    parser.add_argument("--analyze_only", nargs="?", default=False, type=bool)
    args = parser.parse_args()

    # Setup Vars
    build_configs = get_builds()
    combos = [
        (cd, filler)
        for cd in build_configs
        for filler in ["_ME", "_DR"]
    ]  # noqa: E501
    results = utils.get_sim_types()
    push_results = list(utils.get_dungeon_combos())

    # Get aggregate results
    talent_names = get_top_talents(
        results, combos, "talents/results", args.top_matches, args.match_jitter
    )
    # Get individual push dungeon results
    if config["dungeonType"] == "route":
        dungeon_talent_names = get_top_talents(
            push_results, combos, "talents/results/dungeons", 1, 1
        )
    elif config["dungeonType"] == "slice":
        dungeon_talent_names = get_top_talents(
            ["slice"],
            combos,
            "talents/results/dungeons",
            args.top_matches,
            args.match_jitter,
        )
    talent_names.extend(dungeon_talent_names)
    # De-duplicate again
    talent_names = list(set(talent_names))
    print(f"Found {len(talent_names)} top builds.")

    # Build Talent Dictionary
    talent_dictionary = {}
    for talent in talent_names:
        talent_dictionary[talent] = find_talents(talent)

    # Get base actor data
    base = get_base_actor()

    # Create copy actor files we will run (top_talents_X.simc)
    batches = math.ceil(len(talent_dictionary) / 199)
    create_sim_file(base, talent_dictionary, batches)

    # run a sim at 1 iteration in raidbots
    ## must pass the API something for iterations, but we manually set this to 1 when building the file
    talent_string_dictionary = {}
    for batch in range(batches):
        name = f"talents/top/top_talents_{batch}"
        if not args.analyze_only:
            raidbots(
                api_key,
                f"{name}.simc",
                config["simcBuild"],
                f"{name}.json",
                name,
                "smart",
            )
        # pull out the results and find the talent id string per actor
        t = populate_talent_strings(name)
        talent_string_dictionary.update(t)

    # fill out internal/talents.yml with generated talents
    populate_talents(talent_string_dictionary)
