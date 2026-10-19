import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, ReadOnly
from matmul_reference import matmul_reference


@cocotb.test()
async def test_tiled_matmul(dut):
    rows = len(dut.a_wr_en)
    cols = len(dut.b_wr_en)
    depth = 16
    dut.clk.value = 0
    dut.rst.value = 1
    dut.start.value = 0
    dut.step.value = 0
    dut.m_len.value = 1
    dut.n_len.value = 1
    dut.total_k.value = 1
    dut.load_done.value = 0
    dut.result_ready.value = 0
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

    for m, n, length in ((6, 5, 35), (2, 1, 1)):
        a = [[((i + 2) * (k + 1)) % 17 - 8 for k in range(length)] for i in range(m)]
        b = [[((k + 3) * (j + 1)) % 13 - 6 for j in range(n)] for k in range(length)]
        expected = matmul_reference(a, b)
        collected = [[None for j in range(n)] for i in range(m)]
        tiles = [(i, j) for i in range(0, m, rows) for j in range(0, n, cols)]
        dut._log.info(f"Start {m}x{length} by {length}x{n}")
        await FallingEdge(dut.clk)
        dut.rst.value = 0
        dut.start.value = 1
        dut.m_len.value = m
        dut.n_len.value = n
        dut.total_k.value = length
        await RisingEdge(dut.clk)
        await ReadOnly()
        assert dut.busy.value == 1 and dut.done.value == 0

        for tile_index, (tr, tc) in enumerate(tiles):
            for offset in range(0, length, depth):
                count = min(depth, length - offset)
                for cycle in range(200):
                    if int(dut.load_req.value):
                        break
                    await FallingEdge(dut.clk)
                    dut.start.value = 0
                    dut.load_done.value = 0
                    dut.result_ready.value = 0
                    dut.step.value = int(cycle % 5 not in (1, 2))
                    # Live command inputs must not affect accepted work.
                    dut.m_len.value = 1
                    dut.n_len.value = 1
                    dut.total_k.value = 1
                    for r in range(rows):
                        dut.a_wr_en[r].value = 0
                    for c in range(cols):
                        dut.b_wr_en[c].value = 0
                    await RisingEdge(dut.clk)
                    await ReadOnly()
                    assert dut.busy.value == 1 and dut.done.value == 0
                    assert dut.result_valid.value == 0, "Result arrived before all requested chunks"
                else:
                    raise AssertionError(f"Load timeout: tile {tr},{tc}, offset {offset}")

                dut._log.info(f"Load Tile={tr},{tc}, K Offset={offset}, Length={count}")
                assert int(dut.tile_row.value) == tr and int(dut.tile_col.value) == tc
                assert int(dut.valid_rows.value) == min(rows, m - tr)
                assert int(dut.valid_cols.value) == min(cols, n - tc)
                assert int(dut.k_offset.value) == offset and int(dut.chunk_len.value) == count
                held = [dut.acc_outputs[index].value.to_signed() for index in range(rows * cols)]
                for delay in range(2):
                    await FallingEdge(dut.clk)
                    dut.step.value = 0
                    dut.start.value = 0
                    dut.load_done.value = 0
                    for r in range(rows):
                        dut.a_wr_en[r].value = 0
                    for c in range(cols):
                        dut.b_wr_en[c].value = 0
                    await RisingEdge(dut.clk)
                    await ReadOnly()
                    assert dut.load_req.value == 1
                    assert int(dut.k_offset.value) == offset and int(dut.chunk_len.value) == count
                    for index in range(rows * cols):
                        assert dut.acc_outputs[index].value.to_signed() == held[index]

                for local_k in range(count):
                    await FallingEdge(dut.clk)
                    for r in range(rows):
                        dut.a_wr_en[r].value = 1
                        dut.a_wr_addr[r].value = local_k
                        dut.a_wr_data[r].value = a[tr + r][offset + local_k] if tr + r < m else 0
                    for c in range(cols):
                        dut.b_wr_en[c].value = 1
                        dut.b_wr_addr[c].value = local_k
                        dut.b_wr_data[c].value = b[offset + local_k][tc + c] if tc + c < n else 0
                    await RisingEdge(dut.clk)
                    await ReadOnly()
                    assert dut.load_req.value == 1 and dut.done.value == 0

                await FallingEdge(dut.clk)
                for r in range(rows):
                    dut.a_wr_en[r].value = 0
                for c in range(cols):
                    dut.b_wr_en[c].value = 0
                dut.load_done.value = 1
                await RisingEdge(dut.clk)
                await ReadOnly()
                assert dut.load_req.value == 0

            for cycle in range(200):
                if int(dut.result_valid.value):
                    break
                await FallingEdge(dut.clk)
                dut.load_done.value = 0
                dut.step.value = int(cycle % 5 not in (1, 2))
                await RisingEdge(dut.clk)
                await ReadOnly()
                assert dut.busy.value == 1 and dut.done.value == 0
                assert dut.load_req.value == 0, "Unexpected extra chunk"
            else:
                raise AssertionError(f"Result timeout: tile {tr},{tc}")

            dut._log.info(f"Hold And Collect Tile {tr},{tc}")
            for delay in range(3):
                await FallingEdge(dut.clk)
                dut.result_ready.value = 0
                dut.start.value = 1  # Must not restart a busy matrix operation.
                dut.step.value = delay % 2
                await RisingEdge(dut.clk)
                await ReadOnly()
                assert dut.result_valid.value == 1 and dut.busy.value == 1 and dut.done.value == 0
                assert dut.load_req.value == 0
                assert int(dut.tile_row.value) == tr and int(dut.tile_col.value) == tc
                assert int(dut.valid_rows.value) == min(rows, m - tr)
                assert int(dut.valid_cols.value) == min(cols, n - tc)
                for r in range(rows):
                    for c in range(cols):
                        wanted = expected[tr + r][tc + c] if tr + r < m and tc + c < n else 0
                        actual = dut.acc_outputs[r * cols + c].value.to_signed()
                        assert actual == wanted, f"Tile {tr},{tc}, PE {r},{c}: expected {wanted}, got {actual}"

            await FallingEdge(dut.clk)
            dut.start.value = 0
            dut.result_ready.value = 1
            await ReadOnly()
            for r in range(min(rows, m - tr)):
                for c in range(min(cols, n - tc)):
                    assert collected[tr + r][tc + c] is None, "Duplicate result"
                    collected[tr + r][tc + c] = dut.acc_outputs[r * cols + c].value.to_signed()
            await RisingEdge(dut.clk)
            await ReadOnly()
            final = int(tile_index == len(tiles) - 1)
            assert dut.done.value == final and dut.busy.value == 1 - final
            assert dut.result_valid.value == 0

        assert collected == expected, f"Full matrix mismatch: {collected} != {expected}"
        await FallingEdge(dut.clk)
        dut.result_ready.value = 0
        dut.step.value = 0
        await RisingEdge(dut.clk)
        await ReadOnly()
        assert dut.done.value == 0 and dut.busy.value == 0
