#!/bin/sh

set -eu

cd "$(dirname "$(readlink -f "$0")")"

cp 3rdparty/pyexestub/launchc.exe jkmsigen.exe

TDIR=$(mktemp -d) || exit 1

find * -not -path '*/.*' -type f | while read f; do
    if ! git check-ignore -q "$f"; then
        d="$(dirname "$f")"
        mkdir -p "$TDIR/$d"
        cp -a "$f" "$TDIR/$d"
    fi
done

rm -f $TDIR/makedist.sh
rm -rf $TDIR/3rdparty/pyexestub
cp -ar 3rdparty/python3/* $TDIR/3rdparty/python3
cp -ar 3rdparty/wix/* $TDIR/3rdparty/wix
cp 3rdparty/pyexestub/launchc.exe $TDIR/jkmsigen.exe

zipname=jkmsigen-$(date +%Y%m%d).zip
msiname=jkmsigen-$(date +%Y%m%d).msi
msiversion=$(date +%y.%m.%d)

# the cat is necessary here because zip will write to the file directly
# if it detects that stdout is redirected to a file.
(cd "$TDIR"; zip -r - *) | cat > "$zipname"

rm -rf "$TDIR"


# build MSI in wine
wine 3rdparty/python3/python.exe jkmsigen.py -o $msiname --name jkmsigen --upgrade-code=bb12f868-64af-41fe-9c4d-c928d86bdbf9 --version $msiversion $zipname

