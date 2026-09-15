import whisper
import subprocess
import os
import warnings
from typing import Optional

from .gpu_utils import is_cuda_available

warnings.filterwarnings("ignore", message=".*Triton kernels.*")
warnings.filterwarnings("ignore", message=".*slower median kernel.*")
warnings.filterwarnings("ignore", message=".*slower DTW implementation.*")


class LanguageDetector:
    SUPPORTED_LANGUAGES = {
        "tr": "Türkçe",
        "en": "İngilizce",
        "de": "Almanca",
        "fr": "Fransızca",
        "es": "İspanyolca",
        "it": "İtalyanca",
        "pt": "Portekizce",
        "ru": "Rusça",
        "ja": "Japonca",
        "ko": "Korece",
        "zh": "Çince",
        "ar": "Arapça",
        "hi": "Hintçe",
        "nl": "Felemenkçe",
        "pl": "Lehçe",
        "sv": "İsveççe",
        "no": "Norveççe",
        "da": "Danca",
        "fi": "Fince",
        "el": "Yunanca",
        "cs": "Çekçe",
        "ro": "Romence",
        "hu": "Macarca",
        "uk": "Ukraynaca",
        "bg": "Bulgarca",
        "hr": "Hırvatça",
        "sk": "Slovakça",
        "sl": "Slovence",
        "et": "Estonca",
        "lv": "Letonca",
        "lt": "Litvanca",
        "th": "Tayca",
        "vi": "Vietnamca",
        "id": "Endonezce",
        "ms": "Malayca",
        "fil": "Filipino",
        "sw": "Svahili",
        "he": "İbranice",
        "bn": "Bengalce",
        "ta": "Tamilce",
        "te": "Teluguca",
        "mr": "Marathi",
        "gu": "Gujaratça",
        "kn": "Kannada",
        "ml": "Malayalam",
        "pa": "Pencapça",
        "ur": "Urduca",
        "fa": "Farsça",
        "af": "Afrikanca",
        "sq": "Arnavutça",
        "eu": "Baskça",
        "ca": "Katalanca",
        "gl": "Galiçyaca",
        "cy": "Galce",
        "ga": "İrlandaca",
        "is": "İzlandaca",
        "mt": "Maltaca",
        "mk": "Makedonca",
        "sr": "Sırpça",
        "bs": "Boşnakça",
        "ka": "Gürcüce",
        "hy": "Ermenice",
        "az": "Azerice",
        "kk": "Kazakça",
        "uz": "Özbekçe",
        "mn": "Moğolca",
        "ne": "Nepalce",
        "si": "Sinhala",
        "my": "Birmanca",
        "km": "Kmerce",
        "lo": "Lao",
        "am": "Amharca",
        "so": "Somalice",
        "yo": "Yorubaca",
        "zu": "Zuluca",
        "ha": "Hausa",
        "ig": "İgboca",
        "mg": "Malgaşça",
        "sg": "Sango",
        "sn": "Shona",
        "st": "Southern Sotho",
        "ss": "Swati",
        "tn": "Tswana",
        "ts": "Tsonga",
        "ve": "Venda",
        "xh": "Xhosa",
        "rw": "Kinyarwanda",
        "rn": "Kirundi",
        "ny": "Chewa",
        "mh": "Marshall",
        "to": "Tonga",
        "fj": "Fijice",
        "mi": "Maori",
        "sm": "Samoaca",
        "tk": "Türkmence",
        "ky": "Kırgızca",
        "tg": "Tacikçe",
        "ps": "Peştuca",
        "ku": "Kürtçe",
        "eu": "Baskça",
        "gl": "Galiçyaca",
        "af": "Afrikanca",
        "sq": "Arnavutça",
        "be": "Belarusça",
        "bs": "Boşnakça",
        "hr": "Hırvatça",
        "mk": "Makedonca",
        "sr": "Sırpça",
        "sl": "Slovence",
        "sq": "Arnavutça"
    }

    def __init__(self):
        self.model = None
        self.use_gpu = is_cuda_available()

    def detect_language(self, video_path: str, model_size: str = "base",
                        progress_callback=None) -> str:
        if self.model is None or getattr(self, '_current_size', None) != model_size:
            self.model = whisper.load_model(model_size)
            self._current_size = model_size

        if progress_callback:
            progress_callback(20, "Ses çıkarılıyor...")

        audio_path = video_path
        if not video_path.lower().endswith(('.wav', '.mp3', '.flac', '.ogg', '.m4a')):
            audio_path = self._extract_audio(video_path)
            if progress_callback:
                progress_callback(40, "Ses çıkarıldı, dil algılanıyor...")

        if progress_callback:
            progress_callback(60, "Dil algılanıyor...")

        audio = whisper.load_audio(audio_path)
        audio = whisper.pad_or_trim(audio)
        mel = whisper.log_mel_spectrogram(audio).to(self.model.device)
        _, probs = self.model.detect_language(mel)

        if progress_callback:
            progress_callback(90, "Dil algılandı!")

        detected_lang = max(probs, key=probs.get)
        confidence = probs[detected_lang]

        if audio_path != video_path and os.path.exists(audio_path):
            os.remove(audio_path)

        return detected_lang, confidence

    def _extract_audio(self, video_path: str) -> str:
        audio_path = os.path.splitext(video_path)[0] + "_temp_detect.wav"

        cmd = [
            "ffmpeg", "-i", video_path,
            "-vn", "-acodec", "pcm_s16le",
            "-ar", "16000", "-ac", "1",
            audio_path, "-y"
        ]

        subprocess.run(cmd, capture_output=True, check=True)
        return audio_path

    def get_supported_languages(self) -> dict:
        return self.SUPPORTED_LANGUAGES.copy()

    def get_language_name(self, lang_code: str) -> str:
        return self.SUPPORTED_LANGUAGES.get(lang_code, lang_code)
