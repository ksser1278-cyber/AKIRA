# Lyric Grounding Source Policy

## Accepted Source Classes

- official artist lyric page
- official label or publisher lyric page
- official distributor lyric page tied to the released track
- official upload with directly exposed lyric text
- cross-checked lyric databases when two trusted sources agree line-for-line

## Rejected Source Classes

- unattributed lyric mirrors
- forums and repost blogs
- wiki summaries
- fan-maintained lyric wiki mirrors
- machine-translated pages
- AI-generated summaries or reconstructions

## Tie-Break Rules

- official source overrides non-official source
- if only lyric databases are available, require two independent trusted sources that agree
- a single-source lyric database bundle is not enough
- a licensed service or database mirror can support a bundle, but it does not replace the need for either an official source or a second independent trusted source
- if sources conflict and no official source resolves the conflict, leave the track unsubmitted

## Submission Rule

- `full_text_status` must be `full`
- no partial section bundles
- no paraphrases
- if trusted grounded text cannot be secured, do not submit the track
