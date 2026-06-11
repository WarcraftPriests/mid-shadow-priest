"""weight dict definitions"""

weights_raid_season_one = {
    "pw_ba_1": 0.013,
    "pw_sa_1": 0.225,
    "pw_na_1": 0.288,
    "lm_ba_1": 0.000,
    "lm_sa_1": 0.125,
    "lm_na_1": 0.075,
    "hm_ba_1": 0.000,
    "hm_sa_1": 0.000,
    "hm_na_1": 0.013,
    "pw_ba_2": 0.000,
    "pw_sa_2": 0.038,
    "pw_na_2": 0.075,
    "lm_ba_2": 0.000,
    "lm_sa_2": 0.025,
    "lm_na_2": 0.000,
    "hm_ba_2": 0.000,
    "hm_sa_2": 0.000,
    "hm_na_2": 0.000,
    "pw_ba_4": 0.000,
    "pw_sa_4": 0.000,
    "pw_na_4": 0.000,
    "lm_ba_4": 0.000,
    "lm_sa_4": 0.000,
    "lm_na_4": 0.000,
    "hm_ba_4": 0.000,
    "hm_sa_4": 0.000,
    "hm_na_4": 0.000,
    "pw_ba_3": 0.000,
    "pw_sa_3": 0.000,
    "pw_na_3": 0.088,
    "lm_ba_3": 0.000,
    "lm_sa_3": 0.000,
    "lm_na_3": 0.025,
    "hm_ba_3": 0.000,
    "hm_sa_3": 0.000,
    "hm_na_3": 0.013,
    "pw_ba_8": 0.0000,
    "pw_sa_8": 0.0000,
    "pw_na_8": 0.0000,
    "lm_ba_8": 0.0000,
    "lm_sa_8": 0.0000,
    "lm_na_8": 0.0000,
    "hm_ba_8": 0.0000,
    "hm_sa_8": 0.0000,
    "hm_na_8": 0.0000,
}

weights_single = {
    "pw_na_1": 0.767,
    "lm_na_1": 0.200,
    "hm_na_1": 0.033,
}

weights_two_targets = {
    "pw_ba_2": 0.000,
    "pw_sa_2": 0.300,
    "pw_na_2": 0.700,
    "lm_ba_2": 0.000,
    "lm_sa_2": 0.200,
    "lm_na_2": 0.000,
    "hm_ba_2": 0.000,
    "hm_sa_2": 0.000,
    "hm_na_2": 0.000,
}

weights_three_targets = {
    "pw_ba_3": 0.0,
    "pw_sa_3": 0.0,
    "pw_na_3": 0.7,
    "lm_ba_3": 0.0,
    "lm_sa_3": 0.0,
    "lm_na_3": 0.2,
    "hm_ba_3": 0.0,
    "hm_sa_3": 0.0,
    "hm_na_3": 0.1,
}

weights_four_targets = {
    "pw_ba_4": 0.0,
    "pw_sa_4": 0.0,
    "pw_na_4": 0.8,
    "lm_ba_4": 0.0,
    "lm_sa_4": 0.0,
    "lm_na_4": 0.2,
    "hm_ba_4": 0.0,
    "hm_sa_4": 0.0,
    "hm_na_4": 0.0,
}

weights_eight_targets = {
    "pw_ba_8": 0.0,
    "pw_sa_8": 0.0,
    "pw_na_8": 0.8,
    "lm_ba_8": 0.0,
    "lm_sa_8": 0.0,
    "lm_na_8": 0.2,
    "hm_ba_8": 0.0,
    "hm_sa_8": 0.0,
    "hm_na_8": 0.0,
}

weights_season_one = {
    "algethar": 0.125,
    "magisters": 0.125,
    "maisara": 0.125,
    "nexus": 0.125,
    "pitofsaron": 0.125,
    "seat": 0.125,
    "skyreach": 0.125,
    "windrunner": 0.125,
}


def find_weights(key):
    """return the matching dict"""
    if key == "weightsSingle":
        return weights_single
    if key == "weightsTwoTargets":
        return weights_two_targets
    if key == "weightsThreeTargets":
        return weights_three_targets
    if key == "weightsFourTargets":
        return weights_four_targets
    if key == "weightsEightTargets":
        return weights_eight_targets
    if key == "weightsSeasonOne":
        return weights_season_one
    if key == "weightsRaidSeasonOne":
        return weights_raid_season_one
    print(f"{key} not found")
    return None
