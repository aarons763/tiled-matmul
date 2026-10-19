import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, ReadOnly


@cocotb.test()
async def test_chunk_controller(dut):
    dut.clk.value = 0
    dut.rst.value = 1
    dut.start.value = 0
    dut.total_k.value = 1
    dut.load_done.value = 0
    dut.engine_done.value = 0
    clock = Clock(dut.clk, 10, unit="ns")
    clock.start(start_high=False)
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert dut.busy.value == 0 and dut.done.value == 0
    assert dut.load_req.value == 0 and dut.engine_start.value == 0 and dut.engine_clear.value == 0

    # Explicit expected chunks keep this check separate from RTL arithmetic.
    cases = [
        (1, [(0, 1)]),
        (16, [(0, 16)]),
        (17, [(0, 16), (16, 1)]),
        (32, [(0, 16), (16, 16)]),
        (35, [(0, 16), (16, 16), (32, 3)]),
    ]
    for length, chunks in cases:
        dut._log.info(f"Start Total K={length}")
        await FallingEdge(dut.clk)
        dut.rst.value = 0
        dut.start.value = 1
        dut.total_k.value = length
        dut.load_done.value = 0
        dut.engine_done.value = 0
        await RisingEdge(dut.clk)
        await ReadOnly()
        assert dut.busy.value == 1 and dut.done.value == 0
        assert dut.engine_clear.value == 1, "Operation must begin with one clear cycle"
        assert dut.engine_start.value == 0 and dut.load_req.value == 0

        await FallingEdge(dut.clk)
        dut.start.value = 0
        dut.total_k.value = 99  # Captured K must not change.
        await RisingEdge(dut.clk)
        await ReadOnly()
        assert dut.engine_clear.value == 0 and dut.load_req.value == 1

        for chunk_index, (offset, count) in enumerate(chunks):
            dut._log.info(f"Load Offset={offset}, Length={count}")
            assert int(dut.k_offset.value) == offset
            assert int(dut.chunk_len.value) == count
            assert dut.load_req.value == 1
            assert dut.busy.value == 1 and dut.done.value == 0
            assert dut.engine_clear.value == 0, "Later chunks must preserve accumulators"

            # Model a loader taking several clocks. A busy start and an
            # engine completion outside WAIT_ENGINE must have no effect.
            for delay in range(2):
                await FallingEdge(dut.clk)
                dut.start.value = 1
                dut.load_done.value = 0
                dut.engine_done.value = 1
                await RisingEdge(dut.clk)
                await ReadOnly()
                assert dut.load_req.value == 1 and dut.engine_start.value == 0
                assert dut.engine_clear.value == 0 and dut.done.value == 0
                assert int(dut.k_offset.value) == offset
                assert int(dut.chunk_len.value) == count

            await FallingEdge(dut.clk)
            dut.start.value = 0
            dut.engine_done.value = 0
            dut.load_done.value = 1
            await RisingEdge(dut.clk)
            await ReadOnly()
            assert dut.load_req.value == 0 and dut.engine_start.value == 1
            assert dut.engine_clear.value == 0 and dut.done.value == 0

            await FallingEdge(dut.clk)
            dut.load_done.value = 0
            await RisingEdge(dut.clk)
            await ReadOnly()
            assert dut.engine_start.value == 0, "Engine start must last one clock"
            assert dut.busy.value == 1 and dut.done.value == 0

            dut._log.info("Wait For Engine Completion")
            for delay in range(3):
                await FallingEdge(dut.clk)
                dut.start.value = 1  # Must be ignored while busy.
                dut.load_done.value = 1  # Must be ignored outside LOAD.
                await RisingEdge(dut.clk)
                await ReadOnly()
                assert dut.busy.value == 1 and dut.done.value == 0
                assert dut.load_req.value == 0 and dut.engine_start.value == 0
                assert dut.engine_clear.value == 0
                assert int(dut.k_offset.value) == offset
                assert int(dut.chunk_len.value) == count

            await FallingEdge(dut.clk)
            dut.start.value = 0
            dut.load_done.value = 0
            dut.engine_done.value = 1
            await RisingEdge(dut.clk)
            await ReadOnly()
            final = int(chunk_index == len(chunks) - 1)
            assert dut.done.value == final, "Overall done must follow only the final chunk"
            assert dut.busy.value == 1 - final
            assert dut.load_req.value == 1 - final
            assert dut.engine_start.value == 0 and dut.engine_clear.value == 0
            await FallingEdge(dut.clk)
            dut.engine_done.value = 0
            await RisingEdge(dut.clk)
            await ReadOnly()
            assert dut.done.value == 0, "Done must be a one-clock pulse"

    # Check the initial chunk for the maximum-length request, then exercise
    # reset abort in each active phase. This does not run all 8192 chunks.
    for abort_phase in ("CLEAR", "LOAD", "START", "WAIT_ENGINE"):
        dut._log.info(f"Maximum K Capture And Reset In {abort_phase}")
        await FallingEdge(dut.clk)
        dut.start.value = 1
        dut.total_k.value = 131071
        dut.rst.value = 0
        dut.load_done.value = 0
        dut.engine_done.value = 0
        await RisingEdge(dut.clk)
        await ReadOnly()
        assert int(dut.k_offset.value) == 0 and int(dut.chunk_len.value) == 16
        assert dut.engine_clear.value == 1
        if abort_phase != "CLEAR":
            await FallingEdge(dut.clk)
            dut.start.value = 0
            await RisingEdge(dut.clk)
            await ReadOnly()
            assert dut.load_req.value == 1
        if abort_phase in ("START", "WAIT_ENGINE"):
            await FallingEdge(dut.clk)
            dut.load_done.value = 1
            await RisingEdge(dut.clk)
            await ReadOnly()
            assert dut.engine_start.value == 1
        if abort_phase == "WAIT_ENGINE":
            await FallingEdge(dut.clk)
            dut.load_done.value = 0
            await RisingEdge(dut.clk)
            await ReadOnly()
            assert dut.engine_start.value == 0 and dut.busy.value == 1
        await FallingEdge(dut.clk)
        dut.rst.value = 1
        dut.start.value = 1
        dut.load_done.value = 1
        dut.engine_done.value = 1
        await ReadOnly()
        assert dut.engine_clear.value == 0 and dut.engine_start.value == 0 and dut.load_req.value == 0
        await RisingEdge(dut.clk)
        await ReadOnly()
        assert dut.busy.value == 0 and dut.done.value == 0
        assert int(dut.k_offset.value) == 0 and int(dut.chunk_len.value) == 0
