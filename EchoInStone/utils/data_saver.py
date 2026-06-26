import os
import json
import csv
import logging
import time
import uuid
from typing import Optional, List
import cv2

logger = logging.getLogger(__name__)

class DataSaver:
    def __init__(self, output_dir="data_output"):
        """
        Initializes the DataSaver with a specified output directory.

        Args:
            output_dir (str): The directory where data files will be saved.
        """
        self.output_dir = output_dir

    def save_data(self, filename: str, data):
        """
        Saves data to a file in the specified output directory.

        Args:
            filename (str): The name of the file to save the data.
            data: The data to be saved. Can be a dictionary, list, or string.
        """
        # Create the output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        logger.debug(f"Output directory created or already exists: {self.output_dir}")

        file_path = os.path.join(self.output_dir, filename)

        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                if isinstance(data, (list, dict)):
                    json.dump(data, file, ensure_ascii=False, indent=4)
                else:
                    file.write(str(data))
            logger.info(f"Data saved to {file_path}")
        except Exception as e:
            logger.error(f"Error saving data: {e}")

    def save_transcriptions_to_csv(self, filename: str, transcriptions):
        """
        Saves speaker transcriptions to a CSV file.
        
        Args:
            filename (str): The name of the CSV file to save the data.
            transcriptions (list): List of tuples (speaker, start, end, text) or list of lists.
        """
        # Create the output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        logger.debug(f"Output directory created or already exists: {self.output_dir}")
        
        file_path = os.path.join(self.output_dir, filename)
        
        try:
            with open(file_path, 'w', encoding='utf-8', newline='') as file:
                writer = csv.writer(file)
                # Write header
                writer.writerow(["speaker", "start", "end", "text"])
                # Write data rows
                for row in transcriptions:
                    # Handle both tuple and list formats
                    if isinstance(row, (tuple, list)):
                        writer.writerow(row)
                    else:
                        logger.warning(f"Unexpected row format: {row}")
            logger.info(f"CSV saved to {file_path}")
        except Exception as e:
            logger.error(f"Error saving CSV: {e}")

    def save_scene_analysis(self, filename: str, scenes):
        """
        Saves scene analysis results in the standard JSON format.

        Args:
            filename (str): The name of the scene analysis JSON file.
            scenes (list): List of scene analysis records.
        """
        self.save_data(filename, {"scenes": scenes})

    def save_visual_enrichment(self, entries: list, filename: str = "visual_enrichment.json"):
        """Save or merge visual enrichment entries ordered by timestamp."""
        file_path = os.path.join(self.output_dir, filename)
        existing: list = []
        if os.path.isfile(file_path):
            try:
                with open(file_path, encoding="utf-8") as handle:
                    payload = json.load(handle)
                existing = payload.get("entries", [])
            except (json.JSONDecodeError, TypeError):
                existing = []

        merged = {round(e["timestamp_seconds"], 2): e for e in existing}
        for entry in entries:
            key = round(float(entry["timestamp_seconds"]), 2)
            merged[key] = entry

        ordered = sorted(merged.values(), key=lambda e: e["timestamp_seconds"])
        self.save_data(filename, {"entries": ordered})

    def save_job_metadata(
        self,
        job_id: str,
        echo_input: str,
        source_video_path: str | None,
        video_analysis_enabled: bool,
        filename: str = "job_metadata.json",
    ):
        """Persist job metadata for two-pass enrichment."""
        payload = {
            "job_id": job_id,
            "echo_input": echo_input,
            "source_video_path": (
                os.path.abspath(source_video_path) if source_video_path else None
            ),
            "video_analysis_enabled": video_analysis_enabled,
        }
        self.save_data(filename, payload)

    def load_job_metadata(self, filename: str = "job_metadata.json") -> dict | None:
        """Load job metadata from the output directory."""
        file_path = os.path.join(self.output_dir, filename)
        if not os.path.isfile(file_path):
            return None
        try:
            with open(file_path, encoding="utf-8") as handle:
                return json.load(handle)
        except (json.JSONDecodeError, TypeError):
            return None

    def save_image_artifact(
        self,
        job_id: Optional[str],
        scene_id: Optional[int],
        image,
        engine: str,
        variant: str,
        preprocessing: Optional[List[str]] = None,
        ocr_confidence: Optional[float] = None,
        text_excerpt: Optional[str] = None,
        max_per_scene: int = 10,
        image_format: str = "png",
    ) -> Optional[str]:
        """
        Persist an image artifact used for OCR and append an entry to a companion manifest.

        Returns the filename written or None on failure.
        """
        try:
            root_dir = self.output_dir
            resolved_job_id = job_id
            if not resolved_job_id:
                resolved_job_id = os.path.basename(os.path.normpath(self.output_dir)) or "job"
            else:
                root_dir = os.path.join(self.output_dir, resolved_job_id)

            scene_part = f"scene_{scene_id}" if scene_id is not None else "scene_unknown"
            target_dir = os.path.join(root_dir, "ocr_screenshots", scene_part)
            os.makedirs(target_dir, exist_ok=True)

            # enforce max per scene
            existing = [f for f in os.listdir(target_dir) if f.lower().endswith(f".{image_format}")]
            if len(existing) >= max_per_scene:
                logger.debug("Max artifacts per scene reached (%d); skipping save.", max_per_scene)
                return None

            timestamp_ms = int(time.time() * 1000)
            shortid = uuid.uuid4().hex[:6]
            safe_variant = variant.replace(" ", "_") if variant else "v"
            filename = f"{timestamp_ms}_{engine}_{safe_variant}_{shortid}.{image_format}"
            filepath = os.path.join(target_dir, filename)

            # write image using OpenCV
            try:
                cv2.imwrite(filepath, image)
            except Exception as exc:
                logger.error("Failed to write image artifact %s: %s", filepath, exc)
                return None

            # update manifest (atomic write)
            manifest_dir = os.path.join(root_dir, "ocr_screenshots")
            os.makedirs(manifest_dir, exist_ok=True)
            manifest_path = os.path.join(manifest_dir, "manifest.json")
            manifest = {"job_id": resolved_job_id, "images": []}
            if os.path.isfile(manifest_path):
                try:
                    with open(manifest_path, "r", encoding="utf-8") as mf:
                        manifest = json.load(mf)
                except Exception:
                    # if manifest corrupt, overwrite with fresh structure
                    manifest = {"job_id": job_id, "images": []}

            entry = {
                "filename": os.path.join(scene_part, filename),
                "scene_id": scene_id,
                "timestamp": timestamp_ms,
                "engine": engine,
                "variant": variant,
                "preprocessing": preprocessing or [],
                "ocr_confidence": ocr_confidence,
                "text_excerpt": (text_excerpt[:200] if text_excerpt else ""),
            }
            manifest.setdefault("images", []).append(entry)

            tmp_path = manifest_path + ".tmp"
            with open(tmp_path, "w", encoding="utf-8") as mf:
                json.dump(manifest, mf, ensure_ascii=False, indent=2)
            os.replace(tmp_path, manifest_path)

            logger.info("Saved OCR image artifact %s (manifest updated).", filepath)
            return filename
        except Exception as exc:
            logger.error("Unexpected error saving image artifact: %s", exc)
            return None
