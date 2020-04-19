import os
from conans import ConanFile, CMake, tools


class GnConan(ConanFile):
    name = "google-gn"
    version = "1.0"
    license = "MIT"
    author = "Markus Lanner <contact@markus-lanner.com>"
    url = "github.com/freckled-dev/conan-google-webrtc"
    description = "Google Gn"
    topics = ("gn", "google")
    settings = "os", "compiler", "build_type", "arch"

    def source(self):
        git = tools.Git(folder="gn")
        git.clone("https://gn.googlesource.com/gn/", "master")

    def build(self):
        with tools.chdir('%s/gn' % (self.source_folder)):
            self.run("python build/gen.py")
            self.run("ninja -C out")
        # out/gn_unittests

    def package(self):
        bin_source_path = os.path.join(self.source_folder, "gn", "out")
        self.copy("gn", dst="bin", src=bin_source_path)
        self.copy("gn.exe", dst="bin", src=bin_source_path)

    def package_info(self):
        self.env_info.PATH.append(os.path.join(self.package_folder, "bin"))

