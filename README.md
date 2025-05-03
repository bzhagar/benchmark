# Benchmarking Suite for Compiler Flags

This suite is designed to benchmark the compilation time and runtime performance of the LLVM test-suite under different compiler flags, C++ standards, and target architectures. It focuses on providing a repeatable process with low variance for analyzing performance changes, particularly targeting overheads below 10%.

## Components

1.  **`run_benchmark.py`**: A Python script to configure, build, and run the LLVM test-suite with specified flags and target.
2.  **`validate_variance.py`**: A Python script to run a specific benchmark multiple times using `run_benchmark.py` and analyze the execution time variance.
3.  **`arm32_toolchain.cmake`**: A template CMake toolchain file for cross-compiling to ARM32 (arm-linux-gnueabihf) using Clang.
4.  **LLVM Test Suite**: The underlying benchmark suite used for testing (cloned from `https://github.com/llvm/llvm-test-suite.git`).

## Prerequisites

*   Linux Ubuntu environment (tested on 22.04)
*   Python 3 (tested with 3.10+)
*   `pip3` (Python package installer)
*   `git`
*   `cmake`
*   `ninja-build`
*   `clang` and `clang++` (tested with clang-14)
*   Python `lit` package (`pip3 install lit`)
*   (Optional, for ARM32 cross-compilation) `qemu-user` and `crossbuild-essential-armhf` (`sudo apt-get install qemu-user crossbuild-essential-armhf`)
*   LLVM test-suite source code (e.g., cloned into `/home/ubuntu/llvm-test-suite`)

## Configuration

Before running the scripts, you might need to adjust some paths defined as constants within them:

**`run_benchmark.py`**:

*   `LLVM_TEST_SUITE_SRC_DIR`: Absolute path to the cloned LLVM test-suite source directory.
*   `TOOLCHAIN_FILE`: Absolute path to the CMake toolchain file (used for `arm32` target).
*   `QEMU_RUN_UNDER`: Command prefix to run ARM32 binaries using QEMU (used for `arm32` target). Ensure the path to the QEMU sysroot (`-L` option) matches your `crossbuild-essential-armhf` installation.

**`validate_variance.py`**:

*   `RUN_BENCHMARK_SCRIPT`: Absolute path to the `run_benchmark.py` script.
*   `DEFAULT_NUM_RUNS`: Default number of times to run a benchmark for variance analysis.

**`arm32_toolchain.cmake`**:

*   `CMAKE_SYSROOT`: Absolute path to the ARM32 sysroot (usually `/usr/arm-linux-gnueabihf` on Ubuntu/Debian if `crossbuild-essential-armhf` is installed).
*   Compiler paths (`CMAKE_C_COMPILER`, `CMAKE_CXX_COMPILER`) might need adjustment if `clang`/`clang++` are not in the default system PATH or if you need specific versions.

## Usage

### `run_benchmark.py`

This script handles the configuration (CMake), build (Ninja), and execution (lit) of the LLVM test-suite for a given set of flags.

```bash
./run_benchmark.py --label <run_label> [options]
```

**Arguments:**

*   `--label LABEL`: (Required) A unique name for this benchmark run. Used to create the build directory (`build_LABEL`) and results file (`results_LABEL.json`).
*   `--cflags CFLAGS`: C compiler flags (e.g., `"-O2 -march=native"`). Default: `""`.
*   `--cxxflags CXXFLAGS`: C++ compiler flags (e.g., `"-O3 -std=c++17"`). Default: `""`.
*   `--ldflags LDFLAGS`: Linker flags. Default: `""`.
*   `--output-dir OUTPUT_DIR`: Directory to store the final `lit` results JSON file. Default: `/home/ubuntu/benchmark_results`.
*   `--target {native,arm32}`: Target architecture. `native` uses the host system's clang; `arm32` uses the cross-compilation toolchain file. Default: `arm32`.
*   `--test-path TEST_PATH`: Specific test path or directory within the test suite to run (relative to the build directory). Useful for running a subset of tests. Default: `.` (runs all tests).

**Example (Native O3):**

```bash
./run_benchmark.py --label native_O3 --cflags="-O3" --cxxflags="-O3" --target native
```

**Example (ARM32 O2, specific test):**

```bash
./run_benchmark.py --label arm32_O2_memcpy --cflags="-O2" --cxxflags="-O2" --target arm32 --test-path MicroBenchmarks/MemFunctions/MemFunctions.test
```

**Output:**

*   A build directory named `build_<label>` will be created in `/home/ubuntu`.
*   A results file named `results_<label>.json` will be created in the specified `--output-dir`.

### `validate_variance.py`

This script runs a *specific* benchmark test multiple times using `run_benchmark.py` and analyzes the variance of the execution times reported by `lit`.

```bash
./validate_variance.py --label-prefix <prefix> --test-path <test_path> [options]
```

**Arguments:**

*   `--label-prefix PREFIX`: (Required) A prefix used for the labels of the individual benchmark runs (e.g., `mytest_O2`). Runs will be labeled `PREFIX_run_1`, `PREFIX_run_2`, etc.
*   `--test-path TEST_PATH`: (Required) The *specific* test path (relative to the build directory) to execute repeatedly. This should point to a single test file (e.g., `MicroBenchmarks/MemFunctions/MemFunctions.test`), not the whole suite (`.`).
*   `--cflags CFLAGS`: C compiler flags passed to `run_benchmark.py`. Default: `"-O2"`.
*   `--cxxflags CXXFLAGS`: C++ compiler flags passed to `run_benchmark.py`. Default: `"-O2"`.
*   `--ldflags LDFLAGS`: Linker flags passed to `run_benchmark.py`. Default: `""`.
*   `--target {native,arm32}`: Target architecture passed to `run_benchmark.py`. Default: `native`.
*   `--num-runs NUM_RUNS`: Number of times to execute the benchmark. Default: `5`.
*   `--output-dir OUTPUT_DIR`: Directory to store the results JSON files for each run. Default: `/home/ubuntu/variance_results`.

**Example (Run MemFunctions 10 times with O2):**

```bash
./validate_variance.py --label-prefix memfunc_O2_variance --test-path MicroBenchmarks/MemFunctions/MemFunctions.test --num-runs 10 --cflags="-O2" --cxxflags="-O2" --target native
```

**Output:**

*   The script will execute `run_benchmark.py` multiple times, creating build directories (`build_<prefix>_run_N`) and result files (`results_<prefix>_run_N.json`).
*   After all runs complete, it parses the results and prints a statistical summary for each micro-benchmark found within the test, including:
    *   Number of runs
    *   Individual execution times (in milliseconds)
    *   Mean execution time
    *   Standard Deviation (StdDev)
    *   Coefficient of Variation (CV % = StdDev / Mean * 100)
*   A warning is printed if the CV exceeds 2%, suggesting potentially high variance.

## Low Variance Considerations

Achieving low variance is crucial for meaningful benchmark comparisons.

*   **Stable Environment**: Run benchmarks on a quiescent system with minimal background activity.
*   **Disable Frequency Scaling**: Ensure the CPU is running at a fixed frequency (e.g., using `cpupower frequency-set -g performance`).
*   **Disable Address Space Layout Randomization (ASLR)**: `sudo sysctl -w kernel.randomize_va_space=0` (temporary).
*   **Sufficient Runs**: Use `validate_variance.py` with an adequate number of runs (e.g., 5-10) to assess stability.
*   **Single-Threaded Execution**: The scripts configure `lit` to run tests sequentially (`-j 1`), which generally reduces variance compared to parallel execution.
*   **Target Specific Benchmarks**: Focus variance analysis and comparisons on specific, relevant benchmarks rather than the entire suite average.

## Cross-Compilation (ARM32)

The provided `arm32_toolchain.cmake` file facilitates cross-compilation.

*   It sets the system name, processor, and target triple.
*   It configures CMake to use `clang`/`clang++` with the specified target triple.
*   It points CMake to the appropriate sysroot (`/usr/arm-linux-gnueabihf`) for headers and libraries.
*   It configures CMake's find behavior to correctly locate tools on the host and libraries/headers in the sysroot.
*   `run_benchmark.py` uses `QEMU_RUN_UNDER` to execute the compiled ARM32 benchmarks on the x86 host.

Ensure the `crossbuild-essential-armhf` and `qemu-user` packages are installed and the paths in the toolchain file and `run_benchmark.py` are correct for your system.

