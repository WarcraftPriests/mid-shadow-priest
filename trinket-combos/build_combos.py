"""
builds trinket strings
python build_combos.py
"""

from itertools import combinations

combos = {
    # Liberation of Undermine (684)
    "Mugs_Moxie_Jug_684": "mugs_moxie_jug,id=230192,ilevel=684",
    # s3 dungeons (x/730)
    "Empowering_Crystal_of_Anubikkaj_730": "empowering_crystal_of_anubikkaj,id=219312,ilevel=730",
    "Signet_of_the_Priory_730": "signet_of_the_priory,id=219308,ilevel=730",
    "AraKara_Sacbrood_730": "arakara_sacbrood,id=219314,ilevel=730",
    "Lily_of_the_Eternal_Weave_730": "lily_of_the_eternal_weave,id=242494,ilevel=730",
    "Azhiccaran_Parapodia_730": "azhiccaran_parapodia,id=242497,ilevel=730",
    "Soleahs_Secret_Technique_Haste_730": "soleahs_secret_technique_mastery,id=190958,ilevel=730",
    "Soleahs_Secret_Technique_Mastery_730": "soleahs_secret_technique_mastery,id=190958,ilevel=730",
    # Manaforge Omega (?/730)
    "Diamantine_Voidcore_730":"diamantine_voidcore,id=242392,ilevel=730",
    "Astral_Antenna_730":"astral_antenna,id=242395,ilevel=730",
    "Naazindhris_Mystic_Lash_730":"naazindhris_mystic_lash,id=242398,ilevel=730",
    "Screams_of_a_Forgotten_Sky_730":"screams_of_a_forgotten_sky,id=242399,ilevel=730",
    "Arazs_Ritual_Forge_730":"arazs_ritual_forge,id=242402,ilevel=730",
    # delves (717)
    "Incorporeal_Essence_Gorger_NonEthereal_717": "incorporeal_essencegorger,id=246945,ilevel=717",
    # pvp (710)
    "Astral_Gladiators_Badge_of_Ferocity_710": "astral_gladiators_badge_of_ferocity,id=230638,ilevel=710",
}


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
                result += f"profileset.\"{profileset_name}\"+=shadowlands.soleahs_secret_technique_type={stat_type}\n"
            if "Astral_Antenna" in trinket:
                result += f"profileset.\"{profileset_name}\"+=thewarwithin.astral_antenna_miss_chance=0.10\n"
            # TWW S2 Options
            if "Synergistic_Brewterializer" in trinket:
                result += f"profileset.\"{profileset_name}\"+=priest.synergistic_brewterializer_tof_chance=0.90\n"
                result += f"profileset.\"{profileset_name}\"+=priest.synergistic_brewterializer_barrel_hit_chance=0.75\n"
            # TWW S1 Options
            if "Unbound_Changeling" in trinket:
                stat_type = trinket.split("_")[2].lower()
                result += f"profileset.\"{profileset_name}\"+=shadowlands.unbound_changeling_stat_type={stat_type}\n"
        result += f"profileset.\"{profileset_name}\"+=trinket1={trinket_one_value}\n"
        result += f"profileset.\"{profileset_name}\"+=trinket2={trinket_two_value}\n\n"
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
    trinket_combos = build_combos()
    SIMC_STRING = build_simc_string(trinket_combos)
    generate_sim_file(SIMC_STRING)
