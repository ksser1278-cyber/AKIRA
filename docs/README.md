# Docs Index

This directory still contains historical design and workflow documents.

Not all documents reflect the reduced rebuild state.
Use the files below as the current starting point.

## Current Docs

- [C:\JPop_Songwriter\AKIRA ENGINE\docs\cli-skeleton.md](C:\JPop_Songwriter\AKIRA ENGINE\docs\cli-skeleton.md)
  - current command surface through `akira.py`
- [C:\JPop_Songwriter\AKIRA ENGINE\docs\akira-supervised-training-schema.md](C:\JPop_Songwriter\AKIRA ENGINE\docs\akira-supervised-training-schema.md)
  - supervised training sample contract
- [C:\JPop_Songwriter\AKIRA ENGINE\docs\lyric-technique-extraction-fields.md](C:\JPop_Songwriter\AKIRA ENGINE\docs\lyric-technique-extraction-fields.md)
  - extraction contract for turning large lyric corpora into reusable songwriting-technique records
- [C:\JPop_Songwriter\AKIRA ENGINE\docs\sound-profile-field-set.md](C:\JPop_Songwriter\AKIRA ENGINE\docs\sound-profile-field-set.md)
  - sound-intelligence extraction contract for arrangement, texture, energy, and vocal-performance control
- [C:\JPop_Songwriter\AKIRA ENGINE\docs\training-data-shaping.md](C:\JPop_Songwriter\AKIRA ENGINE\docs\training-data-shaping.md)
  - derived training data shaping notes
- [C:\JPop_Songwriter\AKIRA ENGINE\docs\suno-prompt-asset-schema.md](C:\JPop_Songwriter\AKIRA ENGINE\docs\suno-prompt-asset-schema.md)
  - prompt-ready packaging contract for Suno-style generation assets
- [C:\JPop_Songwriter\AKIRA ENGINE\docs\rights-cleared-training-corpus.md](C:\JPop_Songwriter\AKIRA ENGINE\docs\rights-cleared-training-corpus.md)
  - current rule for unblocking supervised training
- [C:\JPop_Songwriter\AKIRA ENGINE\docs\metadata-source-policy.md](C:\JPop_Songwriter\AKIRA ENGINE\docs\metadata-source-policy.md)
  - rule for using VocaDB, Vocaloid Wiki, and other catalog sources as metadata-only support
- [C:\JPop_Songwriter\AKIRA ENGINE\docs\vocaloid-corpus-inclusion-policy.md](C:\JPop_Songwriter\AKIRA ENGINE\docs\vocaloid-corpus-inclusion-policy.md)
  - scope rule for keeping the large reference corpus strictly Vocaloid-focused
- [C:\JPop_Songwriter\AKIRA ENGINE\reports\planning\vocaloid_metadata_10k_roadmap.md](C:\JPop_Songwriter\AKIRA ENGINE\reports\planning\vocaloid_metadata_10k_roadmap.md)
  - operating roadmap for scaling the Vocaloid metadata corpus to 10,000 tracks
- [C:\JPop_Songwriter\AKIRA ENGINE\reports\planning\rights_cleared_corpus_acquisition_plan.md](C:\JPop_Songwriter\AKIRA ENGINE\reports\planning\rights_cleared_corpus_acquisition_plan.md)
  - active intake workflow for a training-eligible corpus

## Historical / Needs Triage

Most other docs in this directory describe older pipeline surfaces, larger pre-quarantine data layouts, or experimental workflows.

Treat them as reference material, not as the current execution contract.

## Current Rule

When rebuilding a workflow:

1. trust `akira.py` and `src/akira_engine/cli/` first
2. trust active root layout second
3. consult older docs only when you need archived design context
