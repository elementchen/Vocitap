; Inno Setup Script for SenseVoice Voice Input
[Setup]
AppId={{C7A9D8E2-F1B4-4B2E-8A5C-F9B2A1D0E3F4}}
AppName=SenseVoice 语音输入
AppVersion=1.0
AppPublisher=SenseVoice Team
DefaultDirName={autopf}\SenseVoiceInput
DefaultGroupName=SenseVoice 语音输入
OutputDir=.
OutputBaseFilename=SenseVoiceInput_Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "chinesesimplified"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; 这里的路径需要指向你打包后的 dist/SenseVoiceInput 文件夹
Source: "dist\SenseVoiceInput\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\SenseVoice 语音输入"; Filename: "{app}\SenseVoiceInput.exe"
Name: "{commondesktop}\SenseVoice 语音输入"; Filename: "{app}\SenseVoiceInput.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\SenseVoiceInput.exe"; Description: "立即运行 SenseVoice 语音输入"; Flags: nowait postinstall skipifsilent
