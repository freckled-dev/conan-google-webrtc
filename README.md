# about

conan build files for google webrtc. \
https://webrtc.org \
https://webrtc.github.io/webrtc-org/

# prerequists

## ubuntu

install system dependencies
```bash
./install-build-deps.sh
```

now you are set up.

## windows

instructions
https://chromium.googlesource.com/chromium/src/+/master/docs/windows_build_instructions.md

use the visual studio installer and install the “Desktop development with C++”
component and the “MFC/ATL support” sub-components.

The SDK Debugging Tools must also be installed. If the Windows 10 SDK was 
installed via the Visual Studio installer, then they can be installed by going
to: Control Panel → Programs → Programs and Features → 
Select the “Windows Software Development Kit” → Change → Change → 
Check “Debugging Tools For Windows” → Change.

create and set the environment variable: "DEPOT_TOOLS_WIN_TOOLCHAIN=1". Else it searches for vs2017 in googly style.

You must have the version 10.0.18362 or higher Windows 10 SDK installed. This can be installed separately or by checking the appropriate box in the Visual Studio Installer. or by https://developer.microsoft.com/en-us/windows/downloads/windows-10-sdk/

disable Antimalware service

use `cmd`. Everything else does not work. Including Power Shell.

because there's no pip, install conan by installer \
https://conan.io/downloads.html
https://dl.bintray.com/conan/installers/conan-win-64_1_24_1.exe

now ur set up. create the packages by

### notes on versions

v69
- install pywin32-227 `python -m pip install pywin32` https://stackoverflow.com/questions/55551188/python-importerror-no-module-named-win32file
Install windows 10 SDK `10.0.17*`

### tips if there're errors

by default the conan script loads depot_tools. To do it manually:
download depot_tools. add it to the system environment.
ensure it's first in PATH so no other pyhton exe can be found before it. \
https://storage.googleapis.com/chrome-infra/depot_tools.zip
verify that python comes first from depot_tools by running
```bat
where python
where python3
```

# create packages and upload them

create release and debug packages
```bash
conan create .
conan create . -s build_type=Debug
```

upload them by
```bat
conan remote add freckled_webrtc https://api.bintray.com/conan/freckled/google-webrtc
conan user -p <APIKEY> -r freckled_webrtc freckled
conan upload --all -r freckled_webrtc google-webrtc
```

