## Why

The `/summarizev2` command processes transcriptions from multi-speaker recordings but lacks guidance on maintaining pronoun consistency across speakers — a technique found in AI-Video-Transcriber's summarizer that significantly improves readability of interview and discussion summaries. Adding this and a semantic paragraph grouping hint will improve output quality with minimal prompt changes.

## What Changes

- **ENHANCE**: Add pronoun consistency rules to `<LANGUAGE_RULES>` section of `summarizev2.md` — distinguish interviewer "you" from interviewee "I/we" perspectives, prevent perspective mixing within paragraphs
- **ENHANCE**: Add semantic paragraph grouping guidance inside sections — group sentences by topic with ~400 character soft limit per paragraph for better readability
- **ENHANCE**: Strengthen the "no translation" rule with more explicit phrasing

## Capabilities

### New Capabilities
- `summarization-prompt-quality`: Improved prompt engineering rules for the summarizev2 command covering pronoun consistency, semantic grouping, and language preservation

### Modified Capabilities

## Impact

- **Affected files**: `.cursor/commands/summarizev2.md` only
- **No code changes**: This is a prompt-only improvement
- **No new dependencies**
- **User-facing**: Summaries will have better pronoun consistency in multi-speaker recordings and more readable paragraph structure
