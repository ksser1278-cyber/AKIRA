# Corpus Audit

After large-scale scraping, the next step is not immediate model training. First run a corpus audit to measure:

- manifest coverage versus raw files
- normalized and analyzed document coverage
- per-track quality blockers such as missing files, very short text, or unusable normalization
- training eligibility at the artist and track level

Run it like this:

```powershell
python audit_corpus.py `
  --project-root .
```

Default outputs:

- `reports/quality/corpus_audit.json`
- `reports/quality/corpus_audit.md`

Recommendation meanings:

- `ready`: enough normalized and analyzed coverage to convert into derived training data now
- `needs_review`: partially usable, but manual QA or normalization improvements are recommended
- `blocked`: do not use for training yet

Current blockers are expected during active scraping. On a fresh bulk run, most artists will stay `blocked` until normalization and lyric analysis complete.
