#!/usr/bin/env python3

# jkmsigen.py - Generate a very simple .msi installer
# Copyright © 2019 Jonas Kümmerlin <jonas@kuemmerlin.eu>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from argparse import ArgumentParser
from uuid import UUID, uuid4, uuid5
from zipfile import ZipFile
import xml.etree.ElementTree as ET
import logging
import os
import tempfile
import subprocess
import shutil
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '3rdparty', 'ico2dll'))

from ico2dll import ico2dll


idcounter = 0
def makeid(prefix):
    global idcounter
    idcounter = idcounter + 1
    return '{}_{}'.format(prefix, idcounter)

ap = ArgumentParser()
ap.add_argument('--output-msi', '-o', metavar='PATH/TO/OUT.MSI', required=True)
ap.add_argument('--output-wxs', metavar='PATH/TO/OUT.WXS')
ap.add_argument('--upgrade-code', type=UUID)
ap.add_argument('--version')
ap.add_argument('--name', metavar='My Application', required=True)
ap.add_argument('--manufacturer')
ap.add_argument('--shortcut', metavar='RELATIVE/PATH/TO/APP.EXE')
ap.add_argument('--shortcut-name-mui-id', type=int)
ap.add_argument('--shortcut-name-mui-dll', metavar='RELATIVE/PATH/TO/FILE.DLL')
ap.add_argument('--codepage', metavar='????', type=int, default=1252)
ap.add_argument('--language', metavar='????', type=int, default=0)
ap.add_argument('--icon', metavar='PATH/TO/FILE.ICO')
ap.add_argument('--with-ui', metavar='CULTURE')
ap.add_argument('--x64', action='store_true')
ap.add_argument('-d', '--variable', metavar='NAME=VALUE', action='append', default=[])
ap.add_argument('--assoc-extension', metavar='ext', action='append', default=[])
ap.add_argument('--assoc-icon-index', type=int, metavar='N')
ap.add_argument('--assoc-target', metavar='RELATIVE/PATH/TO/HANDLER.EXE')
ap.add_argument('--assoc-description', metavar='DESCRIPTION')
ap.add_argument('--installdir', metavar='DIRNAME')
ap.add_argument('sourcedirectory')

args = ap.parse_args()

if args.manufacturer is None:
    args.manufacturer = args.name

if args.assoc_extension is not None and args.assoc_target is None:
    if args.shortcut is None:
        logging.error('No association target and no shortcut specified. Ignoring file associations.')
    else:
        args.assoc_target = args.shortcut

if args.upgrade_code is None:
    logging.warning('no UpgradeCode specified, generating one for you')
    args.upgrade_code = uuid4()
    logging.warning('    --upgrade-code={}'.format(args.upgrade_code))

if args.version is None:
    logging.warning('no version specified, generating one for you')
    args.version = '0.0.1'
    logging.warning('    --version={}'.format(args.version))

wix = ET.Element('Wix', xmlns='http://schemas.microsoft.com/wix/2006/wi')
product = ET.SubElement(wix, 'Product', Name=args.name, Id='*', UpgradeCode=str(args.upgrade_code), Codepage=str(args.codepage), Manufacturer=args.manufacturer, Version=args.version, Language=str(args.language))
package = ET.SubElement(product, 'Package', Id='*', InstallerVersion='200', Compressed='yes', Languages=str(args.language), SummaryCodepage=str(args.codepage), Description=args.name, Manufacturer=args.manufacturer, InstallScope='perMachine')
media = ET.SubElement(product, 'Media', Id='1', Cabinet='Media1.cab', EmbedCab='yes')
ET.SubElement(product, 'MajorUpgrade', AllowDowngrades='yes', Schedule='afterInstallValidate')

targetdir = ET.SubElement(product, 'Directory', Id='TARGETDIR', Name='SourceDir')
if args.x64:
    progfilesdir = ET.SubElement(targetdir, 'Directory', Id='ProgramFiles64Folder', Name='ProgramFiles')
else:
    progfilesdir = ET.SubElement(targetdir, 'Directory', Id='ProgramFilesFolder', Name='ProgramFiles')


if args.installdir is None:
    args.installdir = args.name

installdir = progfilesdir
for d in args.installdir.replace('/', '\\').split('\\'):
    installdir = ET.SubElement(installdir, 'Directory', Id=makeid('Directory'), Name=d)
installdir.attrib['Id'] = 'INSTALLDIR'

feature = ET.SubElement(product, 'Feature', Id='Complete', Level='1')

# reinstallmode 'a' is usually dangerous, but we
# - have no shared components,
# - do only major upgrades,
# - and follow the component rules closely enough
# so it shouldn't be a problem here
ET.SubElement(product, 'Property', Id='REINSTALLMODE', Value='amus')

if args.with_ui is not None:
    ET.SubElement(product, 'Property', Id="WIXUI_INSTALLDIR", Value="INSTALLDIR")
    ET.SubElement(product, 'UIRef', Id='WixUI_InstallDir')
    ET.SubElement(product, 'SetProperty', Id='ARPNOMODIFY', Value='1', After='InstallValidate', Sequence='execute')
else:
    ET.SubElement(product, 'Property', Id='ARPNOMODIFY', Value='yes')

for v in args.variable:
    name, val = (v.split('=', 1) + [''])[0:2]
    ET.SubElement(product, 'WixVariable', Id=name, Value=val)

# registry component helper
def addregcomp(*, Root='HKLM', Key, Name='', Value, Type='string'):
    c = ET.SubElement(targetdir, 'Component', Guid='*', Feature=feature.attrib['Id'])
    r = ET.SubElement(c, 'RegistryValue', Root=Root, Key=Key, Name=Name, Value=Value, Type=Type, KeyPath='yes')

    if len(Name) == 0:
        del r.attrib['Name']

    return c

# recursive file component helper
def walkdir(direl, sourcepath):
    for e in os.scandir(sourcepath):
        if e.is_dir():
            d = ET.SubElement(direl, 'Directory', Name=e.name, Id=makeid('Directory'))
            walkdir(d, e.path)
        else:
            comp = ET.SubElement(direl, 'Component', Guid='*', Feature=feature.attrib['Id'])
            f = ET.SubElement(comp, 'File', Name=e.name, DiskId='1', Source=e.path, KeyPath='yes', Id=makeid('File'))

def findfileelforpath(direl, path):
    path = path.replace('\\', '/')

    i = path.find('/')
    if i < 0:
        # last part, search file component
        for subel in direl:
            if subel.tag == 'Component':
                for subsubel in subel:
                    if subsubel.tag == 'File' and subsubel.attrib['Name'].upper() == path.upper():
                        return subsubel
    else:
        # directory part
        for subel in direl:
            if subel.tag != 'Directory':
                continue

            if subel.attrib['Name'].upper() == path[0:i].upper():
                return findfileelforpath(subel, path[i+1:])

    return None

with tempfile.TemporaryDirectory() as tmpdir:
    if os.path.isdir(args.sourcedirectory):
        walkdir(installdir, args.sourcedirectory)
    else:
        with ZipFile(args.sourcedirectory, 'r') as z:
            s = os.path.join(tmpdir, 'src')
            z.extractall(s)
            walkdir(installdir, s)

    shortcutel = None
    if args.shortcut is not None:
        f = findfileelforpath(installdir, args.shortcut)

        if f is None:
            logging.error('couldn’t create shortcut {}: file not found'.format(args.shortcut))
        else:
            shortcutel = ET.SubElement(f, 'Shortcut', Id='AppShortcut', Directory='ProgramMenuFolder', Advertise='yes', Name=args.name)

            if args.shortcut_name_mui_id is not None:
                if args.shortcut_name_mui_dll is None:
                    args.shortcut_name_mui_dll = args.shortcut

                shortcutel.attrib['DisplayResourceDll'] = '[INSTALLDIR]{}'.format(args.shortcut_name_mui_dll.replace('/', '\\'))
                shortcutel.attrib['DisplayResourceId'] = str(args.shortcut_name_mui_id)

            # need to reference start menu folder, otherwise advertised installation might fail
            ET.SubElement(targetdir, 'Directory', Id='ProgramMenuFolder', Name='All Programs')

    if args.icon is not None:
        # Windows Installer WTF: icons for shortcuts (and file associations) need to reside in EXE or DLL files
        # therefore, we build a DLL file containing the icon (and only the icon) here

        # TODO: if a .exe or .dll file was specified, use that, or,
        # even better, extract the icon from the specified .exe or .dll
        # file and build a new .dll file containing only that icon

        ico2dll(args.icon, os.path.join(tmpdir, 'appico.dll'))

        if shortcutel is not None:
            name, extension = os.path.splitext(args.shortcut)

            # windows installer WTF: shortcut icon id must have same extension as shortcut target
            iconid = 'AppIcon' + extension.upper()
            shortcutel.attrib['Icon'] = iconid
        else:
            iconid = 'app.ico'

        ET.SubElement(product, 'Icon', Id=iconid, SourceFile=os.path.join(tmpdir, 'appico.dll'))
        ET.SubElement(product, 'Property', Id='ARPPRODUCTICON', Value=iconid)

    # file associations
    if len(args.assoc_extension) > 0 and args.assoc_target is not None:
        targetpath = '"[INSTALLDIR]{}"'.format(args.assoc_target.replace('/', '\\'))

        addregcomp(Key='Software\\RegisteredApplications',
                    Name='{}'.format(args.upgrade_code),
                    Value='Software\\Classes\\Applications\\{}.exe\\Capabilities'.format(args.upgrade_code))

        addregcomp(Key='Software\\Classes\\Applications\\{}.exe\\Capabilities'.format(args.upgrade_code),
                    Name='ApplicationDescription',
                    Value=args.name)

        addregcomp(Key='Software\\Classes\\Applications\\{}.exe\\shell\\open\\command'.format(args.upgrade_code),
                    Value='{} "%1"'.format(targetpath))

        for ext in args.assoc_extension:
            progid = '{}.Assoc.{}'.format(args.upgrade_code, ext)

            addregcomp(Key='Software\\Classes\\{}\\DefaultIcon'.format(progid),
                        Value='{},{}'.format(targetpath, args.assoc_icon_index))

            if args.assoc_description is not None:
                addregcomp(Key='Software\\Classes\\{}'.format(progid),
                           Value=args.assoc_description)

            addregcomp(Key='Software\\Classes\\{}\\shell\\open\\command'.format(progid),
                        Value='{} "%1"'.format(targetpath))

            addregcomp(Key='Software\\Classes\\Applications\\{}.exe\\Capabilities\\FileAssociations'.format(args.upgrade_code),
                        Name='.{}'.format(ext),
                        Value=progid)

            addregcomp(Key='Software\\Classes\\.{}\\OpenWithProgIds'.format(ext),
                        Name=progid, Value='')

        if args.x64:
            shchangenotify_dll = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'custom-actions', 'shchangenotify', 'shchangenotify64.dll')
        else:
            shchangenotify_dll = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'custom-actions', 'shchangenotify', 'shchangenotify32.dll')

        binel = ET.SubElement(product, 'Binary', Id='Binary_ShChangeNotifyDll', SourceFile=shchangenotify_dll)
        cael = ET.SubElement(product, 'CustomAction', Id='CA_ShChangeNotify', BinaryKey=binel.attrib['Id'], DllEntry='CallSHChangeNotifyAssocChanged', Return='ignore')

        iesel = ET.SubElement(product, 'InstallExecuteSequence')
        ET.SubElement(iesel, 'Custom', Action=cael.attrib['Id'], After='InstallFinalize')

    # write wxs and build msi
    with open(os.path.join(tmpdir, 'app.wxs'), 'wb') as f:
        f.write(b'<?xml version="1.0" encoding="utf-8" ?>')
        f.write(ET.tostring(wix))

    if args.output_wxs is not None:
        shutil.copyfile(os.path.join(tmpdir, 'app.wxs'), args.output_wxs)

    if os.name == 'nt':
        wixdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '3rdparty', 'wix')
        candleexe = os.path.join(wixdir, 'candle.exe')
        lightexe = os.path.join(wixdir, 'light.exe')
        smokeexe = os.path.join(wixdir, 'smoke.exe')

        if args.x64:
            arch = 'x64'
        else:
            arch = 'x86'

        subprocess.run([candleexe, '-nologo', '-arch', arch, '-out', os.path.join(tmpdir, 'app.wixobj'), os.path.join(tmpdir, 'app.wxs')], check=True)

        lightargs = ['-nologo', '-sval']
        if args.with_ui is not None:
            lightargs += [ '-ext', 'WixUIExtension', '-cultures:' + args.with_ui ]


        subprocess.run([lightexe] + lightargs + ['-out', os.path.join(tmpdir, 'app.msi'), os.path.join(tmpdir, 'app.wixobj')], check=True)

        try:
            subprocess.run([smokeexe, '-nologo', '-sice:ICE61', '-sice:ICE40', os.path.join(tmpdir, 'app.msi')], check=True)
        except subprocess.CalledProcessError as e:
            logging.warning('MSI validation failed')
            logging.warning(e)
    else:
        subprocess.run(['wixl', os.path.join(tmpdir, 'app.wxs')], check=True)

    shutil.copyfile(os.path.join(tmpdir, 'app.msi'), args.output_msi)
