from deep_translator import GoogleTranslator
from typing import Optional
import time


class Translator:
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
        "af": "Afrikança",
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
        "rw": "Kinyarwanda",
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
        "ku": "Kürtçe"
    }

    def __init__(self, source_lang: str = "auto", target_lang: str = "tr"):
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.translator = None
        self._setup_translator()

    def _setup_translator(self):
        if self.source_lang == "auto":
            self.translator = GoogleTranslator(source="auto", target=self.target_lang)
        else:
            self.translator = GoogleTranslator(source=self.source_lang, target=self.target_lang)

    def set_languages(self, source_lang: str, target_lang: str):
        self.source_lang = source_lang
        self.target_lang = target_lang
        self._setup_translator()

    def translate_text(self, text: str) -> str:
        if not text or not text.strip():
            return ""

        try:
            if len(text) > 5000:
                return self._translate_long_text(text)
            return self.translator.translate(text)
        except Exception as e:
            print(f"Çeviri hatası: {e}")
            return text

    def _translate_long_text(self, text: str) -> str:
        chunks = []
        words = text.split()
        current_chunk = []

        for word in words:
            current_chunk.append(word)
            if len(" ".join(current_chunk)) > 4500:
                chunks.append(" ".join(current_chunk))
                current_chunk = []
        if current_chunk:
            chunks.append(" ".join(current_chunk))

        translated_chunks = []
        for chunk in chunks:
            try:
                translated = self.translator.translate(chunk)
                translated_chunks.append(translated)
                time.sleep(0.1)
            except Exception as e:
                print(f"Çeviri hatası (parça): {e}")
                translated_chunks.append(chunk)

        return " ".join(translated_chunks)

    def translate_segments(self, segments: list[dict], target_lang: str = None,
                           source_lang: str = None, progress_callback=None) -> list[dict]:
        if target_lang:
            self.set_languages(source_lang or self.source_lang, target_lang)

        total = len(segments)
        for i, segment in enumerate(segments):
            if progress_callback:
                progress = int((i / total) * 100)
                progress_callback(progress, f"Çevriliyor... ({i + 1}/{total})")

            segment["translated"] = self.translate_text(segment["text"])

        if progress_callback:
            progress_callback(100, "Çeviri tamamlandı!")

        return segments

    def get_supported_languages(self) -> dict:
        return self.SUPPORTED_LANGUAGES.copy()
