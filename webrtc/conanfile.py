import os
from conans import ConanFile, CMake, tools
from conans.tools import os_info
from conans.errors import ConanInvalidConfiguration

class WebrtcConan(ConanFile):
    name = "google-webrtc"
    # versions https://chromiumdash.appspot.com/releases?platform=Linux
    # the version 83.0.4103.61 means v83, branch head 4103 (daily branches)
    # https://groups.google.com/forum/#!msg/discuss-webrtc/Ozvbd0p7Q1Y/M4WN2cRKCwAJ
    version = "94"
    _branchHead = "4606"
    license = "MIT"
    author = "Markus Lanner <contact@markus-lanner.com>"
    url = "github.com/freckled-dev/conan-google-webrtc"
    description = "Google Webrtc"
    topics = ("webrtc", "google")
    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [False], "use_h264": [True, False]}
    default_options = {"shared": False, "use_h264": True}
    no_copy_source = True # on windows we patch. but we patch in source()
    short_paths = True # it's a must. depot_tools checkout otherwise. Even if long paths are activated (win10 and msys)
    _webrtc_source = ""
    _depot_tools_dir = ""

    def configure(self):
        compiler = self.settings.compiler
        if compiler == "gcc" or compiler == "clang":
            # due to webrtc using its own clang. no gcc version is needed. results in better cache hit-rate
            #del self.settings.compiler.version
            del self.settings.compiler

    def source(self):
        self.setup_vars()
        if self.settings.os == "Windows":
            tools.download("https://storage.googleapis.com/chrome-infra/depot_tools.zip", "depot_tools.zip")
            tools.unzip("depot_tools.zip", destination="depot_tools")
        else:
            git_depot_tools = tools.Git(folder="depot_tools")
            git_depot_tools.clone("https://chromium.googlesource.com/chromium/tools/depot_tools.git", "main")
        with tools.environment_append({"PATH": [self._depot_tools_dir], "DEPOT_TOOLS_WIN_TOOLCHAIN": "0"}):
            self.run("gclient")
            if self.settings.os == "iOS":
                self.run("fetch --nohooks webrtc_ios")
            else:
                self.run("fetch --nohooks webrtc")
            with tools.chdir('src'):
                self.run("git checkout -b %s branch-heads/%s" % (self.version, self._branchHead))
                self.run("gclient sync -D")
        self._patch_runtime()

    def _is_debug(self):
        build_type = self.settings.get_safe("build_type", default="Release")
        return build_type == "Debug"

    def _is_release_with_debug_information(self):
        build_type = self.settings.get_safe("build_type", default="Release")
        return build_type == "RelWithDebInfo"

    def build(self):
        self.setup_vars()
        # gn gen out/Default --args='is_debug=true use_custom_libcxx=false
        #   use_custom_libcxx_for_host=false cc_wrapper="ccache" use_rtti=true
        #   is_clang=true use_sysroot=false treat_warnings_as_errors=false
        #   rtc_include_tests=false libyuv_include_tests=false
        #   clang_base_path="/usr" clang_use_chrome_plugins=false
        #   use_lld=false use_gold=false'

        args = ""
        # no bundled libc++
        #if self.settings.os != "iOS":
            # args += "use_custom_libcxx=false use_custom_libcxx_for_host=false "
            # args += "use_custom_libcxx_for_host=false "
        # needed on linux 64bit, else there will be compile errors,
        # like `td::__1::__next_prime`
        #args += "use_custom_libcxx=false "
        args += "treat_warnings_as_errors=false "
        if self._is_debug():
            args += "is_debug=true "
        else:
            args += "is_debug=false "
        # no tests, else the windows debug version will not compile
        args += "rtc_include_tests=false libyuv_include_tests=false "
        # no tools
        args += "rtc_build_tools=false "
        if self.options.use_h264:
            args += "rtc_use_h264=true proprietary_codecs=true ffmpeg_branding=\\\"Chrome\\\" "
        if self.settings.os == "Windows":
            args += self._create_windows_arguments()
        if self.settings.os == "Linux":
            args += self._create_linux_arguments()
        if self.settings.os == "Macos":
            args += self._create_macos_arguments()
        if self.settings.os == "iOS":
            args += self._create_ios_arguments()
        call = "gn gen \"%s\" --args=\"%s\"" % (self.build_folder, args)
        self.output.info("call:%s" % (call))
        with tools.environment_append({"PATH": [self._depot_tools_dir], "DEPOT_TOOLS_WIN_TOOLCHAIN": "0"}):
            # TODO test without. maybe they fixed it
            if self.settings.os == "Windows":
                self.run("python -m pip install --upgrade pywin32")
                self.run("python3 -m pip install --upgrade pywin32")
            with tools.chdir(self._webrtc_source):
                if self.settings.os == "Windows":
                    with tools.vcvars(self.settings):
                        self.run(call)
                        self.run("gn args --list \"%s\"" % (self.build_folder))
                else:
                    self.run(call)
            with tools.chdir(self.build_folder):
                self.run('ninja')

    def _patch_runtime(self):
        # https://groups.google.com/forum/#!topic/discuss-webrtc/f44XZnQDNIA
        # https://stackoverflow.com/questions/49083754/linking-webrtc-with-qt-on-windows
        # https://docs.conan.io/en/latest/reference/tools.html#tools-replace-in-file
        # TODO check the actually set runtime
        if self.settings.os == "Windows":
            with tools.chdir(self._webrtc_source):
                build_gn_file = os.path.join('build', 'config', 'win', 'BUILD.gn')
                tools.replace_in_file(build_gn_file,
                    'configs = [ ":static_crt" ]',
                    'configs = [ ":dynamic_crt" ]')

                thread_file = os.path.join('rtc_base', 'thread.cc')
                # https://stackoverflow.com/questions/62218555/webrtc-stddeque-iterator-exception-when-rtc-dcheck-is-on
                # there's a bug with iterator debug
                tools.replace_in_file(thread_file,
                    '#if RTC_DCHECK_IS_ON',
                    '#if 0 // patched in conanfile, RTC_DCHECK_IS_ON')
        if self.settings.os == "Linux":
            with tools.chdir(self._webrtc_source):
                clockdrift_detector_file = os.path.join(
                        'modules', 'audio_processing', 'aec3', 'clockdrift_detector.h')
                # missing `std::` wont compile with gcc10
                tools.replace_in_file(clockdrift_detector_file,
                    ' size_t stability_counter_;',
                    ' std::size_t stability_counter_;')
        if self.settings.os == "Macos":
            pass

        # there is a `include <cstring>` missing when not compiling with 
        # their stdcxx (`use_custom_libcxx`)
        with tools.chdir(self._webrtc_source):
            stack_copier_signal_file = os.path.join( 'base', 'profiler', 'stack_copier_signal.cc')
            tools.replace_in_file(stack_copier_signal_file,
                '#include <syscall.h>',
                '''#include <syscall.h>
                   #include <cstring>''')


    def setup_vars(self):
        self._depot_tools_dir = os.path.join(self.source_folder, "depot_tools")
        self.output.info("depot_tools_dir '%s'" % (self._depot_tools_dir))
        self._webrtc_source = os.path.join(self.source_folder, "src")

    def _create_windows_arguments(self):
        # remove visual_studio_version? according to documentation this value is always 2015
        args = "is_clang=false visual_studio_version=2019 "
        # args = ""
        if self._is_debug():
            # if not set the compilation will fail with:
            # _iterator_debug_level value '0' doesn't match value '2'
            # does not compile if tests and tools gets compiled in!
            args += "enable_iterator_debugging=true "
            # pass
        return args

    def _create_linux_arguments(self):
        with tools.chdir(self._webrtc_source):
            self.run("./build/linux/sysroot_scripts/install-sysroot.py --arch=amd64")
            if self.settings.arch == "armv8":
                self.run("./build/linux/sysroot_scripts/install-sysroot.py --arch=arm64")
            if self.settings.arch == "armv7":
                self.run("./build/linux/sysroot_scripts/install-sysroot.py --arch=arm")
        args = ""
        args += "use_rtti=true "
        if self.settings.arch != "armv8" and self.settings.arch != "armv7":
            args += "use_sysroot=false "
        # compiler = self.settings.compiler
        # if compiler == "gcc":
        #     args += "is_clang=false use_gold=false use_lld=false "
        # else:
        #     self.output.error("the compiler '%s' is not tested" % (compiler))
        if tools.which('ccache'):
            args += 'cc_wrapper=\\"ccache\\" '
        if self.settings.arch == "armv8":
            args += 'target_cpu=\\"arm64\\" '
        if self.settings.arch == "armv7":
            args += 'target_cpu=\\"arm\\" '
        if self._is_release_with_debug_information():
            # '2' results in a ~450mb static library
            # args += 'symbol_level=2 '
            args += 'symbol_level=1 '
        return args

    def _create_macos_arguments(self):
        args = "use_rtti=true "
        args += "use_sysroot=false "
        if tools.which('ccache'):
            args += 'cc_wrapper=\\"ccache\\" '
        if self._is_release_with_debug_information():
            # '2' results in a ~450mb static library
            # args += 'symbol_level=2 '
            args += 'symbol_level=1 '
        return args

    def _create_ios_arguments(self):
        args = ""
        args += "use_rtti=true "
        # args += "use_sysroot=false "
        args += 'target_os=\\"ios\\" ios_enable_code_signing=false '
        # `enable_ios_bitcode` needs `use_xcode_clang=true`
        # if `use_xcode_clang` is false, it will use the with the repo shipped clang
        args += 'enable_ios_bitcode=true use_xcode_clang=true '
        # for sigining you can add the following, and remove ios_enable_code_signing
        # 'ios_code_signing_identity=\\"<your apple development identity>\\" '
        if self.settings.arch == "armv8":
            args += 'target_cpu=\\"arm64\\" '
        elif self.settings.arch == "x86_64":
            args += 'target_cpu=\\"x64\\" '
        else:
            raise ConanInvalidConfiguration("not a valid iOS arch:" + settings.arch)
        if tools.which('ccache'):
            args += 'cc_wrapper=\\"ccache\\" '
        if self._is_release_with_debug_information():
            # '2' results in a ~450mb static library
            # args += 'symbol_level=2 '
            args += 'symbol_level=1 '
        return args

    def package(self):
        self.copy("*.h", dst="include", src="src")
        self.copy("*.inc", dst="include", src="src")

        self.copy("*webrtc.lib", dst="lib", keep_path=False)
        self.copy("*webrtc.dll", dst="bin", keep_path=False)
        self.copy("*libwebrtc.so", dst="lib", keep_path=False)
        self.copy("*libwebrtc.dylib", dst="lib", keep_path=False)
        self.copy("*libwebrtc.a", dst="lib", keep_path=False)

    def package_info(self):
        self.cpp_info.libs = ["webrtc"]
        self.cpp_info.includedirs = [
                "include",
                "include/api",
                "include/call",
                "include/common_video",
                "include/logging",
                "include/media",
                "include/modules",
                "include/p2p",
                "include/rtc_base",
                "include/system_wrappers",
                "include/third_party/abseil-cpp",
                "include/third_party/boringssl/src/include",
                "include/third_party/libyuv/include",
                ]
        if self.settings.os == "Windows":
            self.cpp_info.defines = ["WEBRTC_WIN", "NOMINMAX"]
            self.cpp_info.system_libs = ['secur32', 'winmm', 'dmoguids',
                    'wmcodecdspuuid', 'msdmo', 'Strmiids']
        if self.settings.os == "Linux":
            self.cpp_info.system_libs = ["dl"]
            self.cpp_info.defines = ["WEBRTC_POSIX", "WEBRTC_LINUX"]
        if self.settings.os == "Macos":
            self.cpp_info.defines = ["WEBRTC_POSIX", "WEBRTC_MAC"]
        if self.settings.os == "iOS":
            self.cpp_info.defines = ["WEBRTC_POSIX", "WEBRTC_IOS", "WEBRTC_MAC"]
        if self.options.use_h264:
            self.cpp_info.defines += ["WEBRTC_USE_H264"]



