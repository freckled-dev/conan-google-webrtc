import os
from conans import ConanFile
from conans import tools
from six import StringIO

class Arm64v8SysrootConan(ConanFile):
    name = "arm64v8-sysroot"
    version = "1.0"
    default_user = "acof"
    default_channel = "stable"
    url = "https://scm-01.karlstorz.com/network-based-recording/infrastructure"
    license = "All rights reserved"
    description = "armv64v8 sysroot"
    settings = "os"
    exports_sources = "Dockerfile"
    #no_copy_source = True

    _target='aarch64-linux-gnu'

    def source(self):
        # build image
        docker_build_output = StringIO()
        self.run('docker build --network host .', output=docker_build_output) 
        # last word is the docker image id
        image_id = docker_build_output.getvalue().split()[-1]
        self.output.success(f"created docker image image_id: {image_id}")
        # create container from image
        docker_create_output = StringIO()
        self.run('docker create ' + image_id, output=docker_create_output)
        container_id = docker_create_output.getvalue().strip().split()[-1]
        self.output.success(f"created docker container container_id: {container_id}")
        # copy sysroot folders from container
        # `/etc` due to `/etc/alternatives` (`libblas.so.3`)
        folders=['/usr', '/lib', '/etc']
        sysroot_dir=f'install/{self._target}/sys-root/'
        tools.mkdir(sysroot_dir)
        for folder in folders:
            self.run(f'docker cp {container_id}:{folder} {sysroot_dir}')
        # remove unneeded folders
        usr_bin=os.path.join(sysroot_dir, 'usr', 'bin')
        tools.rmdir(usr_bin)

        # TODO clean symlinks!

    def build(self):
        pass

    def package(self):
        # Copy all the required files for your toolchain
        self.copy("*", dst="", src="install", symlinks=True)

    def package_info(self):
        # https://docs.conan.io/en/latest/reference/env_vars.html

        # sysroot
        sysroot=os.path.join(self.package_folder, self._target, 'sys-root')
        self.env_info.SYSROOT = sysroot
        self.env_info.CONAN_CMAKE_FIND_ROOT_PATH = sysroot
        self.env_info.CONAN_CMAKE_SYSROOT = sysroot

        # pkgconf
        # don't, gave an error on hive (avahi)
        # self.env_info.PKG_CONFIG_SYSROOT_DIR = sysroot
        # self.env_info.PKG_CONFIG_PATH = "/usr/lib/aarch64-linux-gnu/pkgconfig"

