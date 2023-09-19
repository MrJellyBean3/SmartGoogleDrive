@echo off
call %~dp0env\Scripts\activate.bat
python %~dp0main.py
call deactivate.bat