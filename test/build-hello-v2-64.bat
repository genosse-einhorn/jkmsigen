@echo off
"%~dp0..\jkmsigen.exe" --output-msi "%~dp0out\v2-64.msi" --x64 --name "Hello World" --upgrade-code=d6654670-98eb-41c1-88f6-c39d10bcafa6 --shortcut=bin/hello.exe --version=0.2.64 --icon "%~dp0hello-src-v2\hello.ico" "%~dp0\hello-v2"
