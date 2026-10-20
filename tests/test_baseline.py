import json
import os
from pathlib import Path

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, ReadOnly
from matmul_reference import matmul_reference


@cocotb.test()
async def measure_baseline(dut):
    rows = int(os.environ["TEST_ROWS"])
    cols = int(os.environ["TEST_COLS"])
    depth = int(os.environ["TEST_DEPTH"])
    double_buffer = int(os.environ.get("TEST_DOUBLE_BUFFER", "0"))
    if double_buffer:
        engine = dut.tiled_matmul_inst.double_buffered.engine_inst
    dut.clk.value = 0
    dut.rst.value = 1
    dut.step.value = 1
    dut.cmd_valid.value = 0
    dut.cmd_m.value = 1
    dut.cmd_n.value = 1
    dut.cmd_k.value = 1
    dut.wr_valid.value = 0
    dut.wr_is_b.value = 0
    dut.wr_bank.value = 0
    dut.wr_addr.value = 0
    dut.wr_data.value = 0
    dut.load_complete_valid.value = 0
    dut.result_ready.value = 1
    clock = Clock(dut.clk, 10, unit="ns")
    clock.start(start_high=False)
    await RisingEdge(dut.clk)
    await ReadOnly()

    reports = []
    for m, n, k in ((4, 4, 16), (6, 5, 35), (8, 8, 32)):
        a = [[(r + q) % 13 - 6 for q in range(k)] for r in range(m)]
        b = [[(q - c) % 11 - 5 for c in range(n)] for q in range(k)]
        expected = matmul_reference(a, b)
        received = {}
        cycles = {"load": 0, "result": 0, "compute_control": 0}
        overlap = 0
        active_compute = 0
        writes = 0
        completions = 0
        last_request = None
        pending = []
        position = 0
        await FallingEdge(dut.clk)
        dut.rst.value = 0
        dut.cmd_valid.value = 1
        dut.cmd_m.value = m
        dut.cmd_n.value = n
        dut.cmd_k.value = k
        await ReadOnly()
        assert dut.cmd_ready.value == 1
        await RisingEdge(dut.clk)
        await ReadOnly()
        assert dut.busy.value == 1

        # Exclude command acceptance; include the final accepted result edge.
        for cycle in range(100000):
            await FallingEdge(dut.clk)
            dut.cmd_valid.value = 0
            dut.wr_valid.value = 0
            dut.load_complete_valid.value = 0
            if int(dut.load_req.value):
                tr = int(dut.tile_row.value)
                tc = int(dut.tile_col.value)
                offset = int(dut.k_offset.value)
                count = int(dut.chunk_len.value)
                request = (tr, tc, offset)
                if request != last_request:
                    last_request = request
                    pending = []
                    position = 0
                    for q in range(count):
                        for r in range(rows):
                            value = a[tr + r][offset + q] if tr + r < m else 0
                            pending.append((0, r, q, value))
                        for c in range(cols):
                            value = b[offset + q][tc + c] if tc + c < n else 0
                            pending.append((1, c, q, value))
                if position < len(pending):
                    is_b, bank, address, value = pending[position]
                    dut.wr_valid.value = 1
                    dut.wr_is_b.value = is_b
                    dut.wr_bank.value = bank
                    dut.wr_addr.value = address
                    dut.wr_data.value = value
                else:
                    dut.load_complete_valid.value = 1

            await ReadOnly()
            assert not (int(dut.load_req.value) and int(dut.result_valid.value))
            if double_buffer and int(engine.scheduler_step.value):
                active_compute += 1
                overlap += int(dut.load_req.value)
            if int(dut.load_req.value):
                cycles["load"] += 1
            elif int(dut.result_valid.value):
                cycles["result"] += 1
            else:
                cycles["compute_control"] += 1

            if int(dut.wr_valid.value) and int(dut.wr_ready.value):
                writes += 1
                position += 1
            if int(dut.load_complete_valid.value) and int(dut.load_complete_ready.value):
                completions += 1
            if int(dut.result_valid.value):
                r = int(dut.result_row.value)
                c = int(dut.result_col.value)
                assert (r, c) not in received
                assert 0 <= r < m and 0 <= c < n
                value = dut.result_data.value.to_signed()
                assert value == expected[r][c]
                received[r, c] = value

            await RisingEdge(dut.clk)
            await ReadOnly()
            if int(dut.done.value):
                break
        else:
            raise AssertionError("Baseline measurement timed out")

        tiles = ((m + rows - 1) // rows) * ((n + cols - 1) // cols)
        assert len(received) == m * n
        assert writes == tiles * (rows + cols) * k
        assert completions == tiles * ((k + depth - 1) // depth)
        assert cycles["load"] == writes + completions
        assert cycles["result"] == m * n
        total = sum(cycles.values())
        useful_macs = m * n * k
        report = {
            "m": m, "n": n, "k": k, "rows": rows, "cols": cols, "depth": depth,
            "total_cycles": total, **cycles, "operand_writes": writes,
            "load_completions": completions, "useful_macs": useful_macs,
            "useful_macs_per_cycle": useful_macs / total,
            "end_to_end_utilization": useful_macs / (rows * cols * total),
        }
        if double_buffer:
            # Primary categories remain exclusive with loading taking priority.
            # These extra counters expose useful overlap instead of hiding it.
            report["load_compute_overlap"] = overlap
            report["scheduler_enabled_cycles"] = active_compute
            assert active_compute == tiles * (k + ((k + depth - 1) // depth) * (rows + cols - 1))
            assert overlap > 0 if k > depth else overlap == 0
        reports.append(report)
        dut._log.info("BASELINE " + json.dumps(report, sort_keys=True))
        await FallingEdge(dut.clk)
        dut.load_complete_valid.value = 0
        await RisingEdge(dut.clk)
        await ReadOnly()
        assert dut.busy.value == 0 and dut.done.value == 0

    Path(os.environ["PERF_OUTPUT"]).write_text(json.dumps(reports, indent=2) + "\n")
