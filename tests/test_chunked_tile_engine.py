import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, ReadOnly
from matmul_reference import matmul_reference


@cocotb.test()
async def test_chunked_tile_engine(dut):
    rows = len(dut.a_wr_en)
    cols = len(dut.b_wr_en)
    dut.clk.value = 0
    dut.rst.value = 1
    dut.step.value = 0
    dut.start.value = 0
    dut.total_k.value = 1
    dut.load_done.value = 0
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
    assert dut.busy.value == 0 and dut.done.value == 0 and dut.load_req.value == 0

    # Each new operation must clear old results without resetting memory.
    cases = [
        (35, [(0, 16), (16, 16), (32, 3)]),
        (17, [(0, 16), (16, 1)]),
        (1, [(0, 1)]),
    ]
    for length, chunks in cases:
        a = [[((r + 2) * (k + 1)) % 17 - 8 for k in range(length)] for r in range(rows)]
        b = [[((k + 3) * (c + 1)) % 13 - 6 for c in range(cols)] for k in range(length)]
        expected = matmul_reference(a, b)

        dut._log.info(f"Start K={length}")
        await FallingEdge(dut.clk)
        dut.rst.value = 0
        dut.start.value = 1
        dut.total_k.value = length
        dut.step.value = 0
        dut.load_done.value = 0
        await RisingEdge(dut.clk)
        await ReadOnly()
        assert dut.busy.value == 1 and dut.done.value == 0
        await FallingEdge(dut.clk)
        dut.start.value = 0
        dut.total_k.value = 2  # Operation length must already be latched.
        await RisingEdge(dut.clk)
        await ReadOnly()
        assert dut.load_req.value == 1
        for n in range(rows * cols):
            assert dut.acc_outputs[n].value.to_signed() == 0, "New operation did not clear old sums"

        for chunk_index, (offset, count) in enumerate(chunks):
            dut._log.info(f"Load Offset={offset}, Length={count}")
            assert dut.load_req.value == 1
            assert int(dut.k_offset.value) == offset
            assert int(dut.chunk_len.value) == count
            held = [dut.acc_outputs[n].value.to_signed() for n in range(rows * cols)]

            for delay in range(2):
                await FallingEdge(dut.clk)
                dut.step.value = 0
                dut.load_done.value = 0
                for r in range(rows):
                    dut.a_wr_en[r].value = 0
                for c in range(cols):
                    dut.b_wr_en[c].value = 0
                await RisingEdge(dut.clk)
                await ReadOnly()
                assert dut.load_req.value == 1 and dut.busy.value == 1 and dut.done.value == 0
                assert int(dut.k_offset.value) == offset and int(dut.chunk_len.value) == count
                for n in range(rows * cols):
                    assert dut.acc_outputs[n].value.to_signed() == held[n], "Loading delay changed a partial sum"

            for local_k in range(count):
                await FallingEdge(dut.clk)
                for r in range(rows):
                    dut.a_wr_en[r].value = 1
                    dut.a_wr_addr[r].value = local_k
                    dut.a_wr_data[r].value = a[r][offset + local_k]
                for c in range(cols):
                    dut.b_wr_en[c].value = 1
                    dut.b_wr_addr[c].value = local_k
                    dut.b_wr_data[c].value = b[offset + local_k][c]
                await RisingEdge(dut.clk)
                await ReadOnly()
                assert dut.load_req.value == 1 and dut.busy.value == 1 and dut.done.value == 0
                for n in range(rows * cols):
                    assert dut.acc_outputs[n].value.to_signed() == held[n], "Loading cleared or changed prior chunk results"

            await FallingEdge(dut.clk)
            for r in range(rows):
                dut.a_wr_en[r].value = 0
            for c in range(cols):
                dut.b_wr_en[c].value = 0
            dut.load_done.value = 1
            await RisingEdge(dut.clk)
            await ReadOnly()
            assert dut.load_req.value == 0 and dut.busy.value == 1 and dut.done.value == 0

            dut._log.info("Compute With Stalls And Blocked Write Attempts")
            # Bounded wait: do not let a broken completion handshake hang the test.
            for cycle in range(200):
                held = [dut.acc_outputs[n].value.to_signed() for n in range(rows * cols)]
                advance = int(cycle % 5 not in (1, 2))
                await FallingEdge(dut.clk)
                dut.load_done.value = 0
                dut.step.value = advance
                # Attempt writes outside LOAD, including the engine start edge.
                for r in range(rows):
                    dut.a_wr_en[r].value = 1
                    dut.a_wr_addr[r].value = 0
                    dut.a_wr_data[r].value = 127
                for c in range(cols):
                    dut.b_wr_en[c].value = 1
                    dut.b_wr_addr[c].value = 0
                    dut.b_wr_data[c].value = -128
                await RisingEdge(dut.clk)
                await ReadOnly()
                if not advance:
                    for n in range(rows * cols):
                        assert dut.acc_outputs[n].value.to_signed() == held[n], "Compute stall changed a sum"
                if int(dut.load_req.value) or int(dut.done.value):
                    break
                assert dut.busy.value == 1, "Busy dropped between chunks"
            else:
                raise AssertionError(f"Timeout: K={length}, chunk={chunk_index}")

            final = int(chunk_index == len(chunks) - 1)
            assert dut.done.value == final, "Overall completion at wrong chunk"
            assert dut.load_req.value == 1 - final
            assert dut.busy.value == 1 - final
            completed_k = offset + count
            partial = matmul_reference([row[:completed_k] for row in a], b[:completed_k])
            for r in range(rows):
                for c in range(cols):
                    actual = dut.acc_outputs[r * cols + c].value.to_signed()
                    assert actual == partial[r][c], (
                        f"K={length}, completed K={completed_k}, [{r}][{c}]: "
                        f"expected {partial[r][c]}, got {actual}"
                    )

        dut._log.info("Final Result And Idle Hold")
        for hold_edge in range(2):
            await FallingEdge(dut.clk)
            dut.step.value = 0
            dut.load_done.value = 0
            for r in range(rows):
                dut.a_wr_en[r].value = 0
            for c in range(cols):
                dut.b_wr_en[c].value = 0
            await RisingEdge(dut.clk)
            await ReadOnly()
            assert dut.busy.value == 0 and dut.done.value == 0 and dut.load_req.value == 0
            for r in range(rows):
                for c in range(cols):
                    assert dut.acc_outputs[r * cols + c].value.to_signed() == expected[r][c]
