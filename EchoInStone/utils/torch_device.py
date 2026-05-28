import logging

import torch


def _xpu_is_available() -> bool:
    xpu_module = getattr(torch, "xpu", None)
    return bool(xpu_module and xpu_module.is_available())


def resolve_torch_device() -> torch.device:
    if _xpu_is_available():
        return torch.device("xpu")
    if torch.cuda.is_available():
        return torch.device("cuda")
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def resolve_whisper_device() -> tuple[str, torch.dtype]:
    if _xpu_is_available():
        return "xpu", torch.float16
    if torch.cuda.is_available():
        return "cuda:0", torch.float16
    if torch.backends.mps.is_available():
        return "mps", torch.float16
    return "cpu", torch.float32


def log_accelerator_info(logger: logging.Logger) -> None:
    logger.debug("PyTorch version: %s", torch.__version__)
    logger.debug("CUDA available: %s", torch.cuda.is_available())
    logger.debug("MPS available: %s", torch.backends.mps.is_available())

    xpu_available = _xpu_is_available()
    logger.debug("XPU available: %s", xpu_available)
    if not xpu_available:
        return

    xpu_module = getattr(torch, "xpu", None)
    if xpu_module is None:
        return

    logger.debug("XPU device count: %s", xpu_module.device_count())
    if xpu_module.device_count() > 0:
        logger.debug("XPU device name: %s", xpu_module.get_device_name(0))
