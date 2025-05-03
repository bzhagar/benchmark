## Analysis for Low Variance Benchmarking (Step 002)

**Goal:** Achieve low variance to reliably detect < 10% overhead in compilation time and runtime due to compiler/flag changes.

**Sources of Variance:**
1.  **System Noise:** Background processes, CPU frequency scaling (governors), interrupts, cache contention, memory allocation variability.
2.  **Measurement Method:** Timer precision, benchmarking framework overhead.
3.  **Benchmark Design:** Short execution times, non-deterministic code (e.g., I/O, complex branching based on external factors).
4.  **Build Process:** Potential non-determinism in build tools, impact of optimizations like LTO.

**Strategies for Low Variance:**
1.  **Environment Control:**
    *   Minimize background processes.
    *   Set CPU governor to 'performance' to disable frequency scaling.
    *   Consider pinning processes to specific CPU cores (`taskset` or `numactl`).
    *   Run multiple repetitions and use statistical analysis (mean, median, standard deviation, coefficient of variation).
    *   Include warm-up runs to stabilize caches and branch predictors.
2.  **Tool Selection:**
    *   **Runtime:** Google Benchmark is specifically designed for low-variance C++ runtime microbenchmarking. It handles repetitions, warm-up, and provides detailed statistics.
    *   **Compile Time:** LLVM test-suite (`lit` runner with `TEST_SUITE_COLLECT_STATS`) provides mechanisms to measure compilation time. `metabench` is specialized but adds dependencies (Ruby) and uses a subtraction method that might need careful validation.
    *   **Integration:** The LLVM test-suite integrates both compile-time measurement and runtime benchmarking (using Google Benchmark for its MicroBenchmarks). It uses CMake, supports clang, toolchain files, and custom flags (`CMAKE_C_FLAGS`, etc.).
3.  **Benchmark Design:**
    *   Ensure runtime benchmarks execute long enough for stable measurements (Google Benchmark helps automate this).
    *   Isolate the code under test, avoiding external dependencies or I/O within timed sections.

**Chosen Framework:**
*   The **LLVM test-suite** appears most suitable. It offers a unified framework for both compilation and runtime benchmarking, aligning well with the user's requirements:
    *   **Comprehensive:** Measures compile time and runtime.
    *   **Low Variance Runtime:** Integrates Google Benchmark for microbenchmarks.
    *   **CMake/Clang/Toolchain:** Natively supports CMake, specifying compilers (clang), and using toolchain files for configuration and cross-compilation (arm32).
    *   **Flag Customization:** Allows passing arbitrary C/CXX/Linker flags via standard CMake variables.
    *   **Benchmarking Targets:** Includes its own benchmarks and supports integrating external projects (like SPEC or potentially the user's target software if it uses CMake).
    *   **Analysis:** Provides `compare.py` for statistical comparison of results (JSON format).
    *   **Repeatability:** Structure and tooling support repeatable execution.

**Next Steps:** Proceed to design the CMake toolchain integration (Step 003), focusing on how to specify clang, target architecture (arm32), and custom flags within the LLVM test-suite's CMake structure.
