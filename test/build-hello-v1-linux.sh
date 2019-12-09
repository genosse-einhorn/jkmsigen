#!/bin/sh
d="$(dirname "$(readlink -f "$0")")"
cp "$d/hello-src-v1/hello.exe" "$d/hello-v1/hello.exe"
exec "$d/../jkmsigen.py" --output-msi "$d/out/v1-linux.msi" --name "Hello World" --upgrade-code=9e78359d-aff3-4f8b-9d63-6f19c1760f4d --shortcut=hello.exe --version=0.1 --icon "$d/hello-src-v1/hello.ico" "$d/hello-v1"
