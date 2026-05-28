import sys

import pytest

from EchoInStone.utils import torch_device


@pytest.mark.parametrize(
    ("xpu_available", "cuda_available", "mps_available", "expected"),
    [
        (True, True, True, "xpu"),
        (False, True, True, "cuda"),
        (False, False, True, "mps"),
        (False, False, False, "cpu"),
    ],
)
def test_resolve_torch_device_priority(
    monkeypatch, xpu_available, cuda_available, mps_available, expected
):
    mock_torch = sys.modules["torch"]
    monkeypatch.setattr(mock_torch.xpu, "is_available", lambda: xpu_available)
    monkeypatch.setattr(mock_torch.cuda, "is_available", lambda: cuda_available)
    monkeypatch.setattr(
        mock_torch.backends.mps, "is_available", lambda: mps_available
    )
    monkeypatch.setattr(mock_torch, "device", lambda name: name)

    assert torch_device.resolve_torch_device() == expected


@pytest.mark.parametrize(
    ("xpu_available", "cuda_available", "mps_available", "expected_device"),
    [
        (True, False, False, "xpu"),
        (False, True, False, "cuda:0"),
        (False, False, True, "mps"),
        (False, False, False, "cpu"),
    ],
)
def test_resolve_whisper_device_priority(
    monkeypatch, xpu_available, cuda_available, mps_available, expected_device
):
    mock_torch = sys.modules["torch"]
    monkeypatch.setattr(mock_torch.xpu, "is_available", lambda: xpu_available)
    monkeypatch.setattr(mock_torch.cuda, "is_available", lambda: cuda_available)
    monkeypatch.setattr(
        mock_torch.backends.mps, "is_available", lambda: mps_available
    )

    device, _ = torch_device.resolve_whisper_device()
    assert device == expected_device
