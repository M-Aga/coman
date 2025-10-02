from __future__ import annotations
from coman.core.base_module import BaseModule
from coman.core.config import settings
from fastapi import UploadFile, File
from fastapi.responses import StreamingResponse, JSONResponse
import io
class Module(BaseModule):
    name = "speech"; description = "Speech (TTS/STT) via OpenAI if configured."
    def __init__(self, core):
        super().__init__(core)
        @self.router.get("/status")
        def status(): return {"openai_configured": bool(settings.openai_api_key)}
        @self.router.post("/tts")
        def tts(text: str, voice: str = "alloy", fmt: str = "mp3"):
            if not settings.openai_api_key: return JSONResponse({"error":"OPENAI_API_KEY not configured"}, status_code=400)
            try:
                from openai import OpenAI
                client = OpenAI(api_key=settings.openai_api_key)
                with client.audio.speech.with_streaming_response.create(model="gpt-4o-mini-tts", voice=voice, input=text, format=fmt) as r:
                    buf = io.BytesIO()
                    for chunk in r.iter_bytes(): buf.write(chunk)
                buf.seek(0); return StreamingResponse(buf, media_type=f"audio/{fmt}")
            except Exception as e:
                return JSONResponse({"error":"TTS failed","detail":str(e)}, status_code=500)
        @self.router.post("/stt")
        async def stt(file: UploadFile = File(...), language: str | None = None):
            if not settings.openai_api_key: return JSONResponse({"error":"OPENAI_API_KEY not configured"}, status_code=400)
            try:
                from openai import OpenAI
                client = OpenAI(api_key=settings.openai_api_key)
                data = await file.read(); bio = io.BytesIO(data); bio.name = file.filename or "audio.wav"
                last_err = None
                for m in ["gpt-4o-mini-transcribe","whisper-1"]:
                    try:
                        tr = client.audio.transcriptions.create(model=m, file=bio, language=language)
                        return {"text": tr.text}
                    except Exception as exc:
                        last_err = exc; bio.seek(0)
                raise last_err
            except Exception as e:
                return JSONResponse({"error":"STT failed","detail":str(e)}, status_code=500)
