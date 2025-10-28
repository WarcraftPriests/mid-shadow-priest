"""creates combinations of gems"""
# python .\cyrces.py

item_level = 639
enchant = "radiant_mastery_3"
slot = 2

thunder = {
    'SRC': 228638, # Stormbringer's Runed Citrine
    'TCC': 228634, # Thunderlord's Crackling Citrine
}

sea = {
    'FRC': 228639, # Fathomdweller's Runed Citrine
    'UOC': 228636, # Undersea Overseer's Citrine
}

wind = {
    'LSC': 228646, # Legendary Skipper's Citrine
    'SSC': 228635, # Squall Sailor's Citrine
    'WRC': 228640, # Windsinger's Runed Citrine
}

combinations = [
    f"{t}_{s}_{w}"
    for t in thunder.keys()
    for s in sea.keys()
    for w in wind.keys()
]

def generate_ring(combo):
    thunder_gem = combo.split("_")[0]
    sea_gem = combo.split("_")[1]
    wind_gem = combo.split("_")[2]
    item_level_id = 1472 + ( item_level - 619 )
    gems = f"{thunder.get(thunder_gem)}/{sea.get(sea_gem)}/{wind.get(wind_gem)}"
    profileset = f"profileset.\"Cyrces_Circlet_{thunder_gem}_{sea_gem}_{wind_gem}\"+="
    return f"{profileset}finger{slot}=,id=228411"+f",gem_id={gems}"+f",bonus_id=12025/{item_level_id},enchant={enchant}"

if __name__ == "__main__":
    print(f"generating {len(combinations)} gem strings.")
    for combo in combinations:
        print(generate_ring(combo))
