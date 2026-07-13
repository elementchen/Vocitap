@echo off
echo Cleaning historical builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist Vocitap.exe del /f /q Vocitap.exe

echo Building Vocitap.exe via PyInstaller...
pyinstaller --clean Vocitap.spec

echo Moving final executable...
if exist dist\Vocitap.exe (
    move dist\Vocitap.exe .
    echo Build completed successfully!
) else (
    echo Build failed! Please check logs.
)

echo Cleaning temporary directories...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
