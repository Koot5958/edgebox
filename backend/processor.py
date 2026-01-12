import numpy as np
import queue
from scipy.signal import resample_poly

from utils.parameters import SR, CHUNK


class AudioProcessor():
    def __init__(self):
        self.buffer = queue.Queue()
        self._temp_buffer = []

        self.running = True
        self.active_generators = 0

        self.volume = 0.0

    def _to_float32(self, data):
        if np.issubdtype(data.dtype, np.integer):
            if data.dtype == np.int16:
                return data.astype(np.float32) / 32768.0
            if data.dtype == np.int32:
                return data.astype(np.float32) / 2147483648.0
        return data.astype(np.float32)

    def _to_mono(self, data, frames):
        if frames.layout.name == 'mono':
            return data
        if data.ndim == 2:
            axis = 0 if data.shape[0] <= 8 else 1
            return np.mean(data, axis=axis, dtype=np.float32)
        if data.ndim == 1:
            return data.reshape(-1, 2).mean(axis=1)
        return data

    async def process_track(self, track):
        while self.running:
            frame = await track.recv()

            audio = frame.to_ndarray()
            audio_float = self._to_float32(audio[0])
            audio_mono = self._to_mono(audio_float, frame)
            audio_mono = audio_mono.astype(np.float32)
            audio_16k = resample_poly(audio_mono, up=SR, down=frame.sample_rate)

            self.fill_buffer(audio_16k)

            rms = np.sqrt(np.mean(audio_16k ** 2))
            self.volume = min(rms * 20, 1.0)

    def fill_buffer(self, audio):
        audio_int16 = (audio * 32767).astype(np.int16)
        self._temp_buffer.extend(audio_int16) 

        if len(self._temp_buffer) >= CHUNK:
            # conversion en octets car c'est attendu par l'API
            segment_np = np.array(self._temp_buffer, dtype=np.int16)
            audio_bytes = segment_np.tobytes()

            self.buffer.put(audio_bytes)
            self._temp_buffer = []

    def generator(self):
        self.active_generators += 1
        try:
            while self.running:
                # Use a blocking get() to ensure there's at least one chunk of
                # data, and stop iteration if the chunk is None, indicating the
                # end of the audio stream.
                chunk = self.buffer.get()
                if chunk is None:
                    return
                data = [chunk]

                # Now consume whatever other data's still buffered.
                while True:
                    try:
                        chunk = self.buffer.get(block=False)
                        if chunk is None:
                            return
                        data.append(chunk)
                    except queue.Empty:
                        break

                yield b"".join(data)
        finally:
            self.active_generators -= 1

    def stop(self):
        if self.running:
            self.running = False
            self.buffer.put(None)