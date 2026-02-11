import types
from pathlib import Path
import shutil


import profiles


def test_generate_combination_name():
    name = profiles.generate_combination_name(["mastery", "versatility", "mastery", "crit"])
    assert name == "M2_V1_H0_C1"


def test_generate_stat_string_and_versatility_newline():
    # set a minimal stats config
    profiles.config = {"stats": {"base": 40, "steps": 10}}
    # versatility should append a newline
    vers = profiles.generate_stat_string(["versatility", "versatility"], "versatility")
    assert vers == "gear_versatility_rating=30\n"
    # non-versatility should not append newline
    haste = profiles.generate_stat_string(["haste"], "haste")
    assert haste == "gear_haste_rating=20"


def test_build_settings_includes_expressions():
    # profile string containing patchwerk and single target
    s = profiles.build_settings("pw1", weights=True, dungeons=False)
    assert 'fight_style="Patchwerk"' in s
    assert "desired_targets=1" in s
    # weights flag adds scale factor expression
    assert 'calculate_scale_factors="1"' in s


def test_build_simc_file():
    assert profiles.build_simc_file("tal", "pname") == "profiles/tal/pname.simc"
    assert profiles.build_simc_file(None, "pname") == "profiles/pname.simc"


def test_replace_talents_with_hero(monkeypatch):
    profiles.config = {"forceHeroTalents": True}

    def fake_lookup(name):
        return "heroABC"

    monkeypatch.setattr(profiles, "lookup_hero_talents", fake_lookup)

    data = "spec=shadow\ntalents=old\nother=1"
    out = profiles.replace_talents("newtal", data, "any_DA")
    assert "talents=newtal" in out
    assert "hero_talents=heroABC" in out


def test_lookup_hero_talents_variants():
    # config layout expected by lookup_hero_talents
    profiles.config = {"hero": {"foo": {"foo": "HT1"}, "bar": {"bar": "HT2"}}}
    assert profiles.lookup_hero_talents("foo_DA") == "HT1"
    assert profiles.lookup_hero_talents("bar_VF") == "HT2"


def test_replace_gear_and_placeholders():
    # prepare config and args used by replace_gear
    profiles.config = {
        "gear": {"default": {"main_hand": "weap1", "off_hand": "shield1"}},
        "gems": {"g1": "gem1"},
        "enchants": {"e1": "ench1"},
        "sims": {"sims": {"gearOverride": "none"}},
    }
    profiles.args = types.SimpleNamespace(dir="sims/")
    data = "A${gear.main_hand} B${gems.g1} C${enchants.e1} D${gear.off_hand}"
    out = profiles.replace_gear(data, None)
    assert "weap1" in out
    assert "gem1" in out
    assert "ench1" in out
    # off_hand uses special prefix
    assert "off_hand=shield1" in out


def test_get_sim_files_non_talents():
    profiles.config = {"sims": {"foo": {"files": ["a.simc", "b.simc"]}}}
    assert profiles.get_sim_files("foo") == ["a.simc", "b.simc"]


def test_assure_and_clear_out_folders(tmp_path):
    # assure_path_exists creates parent folder
    target = tmp_path / "some" / "dir" / "file.txt"
    profiles.assure_path_exists(str(target))
    assert (tmp_path / "some" / "dir").exists()

    # clear_out_folders removes files in folder
    folder = tmp_path / "clearme"
    folder.mkdir()
    f1 = folder / "a.txt"
    f1.write_text("x")
    f2 = folder / "b.txt"
    f2.write_text("y")
    profiles.clear_out_folders(str(folder))
    assert not any(folder.iterdir())


def test_build_settings_dungeons_slice_and_route(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    # slice type
    profiles.config = {"dungeonType": "slice"}
    s = profiles.build_settings("any", weights=False, dungeons=True)
    assert 'fight_style="DungeonSlice"' in s

    # route type: create the expected route file
    season = 99
    profname = "standard_combo"
    profiles.config = {"dungeonType": "route", "dungeonSeason": season}
    rdir = Path("internal") / "routes" / f"season{season}" / "standard"
    rdir.mkdir(parents=True, exist_ok=True)
    rfile = rdir / f"{profname}.simc"
    rfile.write_text("ROUTE_CONTENT")
    s2 = profiles.build_settings(profname, weights=False, dungeons=True)
    assert "ROUTE_CONTENT" in s2


def test_build_stats_files(tmp_path, monkeypatch):
    # prepare args and stats.simc
    d = tmp_path
    stats_file = d / "stats.simc"
    stats_file.write_text("BASE_STATS")
    profiles.args = types.SimpleNamespace(dir=str(d) + "/")

    # config to produce combinations
    profiles.config = {
        "stats": {
            "include": ["mastery", "versatility", "haste", "crit"],
            "base": 40,
            "steps": 10,
            "total": 60,
            "min": {"haste": 0, "mastery": 0, "vers": 0, "crit": 0},
            "max": {"haste": 9999, "mastery": 9999, "vers": 9999, "crit": 9999},
        }
    }

    # run
    profiles.build_stats_files()

    out = d / "generated.simc"
    assert out.exists()
    text = out.read_text()
    assert "BASE_STATS" in text
    # should contain at least one profileset line
    assert 'profileset.' in text


def test_create_talent_builds_and_replace_talents(tmp_path, monkeypatch):
    # protect repo-level internal/talents.yml from accidental overwrite
    repo_root = Path(__file__).resolve().parents[2]
    repo_talents = repo_root / "internal" / "talents.yml"
    backup_path = None
    if repo_talents.exists():
        backup_path = tmp_path / "talents.yml.bak"
        shutil.copy(repo_talents, backup_path)
    try:
        # write a small internal/talents.yml inside tmp cwd
        monkeypatch.chdir(tmp_path)
        ty = Path("internal") / "talents.yml"
        ty.parent.mkdir(parents=True, exist_ok=True)
        ty.write_text(
            "builds:\n  mybuild: '1/2/3'\ngenerated:\n  g1: '4/5/6'\n"
        )
        profiles.config = {"forceHeroTalents": True, "hero": {"mybuild": {"mybuild": "HT"}}}
        out = profiles.create_talent_builds()
        assert 'profileset."mybuild"' in out
    finally:
        # restore any repo-level talents.yml that existed
        if backup_path and backup_path.exists():
            repo_talents.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(backup_path, repo_talents)
        else:
            # if the test somehow created a repo-level file, remove it
            if repo_talents.exists():
                try:
                    repo_talents.unlink()
                except Exception:
                    pass


def test_replace_gear_variants(tmp_path, monkeypatch):
    # configure args and config for gearOverride and builds
    profiles.args = types.SimpleNamespace(dir=str(tmp_path) + "/")
    sims_key = profiles.args.dir[:-1]
    profiles.config = {
        "builds": {"b1": {"gearSetup": "special"}},
        "sims": {sims_key: {"gearOverride": "none", "weights": False}},
        "gear": {
            "default": {"main_hand": "wm1", "off_hand": ""},
            "special": {"main_hand": "wm2", "off_hand": "shieldX"},
        },
        "gems": {"g1": "gem1"},
        "enchants": {"e1": "ench1"},
    }

    # talent_string None -> default gear
    data = "X${gear.main_hand}Y${gear.off_hand}Z${gems.g1}${enchants.e1}"
    out = profiles.replace_gear(data, None)
    assert "wm1" in out

    # talent_string provided -> use builds[b1].gearSetup
    out2 = profiles.replace_gear(data, "b1")
    assert "wm2" in out2
    assert "off_hand=shieldX" in out2


def test_build_profiles_basic(tmp_path, monkeypatch):
    # prepare args.dir and file structure
    d = tmp_path
    monkeypatch.chdir(d)
    profiles.args = types.SimpleNamespace(dir=str(d) + "/", dungeons=False, ptr=False)
    (d / "profiles").mkdir()
    (d / "profiles" / "t1").mkdir(parents=True)
    # ensure nested talent folder exists for talent-specific output
    (d / "profiles" / "t1").mkdir(parents=True, exist_ok=True)
    (d / "output").mkdir()
    # create sim file
    sim_file = d / "base.simc"
    sim_file.write_text("LINE1\n${apl}\n${builds}\n")

    # create internal/overrides.simc inside tmp cwd (protect repo file)
    repo_root = Path(__file__).resolve().parents[2]
    repo_over = repo_root / "internal" / "overrides.simc"
    backup_over = None
    if repo_over.exists():
        backup_over = tmp_path / "overrides.simc.bak"
        shutil.copy(repo_over, backup_over)
    try:
        Path("internal").mkdir(exist_ok=True)
        (Path("internal") / "overrides.simc").write_text("OVR\n")
    finally:
        # restore repo-level overrides if necessary
        if backup_over and backup_over.exists():
            repo_over.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(backup_over, repo_over)
        else:
            if repo_over.exists():
                try:
                    repo_over.unlink()
                except Exception:
                    pass

    # monkeypatch find_weights to only enable one profile
    def fake_find(_):
        return {"pw_sa_1": 1}

    monkeypatch.setattr(profiles, "find_weights", fake_find)

    # minimal config
    profiles.config = {
        "sims": {profiles.args.dir[:-1]: {"files": ["base.simc"], "weights": True, "gearOverride": "none"}},
        "builds": {},
        "gear": {"default": {}},
        "gems": {},
        "enchants": {},
        "singleTargetProfiles": [],
        "compositeWeights": {},
        "singleTargetWeights": {},
        "twoTargetWeights": {},
        "threeTargetWeights": {},
        "fourTargetWeights": {},
        "eightTargetWeights": {},
        "councilTargets": 3,
    }

    # avoid create_talent_builds complexity
    monkeypatch.setattr(profiles, "create_talent_builds", lambda: "")

    profiles.build_profiles(None, "APLVAL")

    out_file = d / "profiles" / "base_pw_sa_1.simc"
    assert out_file.exists()
    txt = out_file.read_text()
    assert "APLVAL" in txt
    assert "OVR" in txt
    # settings should include fight style for pw
    assert 'fight_style="Patchwerk"' in txt


def test_build_settings_multiple_and_route_variants(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    # multiple expressions present
    profiles.config = {"dungeonType": "slice"}
    s = profiles.build_settings("pwlm2", weights=False, dungeons=False)
    assert 'fight_style="Patchwerk"' in s
    assert 'fight_style="LightMovement"' in s
    assert 'desired_targets=2' in s

    # route push and generic route file
    season = 7
    profiles.config = {"dungeonType": "route", "dungeonSeason": season}
    # push
    rpush = Path("internal") / "routes" / f"season{season}" / "push"
    rpush.mkdir(parents=True, exist_ok=True)
    (rpush / "push_combo.simc").write_text("PUSH_ROUTE")
    s_push = profiles.build_settings("push_combo", weights=False, dungeons=True)
    assert "PUSH_ROUTE" in s_push
    # generic
    rgen = Path("internal") / "routes" / f"season{season}"
    rgen.mkdir(parents=True, exist_ok=True)
    (rgen / "other.simc").write_text("GEN_ROUTE")
    s_gen = profiles.build_settings("other", weights=False, dungeons=True)
    assert "GEN_ROUTE" in s_gen


def test_build_stats_files_filters(tmp_path, monkeypatch):
    # prepare args and base stats file
    d = tmp_path
    base = d / "stats.simc"
    base.write_text("BASE")
    profiles.args = types.SimpleNamespace(dir=str(d) + "/")

    # create fake distributions to exercise min/max filtering
    def fake_combinations(stats, n):
        # return distributions that will map to different stat counts
        return [
            ("mastery", "mastery", "haste", "crit"),  # higher mastery
            ("versatility", "versatility", "versatility", "versatility"),  # high vers
        ]

    monkeypatch.setattr(profiles, "combinations_with_replacement", fake_combinations)

    profiles.config = {
        "stats": {
            "include": ["mastery", "versatility", "haste", "crit"],
            "base": 40,
            "steps": 10,
            "total": 60,
            "min": {"haste": 0, "mastery": 1000, "vers": 0, "crit": 0},
            "max": {"haste": 9999, "mastery": 9999, "vers": 1, "crit": 9999},
        }
    }

    # run - should create generated.simc but filter out some combos
    profiles.build_stats_files()
    out = d / "generated.simc"
    assert out.exists()
    content = out.read_text()
    assert "BASE" in content


def test_replace_gear_with_override(tmp_path):
    profiles.args = types.SimpleNamespace(dir=str(tmp_path) + "/")
    key = profiles.args.dir[:-1]
    profiles.config = {
        "builds": {},
        "sims": {key: {"gearOverride": "special"}},
        "gear": {"special": {"main_hand": "OVR", "off_hand": ""}},
        "gems": {},
        "enchants": {},
    }
    data = "X${gear.main_hand}Y"
    out = profiles.replace_gear(data, None)
    assert "OVR" in out


def test_build_profiles_skips_when_all_weights_zero(tmp_path, monkeypatch):
    d = tmp_path
    monkeypatch.chdir(d)
    profiles.args = types.SimpleNamespace(dir=str(d) + "/", dungeons=False, ptr=False)
    (d / "profiles").mkdir()
    (d / "output").mkdir()
    (d / "base.simc").write_text("L1\n${apl}\n${builds}\n")
    # protect repo-level overrides.simc while creating test file
    repo_root = Path(__file__).resolve().parents[2]
    repo_over = repo_root / "internal" / "overrides.simc"
    backup_over = None
    if repo_over.exists():
        backup_over = tmp_path / "overrides.simc.bak"
        shutil.copy(repo_over, backup_over)
    try:
        Path("internal").mkdir(exist_ok=True)
        (Path("internal") / "overrides.simc").write_text("O\n")
    finally:
        if backup_over and backup_over.exists():
            repo_over.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(backup_over, repo_over)
        else:
            if repo_over.exists():
                try:
                    repo_over.unlink()
                except Exception:
                    pass

    profiles.config = {
        "sims": {profiles.args.dir[:-1]: {"files": ["base.simc"], "weights": True, "gearOverride": "none"}},
        "builds": {},
        "gear": {"default": {}},
        "gems": {},
        "enchants": {},
        "singleTargetProfiles": [],
        "compositeWeights": {},
        "singleTargetWeights": {},
        "twoTargetWeights": {},
        "threeTargetWeights": {},
        "fourTargetWeights": {},
        "eightTargetWeights": {},
        "councilTargets": 3,
    }

    # find_weights returns empty -> all weights zero -> no files written
    monkeypatch.setattr(profiles, "find_weights", lambda _={}: {})
    # avoid create_talent_builds reading files
    monkeypatch.setattr(profiles, "create_talent_builds", lambda: "")
    profiles.build_profiles(None, "APL")
    # profiles dir should be empty
    assert not any((d / "profiles").iterdir())


def test_replace_talents_no_talents_keyword():
    # when data doesn't contain 'talents=', replace_talents should leave original (code uses data.replace but doesn't assign)
    profiles.config = {"forceHeroTalents": False}
    data = "spec=shadow\nline=1"
    out = profiles.replace_talents("tstring", data, "name_DA")
    assert out == data


def test_get_sim_files_talents(tmp_path, monkeypatch):
    # create talents/builds dir and files inside tmp cwd
    monkeypatch.chdir(tmp_path)
    tb = Path("talents") / "builds"
    tb.mkdir(parents=True, exist_ok=True)
    f = tb / "a.simc"
    f.write_text("x")
    lst = profiles.get_sim_files("talents")
    assert "a.simc" in lst


def test_build_profiles_with_talents(tmp_path, monkeypatch):
    d = tmp_path
    monkeypatch.chdir(d)
    profiles.args = types.SimpleNamespace(dir=str(d) + "/", dungeons=False, ptr=True)
    (d / "profiles").mkdir()
    (d / "profiles" / "t1").mkdir(parents=True, exist_ok=True)
    (d / "output").mkdir()
    (d / "base.simc").write_text("HEADER\n${apl}\n${builds}\n${talents}\n")
    # protect repo-level overrides.simc while creating test file
    repo_root = Path(__file__).resolve().parents[2]
    repo_over = repo_root / "internal" / "overrides.simc"
    backup_over = None
    if repo_over.exists():
        backup_over = tmp_path / "overrides.simc.bak"
        shutil.copy(repo_over, backup_over)
    try:
        Path("internal").mkdir(exist_ok=True)
        (Path("internal") / "overrides.simc").write_text("OVERRIDE\n")
    finally:
        if backup_over and backup_over.exists():
            repo_over.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(backup_over, repo_over)
        else:
            if repo_over.exists():
                try:
                    repo_over.unlink()
                except Exception:
                    pass
    # provide a minimal talents.yml so create_talent_builds can run
    ty = Path("internal") / "talents.yml"
    ty.parent.mkdir(parents=True, exist_ok=True)
    ty.write_text("builds:\n  x: '1'\ngenerated:\n  gx: '2'\n")

    # setup builds with various talent variants
    profiles.config = {
        "sims": {profiles.args.dir[:-1]: {"files": ["base.simc"], "weights": True, "gearOverride": "none"}},
        "builds": {
            "t1": {
                "gearSetup": "default",
                "talents": {
                    "composite": {"string": "COMP_STR", "name": "COMP_NAME"},
                    "single": {"string": "SINGLE_STR", "name": "SINGLE_NAME"},
                    "2t": {"string": "TWO_STR", "name": "TWO_NAME"},
                    "3t": {"string": "THREE_STR", "name": "THREE_NAME"},
                    "8t": {"string": "EIGHT_STR", "name": "EIGHT_NAME"},
                }
            }
        },
        "forceHeroTalents": False,
        "gear": {"default": {}},
        "gems": {},
        "enchants": {},
        "singleTargetProfiles": ["pw_sa_1"],
        "compositeWeights": {},
        "singleTargetWeights": {},
        "twoTargetWeights": {},
        "threeTargetWeights": {},
        "fourTargetWeights": {},
        "eightTargetWeights": {},
        "councilTargets": 3,
    }

    # make find_weights return non-zero for multiple profiles
    def fake_find(_):
        return {"pw_sa_1": 1, "pw_ba_2": 1, "pw_na_3": 1, "pw_sa_8": 1}

    monkeypatch.setattr(profiles, "find_weights", fake_find)

    # run with a talent_string to trigger talent branches
    profiles.build_profiles("t1", "APLVAL")

    # check for files and expected inserted talent strings
    f1 = d / "profiles" / "t1" / "base_pw_sa_1.simc"
    assert f1.exists()
    txt1 = f1.read_text()
    assert "SINGLE_STR" in txt1
    # 2-target
    f2 = d / "profiles" / "t1" / "base_pw_ba_2.simc"
    assert f2.exists()
    assert "TWO_STR" in f2.read_text()
    # 3-target
    f3 = d / "profiles" / "t1" / "base_pw_na_3.simc"
    assert f3.exists()
    assert "THREE_STR" in f3.read_text()
    # 8-target
    f8 = d / "profiles" / "t1" / "base_pw_sa_8.simc"
    assert f8.exists()
    assert "EIGHT_STR" in f8.read_text()
    # ptr should have been added at file start
    assert txt1.startswith("ptr=1")
