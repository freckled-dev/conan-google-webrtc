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

because there's no pip, install conan by installer \
https://conan.io/downloads.html
https://dl.bintray.com/conan/installers/conan-win-64_1_24_1.exe

now ur set up. create the packages by

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

