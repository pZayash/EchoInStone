import json
import os

import numpy as np
import pytest

from EchoInStone.utils.data_saver import DataSaver


def test_save_visual_enrichment_merges_by_timestamp(tmp_path):
    saver = DataSaver(output_dir=str(tmp_path))
    saver.save_visual_enrichment(
        [{"timestamp_seconds": 10.0, "extracted_text": "first", "trigger": "phrase_timestamp"}]
    )
    saver.save_visual_enrichment(
        [{"timestamp_seconds": 20.0, "extracted_text": "second", "trigger": "phrase_timestamp"}]
    )
    path = tmp_path / "visual_enrichment.json"
    with open(path, encoding="utf-8") as handle:
        payload = json.load(handle)
    assert len(payload["entries"]) == 2


def test_save_job_metadata_absolute_path(tmp_path):
    saver = DataSaver(output_dir=str(tmp_path))
    video = tmp_path / "video.mp4"
    video.write_text("stub")
    saver.save_job_metadata("job1", "input.mp4", str(video), True)
    with open(tmp_path / "job_metadata.json", encoding="utf-8") as handle:
        metadata = json.load(handle)
    assert os.path.isabs(metadata["source_video_path"])
    assert metadata["job_id"] == "job1"


def test_run_pass_two_missing_metadata(tmp_path):
    from main import run_pass_two

    assert run_pass_two(str(tmp_path), "1:00") == 1
