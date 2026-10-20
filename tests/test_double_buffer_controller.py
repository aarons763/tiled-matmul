import os
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, ReadOnly


@cocotb.test()
async def test_buffer_ownership(dut):
    depth = int(os.environ["TEST_DEPTH"])
    dut.clk.value = 0
    dut.rst.value = 1
    dut.start.value = 0
    dut.total_k.value = 2 * depth + 1
    dut.load_done.value = 0
    dut.engine_done.value = 0
    clock = Clock(dut.clk, 10, unit="ns")
    clock.start(start_high=False)
    await RisingEdge(dut.clk)
    await ReadOnly()

    for order in ("loader_first", "engine_first", "same_edge"):
        dut._log.info(f"Ownership Test: {order}")
        await FallingEdge(dut.clk)
        dut.rst.value = 0
        dut.start.value = 1
        await RisingEdge(dut.clk)
        await ReadOnly()
        loaded = set()
        started = 0
        finished = 0
        active = None
        request = None
        request_age = 0
        active_age = 0
        clear_count = 0
        witnessed_order = False

        for cycle in range(150):
            await FallingEdge(dut.clk)
            dut.start.value = 0
            dut.load_done.value = 0
            dut.engine_done.value = 0
            if int(dut.load_req.value):
                key = int(dut.k_offset.value)
                if request != key:
                    request = key
                    request_age = 0
                request_age += 1
                load_delay = 7 if order == "engine_first" else 2
                if order == "same_edge" and key != 0:
                    load_delay = 4
                dut.load_done.value = int(request_age >= load_delay)

            if active is not None:
                active_age += 1
                engine_delay = 2 if order == "engine_first" else 7
                if order == "same_edge":
                    engine_delay = 4
                dut.engine_done.value = int(active_age >= engine_delay)

            await ReadOnly()
            if int(dut.engine_clear.value):
                clear_count += 1
            load_accept = int(dut.load_req.value) and int(dut.load_done.value)
            engine_finish = int(dut.engine_done.value)
            if int(dut.load_req.value):
                offset = int(dut.k_offset.value)
                index = offset // depth
                assert offset == index * depth and index < 3
                assert int(dut.chunk_len.value) == (depth if index < 2 else 1)
                assert int(dut.write_bank.value) == index % 2
                if active is not None:
                    assert int(dut.write_bank.value) != int(dut.read_bank.value)
                    if index > 0 and load_accept and not engine_finish and order == "loader_first":
                        witnessed_order = True
                    if index > 0 and engine_finish and not load_accept and order == "engine_first":
                        witnessed_order = True
                    if index > 0 and load_accept and engine_finish and order == "same_edge":
                        witnessed_order = True
            if load_accept:
                assert index not in loaded
                loaded.add(index)
            if engine_finish:
                assert active is not None
                finished += 1
                active = None
            if int(dut.engine_start.value):
                assert active is None and started in loaded
                assert finished == started
                assert int(dut.read_bank.value) == started % 2
                assert int(dut.engine_k_len.value) == (depth if started < 2 else 1)
                active = started
                active_age = 0
                started += 1
            elif active is not None:
                assert int(dut.read_bank.value) == active % 2

            await RisingEdge(dut.clk)
            await ReadOnly()
            if int(dut.done.value):
                assert started == finished == 3
                assert loaded == {0, 1, 2}
                assert clear_count == 1 and witnessed_order
                assert dut.busy.value == 0 and dut.load_req.value == 0
                break
        else:
            raise AssertionError(f"{order}: timeout")

        await FallingEdge(dut.clk)
        dut.engine_done.value = 0
        dut.load_done.value = 0
        await RisingEdge(dut.clk)
        await ReadOnly()
        assert dut.done.value == 0
