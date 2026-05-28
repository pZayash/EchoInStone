---
name: /youtube-summary
id: youtube-summary
category: Workflow
description: "Транскрипт YouTube (sandbox + yt-dlp) и структурированное резюме ролика"
---

Следуй навыку [.cursor/skills/youtube-video-summary/SKILL.md](../../.cursor/skills/youtube-video-summary/SKILL.md) полностью.

**Вход:** аргумент после `/youtube-summary` — URL YouTube (или id). Опционально язык субтитров через `--sub-lang`.

**Sandbox:** извлечение и форматирование — только `sandbox-run` (см. SKILL §2); на хосте — `mkdir` и `> file`, без `python -c`.

**Без субтитров:** скилл переключается на `poetry run python main.py … --disable_subtitle_first` (Whisper + pyannote).
