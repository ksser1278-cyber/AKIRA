# Generation Safety Lyric Grounding Source Acquisition

- status: `open`
- blocked phase: `phase1_core_cleanup`
- tracks: `16`
- artists: `6`

## Goal

Acquire trusted Japanese lyric grounding inputs for the blocked phase1 tracks before any further phase1 retry.

Required output per track:
- trusted lyric source references
- source notes that are sufficient for later internal normalization
- exact or tightly transcribed Japanese `sections`
- exact or tightly transcribed Japanese `hook_lines`

## Source Policy

Allowed source classes:
- official artist / label / publisher lyric pages
- official distributor lyric pages tied to the released track
- official artist or publisher uploads that expose lyric text directly
- cross-checked lyric databases when two trusted sources agree line-for-line

Disallowed source classes:
- unattributed lyric mirrors
- forums, repost blogs, and copy aggregators
- wiki summaries
- fan-maintained lyric wiki mirrors
- machine-translated lyric pages
- AI-generated lyric summaries or reconstructions

Tie-break rules:
- official source wins over non-official source
- if only non-official lyric databases are available, require two cross-checked sources that agree
- a single-source lyric database bundle is not acceptable
- a licensed service lyric page can support a bundle, but it does not replace the need for either an official source or a second independent trusted source
- if sources disagree and no official source resolves the conflict, leave the track unsubmitted

## Submission Completeness

- `lyric_ground_truth.full_text_status` must be `full`
- partial bundles are not acceptable for this workflow
- if exact or tightly transcribed grounded text cannot be secured, leave the track unsubmitted

## Artists

- `iyowa`: `iyowa_1000_nen_ikiteiru`, `iyowa_apricot`, `iyowa_heat_abnormal`
- `kairiki_bear`: `kairiki_bear_alkali_rettoushou`, `kairiki_bear_shippaisaku_shoujo`
- `kanaria`: `kanaria_daino_tekina_rendezvous`, `kanaria_eye`, `kanaria_mira`
- `maretu`: `maretu_darling`, `maretu_umitagari`, `maretu_white_happy`
- `neru`: `neru_abstract_nonsense`, `neru_law_evading_rock`, `neru_lost_ones_weeping`
- `syudou`: `syudou_bakushou`, `syudou_call_boy`
