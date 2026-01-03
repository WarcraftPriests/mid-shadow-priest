"""
builds gem combo profile
python create_combos.py
"""

meta = {
    "IED": 240983, # int + crit
    "PED": 240967, # int
}

# only do color combos for these
meta_combos = {
    "IED": 240983, # int + crit
}

peridot = {
    "FVP": 240894, # haste/vers
    "FMP": 240892, # haste/mastery
    "FDP": 240890, # haste/crit
}

garnet = {
    "FMG": 240908, # crit/mastery
    "FQG": 240906, # crit/haste
}

amethyst = {
    "FDA": 240898, # mastery/crit
    "FQA": 240900, # mastery/haste
    "FVA": 240902, # mastery/vers
}

lapis = {
    "FML": 240918, # vers/mastery
    "FQL": 240916, # vers/haste
}

top = {
    "FQA": 240900, # mastery/haste
    "FMP": 240892, # haste/mastery
}


def build_combos():
    combos = []
    four_colors = [
        f"{m}1_{p}1_{g}1_{a}1_{l}1"
        for m in meta_combos.keys()
        for p in peridot.keys()
        for g in garnet.keys()
        for a in amethyst.keys()
        for l in lapis.keys()  # noqa: E741
    ]
    three_top = []
    four_top = []
    for gem in top.keys():
        three_top.append(f"{gem}3")
        four_top.append(f"{gem}4")
        for b in meta:
            # 9 stacked from top
            combos.append(f"{b}1_{gem}8")
        # Add all top gems without meta in case it sucks
        combos.append(f"{gem}9")
    # 1 per color (4) + 5 from top
    four_colors_four_top = [
        f"{color_gems}_{top_gems}"
        for color_gems in four_colors
        for top_gems in four_top
    ]
    combos.extend(four_colors_four_top)
    return combos

def get_gem_string(name):
    key_name = name[0:3]
    gem_color_a = name[2:3]
    gem_count = name[3:4]
    string = ""
    match gem_color_a:
        case "D":
            string = f"{meta[key_name]}:{gem_count}"
        case "P":
            string = f"{peridot[key_name]}:{gem_count}"
        case "G":
            string = f"{garnet[key_name]}:{gem_count}"
        case "A":
            string = f"{amethyst[key_name]}:{gem_count}"
        case "L":
            string = f"{lapis[key_name]}:{gem_count}"
    return string


def build_simc_string(gem_combos):
    result = ""
    # each item in simc can hold 4 gems?
    for combo in gem_combos:
        full_gem_string = ""
        for gem in combo.split("_"):
            gem_string = get_gem_string(gem)
            gem_id, gem_count = gem_string.split(":")
            for x in range(int(gem_count)):
                full_gem_string += f"{gem_id}/"
        # maybe find a better way that isnt hardcoding
        head_gems = full_gem_string.split("/")[0]
        neck_gems = ""
        shoulder_gems = ""
        for gem in full_gem_string.split("/")[1:5]:
            neck_gems += f"{gem}/"
        for gem in full_gem_string.split("/")[5:10]:
            shoulder_gems += f"{gem}/"
        result += f"profileset.\"{combo}\"+=head=$" + '{gear.head}' + f",gem_id={head_gems}\n"
        result += f"profileset.\"{combo}\"+=neck=$" + '{gear.neck}' + f",gem_id={neck_gems[:-1]}\n"
        result += f"profileset.\"{combo}\"+=shoulders=$" + '{gear.shoulders}' + f",gem_id={shoulder_gems[:-1]}\n"
    return result

def generate_sim_file(input_string):
    """reads in the base simc file and creates the generated.simc file"""
    with open("base.simc", 'r', encoding="utf8") as file:
        data = file.read()
        file.close()
    with open("generated.simc", 'w+', encoding="utf8") as file:
        file.writelines(data)
        file.writelines(input_string)


if __name__ == '__main__':
    gem_combos = build_combos()
    SIMC_STRING = build_simc_string(gem_combos)
    generate_sim_file(SIMC_STRING)
