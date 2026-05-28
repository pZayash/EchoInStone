# Semantic summary: 260528_151235

## Контекст

Исправлены device/API регрессии после XPU-ориентированных отладочных правок:

- восстановлена кроссплатформенная инициализация устройств без потери приоритета Intel XPU;
- убраны небезопасные обращения к `torch.xpu` при старте transcriber;
- выровнен контракт возврата `AudioProcessingOrchestrator.extract_and_transcribe`.

## Изменения

- Добавлен модуль `EchoInStone/utils/torch_device.py`:
  - `resolve_torch_device()` с порядком `xpu -> cuda -> mps -> cpu`;
  - `resolve_whisper_device()` с тем же приоритетом;
  - `log_accelerator_info(logger)` с безопасным доступом к XPU-методам только при доступном XPU.
- `EchoInStone/processing/pyannote_diarizer.py` переведен с hardcode `torch.device("xpu")` на общий resolver.
- `EchoInStone/processing/whisper_audio_transcriber.py`:
  - удалены 4 `print()` с потенциальным падением на не-XPU машинах;
  - подключены `log_accelerator_info` и `resolve_whisper_device`.
- `EchoInStone/processing/audio_processing_orchestrator.py`:
  - `extract_and_transcribe` теперь всегда возвращает tuple
    `Tuple[Optional[list], Optional[list]]`.

## Тесты

- Добавлен `tests/test_torch_device.py` (проверка приоритета выбора устройства).
- Добавлен `tests/test_audio_processing_orchestrator.py` (проверка стабильного tuple-контракта).
- Прогон:
  - `poetry run pytest tests/test_torch_device.py tests/test_audio_processing_orchestrator.py tests/test_transcriber_backends.py -v --no-header --override-ini="addopts="`
  - результат: `22 passed`.

## Что не вошло

Только touched-файлы текущей задачи; без изменений в `results/**`, `diarization/**`,
логах, медиа и секретах.
