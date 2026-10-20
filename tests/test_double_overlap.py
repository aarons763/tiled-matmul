import os
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, ReadOnly
from matmul_reference import matmul_reference


@cocotb.test()
async def test_reset_with_prefetch(dut):
    rows = int(os.environ["TEST_ROWS"])
    cols = int(os.environ["TEST_COLS"])
    depth = int(os.environ["TEST_DEPTH"])
    engine = dut.tiled_matmul_inst.double_buffered.engine_inst
    dut.clk.value = 0
    dut.rst.value = 1
    dut.step.value = 0
    dut.cmd_valid.value = 0
    dut.cmd_m.value = rows
    dut.cmd_n.value = cols
    dut.cmd_k.value = depth + 1
    dut.wr_valid.value = 0
    dut.wr_is_b.value = 0
    dut.wr_bank.value = 0
    dut.wr_addr.value = 0
    dut.wr_data.value = 0
    dut.load_complete_valid.value = 0
    dut.result_ready.value = 0
    clock = Clock(dut.clk, 10, unit="ns")
    clock.start(start_high=False)
    await RisingEdge(dut.clk)
    await ReadOnly()

    for phase in ("partial_prefetch", "recovery", "ready_prefetch", "recovery", "resume_prefetch"):
        dut._log.info(f"Prefetch Reset Test: {phase}")
        a = [[-7 + r + q % 3 for q in range(depth + 1)] for r in range(rows)]
        b = [[5 - c - q % 2 for c in range(cols)] for q in range(depth + 1)]
        expected = matmul_reference(a, b)
        await FallingEdge(dut.clk)
        dut.rst.value = 0
        dut.cmd_valid.value = 1
        await RisingEdge(dut.clk)
        await ReadOnly()
        assert dut.busy.value == 1
        request = None
        writes = []
        position = 0
        compute_edges = 0
        next_writes = 0
        next_complete = False
        collected = {}
        aborted = False
        paused_ready_cycles = 0

        for cycle in range(10000):
            await FallingEdge(dut.clk)
            dut.cmd_valid.value = 0
            dut.wr_valid.value = 0
            dut.load_complete_valid.value = 0
            dut.result_ready.value = int(phase in ("recovery", "resume_prefetch"))
            dut.step.value = int(phase == "recovery" or compute_edges < 3 or
                                 (phase == "resume_prefetch" and paused_ready_cycles == 5))
            if int(dut.load_req.value):
                offset = int(dut.k_offset.value)
                if request != offset:
                    request = offset
                    writes = []
                    position = 0
                    count = int(dut.chunk_len.value)
                    for q in range(count):
                        for r in range(rows):
                            writes.append((0, r, q, a[r][offset + q]))
                        for c in range(cols):
                            writes.append((1, c, q, b[offset + q][c]))
                hold_partial = phase == "partial_prefetch" and offset == depth and next_writes == 1
                if position < len(writes) and not hold_partial:
                    is_b, bank, address, value = writes[position]
                    dut.wr_valid.value = 1
                    dut.wr_is_b.value = is_b
                    dut.wr_bank.value = bank
                    dut.wr_addr.value = address
                    dut.wr_data.value = value
                elif position == len(writes):
                    dut.load_complete_valid.value = 1

            await ReadOnly()
            if int(engine.scheduler_step.value):
                compute_edges += 1
            if int(dut.wr_valid.value) and int(dut.wr_ready.value):
                position += 1
                if request == depth:
                    next_writes += 1
                    assert engine.read_bank.value == 0
                    assert engine.write_bank.value == 1
            if int(dut.load_complete_valid.value) and int(dut.load_complete_ready.value):
                if request == depth:
                    next_complete = True
            if int(dut.result_valid.value) and int(dut.result_ready.value):
                key = (int(dut.result_row.value), int(dut.result_col.value))
                assert key not in collected
                collected[key] = dut.result_data.value.to_signed()
                assert collected[key] == expected[key[0]][key[1]]

            await RisingEdge(dut.clk)
            await ReadOnly()
            if phase == "resume_prefetch" and next_complete and paused_ready_cycles < 5:
                assert engine.read_bank.value == 0
                assert engine.controller_inst.next_ready.value == 1
                assert dut.load_req.value == 0 and dut.result_valid.value == 0
                paused_ready_cycles += 1
            reset_target = ((phase == "partial_prefetch" and next_writes == 1) or
                            (phase == "ready_prefetch" and next_complete))
            if reset_target and compute_edges >= 3:
                assert engine.read_bank.value == 0
                assert dut.result_valid.value == 0 and dut.busy.value == 1
                if phase == "ready_prefetch":
                    assert engine.controller_inst.next_ready.value == 1
                    assert dut.load_req.value == 0
                else:
                    assert dut.load_req.value == 1
                await FallingEdge(dut.clk)
                dut.step.value = 0
                dut.rst.value = 1
                dut.wr_valid.value = 1
                dut.load_complete_valid.value = 1
                dut.result_ready.value = 1
                await ReadOnly()
                assert dut.wr_ready.value == 0 and dut.load_complete_ready.value == 0
                assert dut.result_valid.value == 0
                await RisingEdge(dut.clk)
                await ReadOnly()
                assert dut.busy.value == 0 and dut.done.value == 0
                aborted = True
                break
            if int(dut.done.value):
                assert phase in ("recovery", "resume_prefetch")
                if phase == "resume_prefetch":
                    assert paused_ready_cycles == 5
                assert len(collected) == rows * cols
                break
        else:
            raise AssertionError(f"{phase}: timed out")

        assert aborted == (phase in ("partial_prefetch", "ready_prefetch"))
        for delay in range(4):
            await FallingEdge(dut.clk)
            dut.rst.value = 0
            dut.cmd_valid.value = 0
            dut.wr_valid.value = 0
            dut.load_complete_valid.value = 0
            dut.result_ready.value = 0
            dut.step.value = 1
            await RisingEdge(dut.clk)
            await ReadOnly()
            assert dut.busy.value == 0 and dut.done.value == 0
            assert dut.load_req.value == 0 and dut.result_valid.value == 0
