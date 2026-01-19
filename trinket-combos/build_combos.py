"""
builds trinket strings
python build_combos.py
"""

from itertools import combinations

combos = {
    # s1 dungeons (276/289)
    "Eye_of_the_Drowning_Void_289": "eye_of_the_drowning_void,id=250257,ilevel=289",
    "Soulcatchers_Charm_289": "soulcatchers_charm,id=250223,ilevel=289",
    "Vessel_of_Souls_289": "vessel_of_souls,id=250258,ilevel=289",
    "Emberwing_Feather_289": "emberwing_feather,id=250144,ilevel=289",
    "Heart_of_Wind_289": "heart_of_wind,id=250256,ilevel=289",
    # "Emerald_Coachs_Whistle_289": "emerald_coachs_whistle,id=193718,ilevel=289",
    "Nevermelting_Ice_Crystal_289": "nevermelting_ice_crystal,id=50259,ilevel=289",
    "Reality_Breacher_289": "reality_breacher,id=151310,ilevel=289",
    # s1 raids (?/289)
    "Shadow_of_the_Empyrean_Requiem_289":"shadow_of_the_empyrean_requiem,id=249810,ilevel=289",
    "Gaze_of_the_Alnseer_289":"gaze_of_the_alnseer,id=249343,ilevel=289",
    "Litany_of_Lightblind_Wrath_289":"litany_of_lightblind_wrath,id=249808,ilevel=289",
    "Locus-Walkers_Ribbon_289":"locuswalkers_ribbon,id=249809,ilevel=289",
    "Vaelgors_Final_Stare_289":"vaelgors_final_stare,id=249346,ilevel=289",
    "Wraps_of_Cosmic_Madness_289":"wraps_of_cosmic_madness,id=249340,ilevel=289",
    # delves (276)
    "Glorious_Crusaders_Keepsake_276": "glorious_crusaders_keepsake,id=251792,ilevel=276",
    "Astalors_Anguish_Agitator_276": "astalors_anguish_agitator,id=264878,ilevel=276",
    "Drum_of_Renewed_Bonds_276": "drum_of_renewed_bonds,id=248583,ilevel=276",
    "Ever-Collapsing_Void_Fissure_276": "evercollapsing_void_fissure,id=251786,ilevel=276",
    "Sealed_Chaos_Urn_276": "sealed_chaos_urn,id=251787,ilevel=276",
    "Tangle_of_Vibrant_Vines_276": "tangle_of_vibrant_vines,id=252957,ilevel=276",
    "Void-Reapers_Libram_276": "voidreapers_libram,id=251785,ilevel=276",
    # pvp (263)
    "Galactic_Gladiators_Badge_of_Ferocity_263": "galactic_gladiators_badge_of_ferocity,id=255613,ilevel=263",
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
