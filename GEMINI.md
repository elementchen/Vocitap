# Vocitap 架构与逻辑校准准则 (GEMINI.md)

## 1. 运行模式 (Dual-Mode)
### 源码模式 (GitHub Clone)
*   **运行方式**: `python -m src.main`
*   **代码路径**: 使用当前文件夹下的 `src/*.py`。
*   **资源路径**: 模型和 `config.json` 依然强制存放在 `%APPDATA%\Vocitap`。
*   **限制**: 不允许/不生效“开机自启动”。

### EXE 模式 (Shadow Deployment)
*   **组件**: `Vocitap.exe` (启动器) + `AppData/Vocitap/runtime/src` (影子代码)。
*   **行为**: 
    1. 第一次运行时释放 `src` 文件夹到 `%APPDATA%\Vocitap\runtime`。
    2. **版本校验**: 如果 EXE 内部版本 > AppData 影子版本，必须**全量覆盖**影子代码。
    3. **启动**: 永远使用绝对路径拉起 AppData 里的 `main.py`。
*   **开机自启动**: 必须创建指向 `Vocitap.exe` 本身的快捷方式，放入 Windows 启动项。

## 2. 核心路径定义
*   `APPDATA_DIR`: `%APPDATA%\Vocitap`
*   `RUNTIME_DIR`: `APPDATA_DIR\runtime`
*   `CONFIG_PATH`: `APPDATA_DIR\config.json`
*   `MODELS_DIR`: `APPDATA_DIR\models`

## 3. 开机自启动实现
*   快捷方式目录: `AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup`
*   目标: 优先指向环境变量 `VOCITAP_EXE` (由启动器设置) 或 `sys.executable`。

## 4. 提交规范
*   提交信息格式: `Vocitap X.X.X: <Description>`
*   忽略规则: 严禁提交 `_internal`, `build`, `dist`, `runtime`, `models`, `*.exe`。

## 5. 文档维护准则 (CHANGELOG)
*   **强制同步**: 每当执行功能性代码修改、架构调整或 Bug 修复后，必须在当前会话结束前，以增量方式更新根目录下的 `CHANGELOG.md`。
*   **格式要求**: 必须注明版本号、日期，并按“功能增强”、“架构转型”、“Bug 修复”等类别清晰列出改动点。
