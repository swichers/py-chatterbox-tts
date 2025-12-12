import io
import logging
import torch
from typing import Optional
from torchcodec.encoders import AudioEncoder
from chatterbox.tts import ChatterboxTTS
from src.voice_manager import voice_manager

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TTSWrapper:
    def __init__(self):
        self._initialize_model()

    def _initialize_model(self):
        if torch.cuda.is_available():
            print(f"CUDA is available! Device: {torch.cuda.get_device_name(0)}")
            print(f"CUDA version: {torch.version.cuda}")
            print(f"CuDNN version: {torch.backends.cudnn.version()}")
            device = "cuda"
        else:
            print("CUDA is NOT available. Falling back to CPU.")
            device = "cpu"

        logger.info(f"Initializing Chatterbox TTS on device: {device}")

        try:
            self.model = ChatterboxTTS.from_pretrained(device=device)
            logger.info("Chatterbox TTS model initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize Chatterbox TTS: {e}")
            raise

        print("Compiling model (this takes a minute)...")
        try:
            self.model.t3 = torch.compile(
                self.model.t3, mode="reduce-overhead", fullgraph=True
            )
        except Exception as e:
            print(
                f"Warning: Compilation failed, falling back to standard mode. Error: {e}"
            )

        if device == "cuda":
            self.model.generate(
                "This is a warmup sentence to initialize the CUDA graphs."
            )

    def synthesize(self, text: str, voice: Optional[str] = None, **kwargs) -> bytes:
        """
        Synthesizes text to speech.

        Args:
            text: Text to synthesize.
            voice: Optional voice ID/name.
            **kwargs: Additional overrides (temperature, cfg_weight, exaggeration).

        Returns:
            Audio bytes (WAV formatted PCM).
        """
        logger.info(f"Received synthesis request. Text length: {len(text)}")

        # 1. Start with defaults
        gen_params = {
            "temperature": 0.7,
            "cfg_weight": 0.5,
            "exaggeration": 0.5,
        }

        # 2. Apply voice configuration if provided (overrides defaults)
        if voice:
            voice_config = voice_manager.get_voice_config(voice)
            if voice_config:
                logger.info(f"Using voice configuration for '{voice}'")
                if "audio_path" in voice_config:
                    gen_params["audio_prompt_path"] = voice_config["audio_path"]

                for key in ["temperature", "cfg_weight", "exaggeration"]:
                    if key in voice_config:
                        gen_params[key] = voice_config[key]
            else:
                logger.warning(f"Voice '{voice}' not found. Using defaults.")

        # 3. Apply explicit overrides from request (overrides voice config and defaults)
        for k, v in kwargs.items():
            if v is not None:
                gen_params[k] = v

        try:
            logger.info(f"Generating with params: {gen_params}")
            wav = self.model.generate(text, **gen_params)

            if hasattr(wav, "cpu"):
                wav = wav.detach().cpu()

            if wav.dim() == 1:
                wav = wav.unsqueeze(0)

            buffer = io.BytesIO()

            encoder = AudioEncoder(samples=wav, sample_rate=self.model.sr)
            encoder.to_file_like(buffer, format="wav")
            buffer.seek(0)

            return buffer.read()

        except Exception as e:
            logger.error(f"Synthesis failed: {e}")


try:
    tts_service = TTSWrapper()
except Exception:
    tts_service = None
