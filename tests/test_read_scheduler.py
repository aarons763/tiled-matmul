import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge
from cocotb.triggers import FallingEdge
from cocotb.triggers import ReadOnly


@cocotb.test()
async def test_read_scheduler(dut):
    rows = len(dut.a_rd_en)
    cols = len(dut.b_rd_en)
    dut.clk.value = 0
    dut.rst.value = 1
    dut.step.value = 0
    dut.start.value = 0
    dut.k_len.value = 1
    clock = Clock(dut.clk, 10, unit="ns")
    clock.start(start_high=False)

    dut._log.info("Reset")
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert dut.busy.value == 0, "Reset must clear busy"
    assert dut.done.value == 0, "Reset must clear done"
    assert dut.array_step.value == 0, "Reset must disable the datapath"

    # These workloads target DEPTH=16, including its maximum legal K.
    for length in (1, 3, 16):
        dut._log.info(f"Start K={length}")
        await FallingEdge(dut.clk)
        dut.rst.value = 0
        dut.start.value = 1
        dut.k_len.value = length
        dut.step.value = int(length == 1)
        await ReadOnly()
        assert dut.busy.value == 0, "Must be idle before accepting start"
        assert dut.array_step.value == 0, "Start acceptance edge must not advance datapath"
        await RisingEdge(dut.clk)
        await ReadOnly()
        assert dut.busy.value == 1, "Start must set busy, even when step is low"
        assert dut.done.value == 0, "Start must not assert done"

        # Requests are checked before the edge on which they are accepted.
        total_edges = length + rows + cols - 1
        a_reads = [0] * rows
        b_reads = [0] * cols
        for t in range(total_edges):
            if t in (0, 2, total_edges - 1):
                dut._log.info(f"K={length}: two-edge stall before t={t}")
                for stall_edge in range(2):
                    await FallingEdge(dut.clk)
                    dut.start.value = 0
                    dut.step.value = 0
                    dut.k_len.value = 2 if length != 2 else 1
                    await ReadOnly()
                    assert dut.array_step.value == 0, "Stall must disable datapath"
                    for r in range(rows):
                        assert dut.a_rd_en[r].value == 0, f"A row {r}: read during stall"
                        assert dut.a_rd_addr[r].value == 0, f"A row {r}: inactive address must be zero"
                    for c in range(cols):
                        assert dut.b_rd_en[c].value == 0, f"B col {c}: read during stall"
                        assert dut.b_rd_addr[c].value == 0, f"B col {c}: inactive address must be zero"
                    await RisingEdge(dut.clk)
                    await ReadOnly()
                    assert dut.busy.value == 1, "Stall must retain busy"
                    assert dut.done.value == 0, "Stall must not finish computation"

            await FallingEdge(dut.clk)
            dut.step.value = 1
            # A new start while busy and changes to live K must be ignored.
            dut.start.value = int(t == 1)
            dut.k_len.value = 2
            await ReadOnly()
            assert dut.busy.value == 1, f"K={length}, t={t}: busy dropped early"
            assert dut.done.value == 0, f"K={length}, t={t}: done asserted early"
            assert dut.array_step.value == 1, f"K={length}, t={t}: missing datapath step"
            for r in range(rows):
                k = t - r
                valid = int(0 <= k < length)
                address = k if valid else 0
                assert dut.a_rd_en[r].value == valid, f"K={length}, t={t}, A row {r}: enable mismatch"
                assert int(dut.a_rd_addr[r].value) == address, f"K={length}, t={t}, A row {r}: address mismatch"
                a_reads[r] += valid
            for c in range(cols):
                k = t - c
                valid = int(0 <= k < length)
                address = k if valid else 0
                assert dut.b_rd_en[c].value == valid, f"K={length}, t={t}, B col {c}: enable mismatch"
                assert int(dut.b_rd_addr[c].value) == address, f"K={length}, t={t}, B col {c}: address mismatch"
                b_reads[c] += valid

            await RisingEdge(dut.clk)
            await ReadOnly()
            finished = int(t == total_edges - 1)
            assert dut.done.value == finished, f"K={length}, t={t}: completion timing mismatch"
            assert dut.busy.value == 1 - finished, f"K={length}, t={t}: busy timing mismatch"
            if finished:
                assert dut.array_step.value == 0, "Completion must disable datapath"
                for r in range(rows):
                    assert dut.a_rd_en[r].value == 0, f"A row {r}: read after completion"
                for c in range(cols):
                    assert dut.b_rd_en[c].value == 0, f"B col {c}: read after completion"

        assert a_reads == [length] * rows, f"Wrong A read counts: {a_reads}"
        assert b_reads == [length] * cols, f"Wrong B read counts: {b_reads}"

        dut._log.info("Done Clears Even With Step Low")
        await FallingEdge(dut.clk)
        dut.start.value = 0
        dut.step.value = 0
        await RisingEdge(dut.clk)
        await ReadOnly()
        assert dut.done.value == 0, "Done must last one clock, independent of step"
        assert dut.busy.value == 0, "Scheduler must remain idle"

    dut._log.info("Reset Aborts An Active Run")
    await FallingEdge(dut.clk)
    dut.start.value = 1
    dut.step.value = 1
    dut.k_len.value = 3
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert dut.busy.value == 1
    await FallingEdge(dut.clk)
    dut.start.value = 0
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert dut.busy.value == 1

    await FallingEdge(dut.clk)
    dut.rst.value = 1
    dut.start.value = 1
    dut.step.value = 0
    await ReadOnly()
    assert dut.array_step.value == 0, "Reset must suppress datapath step"
    for r in range(rows):
        assert dut.a_rd_en[r].value == 0
    for c in range(cols):
        assert dut.b_rd_en[c].value == 0
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert dut.busy.value == 0, "Reset must override start and active state"
    assert dut.done.value == 0, "Reset abort is not normal completion"

    dut._log.info("Restart After Abort")
    await FallingEdge(dut.clk)
    dut.rst.value = 0
    dut.k_len.value = 1
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert dut.busy.value == 1, "Restart while paused must be accepted"
    for t in range(rows + cols):
        await FallingEdge(dut.clk)
        dut.start.value = 0
        dut.step.value = 1
        await ReadOnly()
        for r in range(rows):
            assert dut.a_rd_en[r].value == int(t == r), f"Restart A row {r}: schedule did not restart at zero"
            assert int(dut.a_rd_addr[r].value) == 0
        for c in range(cols):
            assert dut.b_rd_en[c].value == int(t == c), f"Restart B col {c}: schedule did not restart at zero"
            assert int(dut.b_rd_addr[c].value) == 0
        await RisingEdge(dut.clk)
        await ReadOnly()
        assert dut.done.value == int(t == rows + cols - 1)
        assert dut.busy.value == int(t < rows + cols - 1)
