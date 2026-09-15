import subprocess
import shutil


def is_cuda_available() -> bool:
    try:
        import torch
        return torch.cuda.is_available()
    except ImportError:
        return False


def get_cuda_device_name() -> str:
    try:
        import torch
        if torch.cuda.is_available():
            return torch.cuda.get_device_name(0)
    except Exception:
        pass
    return ""


def is_nvenc_available(ffmpeg_path: str = "ffmpeg") -> bool:
    try:
        result = subprocess.run(
            [ffmpeg_path, "-encoders"],
            capture_output=True, text=True, timeout=5,
            encoding="utf-8", errors="replace"
        )
        return "h264_nvenc" in result.stdout
    except Exception:
        return False


def get_gpu_info() -> dict:
    info = {
        "cuda_available": False,
        "cuda_device": "",
        "nvenc_available": False,
        "ffmpeg_path": shutil.which("ffmpeg") or "ffmpeg"
    }

    info["cuda_available"] = is_cuda_available()
    if info["cuda_available"]:
        info["cuda_device"] = get_cuda_device_name()

    info["nvenc_available"] = is_nvenc_available(info["ffmpeg_path"])

    return info
