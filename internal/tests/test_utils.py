import os

from internal import utils


def test_get_simc_dir_composite_no_talent():
    assert utils.get_simc_dir(None, "profiles") == "profiles/composite/"
    assert utils.get_simc_dir(None, "output") == "output/composite/"


def test_get_simc_dir_dungeons_no_talent():
    assert utils.get_simc_dir(None, "profiles", dungeons=True) == "profiles/dungeons/"
    assert utils.get_simc_dir(None, "output", dungeons=True) == "output/dungeons/"


def test_get_simc_dir_composite_with_talent():
    assert utils.get_simc_dir("archon", "profiles") == "profiles/composite/archon/"
    assert utils.get_simc_dir("archon", "output") == "output/composite/archon/"


def test_get_simc_dir_dungeons_with_talent():
    assert utils.get_simc_dir("archon", "profiles", dungeons=True) == "profiles/dungeons/archon/"
    assert utils.get_simc_dir("archon", "output", dungeons=True) == "output/dungeons/archon/"


def test_cleanup_isolation(tmp_path):
    """Clearing composite folder does not touch dungeons folder and vice versa."""
    import profiles as profiles_module

    composite_dir = tmp_path / "profiles" / "composite"
    dungeons_dir = tmp_path / "profiles" / "dungeons"
    composite_dir.mkdir(parents=True)
    dungeons_dir.mkdir(parents=True)

    (composite_dir / "base_pw_sa_1.simc").write_text("composite profile", encoding="utf8")
    (dungeons_dir / "base_slice.simc").write_text("dungeons profile", encoding="utf8")

    # Clear composite only
    profiles_module.clear_out_folders(str(composite_dir) + os.sep)

    assert not (composite_dir / "base_pw_sa_1.simc").exists(), "composite file should be removed"
    assert (dungeons_dir / "base_slice.simc").exists(), "dungeons file should be untouched"

    # Restore composite file then clear dungeons only
    (composite_dir / "base_pw_sa_1.simc").write_text("composite profile", encoding="utf8")
    profiles_module.clear_out_folders(str(dungeons_dir) + os.sep)

    assert (composite_dir / "base_pw_sa_1.simc").exists(), "composite file should be untouched"
    assert not (dungeons_dir / "base_slice.simc").exists(), "dungeons file should be removed"
