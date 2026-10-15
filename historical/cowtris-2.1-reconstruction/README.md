# Cowtris 2.1 reference reconstruction

This directory documents the special-cow code added to the original Visual Basic 6
Cowtris 2.1 release. It is a reference reconstruction from the shipped executable,
not recovered original source and not a buildable VB6 project.

The goal is narrower: preserve enough readable, reproducible evidence to answer
questions about the released game's behavior without treating memory, the later
JavaScript port, or the reconstructed names as authoritative.

## Contents

- [`source/special-cows.reconstructed.bas`](source/special-cows.reconstructed.bas)
  is VB-style pseudocode for selection, appearance sounds, and landing effects.
- [`source/ui-and-help.reconstructed.txt`](source/ui-and-help.reconstructed.txt)
  records the special-cow menu and instruction strings embedded in the executable.
- [`evidence/pcode-notes.md`](evidence/pcode-notes.md) ties each conclusion to a
  p-code procedure descriptor and address.
- [`evidence/binary-report.txt`](evidence/binary-report.txt) is a checked-in output
  snapshot from the inspection tool.
- [`evidence/resource-manifest.csv`](evidence/resource-manifest.csv) identifies the
  embedded WAVE resources, including the four special-cow sounds.
- [`tools/inspect_cowtris21.py`](tools/inspect_cowtris21.py) reproduces the binary
  metadata, literal sound-call, resource, and selection-procedure report using only
  the Python standard library.

## Provenance

The analyzed program is the `Cowtris.exe` installed by the historical Cowtris 2.1
installer:

- Archived installer:
  `https://web.archive.org/web/20041205160434id_/http://www.nonsensesoftware.com/Files/download/cowtris2-1.exe`
- Installer SHA-256:
  `a694d599f2f8d30b5c693888392b4aff5b546d73033ad3df3cdcfa037190d0d4`
- Extracted `Cowtris.exe` size: `1,404,928` bytes
- Extracted `Cowtris.exe` SHA-256:
  `4b74269713b7e70b6280a179d1a00399e4b345d92d1fa99db80e6b5e00cbf1df`
- PE timestamp for `Cowtris.exe`: `2003-06-04T03:01:20+00:00`
  (June 3 in US time zones)

The published Cowtris 2.00 VB6 source was used as a naming and structural baseline.
The most relevant baseline file hashes are recorded in
[`evidence/baseline-2.0-manifest.txt`](evidence/baseline-2.0-manifest.txt).

The executable and installer are intentionally not duplicated here. The repository's
existing historical sounds live under `archive/resources/sounds/`.

## Reproducing the report

Extract `Cowtris.exe` from the archived installer, then run from the repository root:

```bash
python3 historical/cowtris-2.1-reconstruction/tools/inspect_cowtris21.py \
  /path/to/Cowtris.exe \
  --sounds-dir archive/resources/sounds
```

The executable hash must match the value above before addresses or byte sequences in
this artifact are assumed to apply.

## Evidence labels

- **Confirmed** means directly visible in p-code, resources, or embedded strings.
- **Baseline-assisted** means the 2.1 binary structure was matched to a named routine
  from the GPL-released 2.00 source.
- **Inferred** means a readable name or source-level arrangement was chosen because
  VB6 p-code does not retain enough information to recover it exactly.

The reconstructed `.bas` file repeats these labels at the relevant sections. Local
variable names, helper names, comments, and formatting are not claimed to be original.

## License

Cowtris is copyright 2000–2003 David Glick and was released under GNU GPL version 2
or later. This reconstruction is a documented derivative/reference representation
and is distributed under the same terms as the rest of the Cowtris source material.
