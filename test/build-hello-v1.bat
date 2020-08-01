@echo off
"%~dp0..\jkmsigen.exe" --output-msi "%~dp0out\v1.msi" --name "Hello World" --upgrade-code=9e78359d-aff3-4f8b-9d63-6f19c1760f4d --shortcut=bin\hello.exe --version=0.1 --icon "%~dp0hello-src-v1\hello.ico" "%~dp0\hello-v1"
