import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, ReadOnly
from matmul_reference import matmul_reference


@cocotb.test()
async def test_tile_engine(dut):
    rows = len(dut.a_wr_en)
    cols = len(dut.b_wr_en)
    a = [[1, -2, 3], [0, 4, -1], [-3, 2, 1], [2, 0, -2]][:rows]
    b = [row[:cols] for row in [[2, 1, -1, 3], [-1, 3, 2, 0], [4, -2, 1, -1]]]
    expected = matmul_reference(a, b)
    K = 3
    dut.clk.value = 0
    dut.rst.value = 1
    dut.step.value = 0
    dut.start.value = 0
    dut.clear.value = 0
    dut.k_len.value = K
    for r in range(rows):
        dut.a_wr_en[r].value = 0
        dut.a_wr_addr[r].value = 0
        dut.a_wr_data[r].value = 0
    for c in range(cols):
        dut.b_wr_en[c].value = 0
        dut.b_wr_addr[c].value = 0
        dut.b_wr_data[c].value = 0
    clock = Clock(dut.clk, 10, unit="ns")
    clock.start(start_high=False)
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert dut.busy.value == 0 and dut.done.value == 0
    for r in range(rows):
        for c in range(cols):
            assert dut.acc_outputs[r * cols + c].value.to_signed() == 0

    dut._log.info("Load While Idle And Paused")
    for k in range(K):
        await FallingEdge(dut.clk)
        dut.rst.value = 0
        for r in range(rows):
            dut.a_wr_en[r].value = 1
            dut.a_wr_addr[r].value = k
            dut.a_wr_data[r].value = a[r][k]
        for c in range(cols):
            dut.b_wr_en[c].value = 1
            dut.b_wr_addr[c].value = k
            dut.b_wr_data[c].value = b[k][c]
        await RisingEdge(dut.clk)
        await ReadOnly()
        assert dut.busy.value == 0

    # Run again without clear to preserve sums, then clear and recompute.
    for run in range(3):
        if run == 2:
            dut._log.info("Idle Clear Overrides Start With Step Low")
            await FallingEdge(dut.clk)
            dut.step.value = 0
            dut.clear.value = 1
            dut.start.value = 1
            await RisingEdge(dut.clk)
            await ReadOnly()
            assert dut.busy.value == 0, "Clear must take priority over start"
            for r in range(rows):
                for c in range(cols):
                    assert dut.acc_outputs[r * cols + c].value.to_signed() == 0, "Idle clear failed"

        dut._log.info(f"Start Run {run}")
        await FallingEdge(dut.clk)
        dut.clear.value = 0
        dut.start.value = 1
        dut.step.value = 0
        dut.k_len.value = K
        for r in range(rows):
            dut.a_wr_en[r].value = 0
        for c in range(cols):
            dut.b_wr_en[c].value = 0
        await RisingEdge(dut.clk)
        await ReadOnly()
        assert dut.busy.value == 1, "Start while paused must be accepted"
        assert dut.done.value == 0
        total_edges = K + rows + cols - 1
        for t in range(total_edges):
            if t in (1, total_edges - 1):
                held = [dut.acc_outputs[n].value.to_signed() for n in range(rows * cols)]
                for stall in range(2):
                    await FallingEdge(dut.clk)
                    dut.start.value = 0
                    dut.step.value = 0
                    dut.clear.value = 1
                    await RisingEdge(dut.clk)
                    await ReadOnly()
                    assert dut.busy.value == 1 and dut.done.value == 0
                    for n in range(rows * cols):
                        assert dut.acc_outputs[n].value.to_signed() == held[n], "Stall or busy clear changed a sum"

            await FallingEdge(dut.clk)
            dut.step.value = 1
            dut.start.value = 0
            dut.clear.value = 1  # Must be ignored while busy.
            dut.k_len.value = 1  # Active run must retain K=3.
            for r in range(rows):
                dut.a_wr_en[r].value = 1
                dut.a_wr_addr[r].value = 0
                dut.a_wr_data[r].value = 99
            for c in range(cols):
                dut.b_wr_en[c].value = 1
                dut.b_wr_addr[c].value = 0
                dut.b_wr_data[c].value = -99
            await RisingEdge(dut.clk)
            await ReadOnly()
            finished = int(t == total_edges - 1)
            assert dut.done.value == finished, f"Run {run}, t={t}: wrong done timing"
            assert dut.busy.value == 1 - finished, f"Run {run}, t={t}: wrong busy timing"

        multiplier = 2 if run == 1 else 1
        for r in range(rows):
            for c in range(cols):
                actual = dut.acc_outputs[r * cols + c].value.to_signed()
                assert actual == multiplier * expected[r][c], (
                    f"Run {run}, [{r}][{c}]: expected {multiplier * expected[r][c]}, got {actual}"
                )
        await FallingEdge(dut.clk)
        dut.clear.value = 0
        dut.step.value = 0
        for r in range(rows):
            dut.a_wr_en[r].value = 0
        for c in range(cols):
            dut.b_wr_en[c].value = 0
        await RisingEdge(dut.clk)
        await ReadOnly()
        assert dut.done.value == 0 and dut.busy.value == 0
        for r in range(rows):
            for c in range(cols):
                assert dut.acc_outputs[r * cols + c].value.to_signed() == multiplier * expected[r][c], "Idle changed result"

    dut._log.info("Reset Aborts Active Computation")
    await FallingEdge(dut.clk)
    dut.start.value = 1
    dut.k_len.value = K
    dut.step.value = 1
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert dut.busy.value == 1
    await FallingEdge(dut.clk)
    dut.start.value = 0
    await RisingEdge(dut.clk)
    await ReadOnly()
    await FallingEdge(dut.clk)
    dut.rst.value = 1
    dut.step.value = 0
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert dut.busy.value == 0 and dut.done.value == 0
    for r in range(rows):
        for c in range(cols):
            assert dut.acc_outputs[r * cols + c].value.to_signed() == 0, "Reset failed to clear datapath"
