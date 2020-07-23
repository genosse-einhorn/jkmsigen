@echo off
"%~dp0..\jkmsigen.exe" --upgrade-code=dc599bd6-d008-41aa-9c8d-556eac268f8e --name "Notepad 2 TEST" --version 0.0.1 --shortcut "Notepad2.exe" --icon "%~dp0notepad2-msi\app.ico" --assoc-icon 2 --assoc-extension txt --assoc-extension dummytext --assoc-description "Notedpad2 TEST Text Document" --output-msi "%~dp0out\notepad2.msi" "%~dp0notepad2-msi\\srcdir"
