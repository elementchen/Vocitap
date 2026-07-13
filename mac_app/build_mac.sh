#!/bin/bash

echo "Cleaning historical builds..."
rm -rf build dist Vocitap.app

echo "Building Vocitap.app via PyInstaller..."
pyinstaller --clean Vocitap_mac.spec

echo "Moving final executable bundle..."
if [ -d "dist/Vocitap.app" ]; then
    mv dist/Vocitap.app .
    echo "Build completed successfully! Vocitap.app is ready."
else
    echo "Build failed! Please check logs."
fi

echo "Cleaning temporary directories..."
rm -rf build dist
