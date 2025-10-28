"""Generates tier.simc tier set combos from base.simc profile"""
import itertools

base_file = 'base.simc'
output_file = 'tier.simc'

def get_item_list(name, combo):
    if len(combo) > 1:
        name = name + combo[0] + "-"
        return get_item_list(name, combo[1:])
    else:
        name = name + combo[0]
        return name

tier = {
    'head': 'head=confessors_unshakable_halo,id=229334',
    'shoulders': 'shoulder=confessors_unshakable_radiance,id=229332',
    'chest': 'chest=confessors_unshakable_vestment,id=229337,enchant=crystalline_radiance_3',
    'hands': 'hands=confessors_unshakable_mitts,id=229335',
    'legs': 'legs=confessors_unshakable_leggings,id=229333,enchant=sunset_spellthread_3'
}

talents = {
    'current': 'CIQAAAAAAAAAAAAAAAAAAAAAAAmxYAAAAAAAAAAAAMMbmxMzswMzMjxMzsMY2YmZmxsxAjxwsY2mamBLwMzMAQAmtZbJY2YBA',
}

# Normal: 658
# Heroic: 665
# Mythic: 678
item_levels = [658, 665, 678]
profiles = []
two_set_combos = list(itertools.combinations(tier.keys(), 2))
four_set_combos = list(itertools.combinations(tier.keys(), 4))
combos = two_set_combos + four_set_combos

for talent in talents:
    for ilevel in item_levels:
        for combo in combos:
            item_list = get_item_list("", combo)
            name = f"{len(combo)}_{item_list}_{ilevel}_{talent}"
            profile_string = ""
            # profile_string += f"profileset.\"{name}\"+=talents={talents[talent]}\n"
            for item in combo:
                profile_string += f"profileset.\"{name}\"+={tier[item]},ilevel={ilevel}\n"
            profiles.append(profile_string + '\n')

base_file_contents = ""
with open(base_file, 'r') as file:
    base_file_contents = file.readlines()
    base_file_contents.append('\n\n')
    file.close()

with open(output_file, 'w') as file:
    file.writelines(base_file_contents)
    file.writelines(profiles)
    file.close()