@echo off
echo ========================================
echo    Dipyazi - PyInstaller Paketleme
echo ========================================
echo.

echo [1/3] Gereksinimler kuruluyor...
pip install -r requirements.txt
pip install pyinstaller

echo.
echo [2/3] Uygulama paketleniyor...
pyinstaller ^
    --onedir ^
    --windowed ^
    --icon=icon.ico ^
    --name=Dipyazi ^
    --add-data="icon.ico;." ^
    --add-data="icon.png;." ^
    --hidden-import=whisper ^
    --hidden-import=deep_translator ^
    --hidden-import=torch ^
    --hidden-import=torchaudio ^
    --hidden-import=tiktoken_ext ^
    --hidden-import=tiktoken_ext.openai_public ^
    --collect-all whisper ^
    main.py

echo.
echo [3/3] Klasör yapısı oluşturuluyor...
if not exist "dist\Dipyazi\projects" mkdir "dist\Dipyazi\projects"
copy icon.ico dist\Dipyazi\icon.ico
copy icon.png dist\Dipyazi\icon.png

echo.
echo Tamamlandı!
echo.
echo Paketlenmiş uygulama: dist\Dipyazi\Dipyazi.exe
echo.
echo Not: projects klasörü uygulama ile aynı dizinde olmalidir.
echo.
pause
