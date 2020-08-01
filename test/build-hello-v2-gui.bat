@echo off
"%~dp0..\jkmsigen.exe" --output-msi "%~dp0out\v2-ui.msi" --name "Hello World" --upgrade-code=9e78359d-aff3-4f8b-9d63-6f19c1760f4d --shortcut=bin/hello.exe --version=0.2 --icon "%~dp0hello-src-v2\hello.ico" --with-ui=en-us -dWixUILicenseRtf="%~dp0hello-src-v1\gpl-3.0.rtf" "%~dp0\hello-v2"
