# P-code evidence notes

These notes apply only to the `Cowtris.exe` whose SHA-256 is
`4b74269713b7e70b6280a179d1a00399e4b345d92d1fa99db80e6b5e00cbf1df`.
Addresses are virtual addresses in that PE image. The executable is VB6 p-code, so
procedure addresses below identify p-code descriptors rather than native x86 bodies.

## Method

1. Read the PE entry point and the pushed `VB5!` project header address.
2. Walk the VB project, object, and method tables.
3. Recover a procedure's p-code start as `descriptor - ProcSize`.
4. Use the Cowtris 2.00 GPL source to associate surviving module structure with
   established procedure names.
5. Resolve p-code call operands through each module's constant pool.
6. Walk the PE resource directory independently to identify WAVE resource IDs.

The checked-in inspection tool performs steps 1–3, 5, and 6 without third-party
packages. Source-level control flow was also checked using the opcode table from the
open-source Semi VB Decompiler project; the reconstruction does not include or depend
on that project's code.

## Special-cow selection

The selection helper has descriptor `0x00412698` and p-code range
`0x00412640..0x00412698`.

Relevant decoded operations, with readable equivalents, are:

```text
Rnd
push 100
convert 100 to R8
multiply
push 1
convert 1 to R8
add
convert R8 to I2 (VB CInt)
store special-roll

push special-roll
push 5
greater-than
load special-cows option
not
or
branch to normal selection when true

special: CInt(Rnd * 2) + 8
normal:  CInt(Rnd * 6) + 1
```

This is equivalent to the reconstructed function:

```vb
If CInt(Rnd * 100 + 1) <= 5 And bUseSpecialCows Then
    Breed = CInt(Rnd * 2) + 8
Else
    Breed = CInt(Rnd * 6) + 1
End If
```

Because VB `CInt` rounds to the nearest integer rather than truncating:

| Result | Conditional distribution | Overall distribution |
|---|---:|---:|
| Mad Cow (8) | 25% of specials | about 1.125% |
| Holy Cow (9) | 50% of specials | about 2.25% |
| Purple Cow (10) | 25% of specials | about 1.125% |
| Any special | — | about 4.5% |

The exact half-way values use VB's banker's rounding, but those boundary points do not
materially change the distribution.

## Appearance sounds

The Cowtris 2.00 source identifies the baseline routine as `BeginPiece`; its 2.1
descriptor is `0x00416a48`. Near the end of that procedure, p-code branches on the
active cow's breed and calls the `PlaySound` thunk at `0x00401530`:

| Call address | Breed comparison | WAVE resource | Meaning |
|---|---:|---:|---|
| `0x004169f6` | 8 | 101 | `madcow.wav` |
| `0x00416a11` | 9 | 107 | `monks cow 2.wav` |
| `0x00416a2c` | 10 | 108 | `purple.wav` |

This establishes that each special sound plays when the previewed cow becomes the
active falling piece. It is not merely a sound attached to the landing effect.

Resource 101 also appears at `0x0041254f` in `Sub Main`, preserving the older startup
use of the Mad Cow clip. It appears separately in the normal row-completion procedure
when the whole board is cleared, as it did in the 2.00 source.

## Mad Cow landing effect

The special landing branch is within the procedure descriptor `0x00414d84`, matched
to the expanded 2.1 `TransPiece` behavior using the 2.00 baseline.

- At `0x00414be2`, the active breed is compared to 8.
- At `0x00414bf3`, literal resource 109 is pushed.
- At `0x00414bf5`, the `PlaySound` thunk is called.
- The following nested loops range from `centerX - 1` through `centerX + 1` and
  `centerY - 1` through `centerY + 1`.
- Bounds checks use columns 1–10 and stored rows -2–22.
- Each in-bounds `Block` record in that 3x3 neighborhood is replaced with the empty
  block record.

The resource directory identifies 109 as the embedded copy of `EXPLODE.WAV`, with two
bytes of resource padding. Thus the released sequence is `madcow.wav` on appearance,
then `EXPLODE.WAV` when the Mad Cow lands and clears its neighborhood.

## Holy Cow effect

Breed 9 follows a distinct downward-movement path that does not treat settled blocks
as blockers. The traversed board cell is cleared as the one-block cow advances. This
matches the executable's embedded instruction text: “Falls through other blocks,
destroying them.”

No second call to resource 107 occurs in the landing-effects procedure. Its only
gameplay call is the `BeginPiece` appearance call at `0x00416a11`.

## Purple Cow effect

At `0x00414cee`, the landing-effects procedure compares the active breed to 10. That
branch removes/collapses the landing row even if it is incomplete, invokes the
row/statistics helper, and then:

- pushes literal resource 102 at `0x00414d7c`;
- calls `PlaySound` at `0x00414d7e`.

Resource 102 is `Zap.wav`. Resource 108 (`purple.wav`) is called earlier by
`BeginPiece`, so the Purple Cow has an appearance cue and a separate row-removal cue.

## Embedded option and help

The form/string resources contain `Use Special &Cows` and the complete help passage
recorded in [`../source/ui-and-help.reconstructed.txt`](../source/ui-and-help.reconstructed.txt).
The Boolean read by the selection helper confirms that the original UI option gates
special selection; when disabled, only the normal selection branch runs.

## Limits

- New local-variable and private-helper names are not recoverable from this p-code.
- Source statement boundaries, comments, and formatting are reconstructed.
- Animation calls are visible, but their source-level wrapper names are not assigned
  where the name is unnecessary to explain gameplay.
- This artifact intentionally does not attempt to recreate `.frm`/`.frx` files or a
  compilable VB6 project.

