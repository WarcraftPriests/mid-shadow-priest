"""
builds gem combo profile
python create_combos.py
"""

meta = {
    "CB": 213743, # crit
}

emerald = {
    "VE": 213485, # haste/vers
    "ME": 213482, # haste/mastery
    "DE": 213479, # haste/crit
}

ruby = {
    "MR": 213458, # crit/mastery
    "QR": 213455, # crit/haste
}

onyx = {
    "DO": 213491, # mastery/crit
    "QO": 213494, # mastery/haste
    "VO": 213497, # mastery/vers
}

sapphire = {
    "MS": 213473, # vers/mastery
    "QS": 213470, # vers/haste
}

amber = {
    "MA": 213509, # stam/mastery
    "QA": 213506, # stam/haste
}

top = {
    "QO": 213494, # mastery/haste
    "ME": 213482, # haste/mastery
}


def build_combos():
    combos = []
    five_colors = [
        f"{b}1_{e}1_{r}1_{o}1_{s}1_{a}1"
        for b in meta.keys()
        for e in emerald.keys()
        for r in ruby.keys()
        for o in onyx.keys()
        for s in sapphire.keys()
        for a in amber.keys()
    ]
    four_colors = [
        f"{b}1_{e}1_{r}1_{o}1_{s}1"
        for b in meta.keys()
        for e in emerald.keys()
        for r in ruby.keys()
        for o in onyx.keys()
        for s in sapphire.keys()
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
    # 1 per color (5) + 4 from top
    five_colors_three_top = [
        f"{color_gems}_{top_gems}"
        for color_gems in five_colors
        for top_gems in three_top
    ]
    combos.extend(five_colors_three_top)
    # 1 per color, not stam (4) + 5 from top
    four_colors_four_top = [
        f"{color_gems}_{top_gems}"
        for color_gems in four_colors
        for top_gems in four_top
    ]
    combos.extend(four_colors_four_top)
    return combos

def get_gem_string(name):
    key_name = name[0:2]
    gem_color_a = name[1:2]
    gem_count = name[2:3]
    string = ""
    match gem_color_a:
        case "B":
            string = f"{meta[key_name]}:{gem_count}"
        case "E":
            string = f"{emerald[key_name]}:{gem_count}"
        case "R":
            string = f"{ruby[key_name]}:{gem_count}"
        case "O":
            string = f"{onyx[key_name]}:{gem_count}"
        case "S":
            string = f"{sapphire[key_name]}:{gem_count}"
        case "A":
            string = f"{amber[key_name]}:{gem_count}"
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
