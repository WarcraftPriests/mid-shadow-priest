"""stores utils that are shared between scripts"""
import argparse
import sys
import yaml

with open("config.yml", "r", encoding="utf8") as ymlfile:
    config = yaml.load(ymlfile, Loader=yaml.FullLoader)


def get_talents(args):
    """lookup talents based on current config"""
    try:
        if args.talents:
            talents = [args.talents]
        elif config["sims"][args.dir[:-1]]["builds"]:
            talents = config["builds"]
        else:
            talents = []
    except KeyError:
        print(
            f"{args.dir[:-1]} is not a valid sim dir.\nOptions are {config['sims'].keys()}"
        )  # noqa: E501
        sys.exit(1)
    return talents


def get_simc_dir(talent, folder_name):
    """get proper directory based on talent options"""
    if talent:
        return f"{folder_name}/{talent}/"
    return f"{folder_name}/"


def generate_parser(description):
    """creates the shared argparser for sim.py and profiles.py"""
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("dir", help="Directory to generate profiles for.")
    parser.add_argument(
        "--dungeons", help="Run a dungeonsimming batch of sims.", action="store_true"
    )
    parser.add_argument(
        "--talents",
        help="indicate talent build for output.",
        choices=config["builds"].keys(),
    )  # noqa: E501
    parser.add_argument(
        "--ptr", help="indicate if the sim should use ptr data.", action="store_true"
    )
    parser.add_argument(
        "--apl",
        help="indicate if the sim should use the custom apl.",
        action="store_true",
    )  # noqa: E501
    parser.add_argument(
        "--iterations",
        help="Pass through specific iterations to run on. Default is 10000",
    )  # noqa: E501
    parser.add_argument(
        "--local",
        help="indicate if the simulation should run local.",
        action="store_true",
    )  # noqa: E501
    parser.add_argument(
        "--auto_download",
        help="indicate if we should automatically download latest simc.",  # noqa: E501
        action="store_true",
    )
    return parser


def get_dungeon_combos():
    """creates a list of the dungeon combinations"""
    season = config["dungeonSeason"]
    type = config["dungeonType"]
    if type == "slice":
        return ["slice"]
    elif type == "route":
        if season == 1:
            keys = [
                "arakara",
                "cityofthreads",
                "dawnbreaker",
                "grimbatol",
                "mists",
                "necrotic",
                "siege",
                "stonevault",
            ]
        elif season == 2:
            keys = [
                "cinderbrew",
                "darkflame",
                "floodgate",
                "motherlode",
                "priory",
                "rookery",
                "theater",
                "workshop",
            ]
        else:
            print(f"No season data defined in for season {season} in utils:get_dungeon_combos")
            exit(1)
        # currently unused, just doing push
        # levels = ["standard", "push"]
        # combos = [
        #     f"{key}-{level}"
        #     for key in keys
        #     for level in levels
        # ]
        combos = [f"{key}" for key in keys]
        return combos
    else:
        print(f"Invalid type given: {type}")
        exit(1)

def get_sim_types():
    type_list = ["Composite", "Single", "2T", "8T"]
    type_list.append(str(config["councilTargets"]) + "T")
    if config["dungeonType"] == "route":
        # type_list.extend(["Dungeons-Standard", "Dungeons-Push"])
        type_list.extend(["Dungeons-Route"])
    if config["dungeonType"] == "slice":
        type_list.extend(["Dungeons-Slice"])
    return type_list