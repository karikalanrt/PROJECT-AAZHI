import os
import time
import logging
import math
import struct
import wave
import random
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

try:
    from gtts import gTTS
    HAS_GTTS = True
except ImportError:
    HAS_GTTS = False

try:
    import pyttsx3
    HAS_PYTTSX3 = True
except ImportError:
    HAS_PYTTSX3 = False


class AudioDispatchEngine:
    """
    Tactical Audio Dispatch Engine for Project Aazhi.
    Converts automated geo-alert and disaster telemetry into military-grade phonetic audio briefings.
    Supports online multi-lingual neural synthesis (gTTS), offline air-gapped TTS (pyttsx3),
    and built-in zero-dependency tactical acoustic carrier fallback.
    """

    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_dispatch_script(self, alert_data: Dict[str, Any]) -> str:
        """
        Converts geo-alert telemetry into a terse, standardized military phonetic tactical script.
        """
        threat = alert_data.get("threat_type", "UNKNOWN THREAT").replace(" / ", " ")
        severity = alert_data.get("severity", "UNKNOWN SEVERITY").split(" ")[0]
        sector = alert_data.get("sector", "Unknown Sector")
        coords = alert_data.get("coords", [0.0, 0.0])
        pop = alert_data.get("population_est", 0)
        action = alert_data.get("ndrf_action", "Standby for orders.")

        is_nominal = "GREEN" in severity.upper() or "NOMINAL" in severity.upper()

        if is_nominal:
            return (
                f"Attention all units. AAZHI SATELLITE COMMAND DISPATCH. "
                f"Status: Routine Surveillance. "
                f"Target sector is {sector}. "
                f"Coordinates: {coords[0]:.2f} North, {coords[1]:.2f} East. "
                f"Observation: {threat}. "
                f"Action: {action}. "
                f"Maintain secure comms. Aazhi Command out."
            )

        return (
            f"Attention all units. AAZHI SATELLITE COMMAND DISPATCH. "
            f"Code {severity}. Threat identified as {threat}. "
            f"Target sector is {sector}. "
            f"Coordinates: {coords[0]:.2f} North, {coords[1]:.2f} East. "
            f"Estimated population at risk: {pop:,} civilians. "
            f"Immediate Action: {action}. "
            f"Maintain secure comms. Aazhi Command out."
        )

    def _generate_tactical_radio_fallback(self, output_path: str, duration_sec: float = 4.5) -> str:
        """
        Generates standard tactical radio transmission tones (military roger beep + telemetry carrier)
        using standard library wave module (zero dependencies).
        """
        sample_rate = 22050
        n_samples = int(sample_rate * duration_sec)
        with wave.open(output_path, "w") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            for i in range(n_samples):
                t = i / sample_rate
                if t < 0.25:
                    sample = int(14000 * math.sin(2 * math.pi * 880 * t))
                elif t < 0.50:
                    sample = int(16000 * math.sin(2 * math.pi * 1200 * t))
                elif t > duration_sec - 0.35:
                    sample = int(14000 * math.sin(2 * math.pi * 880 * t))
                else:
                    carrier = math.sin(2 * math.pi * 520 * t) * 7000
                    noise = (random.random() * 2 - 1) * 2000
                    sample = int(carrier + noise)
                wav_file.writeframes(struct.pack('<h', max(-32767, min(32767, sample))))
        return output_path

    def generate_audio(self, script: str, filename: str = "tactical_dispatch.mp3", force_offline: bool = False) -> str:
        """
        Generates tactical audio file using gTTS (online) or pyttsx3 (air-gapped offline fallback).
        Returns the absolute filepath to the created audio file.
        """
        output_path = os.path.join(self.output_dir, filename)

        # 1. Try Online Neural TTS (gTTS) with multi-domain fallback
        if not force_offline and HAS_GTTS:
            for tld in ['com', 'co.in', 'co.uk']:
                try:
                    tts = gTTS(text=script, lang='en', tld=tld, slow=False)
                    tts.save(output_path)
                    if os.path.exists(output_path) and os.path.getsize(output_path) > 500:
                        return output_path
                except Exception as e:
                    logger.warning(f"gTTS ({tld}) failed: {e}")

        # 2. Try Offline Air-Gapped TTS (pyttsx3)
        if HAS_PYTTSX3:
            try:
                try:
                    import pythoncom
                    pythoncom.CoInitialize()
                except Exception:
                    pass

                offline_path = os.path.join(self.output_dir, "offline_" + filename.replace(".mp3", ".wav"))
                engine = pyttsx3.init()
                rate = engine.getProperty('rate')
                engine.setProperty('rate', rate + 20)
                engine.save_to_file(script, offline_path)
                engine.runAndWait()
                time.sleep(0.3)
                if os.path.exists(offline_path) and os.path.getsize(offline_path) > 500:
                    return offline_path
            except Exception as e:
                logger.error(f"pyttsx3 offline TTS failed: {e}")

        # 3. Secondary gTTS attempt if offline was forced but pyttsx3 failed
        if force_offline and HAS_GTTS:
            try:
                tts = gTTS(text=script, lang='en', tld='com', slow=False)
                tts.save(output_path)
                if os.path.exists(output_path) and os.path.getsize(output_path) > 500:
                    return output_path
            except Exception as e:
                logger.error(f"Secondary gTTS fallback failed: {e}")

        # 4. Zero-Failure Tactical Acoustic Carrier Fallback (Built-in Waveform)
        try:
            fallback_wav = os.path.join(self.output_dir, "tactical_carrier_" + filename.replace(".mp3", ".wav"))
            self._generate_tactical_radio_fallback(fallback_wav)
            if os.path.exists(fallback_wav) and os.path.getsize(fallback_wav) > 500:
                return fallback_wav
        except Exception as e:
            logger.error(f"Tactical wave fallback failed: {e}")

        return ""



