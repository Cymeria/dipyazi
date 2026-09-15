import whisper
import os
import warnings
from typing import Optional

from .gpu_utils import is_cuda_available

warnings.filterwarnings("ignore", message=".*Triton kernels.*")
warnings.filterwarnings("ignore", message=".*slower median kernel.*")
warnings.filterwarnings("ignore", message=".*slower DTW implementation.*")


class Transcriber:
    def __init__(self):
        self.model = None
        self.current_model_size = None
        self.use_gpu = is_cuda_available()

    def load_model(self, model_size: str = "medium"):
        if self.current_model_size != model_size:
            self.model = whisper.load_model(model_size)
            self.current_model_size = model_size

    def transcribe(self, video_path: str, model_size: str = "medium",
                   source_language: Optional[str] = None,
                   progress_callback=None) -> list[dict]:
        self.load_model(model_size)

        if progress_callback:
            progress_callback(10, "Ses çıkarılıyor...")

        audio_path = video_path
        if not video_path.lower().endswith(('.wav', '.mp3', '.flac', '.ogg', '.m4a')):
            audio_path = self._extract_audio(video_path)
            if progress_callback:
                progress_callback(30, "Ses çıkarıldı, transkripsiyon başlıyor...")

        options = {
            "fp16": self.use_gpu,
            "word_timestamps": True
        }
        if source_language and source_language != "auto":
            options["language"] = source_language

        if progress_callback:
            progress_callback(40, "Whisper transkripsiyon yapıyor...")

        result = self.model.transcribe(audio_path, **options)

        if progress_callback:
            progress_callback(90, "Transkripsiyon tamamlandı!")

        raw_segments = []
        for segment in result["segments"]:
            text = segment["text"].strip()
            if not text:
                continue
            raw_segments.append({
                "start": round(segment["start"], 3),
                "end": round(segment["end"], 3),
                "text": text,
                "translated": ""
            })

        # Bitiş sürelerini bir sonraki cümlenin başlangıcına göre ayarla
        segments = self._adjust_end_times(raw_segments)

        # Geçici ses dosyasını temizle
        if audio_path != video_path and os.path.exists(audio_path):
            try:
                os.remove(audio_path)
            except OSError:
                pass

        detected_language = result.get("language", "unknown")

        return {
            "segments": segments,
            "language": detected_language
        }

    def _adjust_end_times(self, segments: list[dict]) -> list[dict]:
        if not segments:
            return segments

        gap = 0.15  # bir sonraki cümlenin başlangıcından önce dur
        for i in range(len(segments) - 1):
            next_start = segments[i + 1]["start"]
            # bitiş, bir sonraki cümlenin başlangıcından gap kadar önce olsun
            segments[i]["end"] = max(segments[i]["start"] + 0.1, next_start - gap)

        return segments

    def _extract_audio(self, video_path: str) -> str:
        import subprocess
        audio_path = os.path.splitext(video_path)[0] + "_temp_audio.wav"

        cmd = [
            "ffmpeg", "-i", video_path,
            "-vn", "-acodec", "pcm_s16le",
            "-ar", "16000", "-ac", "1",
            audio_path, "-y"
        ]

        subprocess.run(cmd, capture_output=True, check=True)
        return audio_path

    def get_available_models(self) -> list[str]:
        return ["tiny", "base", "small", "medium", "large-v3"]
