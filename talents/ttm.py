"""Updates profile names from TTM to be more readable"""
import logging
import math
import os
from pathlib import Path
import yaml

logger = logging.getLogger(__name__)

# load config lazily to avoid side-effects during import
config = None


def load_config(path: str | os.PathLike | None = None):
    """Load YAML config and return a dict.

    If `path` is None, tries to load the config at ../config.yml relative
    to this file (the original behavior).
    """
    global config
    if config is not None:
        return config
    if path is None:
        base = Path(__file__).resolve().parent
        # prefer the repository root config.yml (consistent across the repo)
        path = base.joinpath("..", "config.yml")
    path = Path(path)
    if not path.exists():
        logger.warning("config file %s not found, using empty config", path)
        config = {}
        return config
    with path.open("r", encoding="utf8") as ymlfile:
        config = yaml.load(ymlfile, Loader=yaml.FullLoader)
    # If the config contains a `talents:` section, prefer that for choice-node/idol overrides
    try:
        _apply_config_choices(config.get("talents", config))
    except Exception:
        logger.debug("No choice/idol overrides applied from config")
    return config


def _apply_config_choices(cfg: dict):
    """Apply choice node and idol definitions from a loaded config dict.

    This augments the module-level CHOICE_NODE_* and IDOLS constants.
    """
    if not cfg:
        return
    # add choice_pairs
    for pair in cfg.get("choice_pairs", []):
        keywords = tuple(pair.get("keywords", []))
        suffixes = tuple(pair.get("suffixes", []))
        if len(keywords) == 2 and len(suffixes) == 2:
            if (keywords, suffixes) not in CHOICE_NODE_PAIRS:
                CHOICE_NODE_PAIRS.append((keywords, suffixes))
    # add singletons
    for single in cfg.get("choice_singletons", []):
        kw = single.get("keyword")
        suf = single.get("suffix")
        if kw and suf and (kw, suf) not in CHOICE_NODE_SINGLETONS:
            CHOICE_NODE_SINGLETONS.append((kw, suf))
    # add idols
    for idol in cfg.get("idols", []):
        if idol and idol not in IDOLS:
            IDOLS.append(idol)


# Choice node definitions make it easy to add or change how choice nodes
# are detected and which suffix tokens they produce. Each entry is either:
# - a pair: ((keyword_a, keyword_b), (suffix_a, suffix_b)) meaning prefer
#   suffix_a when keyword_a present, else suffix_b when keyword_b present;
# - a singleton: (keyword, suffix) meaning append suffix when keyword present.
CHOICE_NODE_PAIRS = [
    (("misery", "invoked_nightmare"), ("Mis", "IN")),
    (("improved_voidform", "ancient_madness"), ("IV", "AM")),
    (("distorted_reality", "minds_eye"), ("DR", "ME")),
    (("deathspeaker", "death_and_madness"), ("DS", "DaM")),
]
CHOICE_NODE_SINGLETONS = [
    ("voidtouched", "VT"),
]

# Idol names used when constructing profile suffixes. Add new idols with
# `register_idol(name)` so tests and external callers can extend behavior.
IDOLS = ["yshaarj", "nzoth", "yogg", "cthun"]


def register_choice_pair(keywords: tuple[str, str], suffixes: tuple[str, str]):
    """Register a new pair of choice-node keywords and their suffix tokens.

    `keywords` is a 2-tuple of strings to search for in the input line.
    `suffixes` is a 2-tuple of suffix tokens to add when the corresponding
    keyword is present.
    """
    CHOICE_NODE_PAIRS.append((keywords, suffixes))


def register_choice_singleton(keyword: str, suffix: str):
    """Register a single choice-node keyword and its suffix token."""
    CHOICE_NODE_SINGLETONS.append((keyword, suffix))


def register_idol(name: str):
    """Register a new idol keyword to be detected in builds."""
    if name not in IDOLS:
        IDOLS.append(name)


def generate_suffix(list_of_talents):
    if not list_of_talents:
        return ""
    return "_".join(list_of_talents)


def apply_rules(line):
    # Don't add combos that waste points on TS without Yogg
    if "tormented_spirits" in line and "idol_of_yoggsaron" not in line:
        return True

    # Make sure you are efficiently spending points
    half_selected_mid = sum(1 for t in ("instilled_doubt", "mastermind") if f"{t}:1" in line)
    if half_selected_mid >= 2:
        return True

    half_selected_bot = sum(1 for t in ("madness_weaving", "screams_of_the_void", "insidious_ire") if f"{t}:1" in line)
    if half_selected_bot >= 2:
        return True

    # make sure you have 9+ talent points in the bottom section
    bottom_talents = 0
    bottom_list = [
        "mindbender",
        "deathspeaker",
        "death_and_madness",
        "mind_devourer",
        "auspicious_spirits",
        "inescapable_torment",
        "madness_weaving",
        "deaths_torment",
        "screams_of_the_void",
        "tormented_spirits",
        "insidious_ire",
        "idol_of_yshaarj",
        "idol_of_nzoth",
        "idol_of_yoggsaron",
        "idol_of_cthun",
        "maddening_tentacles",
        "crushing_void",
    ]
    for t in bottom_list:
        if f"{t}:1" in line:
            bottom_talents += 1
        if f"{t}:2" in line:
            bottom_talents += 2
    if bottom_talents < 9:
        return True

    # default case
    return False


def convert_builds(profile):
    profile_path = Path(profile)
    output_file_content = ""
    lines_seen = set()
    data = profile_path.read_text(encoding="utf8").splitlines(keepends=True)

    SIGNATURE = "# Automatically generated by ttm.py\n"
    if not data:
        return
    if data[0] != SIGNATURE:
        data = [SIGNATURE] + data
    else:
        logger.info("%s has already been generated, skipping file.", profile)
        return

    for line in data:
        if "Solved loadout " not in line:
            if line not in lines_seen or line.isspace():
                if "profileset" in line and apply_rules(line):
                    continue
                lines_seen.add(line)
                output_file_content += line
            continue
        TALENT = "NOCD"
        if "voidform" in line:
            TALENT = "VF"
        line = line.replace("Solved loadout ", TALENT + "_")
        # detect choice nodes
        # detect choice nodes using the centralized definitions
        choice_nodes = []
        lowered = line.lower()
        for (kw_a, kw_b), (suf_a, suf_b) in CHOICE_NODE_PAIRS:
            if kw_a in lowered:
                choice_nodes.append(suf_a)
            elif kw_b in lowered:
                choice_nodes.append(suf_b)
        for kw, suf in CHOICE_NODE_SINGLETONS:
            if kw in lowered:
                choice_nodes.append(suf)
        suffix = generate_suffix(choice_nodes)
        # replace numeric clusters with the generated suffix
        for pattern in (" 22111", " 22211", " 21211", " 21111", " 22112", " 22212", " 21212", " 21112"):
            line = line.replace(pattern, "_" + suffix)

        if apply_rules(line):
            continue

        idols = ["yshaarj", "nzoth", "yogg", "cthun"]
        idols_used = []
        for idol in idols:
            if idol in line:
                idols_used.append(idol)
        idols_count = len(idols_used)
        # prefix with underscore and join any used idols with underscores;
        # for a single idol this yields e.g. "_nzoth", for multiple "_yshaarj_nzoth"
        idols_suffix = ("_" + "_".join(idols_used)) if idols_used else ""
        line = line.replace(f'profileset."{TALENT}', f'profileset."{TALENT}{idols_suffix}')

        # ONLY ALLOW 3+ IDOL BUILDS
        if idols_count > 2 and line not in lines_seen:
            lines_seen.add(line)
            output_file_content += line

    profile_path.write_text(output_file_content, encoding="utf8")


class Talents:
    def __init__(self, st, ct, ht):
        self.st = st
        self.ct = ct
        self.ht = ht


def duplicate_builds():
    hero_talents = ["AR", "VW"]
    # TODO: skip duplicate if a comment is added? this can take a long time
    for hero_talent in hero_talents:
        with open(f"hero_{hero_talent}.simc", "r", encoding="utf8") as file:
            data = file.readlines()
        logger.info("Starting with %d builds", len(data))
        # duplicate all builds for minds_eye
        me_data = list(map(lambda x: x.replace("minds_eye", "distorted_reality"), data))
        me_data = list(map(lambda x: x.replace("_ME", "_DR"), me_data))
        data = me_data + data
        logger.info("%d builds after duplicating for Mind's Eye", len(data))
        # create talent dictionary
        talents = {}
        for line in data:
            if "# Automatically generated by ttm.py" in line:
                continue
            name = line.split("+=")[0].split("profileset.")[1].replace('"', "")
            value = line.split("+=", 1)[1].replace('"', "").strip()
            talents[name] = value
        # duplicate all builds for each hero talent combo
        hero_talents = {}
        cfg = config if config is not None else load_config()
        for build in cfg.get("hero", {}).get(hero_talent, {}):
            logger.info("Duplicating builds for %s...", build)
            talent_string = cfg["hero"][hero_talent][build]
            for talent in talents:
                name = f"{build}_{talent}"
                hero_line = f'profileset."{name}"+="hero_talents={talent_string}"\n'
                class_line = ""
                spec_line = f'profileset."{name}"+="{talents[talent]}"\n'
                hero_talents[name] = Talents(spec_line, class_line, hero_line)
        logger.info("Writing builds to hero_%s_duplicated.simc", hero_talent)
        with open(f"hero_{hero_talent}_duplicated.simc", "w", encoding="utf8") as file:
            for build in hero_talents:
                file.writelines(hero_talents[build].st)
                file.writelines(hero_talents[build].ht)
                if hero_talents[build] != "":
                    file.writelines(hero_talents[build].ct)


def make_build_files():
    hero_talents = ["AR", "VW"]
    data = list()
    for hero_talent in hero_talents:
        with open(f"hero_{hero_talent}_duplicated.simc", "r", encoding="utf8") as file:
            data = data + file.readlines()
            file.close()
    with open("base.simc", "r", encoding="utf8") as file:
        base = file.readlines()
        file.close()
    # clear out old files
    for filename in os.listdir("builds/"):
        if os.path.isfile(os.path.join("builds/", filename)):
            os.remove(os.path.join("builds/", filename))
    # TODO make this number configurable
    batch_size = 4002
    batches = math.ceil(len(data) / batch_size)
    # TODO: these batches can cause problems now that builds are no longer on one line (2 for VW, 3 for AR)
    # refactor so this doesnt break
    for batch in range(batches):
        start = 0 + (batch_size * batch)
        end = batch_size + (batch_size * batch)
        with open(f"builds/talents_{batch}.simc", "w", encoding="utf8") as file:
            file.writelines(base)
            for line in data[start:end]:
                file.write(line)
        file.close()


if __name__ == "__main__":
    # Ensure basic logging output is configured for CLI runs
    logging.basicConfig(level=logging.INFO, format="%(levelname)s : %(message)s")
    # load config so duplicate_builds can use it immediately
    load_config()
    convert_builds("hero_AR.simc")
    convert_builds("hero_VW.simc")
    duplicate_builds()
    make_build_files()
