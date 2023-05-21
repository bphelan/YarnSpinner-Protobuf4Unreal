from argparse import ArgumentParser
import glob
import os
import platform
import shutil
import subprocess


def protobuf_source_dir():
    return "protobuf"


def out_dir():
    return "out"


def protobuf_build_dir():
    return os.path.join(out_dir(), "protobuf_build")


def protobuf_install_dir():
    return os.path.join(out_dir(), "protobuf_install")


def yarnspinner_proto_build_dir():
    return os.path.join(out_dir(), "YarnSpinner_proto_build")


def yarnspinner_proto_install_dir():
    return os.path.join(out_dir(), "YarnSpinner_proto_install")


def pb_h_file_dest(plugin_path):
    return os.path.join(plugin_path, "Source", "YarnSpinner", "Public", "YarnSpinnerCore")


def pb_cc_file_dest(plugin_path):
    return os.path.join(plugin_path, "Source", "YarnSpinner", "Private", "YarnSpinnerCore")


def pb_h_files():
    return [ "yarn_spinner.pb.h", "compiler_output.pb.h" ]


def pb_cc_files():
    return [ "yarn_spinner.pb.cc", "compiler_output.pb.cc" ]


def platform_name():
    match platform.system():
        case "Windows":
            return "Win64"
        case "Mac":
            return "Mac"
        case _:
            print("Unsupported platform: " + platform.system())
            exit(1)


def prepare_subrepos():
    print("\nPreparing subrepos...\n")
    subprocess.run(["git", "submodule", "update", "--init", "--recursive"])


def cleanup_previous_build():
    print("\nCleaning up previous build...\n")
    # subprocess.run(["git", "clean", "-fdx"])
    shutil.rmtree(protobuf_install_dir(), ignore_errors=True)
    shutil.rmtree(protobuf_build_dir(), ignore_errors=True)


def build_libprotobuf_windows():
    subprocess.run(["cmake", "-S", protobuf_source_dir(), "-B", protobuf_build_dir(), "-G", "Visual Studio 16 2019", "-A", "x64",
                    "-DCMAKE_BUILD_TYPE=$<$<CONFIG:Debug>:Debug>$<$<CONFIG:Release>:Release>",
                    "-DCMAKE_INSTALL_LIBDIR=lib/" + platform_name() + "/$<$<CONFIG:Debug>:Debug>$<$<CONFIG:Release>:Release>",
                    "-DCMAKE_INSTALL_PREFIX=" + protobuf_install_dir(),
                    # "-DCMAKE_MSVC_RUNTIME_LIBRARY=MultiThreaded$<$<CONFIG:Debug>:Debug>DLL",
                    "-DCMAKE_MSVC_RUNTIME_LIBRARY=MultiThreadedDLL",
                    "-DCMAKE_POLICY_DEFAULT_CMP0091=NEW", # prevent cmake ignoring CMAKE_MSVC_RUNTIME_LIBRARY in cmake v3.15+
                    "-Dprotobuf_BUILD_EXAMPLES=OFF",
                    "-Dprotobuf_BUILD_TESTS=OFF",
                    # "-Dprotobuf_BUILD_SHARED_LIBS=ON",
                    "-Dprotobuf_DEBUG_POSTFIX=",
                    "-Dprotobuf_DISABLE_RTTI=ON",
                    "-Dprotobuf_MSVC_STATIC_RUNTIME=OFF",
                    "-Dprotobuf_WITH_ZLIB=OFF",
                    ])
    subprocess.run(["cmake", "--build", protobuf_build_dir(), "--target", "install", "--config", "Debug"])
    subprocess.run(["cmake", "--build", protobuf_build_dir(), "--target", "install", "--config", "Release"])


def build_libprotobuf_mac():
    subprocess.run(["cmake", "-S", protobuf_source_dir(), "-B", protobuf_build_dir(), "-G", "Xcode",
                    "-DCMAKE_BUILD_TYPE=$<$<CONFIG:Debug>:Debug>$<$<CONFIG:Release>:Release>",
                    "-DCMAKE_INSTALL_LIBDIR=lib/" + platform_name() + "/$<$<CONFIG:Debug>:Debug>$<$<CONFIG:Release>:Release>",
                    "-DCMAKE_INSTALL_PREFIX=" + protobuf_install_dir(),
                    "-Dprotobuf_BUILD_EXAMPLES=OFF",
                    "-Dprotobuf_BUILD_TESTS=OFF",
                    "-Dprotobuf_DEBUG_POSTFIX=",
                    "-Dprotobuf_DISABLE_RTTI=ON",
                    "-Dprotobuf_WITH_ZLIB=OFF",
                    ])
    subprocess.run(["cmake", "--build", protobuf_build_dir(), "--target", "install", "--config", "Debug"])
    subprocess.run(["cmake", "--build", protobuf_build_dir(), "--target", "install", "--config", "Release"])


def build_libprotobuf():
    cleanup_previous_build()

    print("\nBuilding...\n")
    match platform.system():
        case "Windows":
            build_libprotobuf_windows()
        case "Mac":
            build_libprotobuf_mac()
        case _:
            print("Unsupported platform: " + platform.system())
            exit(1)


def copy_libprotobuf_files(plugin_path):
    print("\nCopying protobuf files to Unreal plugin...\n")
    module_path = os.path.join(plugin_path, "Source/ThirdParty/YSProtobuf")

    include_path = os.path.join(module_path, "include")
    lib_path = os.path.join(module_path, "lib", platform_name())

    # Cleanup old install
    shutil.rmtree(include_path, ignore_errors=True)
    os.makedirs(module_path, exist_ok=True)

    # Copy includes
    shutil.copytree(os.path.join(protobuf_install_dir(), "include"), include_path)

    # Copy only libprotobuf lib files to avoid bloating the plugin
    for config in [ "Debug", "Release" ]:
        for file in glob.glob(os.path.join(protobuf_install_dir(), "lib", platform_name(), config, "libprotobuf.*")):
            os.makedirs(os.path.join(lib_path, config), exist_ok=True)
            shutil.copy(file, os.path.join(lib_path, config, os.path.basename(file)))


def pb_h_content_prefix():
    return """
#pragma once

#if defined(_MSC_VER)
    __pragma(warning(push))
	__pragma(warning(disable: 4946))  // reinterpret_cast used between related classes: '<class1>' and '<class1>'
#endif

"""


def pb_cc_content_prefix():
    return """
#if defined(_MSC_VER)
    __pragma(warning(push))
	__pragma(warning(disable: 4125))  // decimal digit terminates octal escape sequence
	__pragma(warning(disable: 4541))  // 'dynamic_cast' used on polymorphic type '<type>' with /GR-; unpredictable behaviour may result
	__pragma(warning(disable: 4668))  // '<preprocessor_macro>' is not defined as a preprocessor macro, replacing with '0' for '#if/#elif'
	__pragma(warning(disable: 4800))  // Implicit conversion from '<type>' to bool. Possible information loss.
	__pragma(warning(disable: 4946))  // reinterpret_cast used between related classes: '<class1>' and '<class1>'
#endif

"""


def pb_content_postfix():
    return """

#if defined(_MSC_VER)
    __pragma(warning(pop))
#endif

"""


def build_pb_files():
    print("\nBuilding .pb. files from .proto files...\n")

    # Cleanup old build
    shutil.rmtree(yarnspinner_proto_build_dir(), ignore_errors=True)
    os.makedirs(yarnspinner_proto_build_dir(), exist_ok=True)
    shutil.rmtree(yarnspinner_proto_install_dir(), ignore_errors=True)
    os.makedirs(yarnspinner_proto_install_dir(), exist_ok=True)

    # Copy .proto files to build dir
    yarn_spinner_proto = os.path.join("YarnSpinner", "YarnSpinner", "yarn_spinner.proto")
    compiler_output_proto = os.path.join("YarnSpinner-Console", "src", "YarnSpinner.Console", "compiler_output.proto")
    for file in [ yarn_spinner_proto, compiler_output_proto ]:
        if os.path.exists(file) is False:
            print("Proto file not found: " + file)
            exit(1)
        shutil.copy(file, yarnspinner_proto_build_dir())

    match platform.system():
        case "Windows":
            protoc = os.path.join(protobuf_install_dir(), "bin", "protoc.exe")
        case "Mac":
            protoc = os.path.join(protobuf_install_dir(), "bin", "protoc")
        case _:
            print("Unsupported platform: " + platform.system())
            exit(1)

    if os.path.exists(protoc) is False:
        print("Protoc not found: " + protoc)
        exit(1)

    # Run the command
    subprocess.run([protoc, "--proto_path=" + yarnspinner_proto_build_dir(), "--cpp_out=dllexport_decl=YARNSPINNER_API:" + yarnspinner_proto_install_dir(), "yarn_spinner.proto", "compiler_output.proto"])


def _fix_pb_file(file, prefix_func):
    old_yarn_include = '#include "yarn_spinner.pb.h"'
    new_yarn_include = '#include "YarnSpinnerCore/yarn_spinner.pb.h"'
    old_compiler_include = '#include "compiler_output.pb.h"'
    new_compiler_include = '#include "YarnSpinnerCore/compiler_output.pb.h"'

    source_file = os.path.join(yarnspinner_proto_install_dir(), file)

    if os.path.exists(source_file) is False:
        print("Compiled proto files not found: " + source_file)
        exit(1)

    with open(source_file, "r") as f:
        file_contents = f.read()
        f.close()

    file_contents = file_contents.replace(old_yarn_include, new_yarn_include)
    file_contents = file_contents.replace(old_compiler_include, new_compiler_include)
    file_contents = prefix_func() + file_contents + pb_content_postfix()

    with open(source_file, "w") as f:
        file_contents = f.write(file_contents)
        f.close()


# Fix the generated .pb.cc & .pb.h files -- update include paths and add pragmas to disable warnings
def fix_pb_files():
    print("\nFixing generated .pb.cc & .pb.h files...\n")

    for source_file in pb_h_files():
        _fix_pb_file(source_file, pb_h_content_prefix)

    for source_file in pb_cc_files():
        _fix_pb_file(source_file, pb_cc_content_prefix)


def copy_pb_files(plugin_path):
    print("\nCopying proto files to Unreal plugin...\n")

    for source_file in pb_h_files():
        shutil.copy(os.path.join(yarnspinner_proto_install_dir(), source_file), pb_h_file_dest(plugin_path))

    for source_file in pb_cc_files():
        shutil.copy(os.path.join(yarnspinner_proto_install_dir(), source_file), pb_cc_file_dest(plugin_path))


if __name__ == "__main__":
    arg_parser = ArgumentParser(description="Builds protobuf and .proto files for YarnSpinner's Unreal plugin")
    arg_parser.add_argument("--plugin_path", help="Path to YarnSpinner's Unreal plugin", required=True)

    args = arg_parser.parse_args()

    if os.path.exists(args.plugin_path) is False:
        print("Plugin path does not exist: " + args.plugin_path)
        exit(1)

    plugin_path = os.path.realpath(args.plugin_path)

    prepare_subrepos()

    # Build and install the protobuf library
    build_libprotobuf()
    copy_libprotobuf_files(plugin_path)

    # Build and install the .proto files
    build_pb_files()
    fix_pb_files()
    copy_pb_files(plugin_path)

    # TODO: build and deliver ysc


