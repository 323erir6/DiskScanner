@echo off
python -m pip install -r requirements.txt
python -m PyInstaller --onefile --windowed --name FileScanner --collect-data customtkinter main.py
