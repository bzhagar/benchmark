#!/usr/bin/env python3

import argparse
import subprocess
import os
import sys
import json
import statistics

# --- Configuration ---
RUN_BENCHMARK_SCRIPT = "/home/ubuntu/run_benchmark.py"
DEFAULT_NUM_RUNS = 5
# --- End Configuration ---

def run_command(cmd, cwd):
    """Runs a command in a subprocess and returns its exit code and stdout/stderr."""
    print(f"\n[RUNNING] CWD: {cwd}\n{' '.join(cmd)}", flush=True)
    process = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    
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

def parse_results(json_file):
    """Parses the lit JSON output to extract execution times for micro-benchmarks."""
    times = {}
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
            # Find the main test entry (assuming only one test was run)
            if data['tests']:
                test_entry = data['tests'][0]
                # Check if micro-benchmark metrics exist
                if 'metrics' in test_entry and 'MicroBenchmarks' in test_entry['metrics']:
                    num_micro_benchmarks = int(test_entry['metrics']['MicroBenchmarks'])
                    # Look for metrics starting with 'exec_time.' which indicate micro-benchmark times
                    for key, value in test_entry['metrics'].items():
                        if key.startswith('exec_time.'):
                            # Extract micro-benchmark name
                            micro_name = key.split('.', 1)[1]
                            times[micro_name] = float(value)
                elif 'metrics' in test_entry and 'exec_time' in test_entry['metrics']:
                    # Fallback for tests without explicit micro-benchmarks
                    times[test_entry['name']] = float(test_entry['metrics']['exec_time'])
    except FileNotFoundError:
        print(f"Error: Results file not found: {json_file}", file=sys.stderr)
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {json_file}", file=sys.stderr)
    except Exception as e:
        print(f"Error parsing {json_file}: {e}", file=sys.stderr)
    return times

def main():
    parser = argparse.ArgumentParser(description="Run a specific benchmark multiple times to analyze variance.")
    parser.add_argument("--label-prefix", required=True, help="Prefix for benchmark run labels.")
    parser.add_argument("--test-path", required=True, help="Specific test path (relative to build dir) to run.")
    parser.add_argument("--cflags", default="-O2", help="CFLAGS for the C compiler.")
    parser.add_argument("--cxxflags", default="-O2", help="CXXFLAGS for the C++ compiler.")
    parser.add_argument("--ldflags", default="", help="Linker flags.")
    parser.add_argument("--target", default="native", choices=["native", "arm32"], help="Target architecture.")
    parser.add_argument("--num-runs", type=int, default=DEFAULT_NUM_RUNS, help="Number of times to run the benchmark.")
    parser.add_argument("--output-dir", default="/home/ubuntu/variance_results", help="Directory to store results.")

    args = parser.parse_args()

    all_results = {}
    result_files = []

    print(f"--- Running Variance Test --- ")
    print(f"Benchmark: {args.test_path}")
    print(f"Config: target={args.target}, cflags='{args.cflags}', cxxflags='{args.cxxflags}', ldflags='{args.ldflags}'")
    print(f"Runs: {args.num_runs}")
    print(f"---------------------------")

    for i in range(args.num_runs):
        run_label = f"{args.label_prefix}_run_{i+1}"
        results_file = os.path.join(args.output_dir, f"results_{run_label}.json")
        result_files.append(results_file)
        
        cmd = [
            RUN_BENCHMARK_SCRIPT,
            f"--label={run_label}",
            f"--cflags={args.cflags}",
            f"--cxxflags={args.cxxflags}",
            f"--ldflags={args.ldflags}",
            f"--target={args.target}",
            f"--test-path={args.test_path}",
            f"--output-dir={args.output_dir}"
        ]
        
        ret_code, _ = run_command(cmd, cwd="/home/ubuntu")
        if ret_code != 0:
            print(f"Error: Benchmark run {i+1} failed!", file=sys.stderr)
            # Decide whether to continue or stop
            # For variance analysis, stopping might be better if a run fails
            sys.exit(1)

    print("\n--- Parsing Results ---")
    for i, res_file in enumerate(result_files):
        print(f"Parsing run {i+1}: {res_file}")
        run_times = parse_results(res_file)
        for micro_name, time_val in run_times.items():
            if micro_name not in all_results:
                all_results[micro_name] = []
            all_results[micro_name].append(time_val)

    print("\n--- Variance Analysis --- ")
    if not all_results:
        print("No results found to analyze.")
        sys.exit(1)

    for micro_name, times in all_results.items():
        if len(times) < 2:
            print(f"\nMicro-Benchmark: {micro_name}")
            print(f"  Only {len(times)} result(s), cannot calculate variance.")
            continue

        mean_time = statistics.mean(times)
        stdev_time = statistics.stdev(times)
        cv = (stdev_time / mean_time) * 100 if mean_time != 0 else 0

        print(f"\nMicro-Benchmark: {micro_name}")
        print(f"  Runs: {len(times)}")
        print(f"  Times (ms): {times}")
        print(f"  Mean: {mean_time:.4f} ms")
        print(f"  StdDev: {stdev_time:.4f} ms")
        print(f"  CV (%): {cv:.2f}%")
        if cv > 2.0: # Threshold for high variance warning
             print(f"  WARNING: High variance detected (CV > 2%)!")

    print("\nVariance analysis complete.")

if __name__ == "__main__":
    main()

