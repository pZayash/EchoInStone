# Task: Create Summary of Conversation

## Objective
Create a comprehensive summary of the conversation from `speaker_transcriptions.csv` and save it to `summary.md`.

## Requirements

### Input
- Format: CSV containing speaker transcriptions with timestamps
- If source file not mentioned in prompt for this task, use `speaker_transcriptions_redacted.csv` or `speaker_transcriptions.csv` as input if exists
- **If CSV file cannot be obtained**: Use JSON file (`.json` format) as source file instead

### Output
- Target file: `summary.md`, in the same folder as source file; 
- Language is the same, as in source file;
- Format: Markdown document
- If the target file exists, ignore its content. Create new file with number at the end. For example `summary_1.md`, `summary_2.md`

### Restrictions
- Do not create any files, except mentioned in part `Output`
- Read file `speaker_transcriptions.csv` as is, dont try process its context with scripts

### Summary Structure

The summary should include:

1. **Overview**
   - Brief description of the conversation topic
   - Main participants and their roles (if identifiable)
   - Conversation format (meeting/discussion/lecture/live/demo/workshop)
   - Total duration/timeline
2. **Key Topics Discussed**
   - List all major topics covered
   - Organize by theme or chronological order

<optional_for_meeting_discussion>
3. **Decisions Made**
   - Document all decisions reached during the conversation
   - Include any agreements or conclusions

4. **Next Steps**
   - Document planned follow-up actions
   - Extract all tasks assigned or mentioned
   - Include deadlines if mentioned
   - Note responsible parties if identified
   - **Future meetings:** If any future meetings are planned during the conversation, create a separate section "Future Meetings" with:
     - Meeting date/time (if specified)
     - Meeting purpose and agenda
     - Expected deliverables or preparations
     - Participants (if mentioned)

5. **Issues/Problems Identified**
   - List problems discovered or discussed
   - Note any technical issues or limitations

6. **Technical Details** (if applicable)
   - Important technical information discussed
   - Configuration details, system features, etc.

7. **Possible buiseness features to develop** (if applicable)
   - Feature description in Gherkin format
</optional_for_meeting_discussion>

<optional_for_lecture_live_demo_workshop>
3. **Code Examples and Demonstrations**
   - Document all code snippets shown
   - Include specific syntax examples
   - Note any practical demonstrations or live coding sessions
   - Document configuration examples, queries, reports, documents, etc.
   - Include timestamps for when each example was shown

4. **Key Concepts and Best Practices**
   - Important principles discussed
   - Features and capabilities
   - Best practices for development
   - Common patterns and anti-patterns
   - Performance optimization tips

5. **Resources and Materials**
   - Links to documentation mentioned
   - References to software versions discussed
   - Additional learning materials recommended
   - Tools, extensions, or software mentioned
   - Sample files or templates provided

6. **Technical Details**
   - Software version(s) discussed
   - Software details and settings
   - System requirements mentioned
   - Integration with other systems (if applicable)

7. **Common Issues and Solutions**
   - Problems discussed
   - Error handling approaches
   - Troubleshooting tips
   - Known limitations and workarounds
  
8. **Questions and Answers**
   - Document all questions asked by participants
   - Include answers provided by the instructor
   - Note any unresolved questions or topics for follow-up
   - Include timestamps for Q&A sessions

9. **Next Steps and Follow-up**
    - Recommended learning path after the webinar
    - Document any exercises or tasks assigned
    - Include homework or practice recommendations    
    - Additional materials or courses mentioned
    - Community resources (forums, groups, etc.)
    - Future webinars scheduled (if any)
    - Contact information for questions
</optional_for_lecture_live_demo_workshop>

### Formatting Guidelines

- Use clear markdown headings (##, ###)
- Use bullet points for lists
- Include timestamps when referencing specific moments
- Preserve important quotes or specific terminology
- Keep language consistent with the original conversation
- Use code blocks for technical terms or system names
- Use code blocks for all code examples with proper syntax highlighting
- Format code examples with language identifier: ` ```{language_id} `
- Use inline code formatting for terms, methods, properties, objects
- Structure code examples clearly with comments if provided
- Use tables for comparing approaches or listing features

### Quality Standards

- Be concise but comprehensive
- Focus on actionable information
- Maintain chronological flow where relevant
- Highlight important examples, decisions and action items
- Ensure readability and clarity
- Include practical tips and real-world applications