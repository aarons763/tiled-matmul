import os
import random
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, ReadOnly
from matmul_reference import matmul_reference


@cocotb.test()
async def test_matmul_host(dut):
    rows = int(os.environ["TEST_ROWS"])
    cols = int(os.environ["TEST_COLS"])
    depth = int(os.environ["TEST_DEPTH"])
    rng = random.Random(763)
    dut._log.info("Reproducible operand and stall seed: 763")
    dut.clk.value = 0
    dut.rst.value = 1
    dut.step.value = 0
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
    dut.result_ready.value = 0
    clock = Clock(dut.clk, 10, unit="ns")
    clock.start(start_high=False)
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert dut.cmd_ready.value == 0 and dut.wr_ready.value == 0
    assert dut.result_valid.value == 0 and dut.error.value == 0

    dut._log.info("Reject Invalid Commands")
    for m, n, k in ((0, 1, 1), (1, 0, 1), (1, 1, 0)):
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
        assert dut.error.value == 1 and dut.busy.value == 0 and dut.load_req.value == 0
        await FallingEdge(dut.clk)
        dut.cmd_valid.value = 0
        await RisingEdge(dut.clk)
        await ReadOnly()
        assert dut.error.value == 0

    cases = [
        (6, 5, 35, "pattern"),
        (1, 1, 1, "random"),
        (rows, cols, depth, "minimum"),
        (rows + 1, cols + 1, depth + 1, "mixed_extremes"),
        (1, cols + 1, max(1, depth - 1), "random"),
        (rows + 1, 1, 2 * depth, "random"),
        (rows, cols, 2 * depth + 1, "zero"),
    ]
    for m, n, length, pattern in cases:
        if pattern == "pattern":
            a = [[((i + 2) * (k + 1)) % 17 - 8 for k in range(length)] for i in range(m)]
            b = [[((k + 3) * (j + 1)) % 13 - 6 for j in range(n)] for k in range(length)]
        elif pattern == "minimum":
            a = [[-128 for k in range(length)] for i in range(m)]
            b = [[-128 for j in range(n)] for k in range(length)]
        elif pattern == "mixed_extremes":
            a = [[-128 if (i + k) % 2 else 127 for k in range(length)] for i in range(m)]
            b = [[127 if (k + j) % 2 else -128 for j in range(n)] for k in range(length)]
        else:
            a = [[0 if pattern == "zero" else rng.randint(-128, 127)
                  for k in range(length)] for i in range(m)]
            b = [[rng.randint(-128, 127) for j in range(n)] for k in range(length)]
        expected = matmul_reference(a, b)
        collected = [[None for j in range(n)] for i in range(m)]
        tiles = [(r, c) for r in range(0, m, rows) for c in range(0, n, cols)]
        dut._log.info(f"Command {m}x{length} by {length}x{n}")
        await FallingEdge(dut.clk)
        dut.cmd_valid.value = 1
        dut.cmd_m.value = m
        dut.cmd_n.value = n
        dut.cmd_k.value = length
        await ReadOnly()
        assert dut.cmd_ready.value == 1
        await RisingEdge(dut.clk)
        await ReadOnly()
        assert dut.busy.value == 1 and dut.error.value == 0 and dut.cmd_ready.value == 0

        for tile_index, (tr, tc) in enumerate(tiles):
            for offset in range(0, length, depth):
                count = min(depth, length - offset)
                for cycle in range(200):
                    if int(dut.load_req.value):
                        break
                    await FallingEdge(dut.clk)
                    dut.cmd_valid.value = 0
                    dut.cmd_m.value = 1
                    dut.cmd_n.value = 1
                    dut.cmd_k.value = 1
                    dut.wr_valid.value = 0
                    dut.load_complete_valid.value = 0
                    dut.result_ready.value = 0
                    dut.step.value = int(rng.randrange(4) != 0)
                    await RisingEdge(dut.clk)
                    await ReadOnly()
                    assert dut.busy.value == 1 and dut.done.value == 0 and dut.result_valid.value == 0
                    assert dut.cmd_ready.value == 0
                else:
                    raise AssertionError("Timeout waiting for load request")

                assert int(dut.tile_row.value) == tr and int(dut.tile_col.value) == tc
                assert int(dut.valid_rows.value) == min(rows, m - tr)
                assert int(dut.valid_cols.value) == min(cols, n - tc)
                assert int(dut.k_offset.value) == offset and int(dut.chunk_len.value) == count
                dut._log.info(f"Serial Load Tile={tr},{tc}, Offset={offset}, Count={count}")

                # Exercise representable invalid destinations on partial loads
                # and on rectangular builds, without corrupting memory.
                if count < depth or rows < (1 << len(dut.wr_bank)):
                    await FallingEdge(dut.clk)
                    dut.cmd_valid.value = 0
                    dut.load_complete_valid.value = 0
                    dut.step.value = 0
                    dut.wr_valid.value = 1
                    dut.wr_is_b.value = 0
                    dut.wr_bank.value = 0 if count < depth else rows
                    dut.wr_addr.value = count if count < depth else 0
                    dut.wr_data.value = 99
                    await ReadOnly()
                    assert dut.wr_ready.value == 0, "Invalid write destination was accepted"
                    await RisingEdge(dut.clk)
                    await ReadOnly()
                    assert dut.load_req.value == 1

                for local_k in range(count):
                    for is_b, bank_count in ((0, rows), (1, cols)):
                        for bank in range(bank_count):
                            for delay in range(rng.randrange(3)):
                                await FallingEdge(dut.clk)
                                dut.wr_valid.value = 0
                                dut.load_complete_valid.value = 0
                                await RisingEdge(dut.clk)
                                await ReadOnly()
                                assert dut.load_req.value == 1 and dut.done.value == 0
                            await FallingEdge(dut.clk)
                            dut.step.value = 0
                            dut.cmd_valid.value = 0
                            dut.wr_valid.value = 1
                            dut.wr_is_b.value = is_b
                            dut.wr_bank.value = bank
                            dut.wr_addr.value = local_k
                            # Even a simultaneous completion request must wait.
                            dut.load_complete_valid.value = 1
                            if is_b:
                                value = b[offset + local_k][tc + bank] if tc + bank < n else 0
                            else:
                                value = a[tr + bank][offset + local_k] if tr + bank < m else 0
                            dut.wr_data.value = value
                            await ReadOnly()
                            assert dut.wr_ready.value == 1
                            assert dut.load_complete_ready.value == 0, "Completion raced the final write"
                            await RisingEdge(dut.clk)
                            await ReadOnly()
                            assert dut.load_req.value == 1 and dut.done.value == 0

                await FallingEdge(dut.clk)
                dut.wr_valid.value = 0
                dut.load_complete_valid.value = 0
                await RisingEdge(dut.clk)
                await ReadOnly()
                assert dut.load_req.value == 1, "Load must wait for explicit completion"
                await FallingEdge(dut.clk)
                dut.load_complete_valid.value = 1
                await ReadOnly()
                assert dut.load_complete_ready.value == 1
                await RisingEdge(dut.clk)
                await ReadOnly()
                assert dut.load_req.value == 0 and dut.wr_ready.value == 0

            for cycle in range(200):
                if int(dut.result_valid.value):
                    break
                await FallingEdge(dut.clk)
                dut.load_complete_valid.value = 0
                dut.step.value = int(rng.randrange(4) != 0)
                await RisingEdge(dut.clk)
                await ReadOnly()
                assert dut.busy.value == 1 and dut.done.value == 0
                assert dut.load_req.value == 0
            else:
                raise AssertionError("Timeout waiting for result stream")

            dut._log.info(f"Read Serialized Results For Tile {tr},{tc}")
            for r in range(min(rows, m - tr)):
                for c in range(min(cols, n - tc)):
                    gr, gc = tr + r, tc + c
                    # Pause each value so stability is checked throughout a tile.
                    for delay in range(rng.randrange(5)):
                        await FallingEdge(dut.clk)
                        dut.result_ready.value = 0
                        dut.step.value = 0
                        dut.cmd_valid.value = 1  # Must not be accepted while busy.
                        await RisingEdge(dut.clk)
                        await ReadOnly()
                        assert dut.result_valid.value == 1 and dut.done.value == 0
                        assert dut.cmd_ready.value == 0 and dut.error.value == 0
                        assert int(dut.result_row.value) == gr and int(dut.result_col.value) == gc
                        assert dut.result_data.value.to_signed() == expected[gr][gc]
                    await FallingEdge(dut.clk)
                    dut.cmd_valid.value = 0
                    dut.result_ready.value = 1
                    await ReadOnly()
                    assert dut.result_valid.value == 1
                    assert int(dut.result_row.value) == gr and int(dut.result_col.value) == gc
                    assert dut.result_data.value.to_signed() == expected[gr][gc]
                    assert collected[gr][gc] is None, "Duplicate result"
                    collected[gr][gc] = dut.result_data.value.to_signed()
                    await RisingEdge(dut.clk)
                    await ReadOnly()
                    last = (tile_index == len(tiles) - 1 and
                            r == min(rows, m - tr) - 1 and c == min(cols, n - tc) - 1)
                    assert dut.done.value == int(last)
                    assert dut.busy.value == int(not last)

        assert collected == expected, f"Full matrix mismatch: {collected}"
        await FallingEdge(dut.clk)
        dut.cmd_valid.value = 0
        dut.result_ready.value = 0
        await RisingEdge(dut.clk)
        await ReadOnly()
        assert dut.done.value == 0 and dut.cmd_ready.value == 1 and dut.busy.value == 0

    dut._log.info("Reset Cancels A Loading Request")
    await FallingEdge(dut.clk)
    dut.cmd_valid.value = 1
    dut.cmd_m.value = 1
    dut.cmd_n.value = 1
    dut.cmd_k.value = 1
    await RisingEdge(dut.clk)
    await ReadOnly()
    for cycle in range(10):
        if int(dut.load_req.value):
            break
        await FallingEdge(dut.clk)
        dut.cmd_valid.value = 0
        await RisingEdge(dut.clk)
        await ReadOnly()
    else:
        raise AssertionError("No load request before reset test")
    await FallingEdge(dut.clk)
    dut.rst.value = 1
    dut.wr_valid.value = 1
    dut.load_complete_valid.value = 1
    dut.result_ready.value = 1
    await ReadOnly()
    assert dut.wr_ready.value == 0 and dut.load_complete_ready.value == 0
    assert dut.result_valid.value == 0 and dut.cmd_ready.value == 0
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert dut.busy.value == 0 and dut.done.value == 0 and dut.error.value == 0


@cocotb.test()
async def test_reset_and_recovery(dut):
    rows = int(os.environ["TEST_ROWS"])
    cols = int(os.environ["TEST_COLS"])
    dut.clk.value = 0
    dut.rst.value = 1
    dut.step.value = 0
    dut.cmd_valid.value = 0
    dut.cmd_m.value = rows
    dut.cmd_n.value = cols
    dut.cmd_k.value = 1
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

    for phase in ("compute_abort", "compute_recovery", "result_abort", "result_recovery"):
        dut._log.info(f"Reset Test: {phase}")
        # Different operands on each recovery expose stale sums or memory.
        a_value = -7 if "recovery" in phase else 3
        b_value = 5 if "recovery" in phase else -4
        expected = a_value * b_value
        await FallingEdge(dut.clk)
        dut.rst.value = 0
        dut.cmd_valid.value = 1
        dut.step.value = 0
        dut.wr_valid.value = 0
        dut.load_complete_valid.value = 0
        dut.result_ready.value = 0
        await ReadOnly()
        assert dut.cmd_ready.value == 1
        await RisingEdge(dut.clk)
        await ReadOnly()
        assert dut.busy.value == 1

        for cycle in range(20):
            if int(dut.load_req.value):
                break
            await FallingEdge(dut.clk)
            dut.cmd_valid.value = 0
            await RisingEdge(dut.clk)
            await ReadOnly()
        else:
            raise AssertionError(f"{phase}: no load request")

        for is_b, banks in ((0, rows), (1, cols)):
            for bank in range(banks):
                await FallingEdge(dut.clk)
                dut.cmd_valid.value = 0
                dut.wr_valid.value = 1
                dut.wr_is_b.value = is_b
                dut.wr_bank.value = bank
                dut.wr_data.value = b_value if is_b else a_value
                await ReadOnly()
                assert dut.wr_ready.value == 1
                await RisingEdge(dut.clk)
                await ReadOnly()

        await FallingEdge(dut.clk)
        dut.wr_valid.value = 0
        dut.load_complete_valid.value = 1
        await ReadOnly()
        assert dut.load_complete_ready.value == 1
        await RisingEdge(dut.clk)
        await ReadOnly()

        if phase == "compute_abort":
            # START, scheduler acceptance, bank read, then first MAC.
            for cycle in range(4):
                await FallingEdge(dut.clk)
                dut.load_complete_valid.value = 0
                dut.step.value = 1
                await RisingEdge(dut.clk)
                await ReadOnly()
                assert dut.busy.value == 1 and dut.result_valid.value == 0
        else:
            for cycle in range(100):
                if int(dut.result_valid.value):
                    break
                await FallingEdge(dut.clk)
                dut.load_complete_valid.value = 0
                dut.step.value = 1
                await RisingEdge(dut.clk)
                await ReadOnly()
                assert dut.done.value == 0
            else:
                raise AssertionError(f"{phase}: no result")

            count = 1 if phase == "result_abort" else rows * cols
            for index in range(count):
                await FallingEdge(dut.clk)
                dut.result_ready.value = 1
                await ReadOnly()
                assert dut.result_valid.value == 1
                assert int(dut.result_row.value) == index // cols
                assert int(dut.result_col.value) == index % cols
                assert dut.result_data.value.to_signed() == expected
                await RisingEdge(dut.clk)
                await ReadOnly()
                assert dut.done.value == int(index == rows * cols - 1)

        if "abort" in phase:
            await FallingEdge(dut.clk)
            dut.step.value = 0
            dut.result_ready.value = 0
            await RisingEdge(dut.clk)
            await ReadOnly()
            assert dut.busy.value == 1 and dut.done.value == 0
            if phase == "result_abort":
                assert dut.result_valid.value == 1
                assert int(dut.result_row.value) == 1 // cols
                assert int(dut.result_col.value) == 1 % cols
                assert dut.result_data.value.to_signed() == expected

            await FallingEdge(dut.clk)
            dut.rst.value = 1
            dut.cmd_valid.value = 1
            dut.wr_valid.value = 1
            dut.load_complete_valid.value = 1
            dut.result_ready.value = 1
            await ReadOnly()
            assert dut.cmd_ready.value == 0 and dut.wr_ready.value == 0
            assert dut.load_complete_ready.value == 0 and dut.result_valid.value == 0
            await RisingEdge(dut.clk)
            await ReadOnly()
            assert dut.busy.value == 0 and dut.done.value == 0 and dut.error.value == 0

        # Release reset and leave several idle clocks to catch stale completion.
        for cycle in range(4):
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
            assert dut.result_valid.value == 0 and dut.load_req.value == 0
            assert dut.cmd_ready.value == 1 and dut.error.value == 0
