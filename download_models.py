import os
from src.config import MODELS_DIR, MODEL_ID
from funasr import AutoModel

def download():
    print("="*50)
    print(f"正在准备将模型下载到本地目录: {MODELS_DIR}")
    print("这可能需要几分钟，取决于您的网络速度...")
    print("="*50)

    # 设置环境变量，强制下载到 models 文件夹
    os.environ["MODELSCOPE_CACHE"] = MODELS_DIR

    try:
        # 初始化模型会自动触发下载
        model = AutoModel(
            model=MODEL_ID,
            vad_model="fsmn-vad",
            device="cpu", # 下载时使用 CPU 即可
            trust_remote_code=True
        )
        print("\n" + "="*50)
        print("恭喜！所有模型已成功下载到 models 文件夹中。")
        print("现在您可以直接拷贝整个项目文件夹到其他电脑运行了。")
        print("="*50)
    except Exception as e:
        print(f"\n下载失败: {e}")

if __name__ == "__main__":
    download()
