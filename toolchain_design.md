## CMake Toolchain Integration Design (Step 003)

**Objective:** Design the integration of a CMake toolchain file with the LLVM test-suite to enable benchmarking with specific compilers (clang), target architectures (arm32 cross-compilation), and arbitrary user-provided flags (CFLAGS, CXXFLAGS, LDFLAGS).

**Framework:** LLVM test-suite (chosen in Step 002).

**Components:**

1.  **CMake Toolchain File (`arm32_toolchain.cmake`):**
    *   This file defines the cross-compilation environment.
    *   `CMAKE_SYSTEM_NAME`: Set to `Linux`.
    *   `CMAKE_SYSTEM_PROCESSOR`: Set to `arm` (or a more specific variant like `armv7-a` if required by the toolchain/target).
    *   `CMAKE_C_COMPILER`: Path to the clang C cross-compiler (e.g., `/usr/bin/clang`).
    *   `CMAKE_CXX_COMPILER`: Path to the clang++ C++ cross-compiler (e.g., `/usr/bin/clang++`).
    *   `CMAKE_C_COMPILER_TARGET`: Specify the target triple (e.g., `arm-linux-gnueabihf`).
    *   `CMAKE_CXX_COMPILER_TARGET`: Specify the target triple (e.g., `arm-linux-gnueabihf`).
    *   `CMAKE_FIND_ROOT_PATH`: Path to the arm32 sysroot containing headers and libraries for the target.
    *   `CMAKE_FIND_ROOT_PATH_MODE_*`: Set `PROGRAM` to `NEVER`, and `LIBRARY`, `INCLUDE`, `PACKAGE` to `ONLY` to ensure CMake searches only within the sysroot for target dependencies.
    *   **Note:** This file sets up the *environment*. It should *not* contain the arbitrary C/CXX/Linker flags intended for benchmarking variations. Those will be passed during configuration.

2.  **LLVM Test-Suite CMake Configuration:**
    *   The user will invoke CMake to configure the LLVM test-suite build directory.
    *   **Toolchain Specification:** Pass `-DCMAKE_TOOLCHAIN_FILE=/path/to/arm32_toolchain.cmake` to the CMake command.
    *   **Compiler Specification:** The toolchain file handles setting `CMAKE_C(XX)_COMPILER`. The LLVM test-suite build should pick these up automatically.
    *   **Arbitrary Flag Injection:** Pass the desired flags for the specific benchmark run using standard CMake variables:
        *   `-DCMAKE_C_FLAGS="<user_cflags>"`
        *   `-DCMAKE_CXX_FLAGS="<user_cxxflags>"`
        *   `-DCMAKE_EXE_LINKER_FLAGS="<user_ldflags>"` (or `SHARED`/`MODULE` as appropriate)
    *   **LLVM Test-Suite Options:** Include necessary options for benchmarking:
        *   `-DTEST_SUITE_BENCHMARKING_ONLY=ON`
        *   `-DTEST_SUITE_COLLECT_STATS=ON`
        *   Consider `-DTEST_SUITE_RUN_UNDER=<qemu-arm ...>` if execution requires an emulator.
        *   Consider `-DTEST_SUITE_REMOTE_HOST=<arm-device-ip>` if running on actual hardware via SSH.

**Workflow:**

1.  Prepare the arm32 cross-compilation toolchain (clang, sysroot).
2.  Create the `arm32_toolchain.cmake` file pointing to the correct paths and target.
3.  Clone the LLVM test-suite repository.
4.  For each set of compiler flags to test:
    a.  Create a separate build directory.
    b.  Run CMake, providing the `CMAKE_TOOLCHAIN_FILE`, the desired `CMAKE_C_FLAGS`, `CMAKE_CXX_FLAGS`, `CMAKE_EXE_LINKER_FLAGS`, and other LLVM test-suite options.
    c.  Build the benchmarks (`ninja` or `make`).
    d.  Run the benchmarks using `llvm-lit` (e.g., `llvm-lit -v -j 1 -o results.json .`).
5.  Compare the `results.json` files from different flag sets using `test-suite/utils/compare.py`.

**Rationale:**
*   This design leverages standard CMake toolchain functionality, ensuring maximum compatibility (Priority 1).
*   It uses the LLVM test-suite's built-in mechanisms for flag injection and benchmarking, including Google Benchmark integration for runtime (Priority 2 & 3).
*   The separation of toolchain definition and flag injection makes the process repeatable and easy to script for different flag combinations (Priority 4).

**Next Step:** Implement the benchmark suite structure based on this design (Step 004), starting with setting up the necessary directories and potentially creating a template `arm32_toolchain.cmake` file.
