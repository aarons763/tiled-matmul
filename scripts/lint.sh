#!/usr/bin/env bash
set -eu
cd "$(dirname "$0")/.."
verilator --lint-only --Wall --top-module matmul_host rtl/*.sv "$@"
