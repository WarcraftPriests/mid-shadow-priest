import csv
from statistics import mean

import yaml

with open("../config.yml", "r", encoding="utf8") as ymlfile:
    config = yaml.load(ymlfile, Loader=yaml.FullLoader)


def get_talents():
    talents = config["builds"].keys()
    return talents


def get_change(current, previous):
    if current == previous:
        return 100.0
    try:
        return round((((current - previous) / previous) * 100.0), 2)
    except ZeroDivisionError:
        return 0


class Talents:
    def __init__(self, st, dps):
        self.st = st
        self.dps = dps


def check_build_in_talent(build, talent_string):
    match build:
        case "vw-da-cthun-dr":
            return (
                talent_string.startswith("VW_")
                and "_DA_" in talent_string
                and "cthun" in talent_string
                and talent_string.endswith("_DR")
            )
        case "ar-cthun":
            return talent_string.startswith("AR_") and "cthun" in talent_string
        case "vw-da-cthun-me":
            return (
                talent_string.startswith("VW_")
                and "_DA_" in talent_string
                and "cthun" in talent_string
                and talent_string.endswith("_ME")
            )
        case "vw-vf-cthun":
            return (
                talent_string.startswith("VW_")
                and "_VF_" in talent_string
                and "cthun" in talent_string
            )


if __name__ == "__main__":
    talent_builds = get_talents()
    hero_talents = ["AR", "VW"]
    talent_spec_strings = {}
    for hero_talent in hero_talents:
        with open(f"hero_{hero_talent}_duplicated.simc", "r", encoding="utf8") as file:
            for line in file:
                if "spec_talents" in line:
                    talent_string = line[12:].split('"')[0]
                    spec_talents = (
                        line.split("+=")[1].replace('"', "").replace("\n", "")
                    )
                    talent_spec_strings[talent_string] = Talents(spec_talents, 0)
            file.close()
    print(f"Found {len(talent_spec_strings)} talent builds")
    # just do single target for now
    fights = ["2T", "4T", "8T", "Composite", "Dungeons-Slice", "Single"]
    for fight in fights:
        print(f"generating Results_{fight}-info.md")
        with open(f"results/Results_{fight}.csv", "r", encoding="utf8") as file:
            reader = csv.reader(file)
            for row in reader:
                if talent_spec_strings.get(row[1]):
                    talent_spec_strings[row[1]].dps = row[2]
            file.close()

        with open(f"results/Results_{fight}-info.md", "w", encoding="utf8") as file:
            file.write(f"# {fight} Talent Info\n")
            for build in talent_builds:
                info_talents = {
                    "whispering_shadows:1": [],
                    "mental_decay:1": [],
                    "mind_spike:1": [],
                    "maddening_touch:2": [],
                    "dark_evangelism:2": [],
                    "mind_devourer:2": [],
                    "phantasmal_pathogen:2": [],
                    "voidtouched:1": [],
                    "mindbender:1": [],
                    "inescapable_torment:1": [],
                    "mastermind:2": [],
                    "idol_of_yshaarj:1": [],
                    "deathspeaker:1": [],
                    "idol_of_nzoth:1": [],
                    "screams_of_the_void:2": [],
                    "auspicious_spirits:1": [],
                    "idol_of_yoggsaron:1": [],
                    "insidious_ire:2": [],
                }

                not_talents = {
                    "whispering_shadows:1": [],
                    "mental_decay:1": [],
                    "mind_spike:1": [],
                    "maddening_touch:2": [],
                    "dark_evangelism:2": [],
                    "mind_devourer:2": [],
                    "phantasmal_pathogen:2": [],
                    "voidtouched:1": [],
                    "mindbender:1": [],
                    "inescapable_torment:1": [],
                    "mastermind:2": [],
                    "idol_of_yshaarj:1": [],
                    "deathspeaker:1": [],
                    "idol_of_nzoth:1": [],
                    "screams_of_the_void:2": [],
                    "auspicious_spirits:1": [],
                    "idol_of_yoggsaron:1": [],
                    "insidious_ire:2": [],
                }
                file.write(f"## {build}\n|talent|min|max|mean|\n|---|---|---|---|\n")
                # populate info_talents and not_talents
                for talent in talent_spec_strings:
                    if not check_build_in_talent(build, talent):
                        continue
                    talents = talent_spec_strings.get(talent)
                    spec_talents = talents.st
                    dps = talents.dps
                    for t, values in info_talents.items():
                        if t in spec_talents:
                            values.append(int(dps))
                        else:
                            not_talents[t].append(int(dps))
                # print stats
                for t, values in info_talents.items():
                    if len(values) == 0:
                        print(f"Build {build} never takes {t}, skipping")
                        continue
                    if len(not_talents[t]) == 0:
                        print(f"Build {build} always takes {t}, skipping")
                        continue
                    min_change = get_change(min(values), min(not_talents[t]))
                    max_change = get_change(max(values), max(not_talents[t]))
                    mean_change = get_change(mean(values), mean(not_talents[t]))
                    file.write(f"|{t}|{min_change}%|{max_change}%|{mean_change}%\n")
            file.close()
