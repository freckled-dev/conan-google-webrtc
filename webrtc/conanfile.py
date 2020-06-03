import os
from conans import ConanFile, CMake, tools

class WebrtcConan(ConanFile):
    name = "google-webrtc"
    # versions https://chromiumdash.appspot.com/releases?platform=Linux
    # the version 83.0.4103.61 means v83, branch head 4103 (daily branches)
    # https://groups.google.com/forum/#!msg/discuss-webrtc/Ozvbd0p7Q1Y/M4WN2cRKCwAJ
    version = "83"
    _branchHead = "4103"
    license = "MIT"
    author = "Markus Lanner <contact@markus-lanner.com>"
    url = "github.com/freckled-dev/conan-google-webrtc"
    description = "Google Webrtc"
    topics = ("webrtc", "google")
    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [False]}
    default_options = {"shared": False}
    # no_copy_source = True # on windows we patch. so we can't set it
    short_paths = True
    _webrtc_source = ""
    _depot_tools_dir = ""

    def source(self):
        self.setup_vars()
        if self.settings.os == "Windows":
            tools.download("https://storage.googleapis.com/chrome-infra/depot_tools.zip", "depot_tools.zip")
            tools.unzip("depot_tools.zip", destination="depot_tools")
        else:
            git_depot_tools = tools.Git(folder="depot_tools")
            git_depot_tools.clone("https://chromium.googlesource.com/chromium/tools/depot_tools.git", "master")
        with tools.environment_append({"PATH": [self._depot_tools_dir]}):
            self.run("gclient")
            self.run("fetch --nohooks webrtc")
            with tools.chdir('src'):
                self.run("git checkout -b %s branch-heads/%s" % (self.version, self._branchHead))
                self.run("gclient sync -D")

    def build(self):
        self.setup_vars()
        self._patch_runtime()
        # gn gen out/Default --args='is_debug=true use_custom_libcxx=false
        #   use_custom_libcxx_for_host=false cc_wrapper="ccache" use_rtti=true
        #   is_clang=true use_sysroot=false treat_warnings_as_errors=false
        #   rtc_include_tests=false libyuv_include_tests=false
        #   clang_base_path="/usr" clang_use_chrome_plugins=false
        #   use_lld=false use_gold=false'

        # no bundled libc++
        args = "use_custom_libcxx=false use_custom_libcxx_for_host=false "
        build_type = self.settings.get_safe("build_type", default="Release")
        if build_type == "Debug":
            args += "is_debug=true "
        else:
            args += "is_debug=false "
        # no tests
        # args += "rtc_include_tests=false libyuv_include_tests=false "
        # no tools
        # args += "rtc_build_tools=false "
        if self.settings.os == "Windows":
            args += self.create_windows_arguments()
        if self.settings.os == "Linux":
            args += self.create_linux_arguments()
        call = "gn gen \"%s\" --args=\"%s\"" % (self.build_folder, args)
        self.output.info("call:%s" % (call))
        with tools.environment_append({"PATH": [self._depot_tools_dir]}):
            # TODO test without. maybe they fixed it
            if self.settings.os == "Windows":
                self.run("python -m pip install --upgrade pywin32")
                self.run("python3 -m pip install --upgrade pywin32")
            with tools.chdir(self._webrtc_source):
                if self.settings.os == "Windows":
                    with tools.vcvars(self.settings):
                        self.run(call)
                else:
                    self.run(call)
            with tools.chdir(self.build_folder):
                self.run('ninja')

    def _patch_runtime(self):
        if self.settings.os != "Windows":
            return
        # https://groups.google.com/forum/#!topic/discuss-webrtc/f44XZnQDNIA
        # https://stackoverflow.com/questions/49083754/linking-webrtc-with-qt-on-windows
        # https://docs.conan.io/en/latest/reference/tools.html#tools-replace-in-file
        # TODO check the actually set runtime
        with tools.chdir(self._webrtc_source):
            build_gn_file = os.path.join('build', 'config', 'win', 'BUILD.gn')
            tools.replace_in_file(build_gn_file,
                'configs = [ ":static_crt" ]',
                'configs = [ ":dynamic_crt" ]')

    def setup_vars(self):
        self._depot_tools_dir = os.path.join(self.source_folder, "depot_tools")
        self.output.info("depot_tools_dir '%s'" % (self._depot_tools_dir))
        self._webrtc_source = os.path.join(self.source_folder, "src")

    def create_windows_arguments(self):
        args = ""
        return args

    def create_linux_arguments(self):
        args = "use_rtti=true treat_warnings_as_errors=false "
        args += "use_sysroot=false "
        # compiler = self.settings.compiler
        # if compiler == "gcc":
        #     args += "is_clang=false use_gold=false use_lld=false "
        # else:
        #     self.output.error("the compiler '%s' is not tested" % (compiler))
        if tools.which('ccache'):
            args += 'cc_wrapper=\\"ccache\\" '
        return args

    def package(self):
        self.copy("*.h", dst="include", src="src")

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
                ]
        if self.settings.os == "Windows":
            self.cpp_info.defines = ["WEBRTC_WIN", "NOMINMAX"]
            self.cpp_info.system_libs = ['secur32', 'winmm', 'dmoguids',
                    'wmcodecdspuuid', 'msdmo', 'Strmiids']
        if self.settings.os == "Linux":
            self.cpp_info.system_libs = ["dl"]
            self.cpp_info.defines = ["WEBRTC_POSIX", "WEBRTC_LINUX"]


