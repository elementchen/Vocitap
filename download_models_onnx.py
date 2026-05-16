import os
import requests
import tarfile
from src.config import MODELS_DIR

def download_onnx_model():
    # 目标子目录
    model_dest = os.path.join(MODELS_DIR, "sensevoice-small-onnx")
    if os.path.exists(os.path.join(model_dest, "model.int8.onnx")):
        print("ONNX 模型已存在，跳过下载。")
        return

    print("="*50)
    print("正在准备下载 Vocitap 4.0 专用轻量化 ONNX 模型...")
    print("目标目录:", model_dest)
    print("="*50)

    url = "https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17.tar.bz2"
    tmp_tar = "model_tmp.tar.bz2"

    try:
        # 下载
        print("正在从 GitHub 下载模型压缩包 (约 240MB)...")
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(tmp_tar, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # 解压
        print("下载完成，正在解压...")
        with tarfile.open(tmp_tar, "r:bz2") as tar:
            # 找到内部文件夹名称
            member_names = tar.getnames()
            root_folder = member_names[0].split('/')[0]
            tar.extractall()
            
            # 重命名为标准目录
            if os.path.exists(model_dest):
                import shutil
                shutil.rmtree(model_dest)
            os.rename(root_folder, model_dest)
            
        print("\n" + "="*50)
        print("恭喜！ONNX 模型已成功安装到本地。")
        print("现在您可以体验 Vocitap 4.0 的极速响应了。")
        print("="*50)
        
    except Exception as e:
        print(f"\n下载或安装失败: {e}")
    finally:
        if os.path.exists(tmp_tar):
            os.remove(tmp_tar)

if __name__ == "__main__":
    download_onnx_model()
