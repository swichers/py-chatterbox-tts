import logging
import tomllib
from typing import Dict, Optional, List, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class VoiceManager:
    def __init__(self, voices_dir: str = "voices"):
        self.voices_dir = Path(voices_dir)
        self._voices: Dict[str, Dict[str, Any]] = {}
        self.load_voices()

    def load_voices(self):
        """Scans the voices directory and loads all .toml configurations."""
        if not self.voices_dir.exists():
            logger.warning(
                f"Voices directory '{self.voices_dir}' does not exist. Creating it."
            )
            self.voices_dir.mkdir(parents=True, exist_ok=True)
            return

        loaded_count = 0
        for file_path in self.voices_dir.glob("*.toml"):
            try:
                with open(file_path, "rb") as f:
                    config = tomllib.load(f)

                voice_name = file_path.stem

                # Resolve audio path relative to the config file
                if "audio_path" in config:
                    audio_path = (file_path.parent / config["audio_path"]).resolve()
                    if not audio_path.exists():
                        logger.warning(
                            f"Voice '{voice_name}' defined in {file_path.name} refers to missing audio file: {audio_path}"
                        )
                        continue
                    config["audio_path"] = str(audio_path)

                self._voices[voice_name] = config
                loaded_count += 1
            except Exception as e:
                logger.error(f"Failed to load voice config from {file_path}: {e}")

        logger.info(f"Loaded {loaded_count} voices from {self.voices_dir}")

    def get_voice_config(self, voice_name: str) -> Optional[Dict[str, Any]]:
        """Returns the configuration for a given voice name, or None if not found."""
        return self._voices.get(voice_name)

    def list_voices(self) -> List[str]:
        """Returns a list of available voice names."""
        return list(self._voices.keys())


voice_manager = VoiceManager()
