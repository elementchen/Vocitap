import sounddevice as sd
import numpy as np
import wave
import os
import threading
from src.config import SAMPLE_RATE, CHANNELS

class Recorder:
    def __init__(self):
        self.fs = SAMPLE_RATE
        self.channels = CHANNELS
        self.recording = False
        self.audio_data = []

    def start_recording(self):
        self.recording = True
        self.audio_data = []
        print("开始录音...")
        
        # 在后台线程中进行录音
        self.stream = sd.InputStream(samplerate=self.fs, channels=self.channels, callback=self._audio_callback)
        self.stream.start()

    def _audio_callback(self, indata, frames, time, status):
        if status:
            print(status)
        if self.recording:
            self.audio_data.append(indata.copy())

    def get_current_data(self):
        """获取当前已录制的音频数据拷贝"""
        if not self.audio_data:
            return None
        return np.concatenate(self.audio_data, axis=0)

    def stop_recording(self):
        self.recording = False
        self.stream.stop()
        self.stream.close()
        print("录音停止。")
        
        if not self.audio_data:
            return None
        
        # 合并所有音频块
        return np.concatenate(self.audio_data, axis=0)

    def save_wav(self, data, filename="temp_recording.wav"):
        """将音频数据保存为 WAV 文件，方便模型读取"""
        if data is None:
            return None
        
        # 将 float32 转换为 int16
        audio_int16 = (data * 32767).astype(np.int16)
        
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2) # 16-bit
            wf.setframerate(self.fs)
            wf.writeframes(audio_int16.tobytes())
        
        return os.path.abspath(filename)

if __name__ == "__main__":
    import time
    rec = Recorder()
    rec.start_recording()
    time.sleep(3) # 录制 3 秒
    data = rec.stop_recording()
    path = rec.save_wav(data)
    print(f"录音已保存至: {path}")
