import asyncio
from typing import Optional
from dataclasses import dataclass

from fastapi import HTTPException

from src.services.asr_service import ASRService

@dataclass
class TranscriptionJob:
    audio_file_path: str
    future: asyncio.Future

class ASRQueue:
    def __init__(self, asr_service: ASRService, maxsize: int = 0):
        self.service = asr_service
        self.queue: asyncio.Queue[TranscriptionJob] = asyncio.Queue(maxsize=maxsize)
        self.worker_task: Optional[asyncio.Task] = None

    async def start(self):
        self.worker_task = asyncio.create_task(self._worker())

    async def stop(self):
        if self.worker_task:
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass

    async def submit(self, audio_file_path: str) -> str:
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        job = TranscriptionJob(audio_file_path=audio_file_path, future=future)

        try:
            self.queue.put_nowait(job)
        except asyncio.QueueFull:
            raise HTTPException(status_code=503, detail="Transcription queue is full")

        return await future

    async def _worker(self):
        while True:
            job = await self.queue.get()
            try:
                result = await asyncio.to_thread(self.service.transcribe, job.audio_file_path)
                job.future.set_result(result)
            except Exception as exc:
                if not job.future.done():
                    job.future.set_exception(exc)
            finally:
                self.queue.task_done()
