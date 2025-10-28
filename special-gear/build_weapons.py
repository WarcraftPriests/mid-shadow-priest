"""
builds weapon strings
python build_weapons.py
"""

enchant = "enchant=stormriders_fury_3"

one_hands = {
    "1h_stixs_metal_detector_678": "main_hand=stixs_metal_detector,id=228896,ilevel=678",
    "1h_big_earners_bludgeon_678": "main_hand=big_earners_bludgeon,id=228901,ilevel=678",
    "1h_scalding_queenmakers_shiv_678": "main_hand=scalding_queenmakers_shiv,id=221062,ilevel=678",
    "1h_hand_of_beledar_678": "main_hand=hand_of_beledar,id=221122,ilevel=678",
    "1h_fleshcrafters_knife_678": "main_hand=fleshcrafters_knife,id=178789,ilevel=678",
    "1h_electrifying_cognitive_amplifier_678": "main_hand=electrifying_cognitive_amplifier,id=168955,ilevel=678",
    "1h_g3t00t_678": "main_hand=g3t00t,id=159641,ilevel=678",
}

off_hands = {
    "OH_Pail_of_Preserved_Obscurity_639": "off_hand=pail_of_preserved_obscurity,id=221172,ilevel=639",  # noqa: E501
}

combos = [(mh, oh) for mh in one_hands.keys() for oh in off_hands.keys()]

for combo in combos:
    name = combo[0] + "-" + combo[1]
    mh = one_hands[combo[0]] + f",{enchant}"
    oh = off_hands[combo[1]]
    profileset = f"profileset.\"{name}\"+={mh}\nprofileset.\"{name}\"+={oh}\n"
    print(profileset)
