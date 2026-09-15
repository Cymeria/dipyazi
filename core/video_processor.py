import subprocess
import os
import json
from typing import Optional

from .gpu_utils import is_nvenc_available


class VideoProcessor:
    def __init__(self):
        self.ffmpeg_path = self._find_ffmpeg()
        self.ffprobe_path = self._find_ffprobe()
        self.use_nvenc = is_nvenc_available(self.ffmpeg_path)

    def _find_ffmpeg(self) -> str:
        try:
            subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
            return "ffmpeg"
        except (subprocess.CalledProcessError, FileNotFoundError):
            possible_paths = [
                r"C:\ffmpeg\bin\ffmpeg.exe",
                r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
                os.path.expanduser(r"~\ffmpeg\bin\ffmpeg.exe"),
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    return path
            raise FileNotFoundError(
                "FFmpeg bulunamadı. Lütfen FFmpeg'i kurun veya PATH'e ekleyin."
            )

    def _find_ffprobe(self) -> str:
        try:
            subprocess.run(["ffprobe", "-version"], capture_output=True, check=True)
            return "ffprobe"
        except (subprocess.CalledProcessError, FileNotFoundError):
            possible_paths = [
                r"C:\ffmpeg\bin\ffprobe.exe",
                r"C:\Program Files\ffmpeg\bin\ffprobe.exe",
                os.path.expanduser(r"~\ffmpeg\bin\ffprobe.exe"),
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    return path
            return self.ffmpeg_path

    def get_video_info(self, video_path: str) -> dict:
        cmd = [
            self.ffprobe_path, "-i", video_path,
            "-print_format", "json",
            "-show_format", "-show_streams"
        ]

        result = subprocess.run(
            cmd, capture_output=True, text=True,
            encoding="utf-8", errors="replace"
        )

        try:
            info = json.loads(result.stdout)
        except (json.JSONDecodeError, TypeError):
            info = self._parse_ffmpeg_output(video_path)

        video_stream = None
        for stream in info.get("streams", []):
            if stream.get("codec_type") == "video":
                video_stream = stream
                break

        try:
            duration = float(info.get("format", {}).get("duration", 0))
        except (ValueError, TypeError):
            duration = 0.0

        try:
            width = int(video_stream.get("width", 0)) if video_stream else 0
        except (ValueError, TypeError):
            width = 0

        try:
            height = int(video_stream.get("height", 0)) if video_stream else 0
        except (ValueError, TypeError):
            height = 0

        fps_str = video_stream.get("r_frame_rate", "0/1") if video_stream else "0/1"
        try:
            if "/" in str(fps_str):
                num, den = str(fps_str).split("/")
                fps = float(num) / float(den) if float(den) != 0 else 0.0
            else:
                fps = float(fps_str)
        except (ValueError, ZeroDivisionError, TypeError):
            fps = 0.0

        codec = video_stream.get("codec_name", "unknown") if video_stream else "unknown"

        try:
            size = int(info.get("format", {}).get("size", 0))
        except (ValueError, TypeError):
            size = 0

        return {
            "duration": duration,
            "width": width,
            "height": height,
            "fps": fps,
            "codec": codec,
            "format": info.get("format", {}).get("format_long_name", "unknown"),
            "size": size
        }

    def embed_subtitles(self, video_path: str, subtitle_path: str,
                        output_path: str, style_config: dict = None,
                        hard_sub: bool = True, progress_callback=None) -> str:

        if progress_callback:
            progress_callback(10, "Video işleniyor...")

        subtitle_ext = os.path.splitext(subtitle_path)[1].lower()

        video_path_fwd = video_path.replace("\\", "/")
        subtitle_path_fwd = subtitle_path.replace("\\", "/")
        output_path_fwd = output_path.replace("\\", "/")

        if hard_sub:
            escaped_subtitle = subtitle_path_fwd.replace(":", "\\:").replace("'", "\\'")
            if subtitle_ext == ".ass":
                vf = f"ass='{escaped_subtitle}'"
            else:
                vf = f"subtitles='{escaped_subtitle}'"

            if self.use_nvenc:
                cmd = [
                    self.ffmpeg_path, "-hwaccel", "cuda", "-i", video_path_fwd,
                    "-vf", vf,
                    "-c:a", "copy",
                    "-c:v", "h264_nvenc",
                    "-preset", "medium",
                    "-rc", "constqp",
                    "-qp", "18",
                    "-y", output_path_fwd
                ]
            else:
                cmd = [
                    self.ffmpeg_path, "-i", video_path_fwd,
                    "-vf", vf,
                    "-c:a", "copy",
                    "-c:v", "libx264",
                    "-preset", "medium",
                    "-crf", "18",
                    "-y", output_path_fwd
                ]
        else:
            subtitle_dir = os.path.dirname(output_path_fwd)
            new_subtitle_path = os.path.join(
                subtitle_dir,
                os.path.splitext(os.path.basename(output_path_fwd))[0] + subtitle_ext
            )
            import shutil
            shutil.copy2(subtitle_path_fwd, new_subtitle_path)

            cmd = [
                self.ffmpeg_path, "-i", video_path_fwd,
                "-c", "copy",
                "-y", output_path_fwd
            ]

        if progress_callback:
            progress_callback(30, "Video kodlanıyor...")

        stderr_output = []
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            encoding='utf-8',
            errors='replace'
        )

        try:
            duration = self.get_video_info(video_path)["duration"]
            if not duration or duration == 0:
                duration = 1
        except Exception:
            duration = 1

        while True:
            line = process.stderr.readline()
            if not line and process.poll() is not None:
                break
            stderr_output.append(line)

            if "time=" in line:
                try:
                    time_str = line.split("time=")[1].split(" ")[0]
                    h, m, s = time_str.split(":")
                    current_time = float(h) * 3600 + float(m) * 60 + float(s)
                    progress = min(90, 30 + int((current_time / duration) * 60))
                    if progress_callback:
                        progress_callback(progress, f"Kodlanıyor... %{progress}")
                except (IndexError, ValueError):
                    pass

        process.wait()

        if process.returncode != 0:
            error_msg = "".join(stderr_output)
            raise RuntimeError(f"FFmpeg hatası: {error_msg[-500:]}")

        if progress_callback:
            progress_callback(100, "Video hazır!")

        return output_path_fwd

    def _parse_ffmpeg_output(self, video_path: str) -> dict:
        cmd = [self.ffmpeg_path, "-i", video_path]
        result = subprocess.run(
            cmd, capture_output=True, text=True,
            encoding="utf-8", errors="replace"
        )
        stderr = result.stderr or ""

        info = {"format": {}, "streams": []}

        for line in stderr.split('\n'):
            if 'Duration:' in line:
                duration_str = line.split('Duration:')[1].split(',')[0].strip()
                parts = duration_str.split(':')
                if len(parts) == 3:
                    hours, mins, secs = parts
                    duration = float(hours) * 3600 + float(mins) * 60 + float(secs)
                    info["format"]["duration"] = duration
            elif 'Video:' in line:
                stream_info = {"codec_type": "video"}
                parts = line.split('Video:')[1].split(',')
                if len(parts) > 0:
                    stream_info["codec_name"] = parts[0].strip().split()[0]
                for part in parts:
                    part = part.strip()
                    if 'x' in part and any(c.isdigit() for c in part):
                        try:
                            res = part.split()[0]
                            w, h = res.split('x')
                            stream_info["width"] = int(w)
                            stream_info["height"] = int(h)
                        except:
                            pass
                    elif 'fps' in part:
                        try:
                            fps_val = part.split()[0]
                            stream_info["r_frame_rate"] = fps_val
                        except:
                            pass
                info["streams"].append(stream_info)

        try:
            size_cmd = [self.ffprobe_path, "-v", "error", "-show_entries",
                       "format=size", "-of", "csv=p=0", video_path]
            size_result = subprocess.run(
                size_cmd, capture_output=True, text=True,
                encoding="utf-8", errors="replace"
            )
            if size_result.stdout.strip():
                info["format"]["size"] = int(size_result.stdout.strip())
        except:
            info["format"]["size"] = 0

        if "duration" not in info["format"]:
            info["format"]["duration"] = 0

        return info

    def extract_audio(self, video_path: str, output_path: str = None) -> str:
        if output_path is None:
            output_path = os.path.splitext(video_path)[0] + ".wav"

        cmd = [
            self.ffmpeg_path, "-i", video_path,
            "-vn", "-acodec", "pcm_s16le",
            "-ar", "16000", "-ac", "1",
            output_path, "-y"
        ]

        subprocess.run(cmd, capture_output=True, check=True)
        return output_path

    def convert_subtitle_format(self, input_path: str, output_path: str) -> str:
        cmd = [
            self.ffmpeg_path, "-i", input_path,
            output_path, "-y"
        ]

        subprocess.run(cmd, capture_output=True, check=True)
        return output_path
