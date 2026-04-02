# Practical Ado Workflow

## What To Do

1. Put Ado lyric `.txt` or `.md` files into `lyrics/raw/ado/`
2. Run:

```powershell
python run_artist_pipeline.py `
  --artist-id ado `
  --artist-name Ado `
  --raw-dir lyrics/raw/ado
```

The manifest is generated automatically from the files in `lyrics/raw/ado/`.
If the folder only contains the placeholder file, it is ignored and the command will stop with a clear message.

## What You Get

- normalized lyric JSON files
- track analysis JSON files
- artist analysis JSON
- a human-readable style report
- a draft profile scaffold

## Why This Is Practical

You no longer have to edit the manifest by hand or think about each stage separately.

Once the lyric files exist, one command moves the artist through the whole pipeline.
