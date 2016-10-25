from conans import ConanFile
import os, shutil
from conans.tools import download, unzip, replace_in_file, check_md5
from conans import CMake


class NettleConan(ConanFile):
    name = "nettle"
    version = "3.3"
    branch = "master"
    ZIP_FOLDER_NAME = "nettle-%s" % version
    generators = "cmake"
    settings =  "os", "compiler", "arch", "build_type"
    options = {"shared": [True, False]}
    requires = 'gmp/6.1.1@DEGoodmanWilson/testing'

    url = "http://github.com/DEGoodmanWilson/conan-nettle"
    default_options = "shared=False"

    def source(self):
        zip_name = "nettle-%s.tar.gz" % self.version
        download("https://ftp.gnu.org/gnu/nettle//%s" % zip_name, zip_name)
        check_md5(zip_name, "10f969f78a463704ae73529978148dbe")
        unzip(zip_name)
        os.unlink(zip_name)

    def config(self):
        del self.settings.compiler.libcxx

    def generic_env_configure_vars(self, verbose=False):
        """Reusable in any lib with configure!!"""

        if self.settings.os == "Windows":
            self.output.fatal("Cannot build on Windows, sorry!")
            return

        if self.settings.os == "Linux" or self.settings.os == "Macos":
            libs = 'LIBS="%s"' % " ".join(["-l%s" % lib for lib in self.deps_cpp_info.libs])
            ldflags = 'LDFLAGS="%s"' % " ".join(["-L%s" % lib for lib in self.deps_cpp_info.lib_paths]) 
            archflag = "-m32" if self.settings.arch == "x86" else ""
            cflags = 'CFLAGS="-fPIC %s %s %s"' % (archflag, " ".join(self.deps_cpp_info.cflags), " ".join(['-I"%s"' % lib for lib in self.deps_cpp_info.include_paths]))
            cpp_flags = 'CPPFLAGS="%s %s %s"' % (archflag, " ".join(self.deps_cpp_info.cppflags), " ".join(['-I"%s"' % lib for lib in self.deps_cpp_info.include_paths]))
            command = "env %s %s %s %s" % (libs, ldflags, cflags, cpp_flags)
        elif self.settings.os == "Windows" and self.settings.compiler == "Visual Studio":
            cl_args = " ".join(['/I"%s"' % lib for lib in self.deps_cpp_info.include_paths])
            lib_paths= ";".join(['"%s"' % lib for lib in self.deps_cpp_info.lib_paths])
            command = "SET LIB=%s;%%LIB%% && SET CL=%s" % (lib_paths, cl_args)
            if verbose:
                command += " && SET LINK=/VERBOSE"
        
        return command
       
    def build(self):
        if self.settings.os == "Windows":
            self.output.fatal("Cannot build on Windows, sorry!")
            return # no can do boss!

        self.build_with_configure()
            
        
    def build_with_configure(self):
        config_options_string = ""

        for option_name in self.options.values.fields:
            activated = getattr(self.options, option_name)
            if activated:
                self.output.info("Activated option! %s" % option_name)
                config_options_string += " --%s" % option_name.replace("_", "-")

        configure_command = "cd %s && %s ./configure --enable-static --enable-shared %s" % (self.ZIP_FOLDER_NAME, self.generic_env_configure_vars(), config_options_string)
        self.output.warn(configure_command)
        self.run(configure_command)
        self.run("cd %s && make" % self.ZIP_FOLDER_NAME)
       

    def package(self):
        if self.settings.os == "Windows":
            self.output.fatal("Cannot build on Windows, sorry!")
            return

        self.copy("*.h", dst="include/nettle", src="%s" % (self.ZIP_FOLDER_NAME), keep_path=True)
        if self.options.shared:
            self.copy(pattern="*.so*", dst="lib", src=self.ZIP_FOLDER_NAME, keep_path=False)
            self.copy(pattern="*.dll*", dst="bin", src=self.ZIP_FOLDER_NAME, keep_path=False)
        else:
            self.copy(pattern="*.a", dst="lib", src="%s" % self.ZIP_FOLDER_NAME, keep_path=False)
        
        self.copy(pattern="*.lib", dst="lib", src="%s" % self.ZIP_FOLDER_NAME, keep_path=False)
        
    def package_info(self):
        self.cpp_info.libs = ['nettle', 'hogweed']


