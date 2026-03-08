**Trinkets Config & Build Script**

- **Location**: `trinkets.yml` lives in this folder alongside `build_trinkets.py` and `base.simc`.
- **Purpose**: Define trinket entries (dungeons / other / raid) and produce `.simc` files used for SimulationCraft runs.

**YAML Structure**

- Top-level optional `item_levels` map: define named lists of ilevels you can reuse across categories. Example:

```yaml
item_levels:
  dungeons: [697]
  other: [697]
  raid: [697, 710, 717, 730]
  delves: [710]
```

- **Top-level sections**: `dungeons`, `other`, `raid` (any unknown sections are ignored).
- **Each section** contains:
  - **`item_levels`**: either a string referencing one of the top-level item_levels keys (e.g. `"dungeons"`) or a list of integers. The script resolves the section-level value against the top-level map if a string is provided.
  - **`trinkets`**: list of trinket entries.

Item-level resolution priority:
- Per-trinket `item_levels` (if present) take highest precedence. They may be a list or a string key referencing the top-level map.
- Then the section's `item_levels` (list or string key).
- If neither is present, no profiles will be emitted for that trinket/section.

**Trinket entry fields**

- **`id`**: (required) numeric item id for the trinket.
- **`name`**: (required) display name used in the `profileset` label. Use the same human-readable casing you want to see in labels.
- **`option`** or **`options`**: (optional) list of option objects to generate alternate profiles for trinkets that have variants.

Option object keys:

- **`name`**: (required) short option name (e.g. Haste, Mastery). This is used in the generated profile label and as the suffix for the option-specific `trinket1=` identifier (normalized and lowercased).
- **`value`**: (required) either a single string or a list of strings. Each string is written verbatim as a `profileset` assignment line following the generated `trinket1=` line. Example values are `midnight.crucible_of_erratic_energies_violence=1` or a list of such assignment strings to produce multiple assignment lines for a single option.

Example — multi-value option (from `trinkets.yml`):

YAML:
```
- id: 264507
  name: "Crucible_of_Erratic_Energies"
  option:
    - name: "All"
      value:
        - "midnight.crucible_of_erratic_energies_violence=1"
        - "midnight.crucible_of_erratic_energies_sustenance=1"
        - "midnight.crucible_of_erratic_energies_predation=1"
```

Generates (for ilevel `263`):
```
profileset."Crucible_of_Erratic_Energies_All_263"+=trinket1=crucible_of_erratic_energies_all,id=264507,ilevel=263
profileset."Crucible_of_Erratic_Energies_All_263"+=midnight.crucible_of_erratic_energies_violence=1
profileset."Crucible_of_Erratic_Energies_All_263"+=midnight.crucible_of_erratic_energies_sustenance=1
profileset."Crucible_of_Erratic_Energies_All_263"+=midnight.crucible_of_erratic_energies_predation=1
```

Notes about normalization

- The script derives the `trinket1=` identifier by lowercasing the `name` and replacing non-alphanumeric characters with underscores (e.g. `Soleahs_Secret_Technique` -> `soleahs_secret_technique`).
- For option-specific trinket ids the script appends the normalized option name (also lowercased and cleaned) separated by an underscore: e.g. `soleahs_secret_technique_haste`.

Script usage

- Basic (generate files in this folder):
  - `python build_trinkets.py`
- Dry-run (print generated content to stdout):
  - `python build_trinkets.py --dry-run`
- Specify custom input/output/base paths:
  - `python build_trinkets.py --in-file path\to\trinkets.yml --out-dir path\to\out --base-file path\to\base.simc`

Behavior details

- The script writes three output files: `dungeons.simc`, `other.simc`, and `raid.simc` (one per recognized top-level section).
- If a `base.simc` file is present (by default looked for next to the YAML), its contents are written into each output file before the generated `profileset` lines. This mirrors the existing example files.
- If the base file is missing the script will still generate profile lines but will not error.

Dependencies

- Python 3.8+ and the `PyYAML` package:
  - `pip install pyyaml`

Extending the format

- If you want different assigned values than `name.lower()`, use the optional `assign` key inside option objects.
- If you want to add more per-trinket custom output lines the script can be extended; open a PR or tell me what format you'd prefer and I can modify `build_trinkets.py`.

Contact

- If anything generated looks off, run with `--dry-run` and paste the output or open an issue in the repo.
