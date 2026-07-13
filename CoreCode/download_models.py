import os
import requests
import tarfile
import shutil
import time

# 自定义配置（不依赖主项目的 src.config，方便独立运行）
APP_NAME = "Vocitap"
APPDATA_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), APP_NAME)
MODELS_DIR = os.path.join(APPDATA_DIR, "models")

def log(text):
    print(f"[*] {text}")

def download_and_extract():
    """为开发者准备的一键模型下载脚本"""
    raw_url = "https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17.tar.bz2"
    proxy_url = f"https://mirror.ghproxy.com/{raw_url}"
    
    tmp_tar = "model_tmp.tar.bz2"
    model_dest = os.path.join(MODELS_DIR, "sensevoice-small-onnx")

    log("="*50)
    log(f"Vocitap 开发者模型预下载工具")
    log(f"目标目录: {model_dest}")
    log("="*50)

    try:
        log(f"正在从加速镜像下载模型 (约 240MB)...")
        response = requests.get(proxy_url, stream=True, timeout=60)
        response.raise_for_status()
        
        with open(tmp_tar, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024*1024):
                if chunk: f.write(chunk)
        
        log("下载完成，正在解压...")
        if not os.path.exists(MODELS_DIR): os.makedirs(MODELS_DIR)
        
        # 临时解压区
        temp_extract = "extract_tmp_dev"
        if os.path.exists(temp_extract): shutil.rmtree(temp_extract)
        
        with tarfile.open(tmp_tar, "r:bz2") as tar:
            tar.extractall(path=temp_extract)
        
        # 寻找模型文件
        found_dir = None
        for root, dirs, files in os.walk(temp_extract):
            if "model.int8.onnx" in files:
                found_dir = root
                break
        
        if found_dir:
            if os.path.exists(model_dest): shutil.rmtree(model_dest)
            shutil.move(found_dir, model_dest)
            log("模型安装成功！")
        
        # 清理
        if os.path.exists(tmp_tar): os.remove(tmp_tar)
        if os.path.exists(temp_extract): shutil.rmtree(temp_extract)
        
        log("="*50)
        log("环境就绪。您现在可以运行 'python -m src.main' 启动程序了。")
        
    except Exception as e:
        log(f"错误: {e}")

if __name__ == "__main__":
    download_and_extract()
