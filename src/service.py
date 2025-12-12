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
        self.model = None
        self._initialize_model()

    def _initialize_model(self):
        try:
            if torch.cuda.is_available():
                logger.info(
                    f"CUDA is available! Device: {torch.cuda.get_device_name(0)}"
                )
                logger.info(f"CUDA version: {torch.version.cuda}")
                # Wrapping version check in try/except to prevent obscure crashes
                try:
                    logger.info(f"CuDNN version: {torch.backends.cudnn.version()}")
                except Exception:
                    logger.warning("Could not determine CuDNN version.", exc_info=True)
                device = "cuda"
            else:
                logger.info("CUDA is NOT available. Falling back to CPU.")
                device = "cpu"

            logger.info(f"Initializing Chatterbox TTS on device: {device}...")

            # Initialization with full traceback logging
            try:
                self.model = ChatterboxTTS.from_pretrained(device=device)
                logger.info("Chatterbox TTS model initialized successfully.")
            except Exception:
                logger.critical(
                    "Critical Failure: ChatterboxTTS failed to download or load.",
                    exc_info=True,
                )
                raise

            logger.info("Compiling model (this takes a minute)...")
            try:
                self.model.t3 = torch.compile(
                    self.model.t3, mode="reduce-overhead", fullgraph=True
                )
                logger.info("Model compiled successfully.")
            except Exception:
                logger.warning(
                    "Compilation failed, falling back to standard mode.", exc_info=True
                )

            if device == "cuda":
                logger.info("Running warmup generation...")
                try:
                    self.model.generate(
                        "This is a warmup sentence to initialize the CUDA graphs."
                    )
                    logger.info("Warmup complete.")
                except Exception:
                    logger.warning("Warmup generation failed.", exc_info=True)

        except Exception as e:
            logger.error(f"Fatal error during TTS initialization: {e}", exc_info=True)
            raise

    def synthesize(self, text: str, voice: Optional[str] = None, **kwargs) -> bytes:
        """
        Synthesizes text to speech.
        """
        if not text:
            logger.warning("Synthesis requested with empty text.")
            return b""

        if self.model is None:
            logger.error("Attempted synthesis but model is not initialized.")
            return b""

        try:
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

            logger.info("Audio synthesis complete.")
            return buffer.read()

        except Exception:
            logger.error("Synthesis failed during generation step.", exc_info=True)
            return b""


try:
    tts_service = TTSWrapper()
except Exception:
    logger.critical("Failed to initialize TTS service application-wide.", exc_info=True)
    tts_service = None
