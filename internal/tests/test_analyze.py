from internal import analyze as analyze_module


def test_analyze_reads_dungeons_statweights(tmp_path, monkeypatch):
    sim_dir = tmp_path / "talents"
    output_dir = sim_dir / "output" / "dungeons"
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "statweights.csv").write_text(
        "profile,actor,DD,DPS\ntalents_0_algethar,Base,1,100\n",
        encoding="utf8",
    )

    monkeypatch.chdir(output_dir)
    monkeypatch.setattr(
        analyze_module,
        "config",
        {
            "councilTargets": 3,
            "dungeonType": "route",
            "analyze": {
                "markdown": False,
                "csv": False,
                "json": False,
                "dungeonCharts": False,
            },
            "sims": {"talents": {"files": ["a.simc"]}},
            "builds": {},
        },
    )

    captured = {}

    def fake_read_csv(path, usecols):
        captured["path"] = path

        class FakeData:
            def iterrows(self):
                return iter([])

        return FakeData()

    monkeypatch.setattr(analyze_module.pandas, "read_csv", fake_read_csv)
    monkeypatch.setattr(
        analyze_module, "build_results", lambda *args, **kwargs: {"Base": 0}
    )
    monkeypatch.setattr(
        analyze_module, "clear_output_files", lambda *args, **kwargs: None
    )
    monkeypatch.setattr(analyze_module, "build_readme_md", lambda *args, **kwargs: None)

    analyze_module.analyze(None, "talents/", True, False, 0)

    assert captured["path"] == "output/dungeons/statweights.csv"


def test_resolve_sim_steps_autodiscovers_trinket_item_levels(monkeypatch):
    monkeypatch.setattr(
        analyze_module,
        "config",
        {
            "sims": {
                "trinkets": {"steps": [285, 298]},
            }
        },
    )

    results = {
        "Base": 100,
        "Eye_of_the_Drowning_Void_285": 101,
        "Darkmoon_Dominion_Void_295": 102,
        "Locus_Walkers_Ribbon_298": 103,
    }

    steps = analyze_module.resolve_sim_steps("trinkets/", results)

    assert steps == [285, 295, 298]


def test_resolve_sim_steps_uses_config_for_non_trinkets(monkeypatch):
    monkeypatch.setattr(
        analyze_module,
        "config",
        {
            "sims": {
                "enchants": {"steps": [1, 2]},
            }
        },
    )

    results = {
        "Base": 100,
        "Mark_of_the_Worldsoul_2": 101,
    }

    steps = analyze_module.resolve_sim_steps("enchants/", results)

    assert steps == [1, 2]


def test_resolve_sim_steps_trinkets_defaults_to_dps_when_no_config_or_suffixes(
    monkeypatch,
):
    monkeypatch.setattr(
        analyze_module,
        "config",
        {
            "sims": {
                "trinkets": {},
            }
        },
    )

    results = {
        "Base": 100,
        "Some_Profile_With_No_Item_Level": 101,
    }

    steps = analyze_module.resolve_sim_steps("trinkets/", results)

    assert steps == ["DPS"]
