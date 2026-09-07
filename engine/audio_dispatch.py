import os
import threading
import time

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
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        
    def generate_dispatch_script(self, alert_data: dict) -> str:
        """
        Converts the geo-alert data into a terse, military-style phonetic script.
        """
        threat = alert_data.get("threat_type", "UNKNOWN THREAT").replace(" / ", " ")
        headline = alert_data.get("headline", "Unidentified Event")
        severity = alert_data.get("severity", "UNKNOWN SEVERITY").split(" ")[0]
        sector = alert_data.get("sector", "Unknown Sector")
        coords = alert_data.get("coords", [0.0, 0.0])
        pop = alert_data.get("population_est", 0)
        action = alert_data.get("ndrf_action", "Standby for orders.")
        
        is_nominal = "GREEN" in severity.upper() or "NOMINAL" in severity.upper()
        
        if is_nominal:
            script = (
                f"Attention all units. AAZHI SATELLITE COMMAND DISPATCH. "
                f"Status: Routine Surveillance. "
                f"Target sector is {sector}. "
                f"Coordinates: {coords[0]:.2f} North, {coords[1]:.2f} East. "
                f"Observation: {threat}. "
                f"Action: {action}. "
                f"Maintain secure comms. Aazhi Command out."
            )
        else:
            script = (
                f"Attention all units. AAZHI SATELLITE COMMAND DISPATCH. "
                f"Code {severity}. Threat identified as {threat}. "
                f"Target sector is {sector}. "
                f"Coordinates: {coords[0]:.2f} North, {coords[1]:.2f} East. "
                f"Estimated population at risk: {pop} civilians. "
                f"Immediate Action: {action}. "
                f"Maintain secure comms. Aazhi Command out."
            )
        return script

    def generate_audio(self, script: str, filename: str = "tactical_dispatch.mp3", force_offline: bool = False) -> str:
        """
        Generates the audio file using gTTS (online) or pyttsx3 (offline fallback).
        Returns the path to the generated audio file.
        """
        output_path = os.path.join(self.output_dir, filename)
        
        if not force_offline and HAS_GTTS:
            try:
                tts = gTTS(text=script, lang='en', tld='co.in', slow=False)
                tts.save(output_path)
                return output_path
            except Exception as e:
                print(f"gTTS online synthesis failed: {e}. Falling back to offline engine.")
                
        # Offline fallback using pyttsx3
        if HAS_PYTTSX3:
            try:
                # pyttsx3 needs to save to file (usually .wav, but some support .mp3 if ffmpeg is around)
                # Let's save as .mp3 but it might be wav depending on the platform driver
                offline_path = os.path.join(self.output_dir, "offline_" + filename.replace(".mp3", ".wav"))
                engine = pyttsx3.init()
                # Set voice rate slightly faster for military style
                rate = engine.getProperty('rate')
                engine.setProperty('rate', rate + 20)
                engine.save_to_file(script, offline_path)
                engine.runAndWait()
                # Wait for file to be flushed
                time.sleep(0.5)
                if os.path.exists(offline_path):
                    return offline_path
            except Exception as e:
                print(f"pyttsx3 offline synthesis failed: {e}.")
        
        return ""
