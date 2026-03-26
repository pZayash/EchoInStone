## ADDED Requirements

### Requirement: Pronoun consistency in multi-speaker summaries
The summarization prompt SHALL include rules for maintaining consistent pronoun usage per speaker in multi-speaker recordings. The prompt SHALL instruct the LLM to distinguish interviewer perspectives from interviewee perspectives and prevent mixing speaker viewpoints within a single paragraph.

#### Scenario: Interview with two speakers
- **WHEN** summarizing a recording with an interviewer and an interviewee
- **THEN** the summary maintains consistent pronoun usage: "you" for the interviewer's questions, "I/we" for the interviewee's responses
- **AND** no paragraph mixes perspectives from different speakers

#### Scenario: Multi-participant discussion
- **WHEN** summarizing a recording with multiple discussion participants
- **THEN** the summary attributes viewpoints to specific speakers where possible
- **AND** avoids ambiguous pronoun references

### Requirement: Semantic paragraph grouping
The summarization prompt SHALL include guidance for grouping content by semantic topic within sections, with a soft limit of approximately 400 characters per paragraph to prevent wall-of-text output.

#### Scenario: Long section content
- **WHEN** a summary section contains multiple distinct topics
- **THEN** the content is broken into separate paragraphs by topic
- **AND** each paragraph stays approximately within 400 characters

#### Scenario: Short section content
- **WHEN** a summary section covers a single cohesive topic
- **THEN** the content remains as a single paragraph regardless of the 400-character guideline

### Requirement: Strengthened language preservation
The summarization prompt SHALL explicitly prohibit translation of content into other languages, using unambiguous phrasing to prevent the LLM from translating technical terms or domain-specific vocabulary.

#### Scenario: Mixed-language source with technical terms
- **WHEN** source transcription contains both natural language and technical terms in English
- **THEN** the summary preserves all terms in their original language
- **AND** does not translate any content
