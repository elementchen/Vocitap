import os
import time
import numpy as np
import re
from src.config import MODELS_DIR, DEVICE

class Transcriber:
    def __init__(self, device=DEVICE):
        self.recognizer = None
        self.device = device
        # 模型文件路径
        self.model_path = os.path.join(MODELS_DIR, "sensevoice-small-onnx", "model.int8.onnx")
        self.tokens_path = os.path.join(MODELS_DIR, "sensevoice-small-onnx", "tokens.txt")

    def _ensure_loaded(self):
        """使用工厂方法延迟加载 sherpa-onnx 推理引擎"""
        if self.recognizer is not None:
            return
            
        if not os.path.exists(self.model_path) or not os.path.exists(self.tokens_path):
            raise FileNotFoundError(f"未找到 ONNX 模型文件，请检查 AppData 路径。")

        print(f"正在启动 Vocitap 4.5 AI 引擎 (sherpa-onnx)...")
        start_time = time.time()
        
        import sherpa_onnx
        
        # 使用 1.13.x 版本最推荐的工厂方法，彻底规避构造函数参数问题
        try:
            self.recognizer = sherpa_onnx.OfflineRecognizer.from_sense_voice(
                model=self.model_path,
                tokens=self.tokens_path,
                num_threads=2,
                use_itn=True,
                debug=False
            )
            print(f"AI 引擎通过工厂方法启动完成，耗时: {time.time() - start_time:.2f}s")
        except AttributeError:
            # 如果工厂方法不存在（极旧版本），回退到旧逻辑，但使用关键字参数
            print("警告：未找到 from_sense_voice 方法，尝试使用通用构造函数...")
            sense_voice_config = sherpa_onnx.OfflineSenseVoiceModelConfig(
                model=self.model_path,
                language="auto",
                use_itn=True
            )
            model_config = sherpa_onnx.OfflineModelConfig(
                sense_voice=sense_voice_config,
                tokens=self.tokens_path,
                num_threads=2,
                debug=False
            )
            feat_config = sherpa_onnx.FeatureExtractorConfig(
                sampling_rate=16000, 
                feature_dim=80
            )
            recognizer_config = sherpa_onnx.OfflineRecognizerConfig(
                model_config=model_config,
                feat_config=feat_config,
                decoding_method="greedy_search"
            )
            # 尝试通过 config 关键字传递
            self.recognizer = sherpa_onnx.OfflineRecognizer(config=recognizer_config)

    def clean_text(self, text, remove_filler=True, remove_punctuation=False):
        """清洗文本：移除语气词、标点和不必要的空格"""
        if not text: return ""
        
        if remove_filler:
            filler_words = ["嗯", "啊", "呃", "哦", "吧", "呢", "呀", "嘛"]
            for word in filler_words:
                text = re.sub(rf"{word}+", "", text)
        
        if remove_punctuation:
            text = re.sub(r'[^\w\s\u4e00-\u9fa5]', '', text)
            
        text = text.replace(" ", "")
        return text.strip()

    def transcribe(self, audio_path, remove_filler=True, remove_punctuation=False):
        """识别音频文件内容"""
        if not audio_path or not os.path.exists(audio_path):
            return ""
        
        self._ensure_loaded()
        
        try:
            import soundfile as sf
            audio, sample_rate = sf.read(audio_path)
            if len(audio.shape) > 1: audio = audio[:, 0]
            
            # 创建流并识别
            stream = self.recognizer.create_stream()
            stream.accept_waveform(sample_rate, audio)
            self.recognizer.decode_stream(stream)
            
            raw_text = stream.result.text
            if raw_text:
                return self.clean_text(raw_text, 
                                     remove_filler=remove_filler, 
                                     remove_punctuation=remove_punctuation)
        except Exception as e:
            print(f"识别出错: {e}")
        return ""
