"""weight dict definitions"""

weights_manaforge_omega = {
    'pw_ba_1': 0.0750,
    'pw_sa_1': 0.3375,
    'pw_na_1': 0.3125,
    'lm_ba_1': 0.0250,
    'lm_sa_1': 0.1000,
    'lm_na_1': 0.0625,
    'hm_ba_1': 0.0000,
    'hm_sa_1': 0.0375,
    'hm_na_1': 0.0125,
    'pw_ba_2': 0.0000,
    'pw_sa_2': 0.0000,
    'pw_na_2': 0.0000,
    'lm_ba_2': 0.0000,
    'lm_sa_2': 0.0000,
    'lm_na_2': 0.0375,
    'hm_ba_2': 0.0000,
    'hm_sa_2': 0.0000,
    'hm_na_2': 0.0000,
    'pw_ba_4': 0.0000,
    'pw_sa_4': 0.0000,
    'pw_na_4': 0.0000,
    'lm_ba_4': 0.0000,
    'lm_sa_4': 0.0000,
    'lm_na_4': 0.0000,
    'hm_ba_4': 0.0000,
    'hm_sa_4': 0.0000,
    'hm_na_4': 0.0000,
    'pw_ba_3': 0.0000,
    'pw_sa_3': 0.0000,
    'pw_na_3': 0.0000,
    'lm_ba_3': 0.0000,
    'lm_sa_3': 0.0000,
    'lm_na_3': 0.0000,
    'hm_ba_3': 0.0000,
    'hm_sa_3': 0.0000,
    'hm_na_3': 0.0000,
    'pw_ba_8': 0.0000,
    'pw_sa_8': 0.0000,
    'pw_na_8': 0.0000,
    'lm_ba_8': 0.0000,
    'lm_sa_8': 0.0000,
    'lm_na_8': 0.0000,
    'hm_ba_8': 0.0000,
    'hm_sa_8': 0.0000,
    'hm_na_8': 0.0000,
}

weights_single = {
    'pw_na_1': 0.80645161290,
    'lm_na_1': 0.16129032258,
    'hm_na_1': 0.03225806452,
}

weights_two_targets = {
    'pw_ba_2': 0.000,
    'pw_sa_2': 0.8571428571,
    'pw_na_2': 0.000,
    'lm_ba_2': 0.000,
    'lm_sa_2': 0.1428571429,
    'lm_na_2': 0.000,
    'hm_ba_2': 0.000,
    'hm_sa_2': 0.000,
    'hm_na_2': 0.000,
}

weights_three_targets = {
    'pw_ba_3': 0.0,
    'pw_sa_3': 0.0,
    'pw_na_3': 0.8,
    'lm_ba_3': 0.0,
    'lm_sa_3': 0.0,
    'lm_na_3': 0.2,
    'hm_ba_3': 0.0,
    'hm_sa_3': 0.0,
    'hm_na_3': 0.0,
}

weights_four_targets = {
    'pw_ba_4': 0.0,
    'pw_sa_4': 0.0,
    'pw_na_4': 0.8,
    'lm_ba_4': 0.0,
    'lm_sa_4': 0.0,
    'lm_na_4': 0.2,
    'hm_ba_4': 0.0,
    'hm_sa_4': 0.0,
    'hm_na_4': 0.0,
}

weights_eight_targets = {
    'pw_ba_8': 0.0,
    'pw_sa_8': 0.0,
    'pw_na_8': 0.8,
    'lm_ba_8': 0.0,
    'lm_sa_8': 0.0,
    'lm_na_8': 0.2,
    'hm_ba_8': 0.0,
    'hm_sa_8': 0.0,
    'hm_na_8': 0.0,
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
    if key == 'weightsSingle':
        return weights_single
    if key == 'weightsTwoTargets':
        return weights_two_targets
    if key == 'weightsThreeTargets':
        return weights_three_targets
    if key == 'weightsFourTargets':
        return weights_four_targets
    if key == 'weightsEightTargets':
        return weights_eight_targets
    if key == 'weightsSeasonOne':
        return weights_season_one
    if key == 'weightsManaforgeOmega':
        return weights_manaforge_omega
    print(f"{key} not found")
    return None
