Set-Location $PSScriptRoot
python -m pip install -r requirements.txt pyinstaller
python -m PyInstaller --noconfirm --onedir --windowed --name PolarCompress --icon PolarCompress.ico --add-data 'PolarCompress.ico;.' --add-data 'PolarCompress.png;.' polarcompress.py
