import sounddevice as sd
import numpy as np
import soundfile as sf

def record_loop(q: queue.Queue, stop: threading.Event):
    """Background thread: captures mic audio in 5-second chunks using sounddevice."""
    RATE = 16000
    SECS = 5

    while not stop.is_set():
        try:
            audio = sd.rec(
                int(RATE * SECS),
                samplerate=RATE,
                channels=1,
                dtype='int16'
            )
            sd.wait()
            if not stop.is_set():
                q.put(audio)
        except Exception as e:
            q.put({"error": str(e)})
            break
