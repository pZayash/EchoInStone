## Context

EchoInStone's summarization is performed by the `/summarizev2` Cursor command (`.cursor/commands/summarizev2.md`), an LLM prompt that processes speaker transcription CSV/JSON files into structured markdown summaries. The prompt handles meeting and lecture formats with detailed output schemas.

Analysis of AI-Video-Transcriber's `summarizer.py` revealed prompt engineering techniques that address gaps in the current summarizev2 prompt, specifically around multi-speaker pronoun handling and paragraph organization.

## Goals / Non-Goals

**Goals:**
- Improve pronoun consistency in summaries of multi-speaker recordings
- Add semantic paragraph grouping guidance for better readability
- Strengthen language preservation rules

**Non-Goals:**
- Changing the output format or section structure of summarizev2
- Adding AI-powered post-processing pipeline (out of scope — this is prompt-only)
- Implementing chunking or hierarchical summarization (LLM handles context natively)

## Decisions

### Pronoun consistency rule
**Decision**: Add a new rule #4 under `<LANGUAGE_RULES>` section.

The rule instructs the LLM to maintain consistent pronoun usage per speaker and explicitly distinguish interviewer ("you") from interviewee ("I/we") perspectives. This prevents confusing perspective shifts that occur when the LLM paraphrases different speakers' words within the same paragraph.

Source: AI-Video-Transcriber's content optimization prompt requires "pronoun consistency critical for interviews" and forbids mixing speaker perspectives.

### Semantic paragraph grouping
**Decision**: Add guidance in `<FORMATTING_RULES>` section for grouping content by semantic topic within sections, with a soft limit of ~400 characters per paragraph.

This prevents wall-of-text summaries where an entire section is one paragraph. The 400-character guidance (not hard limit) encourages natural paragraph breaks at topic boundaries.

### Language rule strengthening
**Decision**: Add explicit "absolutely do not translate" phrasing to rule #2 under `<LANGUAGE_RULES>`.

Current rule says "Write entire summary in detected language" — this is sometimes interpreted as permission to translate technical terms. Stronger phrasing prevents this.

## Risks / Trade-offs

### Prompt length increase
**Risk**: Additional rules increase prompt token count.
**Mitigation**: Additions are ~100 tokens total — negligible impact on context window.

### Over-constraining LLM behavior
**Risk**: Too many rules may cause the LLM to focus on compliance over quality.
**Mitigation**: Rules are framed as guidance, not rigid constraints. The pronoun rule only applies to multi-speaker content.
