from pathlib import Path

import top


def test_get_top_talents_skips_missing_results(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    results_dir = Path("talents") / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    existing = results_dir / "Results_Composite.csv"
    existing.write_text(
        "profile,actor,DPS,increase,\n"
        "Composite,Base,10000,0%,\n"
        "Composite,AR_EC_SW_VF_nzoth_yogg_cthun_foo_ME,10500,5%,\n",
        encoding="utf8",
    )

    # Dungeons-Route intentionally missing
    output = top.get_top_talents(
        ["Composite", "Dungeons-Route"],
        [("AR_EC_SW_VF_nzoth_yogg_cthun", "_ME")],
        str(results_dir),
        matches=1,
        jitter=1,
    )

    assert "AR_EC_SW_VF_nzoth_yogg_cthun_foo_ME" in output


def test_get_top_talents_matches_role_suffix_when_name_contains_mis_tag(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)

    results_dir = Path("talents") / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    existing = results_dir / "Results_Composite.csv"
    existing.write_text(
        "profile,actor,DPS,increase,\n"
        "Composite,Base,10000,0%,\n"
        "Composite,AR_EC_SW_VF_nzoth_yogg_cthun_1_Mis_IV_ME,11000,10%,\n",
        encoding="utf8",
    )

    output = top.get_top_talents(
        ["Composite"],
        [("AR_EC_SW_VF_nzoth_yogg_cthun", "_ME")],
        str(results_dir),
        matches=0,
        jitter=1,
    )

    assert "AR_EC_SW_VF_nzoth_yogg_cthun_1_Mis_IV_ME" in output


def test_get_base_actor_uses_mode_scoped_profiles(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    profile_dir = Path("talents") / "profiles" / "composite" / "t1"
    profile_dir.mkdir(parents=True, exist_ok=True)
    profile_file = profile_dir / "base_pw_sa_1.simc"
    profile_file.write_text(
        "line1\nline2\nmain_hand=foo\nline4\n",
        encoding="utf8",
    )

    head = top.get_base_actor(ptr=False)

    assert "main_hand=foo\n" in head
