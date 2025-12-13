import logging
import io

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from src.tts_wrapper import tts
from src.voice_manager import voice_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api")

app = FastAPI(title="Chatterbox TTS Service")


class SynthesisRequest(BaseModel):
    text: str
    voice: Optional[str] = None
    temperature: Optional[float] = None
    cfg_weight: Optional[float] = None
    exaggeration: Optional[float] = None


@app.on_event("startup")
async def startup_event():
    if tts is None:
        logger.error("TTS Service failed to initialize!")
    logger.info(f"Loaded voices: {voice_manager.list_voices()}")


@app.get("/api/v1/voices")
async def list_voices():
    """Returns a list of available custom voices."""
    return {"voices": voice_manager.list_voices()}


@app.post("/api/v1/synthesize")
async def synthesize(request: SynthesisRequest):
    if not tts:
        raise HTTPException(status_code=503, detail="TTS Service unavailable")

    try:
        kwargs = {}

        if request.temperature is not None:
            kwargs["temperature"] = request.temperature
        if request.cfg_weight is not None:
            kwargs["cfg_weight"] = request.cfg_weight
        if request.exaggeration is not None:
            kwargs["exaggeration"] = request.exaggeration

        result = tts.synthesize(text=request.text, voice=request.voice, **kwargs)

        return StreamingResponse(io.BytesIO(result), media_type="audio/wav")

    except Exception as e:
        logger.error(f"Error processing request: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    return {"status": "ok", "cuda_available": tts.model is not None}
