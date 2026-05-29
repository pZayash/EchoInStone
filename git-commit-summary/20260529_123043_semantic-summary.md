# Semantic summary: 20260529_123043

## Контекст

Сессия: исправление недостижимой проверки `os.path.isfile()` в `get_video_downloader`.
Ранний `endswith` по расширению перехватывал все строки с видео-суффиксом до проверки
локального файла; несуществующие пути вроде `missing.mp4` ошибочно получали `VideoDownloader`.

## Изменения

- **EchoInStone/capture/downloader_factory.py**: порядок веток в `get_video_downloader` —
  сначала существующий локальный файл с видео-расширением, затем HTTP(S) URL (полный URL
  или `urlparse.path`).

## Технические детали

- Удалена дублирующая ветка `url.lower().endswith(video_extensions)` перед `isfile`.
- Для URL сохранено сопоставление по `netloc` и расширению в path или в конце строки.
- Поведение: несуществующий локальный путь с `.mp4` → `None` (раньше — `VideoDownloader`).

## Не вошло в коммит

- `memory.md` (untracked) — корневой шаблон памяти, вне scope сессии.

## OpenSpec

- Активных changes нет (`openspec list` → `[]`). Archive не требовался.
