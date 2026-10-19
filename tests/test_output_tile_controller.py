import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, ReadOnly
import os


@cocotb.test()
async def test_output_tile_controller(dut):
    rows = int(os.environ["TEST_ROWS"])
    cols = int(os.environ["TEST_COLS"])
    dim_width = len(dut.m_len)
    dut.clk.value = 0
    dut.rst.value = 1
    dut.start.value = 0
    dut.m_len.value = 1
    dut.n_len.value = 1
    dut.engine_done.value = 0
    dut.result_ready.value = 0
    clock = Clock(dut.clk, 10, unit="ns")
    clock.start(start_high=False)
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert dut.busy.value == 0 and dut.done.value == 0
    assert dut.engine_start.value == 0 and dut.result_valid.value == 0

    cases = [(1, 1), (rows, cols), (2 * rows, 2 * cols),
             (rows + 2, cols + 1), (1, 2 * cols + 1), (2 * rows + 1, 1)]
    # A small dimension-width build exercises the real counter boundary
    # without traversing an enormous default-width matrix.
    if dim_width == 4:
        cases.append((15, 15))

    for m, n in cases:
        tiles = [(r, c, min(rows, m - r), min(cols, n - c))
                 for r in range(0, m, rows) for c in range(0, n, cols)]
        dut._log.info(f"Matrix {m}x{n}: {len(tiles)} output tiles")
        await FallingEdge(dut.clk)
        dut.rst.value = 0
        dut.start.value = 1
        dut.m_len.value = m
        dut.n_len.value = n
        dut.engine_done.value = 0
        dut.result_ready.value = 0
        await RisingEdge(dut.clk)
        await ReadOnly()

        for tile_index, (row, col, height, width) in enumerate(tiles):
            assert dut.busy.value == 1 and dut.done.value == 0
            assert dut.engine_start.value == 1, "Each tile needs one start cycle"
            assert dut.result_valid.value == 0
            assert int(dut.tile_row.value) == row and int(dut.tile_col.value) == col
            assert int(dut.valid_rows.value) == height and int(dut.valid_cols.value) == width

            await FallingEdge(dut.clk)
            dut.start.value = 0
            dut.m_len.value = 1  # Must use captured dimensions.
            dut.n_len.value = 1
            dut.engine_done.value = 0
            dut.result_ready.value = 1  # Early ready cannot skip computation.
            await RisingEdge(dut.clk)
            await ReadOnly()
            assert dut.engine_start.value == 0 and dut.result_valid.value == 0

            for delay in range(2):
                await FallingEdge(dut.clk)
                dut.start.value = 1  # Busy starts must be ignored.
                await RisingEdge(dut.clk)
                await ReadOnly()
                assert dut.busy.value == 1 and dut.done.value == 0
                assert dut.engine_start.value == 0 and dut.result_valid.value == 0
                assert int(dut.tile_row.value) == row and int(dut.tile_col.value) == col

            await FallingEdge(dut.clk)
            dut.start.value = 0
            dut.engine_done.value = 1
            # Cover both ready already high and delayed result acceptance.
            immediate = tile_index % 2 == 0
            dut.result_ready.value = int(immediate)
            await RisingEdge(dut.clk)
            await ReadOnly()
            assert dut.result_valid.value == 1, "Engine done must expose a result"
            assert dut.engine_start.value == 0 and dut.done.value == 0
            assert int(dut.tile_row.value) == row and int(dut.tile_col.value) == col

            if not immediate:
                for delay in range(3):
                    await FallingEdge(dut.clk)
                    dut.engine_done.value = 0
                    dut.start.value = 1
                    await RisingEdge(dut.clk)
                    await ReadOnly()
                    assert dut.result_valid.value == 1 and dut.busy.value == 1
                    assert dut.engine_start.value == 0 and dut.done.value == 0
                    assert int(dut.tile_row.value) == row and int(dut.tile_col.value) == col
                    assert int(dut.valid_rows.value) == height and int(dut.valid_cols.value) == width

            await FallingEdge(dut.clk)
            dut.start.value = 0
            dut.engine_done.value = 0
            dut.result_ready.value = 1
            await ReadOnly()
            # Receiver captures these coordinates and counts at this edge.
            assert dut.result_valid.value == 1
            assert int(dut.tile_row.value) == row and int(dut.tile_col.value) == col
            assert int(dut.valid_rows.value) == height and int(dut.valid_cols.value) == width
            await RisingEdge(dut.clk)
            await ReadOnly()
            final = int(tile_index == len(tiles) - 1)
            assert dut.done.value == final
            assert dut.busy.value == 1 - final
            assert dut.result_valid.value == 0
            assert dut.engine_start.value == 1 - final

        await FallingEdge(dut.clk)
        dut.result_ready.value = 0
        await RisingEdge(dut.clk)
        await ReadOnly()
        assert dut.done.value == 0 and dut.busy.value == 0, "Done must last one clock"

    for abort_phase in ("START", "WAIT_ENGINE", "RESULT"):
        dut._log.info(f"Reset In {abort_phase}")
        await FallingEdge(dut.clk)
        dut.rst.value = 0
        dut.start.value = 1
        dut.m_len.value = rows + 1
        dut.n_len.value = cols + 1
        dut.engine_done.value = 0
        dut.result_ready.value = 0
        await RisingEdge(dut.clk)
        await ReadOnly()
        assert dut.engine_start.value == 1
        if abort_phase != "START":
            await FallingEdge(dut.clk)
            dut.start.value = 0
            await RisingEdge(dut.clk)
            await ReadOnly()
            assert dut.busy.value == 1 and dut.engine_start.value == 0
        if abort_phase == "RESULT":
            await FallingEdge(dut.clk)
            dut.engine_done.value = 1
            await RisingEdge(dut.clk)
            await ReadOnly()
            assert dut.result_valid.value == 1
        await FallingEdge(dut.clk)
        dut.rst.value = 1
        dut.start.value = 1
        dut.engine_done.value = 1
        dut.result_ready.value = 1
        await ReadOnly()
        assert dut.engine_start.value == 0 and dut.result_valid.value == 0
        await RisingEdge(dut.clk)
        await ReadOnly()
        assert dut.busy.value == 0 and dut.done.value == 0
        assert int(dut.tile_row.value) == 0 and int(dut.tile_col.value) == 0
