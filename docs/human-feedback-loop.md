# Human Feedback Loop

The next quality gains do not come from scraping more lyrics. They come from collecting better human judgments and using them to refine weak generations.

## Layers

1. Gold review bundle
   - Pull strong candidates into a review queue.
   - Annotate which outputs are actually worth keeping.
   - Store best lines and weak lines for future rewrite supervision.

2. Pairwise preference bundle
   - Compare two systems on the same track.
   - Let a human choose the stronger version.
   - Capture why one option wins.

3. Section rewrite loop
   - Rewrite only the weakest section instead of rerunning the whole song.
   - Merge the revised section back into the full lyric.
   - Re-score the merged result with the same critic.

## Recommended Workflow

1. Run a validated Gemini roundtrip over a batch.
2. Export a gold review bundle from the high-scoring subset.
3. Export a preference bundle when two systems disagree or a revision pass exists.
4. Run section rewrite only for tracks below your operational threshold.
5. Promote approved lyrics and preference decisions into future training assets.

## Current Ado Baseline

- 20-track validated Gemini roundtrip average: `88.59`
- 20-track internal heuristic average: `75.23`
- Section rewrite on a 6-track weak subset: average delta `+0.9`

The implication is simple: the planning dataset is now useful as a control layer, but the strongest next signal has to come from human preference and line-quality judgment.
