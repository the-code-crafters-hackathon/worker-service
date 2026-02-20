from pathlib import Path
from typing import List, Tuple
import shutil
import subprocess
import zipfile
import logging
import os

from app.gateways.s3_gateway import S3Gateway

logger = logging.getLogger(__name__)


class VideoProcessingGateway:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.uploads_dir = base_dir / "uploads"
        self.outputs_dir = base_dir / "outputs"
        self.temp_dir = base_dir / "temp"

        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def _create_zip(self, files: List[Path], zip_path: Path) -> None:
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for f in files:
                zipf.write(f, arcname=f.name)

    def process_video(self, video_path: str, timestamp: str, fps: int = 1) -> Tuple[Path, int, List[str]]:
        proc_temp = self.temp_dir / timestamp
        proc_temp.mkdir(parents=True, exist_ok=True)

        frame_pattern = str(proc_temp / "frame_%04d.png")
        cmd = [
            "ffmpeg",
            "-i",
            str(video_path),
            "-vf",
            f"fps={fps}",
            "-y",
            frame_pattern,
        ]

        logger.info(f"Executando FFmpeg: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"FFmpeg error: {result.stderr}")
            try:
                shutil.rmtree(proc_temp)
            except Exception:
                pass
            raise RuntimeError(f"FFmpeg error: {result.stderr}")

        frames = sorted(proc_temp.glob("*.png"))
        if not frames:
            shutil.rmtree(proc_temp)
            raise RuntimeError("Nenhum frame extraído do vídeo")

        zip_filename = f"frames_{timestamp}.zip"
        zip_path = self.outputs_dir / zip_filename
        self._create_zip(frames, zip_path)

        logger.info(f"Arquivo ZIP criado: {zip_path} com {len(frames)} frames")

        image_names = [f.name for f in frames]

        env = os.getenv("APP_ENV", "development")
        if env == "production":
            s3 = S3Gateway(self.base_dir)
            s3_key = f"outputs/{zip_filename}"
            uploaded = s3.upload_video(str(zip_path), s3_key)
            try:
                shutil.rmtree(proc_temp)
            except Exception:
                pass

            if not uploaded:
                raise RuntimeError("Falha ao enviar ZIP para o S3")

            s3_uri = f"s3://{s3.bucket_name}/{s3_key}"
            return s3_uri, len(frames), image_names

        try:
            shutil.rmtree(proc_temp)
        except Exception:
            pass

        return zip_path, len(frames), image_names
