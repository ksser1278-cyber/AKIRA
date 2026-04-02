# Analysis Reporting

## Why This Exists

Raw JSON is useful for pipelines, but it is not a good medium for quickly feeling an artist's vibe.

The reporting step translates:

- imagery clusters
- hook patterns
- emotional flow
- section behavior
- mode candidates

into a short markdown report for humans.

## Command

```powershell
python render_analysis_report.py `
  --artist-analysis lyrics/analyzed/artists/demo.json
```

## Output

- `reports/style/<artist_id>_style_report.md`

## Use Case

Read this report before editing a profile or prompt package. It should answer:

- what kind of lyric world this feels like
- where the hook energy lives
- how the emotional movement behaves
- which mode directions are the best fit
