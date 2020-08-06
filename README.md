# jkmsigen

Script to generate simple `.msi` installers. Frontend for [WiX](https://wixtoolset.org/).

## Features

 * Install files in `C:\Program Files\<My App>`
 * Create a Start Menu Shortcut
 * Installer supports upgrades and downgrades
 * Installer supports [advertised installs](https://docs.microsoft.com/en-us/windows/win32/msi/advertisement)
 * Can build a 64bit installer

## Quick Start

I recommend downloading the ZIP or MSI package from the release page. It bundles Python and WiX, so you can start right away.

Generate a `.msi` installer using a command similar to this one:

    jkmsigen.exe --output-msi hello.msi --name "Hello World" path\to\hello\world

It is very much recommended that you also supply the `--upgrade-code` and `--version` arguments.
If you don’t supply them, `jkmsigen` will generate an upgrade code and version for you.

Also see the examples in the `test` directory.

## Parameters

#### --output-msi=PATH/TO/INSTALLER.MSI

Specifies where to put the generated `.msi` file.

#### --output-wxs=PATH/TO/INSTALLER.WXS

Optional, can save the temporarily created `.wxs` file somewhere for inspection

#### --upgrade-code=

Upgrade Code GUID. The upgrade code is used to identify already installed versions of
your application. Upgrades and downgrades will only work if the two versions share
the same upgrade code.

If you don’t specify this parameter, a random upgrade code is generated and a warning
containing the generated GUID will be emitted.

#### --name=

Name of your application. The name will be used as

* Name of the subdirectory in `C:\Program Files`
* Title of the start menu shortcut
* Name of the application in the `Add/Remove Programs` control panel

#### --manufacturer=

Manufacturer name. Will be displayed in `Add/Remove Programs` control panel.

#### --shortcut=

Path to the shortcut target. The path must be relative to the directory of files
given as postional argument on the command line. It must use forward slashes (`/`),
not backslashes (`\`).

The shortcut target is required to be an `EXE` file. It is also recommended to specify
the `--icon` argument because otherwise the shortcut might not have an icon.

#### --icon=

Path to a `.ico` file. The icon is used as shortcut icon and displayed in the `Add/Remove Programs` control panel

#### --with-ui=CULTURE

Enables WixUI. The `WixUI_InstallDir` dialog set is used. You also have to specify a culture which controls
the language of the setup UI (e.g. `en-us`).

Use `-dWixUILicenseRtf="path\to\license.rtf"` to choose the license displayed during the installation.

#### --x64

Build a 64bit installer.

#### --codepage

Set the codepage used for the installer. Windows installer `.msi` files cannot reliably use Unicode, they
have to use one of the ancient ANSI codepages. The default codepage is 1252.

The application name, the manufacturer name and all filenames have to consist of characters in the
given codepage only.

#### --language

Set the language of the installer. The default is 0 (i.e. language neutral).

#### source\directory

Path to the installed files. Can also be a ZIP file.

The files and directories contained there will be installed under `C:\Program Files\<App Name>`.

## Limitations

#### Installer features not supported by jkmsigen

* Registering file extensions
* Registering COM components
* Adding registry entries
* Installing files outside of `C:\Program Files`
* Checking prerequisites such as Windows versions or installed runtime libraries
* Install runtime libraries during setup
* Adding shortcuts on the desktop, adding more than one shortcut or creating a directory in the start menu
* Multi-Language installers

Most of these are deliberate.

#### MSI and Unicode

Windows installer `.msi` files cannot reliably use Unicode, they
have to use one of the ancient ANSI codepages.

The application name, the manufacturer name and all filenames have to consist of characters in the
given codepage only. You can change the codepage using the `--codepage` parameter.

#### Building on linux with Wine

WiX and `jkmsigen` mostly work in Wine with the following limitations:

* The `jkmsigen.exe` wrapper does not work. You have to run it using `3rdparty\python3\python.exe jkmsigen.py`.
* MSI validation will always fail.
* You might need to install the original .NET Framework (`winetricks dotnet35sp1`).

## Related Projects

* [msicreator by jpakkane](https://github.com/jpakkane/msicreator)
* [WiX.python](https://wix.sk1project.net/)

