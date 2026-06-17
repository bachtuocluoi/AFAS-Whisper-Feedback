from src.services.asr_service import get_asr_service
from src.services.queue import ASRQueue

asr_service = get_asr_service()
asr_queue = ASRQueue(asr_service, 100)