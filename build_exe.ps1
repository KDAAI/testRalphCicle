$ErrorActionPreference = "Stop"

python -m pip install -r requirements.txt
python -m PyInstaller --noconfirm --onefile --windowed --name RalphNotes app.py

Write-Host ""
Write-Host "Done: dist\RalphNotes.exe"
