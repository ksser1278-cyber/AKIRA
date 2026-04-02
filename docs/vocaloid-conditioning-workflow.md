# Vocaloid Conditioning Workflow

This is the operational path for the new `PinocchioP + DECO*27` anchor benchmark.

## Queue Files

- [pinocchiop/conditioning_queue.json](C:\JPop_Songwriter\AKIRA ENGINE\data\reference_tracks\pinocchiop\conditioning_queue.json)
- [deco27/conditioning_queue.json](C:\JPop_Songwriter\AKIRA ENGINE\data\reference_tracks\deco27\conditioning_queue.json)

## Per-Track Completion Rule

A track is ready only when these are filled:

1. `lyrics`
2. `credits`
3. `release year`
4. `hook lines`
5. `section map`
6. `prompt conditioning`

## Recommended Order

1. complete all `PinocchioP` ironic_meta anchors
2. complete all `DECO*27` direct_emotional_pop anchors
3. complete dark_cute_breakdown anchors from both sides

This order is deliberate.

- it establishes the two cleanest poles first
- then fills the hybrid lane after the planner and critic have better boundaries

## Output Target

Each queue item should eventually become:

- `data/reference_tracks/<artist>/<track>.conditioning.json`

The queue should then be updated from `pending` to:

- `in_progress`
- `drafted`
- `validated`

## Next Benchmark Gate

Do not retune the planner on broad intuition.

Retune only after:

- at least `5` PinocchioP anchors are validated
- at least `5` DECO*27 anchors are validated

That is the minimum useful subculture benchmark.
