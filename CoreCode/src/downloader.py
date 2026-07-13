import os
import requests
import threading
from tqdm import tqdm

def download_file(url, dest_path, gui_callback=None):
    """通用的带进度条下载函数"""
    if os.path.exists(dest_path):
        return True
    
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        total_size = int(response.headers.get('content-length', 0))
        
        with open(dest_path, 'wb') as f:
            downloaded = 0
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if gui_callback:
                        progress = int((downloaded / total_size) * 100)
                        gui_callback(progress)
        return True
    except Exception as e:
        print(f"下载失败: {e}")
        return False

def get_onnx_model_urls():
    """
    获取 SenseVoice ONNX 模型下载地址。
    这里使用中转或可靠源，量化版 model.int8.onnx 约 240MB
    """
    base_url = "https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/"
    # 注意：实际生产中建议使用更稳定的国内镜像加速
    return {
        "model": "https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17.tar.bz2",
        # 这是一个压缩包，我们可能需要解压。
        # 或者直接提供单文件下载（如果能找到）。
    }

# 为了简化，我们假设用户手动准备或我们在启动器里通过 python 脚本解压
