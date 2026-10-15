Attribute VB_Name = "modGame_SpecialCows_Reconstructed"
'Cowtris 2.1 special-cow reference reconstruction
'---------------------------------------------------------------------------
'Copyright 2000-2003 David Glick; GNU GPL version 2 or later.
'
'THIS IS NOT ORIGINAL OR COMPILABLE SOURCE.
'It is VB6-style pseudocode reconstructed in 2026 from the released Cowtris 2.1
'executable, with Cowtris 2.00 source used to recover established names and types.
'See ../README.md and ../evidence/pcode-notes.md before treating a detail as exact.

Option Explicit

'[CONFIRMED] The published 2.00 enum already contained these three commented names.
'The 2.1 p-code compares the active Breed to numeric values 8, 9, and 10.
Public Enum eCowBreeds_21_Additions
    MadCow = 8
    HolyCow = 9
    PurpleCow = 10
End Enum

'[INFERRED NAME, CONFIRMED ROLE] The executable has a Boolean gate for special cows.
'The form resource calls the corresponding option "Use Special &Cows".
Public bUseSpecialCows As Boolean


Public Function RandomBreed_Reconstructed() As eCowBreeds
'[CONFIRMED ARITHMETIC; INFERRED PROCEDURE NAME]
'
'The released code uses CInt, which rounds rather than truncates. Therefore:
'  - CInt(Rnd * 100 + 1) <= 5 is true for about 4.5% of calls.
'  - CInt(Rnd * 2) produces 0, 1, 2 in a 1:2:1 ratio.
'  - Holy Cow is twice as common as Mad Cow or Purple Cow.

    If CInt(Rnd * 100 + 1) <= 5 And bUseSpecialCows Then
        RandomBreed_Reconstructed = CInt(Rnd * 2) + MadCow
    Else
        RandomBreed_Reconstructed = CInt(Rnd * 6) + Guernsey
    End If
End Function


Private Sub PlaySpecialAppearanceSound_Reconstructed(ByVal Breed As eCowBreeds)
'[CONFIRMED CALLS; SOURCE-LEVEL ARRANGEMENT INFERRED]
'
'These calls occur near the end of BeginPiece. They apply when the cow becomes the
'active falling piece, not when it first appears in the Next preview.

    If Not bSoundEnabled Then Exit Sub

    Select Case Breed
        Case MadCow
            PlaySound 101       'madcow.wav
        Case HolyCow
            PlaySound 107       'monks cow 2.wav
        Case PurpleCow
            PlaySound 108       'purple.wav
    End Select
End Sub


Private Sub ResolveMadCow_Reconstructed(ByVal iBoard As Integer)
'[CONFIRMED EFFECT, BOUNDS, AND SOUND; LOCAL NAMES INFERRED]
'
'The landing-effects procedure compares Breed to 8, plays WAVE resource 109, then
'iterates over the 3x3 neighborhood centered on the one-block cow. Board coordinates
'are checked against the original 1..10 columns and -2..22 stored rows.

    Dim x As Integer, y As Integer
    Dim centerX As Integer, centerY As Integer

    centerX = uBoard(iBoard).CurPiece.Position.x
    centerY = uBoard(iBoard).CurPiece.Position.y

    If bSoundEnabled Then PlaySound 109       'EXPLODE.WAV

    For x = centerX - 1 To centerX + 1
        For y = centerY - 1 To centerY + 1
            If x >= 1 And x <= NUM_COLS _
             And y >= -2 And y <= NUM_ROWS Then
                uBoard(iBoard).Square(x, y) = uEmptyBlock
            End If
        Next y
    Next x

    '[CONFIRMED] The original performs a short visual delay/animation here.
End Sub


Private Sub ResolveHolyCowStep_Reconstructed(ByVal iBoard As Integer)
'[CONFIRMED PLAYER-VISIBLE EFFECT; CONTROL FLOW SIMPLIFIED]
'
'During downward movement, occupied cells do not block the Holy Cow. Each cell in its
'vertical path is replaced with the empty block, producing the documented tunnel.
'Horizontal movement still uses normal collision handling. No second Holy-Cow sound
'is called when the tunnel completes; resource 107 was already played in BeginPiece.

    Dim x As Integer, y As Integer
    x = uBoard(iBoard).CurPiece.Position.x
    y = uBoard(iBoard).CurPiece.Position.y

    uBoard(iBoard).Square(x, y) = uEmptyBlock
    'Continue the normal downward translation until the board floor is reached.
End Sub


Private Sub ResolvePurpleCow_Reconstructed(ByVal iBoard As Integer)
'[CONFIRMED PLAYER-VISIBLE EFFECT AND SOUND; ROW-MOVE HELPER EXPANDED FOR CLARITY]
'
'The entire landing row is removed even when it is incomplete. Rows above it move
'down in the same manner as a normal completed-row removal. The Purple sound itself
'was played in BeginPiece; the landing effect separately plays WAVE 102 (Zap.wav).

    Dim x As Integer, y As Integer, landingRow As Integer
    landingRow = uBoard(iBoard).CurPiece.Position.y

    For y = landingRow To -1 Step -1
        For x = 1 To NUM_COLS
            uBoard(iBoard).Square(x, y) = uBoard(iBoard).Square(x, y - 1)
        Next x
    Next y

    'The released procedure updates the row/score state through an internal helper.
    '[INFERRED] Its exact source-level name and statement boundaries are not retained.
    UpdateStatsForOneRemovedRow_Reconstructed iBoard

    If bSoundEnabled Then PlaySound 102       'Zap.wav
End Sub


Private Sub ResolveSpecialLanding_Reconstructed(ByVal iBoard As Integer)
'[INFERRED WRAPPER] This presents the confirmed branches as readable source.

    Select Case uBoard(iBoard).CurPiece.Breed
        Case MadCow
            ResolveMadCow_Reconstructed iBoard
        Case PurpleCow
            ResolvePurpleCow_Reconstructed iBoard
        Case HolyCow
            'Holy Cow's destruction occurs while moving, not as a landing blast.
    End Select
End Sub

