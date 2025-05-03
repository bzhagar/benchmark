#!/usr/bin/env python3

import argparse
import subprocess
import os
import sys
import shutil

# --- Configuration ---
LLVM_TEST_SUITE_SRC_DIR = "/home/ubuntu/llvm-test-suite"
TOOLCHAIN_FILE = "/home/ubuntu/arm32_toolchain.cmake"
# QEMU path might need adjustment depending on installation
QEMU_RUN_UNDER = "qemu-arm -L /usr/arm-linux-gnueabihf"
# --- End Configuration ---

def run_command(cmd, cwd, env=None):
    """Runs a command in a subprocess and prints output/errors."""
    print(f"\n[RUNNING] CWD: {cwd}\n{' '.join(cmd)}", flush=True)
    process = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env)
    
    stdout_lines = []
    while True:
        line = process.stdout.readline()
        if not line:
            break
        print(line.strip(), flush=True)
        stdout_lines.append(line)

    process.wait()
    print(f"[FINISHED] {' '.join(cmd)} with exit code {process.returncode}", flush=True)
    return process.returncode, "".join(stdout_lines)

def main():
    parser = argparse.ArgumentParser(description="Run LLVM test-suite benchmark with specific flags.")
    parser.add_argument("--label", required=True, help="A unique label for this benchmark run (used for build/output dirs).")
    parser.add_argument("--cflags", default="", help="CFLAGS for the C compiler.")
    parser.add_argument("--cxxflags", default="", help="CXXFLAGS for the C++ compiler.")
    parser.add_argument("--ldflags", default="", help="Linker flags.")
    parser.add_argument("--output-dir", default="/home/ubuntu/benchmark_results", help="Directory to store results.")
    parser.add_argument("--target", default="arm32", choices=["native", "arm32"], help="Target architecture (native or arm32 cross-compile).")
    parser.add_argument("--test-path", default=".", help="Specific test path or directory to run (relative to build dir). Defaults to all tests '.')")

    args = parser.parse_args()

    build_dir = os.path.join("/home/ubuntu", f"build_{args.label}")
    results_file = os.path.join(args.output_dir, f"results_{args.label}.json")

    # Create output and build directories
    os.makedirs(args.output_dir, exist_ok=True)
    if os.path.exists(build_dir):
        print(f"Build directory {build_dir} already exists. Removing.", flush=True)
        shutil.rmtree(build_dir)
    os.makedirs(build_dir)

    # Construct CMake command
    cmake_cmd = [
        "cmake",
        "-G", "Ninja",
        f"-DCMAKE_C_FLAGS={args.cflags}",
        f"-DCMAKE_CXX_FLAGS={args.cxxflags}",
        f"-DCMAKE_EXE_LINKER_FLAGS={args.ldflags}",
        "-DTEST_SUITE_BENCHMARKING_ONLY=ON",
        "-DTEST_SUITE_COLLECT_STATS=ON",
        "-DTEST_SUITE_COLLECT_CODE_SIZE=OFF",
    ]

    if args.target == "arm32":
        cmake_cmd.extend([
            f"-DCMAKE_TOOLCHAIN_FILE={TOOLCHAIN_FILE}",
            f"-DTEST_SUITE_RUN_UNDER={QEMU_RUN_UNDER}" # Use QEMU to run arm32 binaries
        ])
    elif args.target == "native":
        # Assuming native compiler is clang/clang++
        cmake_cmd.extend([
            "-DCMAKE_C_COMPILER=clang",
            "-DCMAKE_CXX_COMPILER=clang++",
        ])
    else:
        print(f"Error: Unknown target '{args.target}'", file=sys.stderr)
        sys.exit(1)

    cmake_cmd.append(LLVM_TEST_SUITE_SRC_DIR)

    # Run CMake
    cmake_ret, _ = run_command(cmake_cmd, cwd=build_dir)
    if cmake_ret != 0:
        print("CMake configuration failed!", file=sys.stderr)
        sys.exit(1)

    # Run Build (Ninja)
    build_cmd = ["ninja"]
    build_ret, _ = run_command(build_cmd, cwd=build_dir)
    if build_ret != 0:
        print("Build failed!", file=sys.stderr)
        sys.exit(1)

    # Run Benchmarks (llvm-lit)
    # Use -j 1 for potentially lower variance, though slower.
    lit_cmd = ["lit", "-v", "-j", "1", "-o", results_file, args.test_path]
    lit_ret, _ = run_command(lit_cmd, cwd=build_dir)
    if lit_ret != 0:
        print("llvm-lit run failed!", file=sys.stderr)
        # Don't exit immediately, results.json might still contain partial data
        # sys.exit(1)

    print(f"\nBenchmark run '{args.label}' complete.")
    print(f"Build directory: {build_dir}")
    print(f"Results file: {results_file}")

if __name__ == "__main__":
    main()

