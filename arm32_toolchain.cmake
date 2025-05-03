# CMake Toolchain File for ARM32 Cross-Compilation (arm-linux-gnueabihf)
# Template - Adjust paths as necessary

# Set the target system name
set(CMAKE_SYSTEM_NAME Linux)

# Set the target system processor
set(CMAKE_SYSTEM_PROCESSOR arm)

# Specify the cross-compiler target triple
set(TARGET_TRIPLE "arm-linux-gnueabihf")

# Specify the cross compilers (using clang)
# Ensure clang is installed and configured for cross-compilation, or adjust path
set(CMAKE_C_COMPILER clang)
set(CMAKE_CXX_COMPILER clang++)

# Set the target triple for the compilers
set(CMAKE_C_COMPILER_TARGET ${TARGET_TRIPLE})
set(CMAKE_CXX_COMPILER_TARGET ${TARGET_TRIPLE})

# Specify the path to the sysroot for the target architecture
# This path contains the headers and libraries for arm-linux-gnueabihf
# Typically found in /usr/arm-linux-gnueabihf on Debian/Ubuntu systems
# Adjust this path based on your cross-compilation setup
set(CMAKE_SYSROOT /usr/arm-linux-gnueabihf)

# Set the find root path to the sysroot
set(CMAKE_FIND_ROOT_PATH ${CMAKE_SYSROOT})

# Modify CMake search behavior:
# Search for programs only in the host system paths (NEVER in sysroot)
set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
# Search for libraries and headers only in the target system paths (ONLY in sysroot)
set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_PACKAGE ONLY)

# Optional: Set default compilation flags for the target, if needed
# These are *defaults* for the toolchain, not the benchmark-specific flags
# set(CMAKE_C_FLAGS_INIT "-march=armv7-a -mfpu=neon" CACHE STRING "")
# set(CMAKE_CXX_FLAGS_INIT "-march=armv7-a -mfpu=neon" CACHE STRING "")

# Note: Benchmark-specific CFLAGS, CXXFLAGS, LDFLAGS should be passed
# during the CMake configuration step, e.g.:
# cmake -DCMAKE_TOOLCHAIN_FILE=... -DCMAKE_C_FLAGS="-O2" ... /path/to/llvm-test-suite

