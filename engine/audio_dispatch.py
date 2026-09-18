import os
import time
import logging
import re
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
    Supports online neural synthesis (gTTS) and offline air-gapped TTS (pyttsx3).
    """

    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def clean_script_for_tts(self, text: str) -> str:
        """Sanitizes script text for clean acoustic pronunciation."""
        # Replace abbreviations with exact word boundaries
        text = text.replace(" / ", " ")
        text = re.sub(r'\bAOI\b', 'A-O-I', text)
        text = re.sub(r'\bNDRF\b', 'N-D-R-F', text)
        text = re.sub(r'\bSDRF\b', 'S-D-R-F', text)
        text = re.sub(r'\bkm²\b', 'square kilometers', text)
        text = re.sub(r'\bHa\b', 'Hectares', text)
        text = re.sub(r'\bcoords\b', 'coordinates', text, flags=re.IGNORECASE)
        text = re.sub(r'[*_#`\[\]"\']', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

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
            raw_script = (
                f"Attention all units. AAZHI SATELLITE COMMAND DISPATCH. "
                f"Status: Routine Surveillance. "
                f"Target sector is {sector}. "
                f"Coordinates: {coords[0]:.2f} North, {coords[1]:.2f} East. "
                f"Observation: {threat}. "
                f"Action: {action}. "
                f"Maintain secure comms. Aazhi Command out."
            )
        else:
            raw_script = (
                f"Attention all units. AAZHI SATELLITE COMMAND DISPATCH. "
                f"Code {severity}. Threat identified as {threat}. "
                f"Target sector is {sector}. "
                f"Coordinates: {coords[0]:.2f} North, {coords[1]:.2f} East. "
                f"Estimated population at risk: {pop:,} civilians. "
                f"Immediate Action: {action}. "
                f"Maintain secure comms. Aazhi Command out."
            )

        return self.clean_script_for_tts(raw_script)

    def generate_audio(self, script: str, filename: Optional[str] = None, force_offline: bool = False) -> str:
        """
        Generates genuine voice audio reading the complete script.
        Auto-failovers between Online Neural TTS (gTTS) and Offline Air-Gapped TTS (pyttsx3).
        Returns the path to the verified audio file.
        """
        import hashlib
        clean_text = self.clean_script_for_tts(script)
        if not clean_text:
            return ""

        h = hashlib.md5(clean_text.encode('utf-8')).hexdigest()[:8]
        if not filename:
            filename = f"tactical_dispatch_{h}.mp3"

        mp3_path = os.path.join(self.output_dir, filename if filename.endswith(".mp3") else f"tactical_dispatch_{h}.mp3")
        wav_path = os.path.join(self.output_dir, filename.replace(".mp3", ".wav") if ".mp3" in filename else f"tactical_dispatch_{h}.wav")

        # Return cached file if already synthesized
        if os.path.exists(mp3_path) and os.path.getsize(mp3_path) > 2000:
            return mp3_path
        if os.path.exists(wav_path) and os.path.getsize(wav_path) > 2000:
            return wav_path

        # 1. Offline Air-Gapped SAPI5 / eSpeak TTS (Instant & 100% Reliable Offline)
        if force_offline and HAS_PYTTSX3:
            try:
                try:
                    import pythoncom
                    pythoncom.CoInitialize()
                except Exception:
                    pass

                engine = pyttsx3.init()
                rate = engine.getProperty('rate')
                engine.setProperty('rate', rate)
                engine.save_to_file(clean_text, wav_path)
                engine.runAndWait()
                time.sleep(0.3)
                if os.path.exists(wav_path) and os.path.getsize(wav_path) > 2000:
                    return wav_path
            except Exception as e:
                logger.error(f"pyttsx3 offline synthesis error: {e}")

        # 2. Online Neural TTS (gTTS)
        if not force_offline and HAS_GTTS:
            for tld in ['com', 'co.in']:
                try:
                    tts = gTTS(text=clean_text, lang='en', tld=tld, slow=False)
                    tts.save(mp3_path)
                    if os.path.exists(mp3_path) and os.path.getsize(mp3_path) > 2000:
                        return mp3_path
                except Exception as e:
                    logger.warning(f"gTTS ({tld}) attempt failed: {e}")

        # 3. Fallback to pyttsx3 if gTTS failed or offline
        if HAS_PYTTSX3:
            try:
                try:
                    import pythoncom
                    pythoncom.CoInitialize()
                except Exception:
                    pass

                engine = pyttsx3.init()
                rate = engine.getProperty('rate')
                engine.setProperty('rate', rate)
                engine.save_to_file(clean_text, wav_path)
                engine.runAndWait()
                time.sleep(0.3)
                if os.path.exists(wav_path) and os.path.getsize(wav_path) > 2000:
                    return wav_path
            except Exception as e:
                logger.error(f"pyttsx3 fallback failed: {e}")

        return ""




