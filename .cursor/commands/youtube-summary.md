---
name: /youtube-summary
id: youtube-summary
category: Workflow
description: "Транскрипт YouTube через echoinstone и структурированное резюме ролика"
---

Следуй навыку [.cursor/skills/youtube-video-summary/SKILL.md](../../.cursor/skills/youtube-video-summary/SKILL.md) полностью.

**Вход:** аргумент после `/youtube-summary` — URL YouTube (или id).

**CLI:** `echoinstone "URL"` (глобальный шорткат; параметры — [docs/ai/echoinstone-cli.md](../../docs/ai/echoinstone-cli.md)). Без однострочников и без `sandbox-run` для транскрипта.

**Полная диаризация:** `echoinstone "URL" --disable_subtitle_first` (Whisper + pyannote).
