from conans import ConanFile, CMake, tools


class WebrtcConan(ConanFile):
    name = "google-webrtc"
    version = "m79"
    license = "MIT"
    author = "Markus Lanner <contact@markus-lanner.com>"
    url = "github.com/freckled-dev/conan-google-webrtc"
    description = "Google Webrtc"
    topics = ("webrtc", "google")
    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [False]}
    default_options = {"shared": False}
    no_copy_source = True
    build_requires = "google-gn/1.0"

    def source(self):
        git = tools.Git(folder="webrtc")
        git.clone("https://github.com/lileimt/WebRTC.git", "master")

    def build(self):
        # gn gen out/Default --args='is_debug=true use_custom_libcxx=false
        #   use_custom_libcxx_for_host=false cc_wrapper="ccache" use_rtti=true
        #   is_clang=true use_sysroot=false treat_warnings_as_errors=false
        #   rtc_include_tests=false libyuv_include_tests=false
        #   clang_base_path="/usr" clang_use_chrome_plugins=false
        #   use_lld=false use_gold=false'

        args = "use_rtti=true treat_warnings_as_errors=false "
        args += "use_sysroot=false "
        # no tests
        args += "rtc_include_tests=false libyuv_include_tests=false "
        # no bundled libc++
        args += "use_custom_libcxx=false use_custom_libcxx_for_host=false "
        if tools.which('ccache'):
            args += 'cc_wrapper="ccache" '
        with tools.chdir('%s/webrtc/src' % (self.source_folder)):
            self.run("gn gen %s --args='%s'" % (self.build_folder, args))
        with tools.chdir(self.build_folder):
            self.run('ninja')

    def package(self):
        self.copy("api/*.h", dst="include", src="webrtc/src")
        self.copy("call/*.h", dst="include", src="webrtc/src")
        self.copy("common_types.h", dst="include", src="webrtc/src")
        self.copy("common_video/*.h", dst="include", src="webrtc/src")
        self.copy("logging/*.h", dst="include", src="webrtc/src")
        self.copy("media/*.h", dst="include", src="webrtc/src")
        self.copy("modules/*.h", dst="include", src="webrtc/src")
        self.copy("p2p/*.h", dst="include", src="webrtc/src")
        self.copy("rtc_base/*.h", dst="include", src="webrtc/src")
        self.copy("system_wrappers/*.h", dst="include", src="webrtc/src")
        self.copy("absl/*.h", dst="include",
                src="webrtc/src/third_party/abseil-cpp")

        # self.copy("*.hpp", dst="include", src="webrtc/src/api")
        self.copy("*webrtc.lib", dst="lib", keep_path=False)
        self.copy("*webrtc.dll", dst="bin", keep_path=False)
        self.copy("*libwebrtc.so", dst="lib", keep_path=False)
        self.copy("*libwebrtc.dylib", dst="lib", keep_path=False)
        self.copy("*libwebrtc.a", dst="lib", keep_path=False)

    def package_info(self):
        self.cpp_info.libs = ["webrtc"]
        self.cpp_info.system_libs = ["dl"]
        self.cpp_info.defines = ["WEBRTC_POSIX", "WEBRTC_LINUX", 
                "_GLIBCXX_USE_CXX11_ABI=1"]


