# AKIRA Professional Song Quality Target

## Goal

AKIRA is not targeting prompt novelty alone.

The end state is a generation system that can repeatedly produce songs with the level of finish expected from a working professional songwriter and producer.

That means the system must support:

- strong hook behavior
- coherent section motion
- controlled emotional arc
- non-generic lyric surface
- arrangement lift and release
- sound texture specificity
- prompt packaging that is reusable without collapsing into generic output

## Working Definition

A track is closer to the target only when all of these are true:

1. `lyric control`
   - section behavior is known
   - hook behavior is explicit
   - emotional arc is visible
   - imagery and diction are not placeholder-level

2. `sound control`
   - arrangement motion is described
   - vocal character is described
   - texture and production markers are specific
   - negative anchors block generic drift

3. `generation control`
   - metadata, lyric technique, and sound profile can be joined
   - prompt-ready packaging can be exported
   - blocked reasons are explicit and reducible

4. `reuse safety`
   - records are structured enough to be transformed into Suno-style prompt assets
   - the same assets can later support evaluation or training workflows

## Quality Levels

### 1. `metadata_only`

The track is cataloged but cannot support serious song generation.

### 2. `joinable`

Metadata and lyric technique exist in the same track-id space.
This is the first practical threshold for generation readiness.

### 3. `prompt_ready`

The track can export a usable prompt asset with lyric and sound support.

### 4. `production_candidate`

The prompt asset contains enough lyric, sound, and negative-control detail to be worth spending generation budget on.

### 5. `professional_target`

The record has enough structural, lyrical, and sound detail to serve as a high-confidence model for professional-grade song generation.

## Operational Rule

Corpus growth alone does not count as progress toward the final goal.

Progress is measured by:

- more `joinable` tracks
- more `prompt_ready` tracks
- more `production_candidate` tracks
- higher ratio of non-generic sound and lyric anchors per track

## Immediate Implication

All future generation work should be auditable against this quality target.

That requires a machine-readable audit layer over `track_generation_record`.
