import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge
from cocotb.triggers import FallingEdge
from cocotb.triggers import ReadOnly


@cocotb.test()
async def test_operand_buffer(dut):
    dut.clk.value = 0
    dut.rst.value = 1
    dut.step.value = 0

    for i in range(4):
        dut.a_wr_en[i].value = 0
        dut.b_wr_en[i].value = 0
        dut.a_wr_addr[i].value = 0
        dut.b_wr_addr[i].value = 0
        dut.a_wr_data[i].value = 0
        dut.b_wr_data[i].value = 0
        dut.a_rd_en[i].value = 0
        dut.b_rd_en[i].value = 0
        dut.a_rd_addr[i].value = 0
        dut.b_rd_addr[i].value = 0

    clock = Clock(dut.clk, 10, unit="ns")
    clock.start(start_high=False)

    dut._log.info("Reset Test")
    await RisingEdge(dut.clk)
    await ReadOnly()
    for i in range(4):
        assert dut.a_valid[i].value == 0, f"A bank {i}: reset must clear valid"
        assert dut.b_valid[i].value == 0, f"B bank {i}: reset must clear valid"
    # Memory and read data are not initialized by reset.

    dut._log.info("Load While Paused")
    await FallingEdge(dut.clk)
    dut.rst.value = 0
    for i in range(4):
        dut.a_wr_en[i].value = 1
        dut.b_wr_en[i].value = 1
        dut.a_wr_data[i].value = 10 + i
        dut.b_wr_data[i].value = 20 + i
    await RisingEdge(dut.clk)
    await ReadOnly()

    await FallingEdge(dut.clk)
    for i in range(4):
        dut.a_wr_addr[i].value = 1
        dut.b_wr_addr[i].value = 1
        dut.a_wr_data[i].value = -10 - i
        dut.b_wr_data[i].value = -20 - i
    await RisingEdge(dut.clk)
    await ReadOnly()
    for i in range(4):
        assert dut.a_valid[i].value == 0, f"A bank {i}: loading must not assert valid"
        assert dut.b_valid[i].value == 0, f"B bank {i}: loading must not assert valid"

    dut._log.info("Read All Banks")
    await FallingEdge(dut.clk)
    dut.step.value = 1
    for i in range(4):
        dut.a_wr_en[i].value = 0
        dut.b_wr_en[i].value = 0
        dut.a_rd_en[i].value = 1
        dut.b_rd_en[i].value = 1
    await RisingEdge(dut.clk)
    await ReadOnly()
    for i in range(4):
        assert dut.a_rd_data[i].value.to_signed() == 10 + i, f"A bank {i}: address 0 read mismatch"
        assert dut.b_rd_data[i].value.to_signed() == 20 + i, f"B bank {i}: address 0 read mismatch"
        assert dut.a_valid[i].value == 1, f"A bank {i}: read must assert valid"
        assert dut.b_valid[i].value == 1, f"B bank {i}: read must assert valid"

    dut._log.info("Mixed Read Requests")
    await FallingEdge(dut.clk)
    for i in range(4):
        dut.a_rd_addr[i].value = 1
        dut.b_rd_addr[i].value = 1
        dut.a_rd_en[i].value = int(i % 2 == 0)
        dut.b_rd_en[i].value = int(i % 2 == 0)
    await RisingEdge(dut.clk)
    await ReadOnly()
    for i in range(4):
        expected_a = -10 - i if i % 2 == 0 else 10 + i
        expected_b = -20 - i if i % 2 == 0 else 20 + i
        expected_valid = int(i % 2 == 0)
        assert dut.a_rd_data[i].value.to_signed() == expected_a, f"A bank {i}: mixed-read data mismatch"
        assert dut.b_rd_data[i].value.to_signed() == expected_b, f"B bank {i}: mixed-read data mismatch"
        assert dut.a_valid[i].value == expected_valid, f"A bank {i}: mixed-read valid mismatch"
        assert dut.b_valid[i].value == expected_valid, f"B bank {i}: mixed-read valid mismatch"

    dut._log.info("Two-Edge Stall With Changing Requests")
    for stall_edge in range(2):
        await FallingEdge(dut.clk)
        dut.step.value = 0
        for i in range(4):
            dut.a_rd_addr[i].value = stall_edge
            dut.b_rd_addr[i].value = 1 - stall_edge
            dut.a_rd_en[i].value = int((i + stall_edge) % 2 == 1)
            dut.b_rd_en[i].value = int((i + stall_edge) % 2 == 0)
        await RisingEdge(dut.clk)
        await ReadOnly()
        for i in range(4):
            expected_a = -10 - i if i % 2 == 0 else 10 + i
            expected_b = -20 - i if i % 2 == 0 else 20 + i
            expected_valid = int(i % 2 == 0)
            assert dut.a_rd_data[i].value.to_signed() == expected_a, f"A bank {i}: data changed during stall {stall_edge}"
            assert dut.b_rd_data[i].value.to_signed() == expected_b, f"B bank {i}: data changed during stall {stall_edge}"
            assert dut.a_valid[i].value == expected_valid, f"A bank {i}: valid changed during stall {stall_edge}"
            assert dut.b_valid[i].value == expected_valid, f"B bank {i}: valid changed during stall {stall_edge}"

    dut._log.info("Resume")
    await FallingEdge(dut.clk)
    dut.step.value = 1
    for i in range(4):
        dut.a_rd_addr[i].value = 1
        dut.b_rd_addr[i].value = 1
        dut.a_rd_en[i].value = 1
        dut.b_rd_en[i].value = 1
    await RisingEdge(dut.clk)
    await ReadOnly()
    for i in range(4):
        assert dut.a_rd_data[i].value.to_signed() == -10 - i, f"A bank {i}: resume data mismatch"
        assert dut.b_rd_data[i].value.to_signed() == -20 - i, f"B bank {i}: resume data mismatch"
        assert dut.a_valid[i].value == 1, f"A bank {i}: resume valid mismatch"
        assert dut.b_valid[i].value == 1, f"B bank {i}: resume valid mismatch"

    dut._log.info("Bubbles Hold Data And Clear Valid")
    await FallingEdge(dut.clk)
    for i in range(4):
        dut.a_rd_en[i].value = 0
        dut.b_rd_en[i].value = 0
        dut.a_rd_addr[i].value = 0
        dut.b_rd_addr[i].value = 0
    await RisingEdge(dut.clk)
    await ReadOnly()
    for i in range(4):
        assert dut.a_rd_data[i].value.to_signed() == -10 - i, f"A bank {i}: bubble changed data"
        assert dut.b_rd_data[i].value.to_signed() == -20 - i, f"B bank {i}: bubble changed data"
        assert dut.a_valid[i].value == 0, f"A bank {i}: bubble must clear valid"
        assert dut.b_valid[i].value == 0, f"B bank {i}: bubble must clear valid"

    dut._log.info("Independent Bank Addresses")
    await FallingEdge(dut.clk)
    for i in range(4):
        dut.a_rd_en[i].value = 1
        dut.b_rd_en[i].value = 1
        dut.a_rd_addr[i].value = i % 2
        dut.b_rd_addr[i].value = 1 - i % 2
    await RisingEdge(dut.clk)
    await ReadOnly()
    for i in range(4):
        expected_a = 10 + i if i % 2 == 0 else -10 - i
        expected_b = -20 - i if i % 2 == 0 else 20 + i
        assert dut.a_rd_data[i].value.to_signed() == expected_a, f"A bank {i}: independent address mismatch"
        assert dut.b_rd_data[i].value.to_signed() == expected_b, f"B bank {i}: independent address mismatch"
        assert dut.a_valid[i].value == 1, f"A bank {i}: independent read valid mismatch"
        assert dut.b_valid[i].value == 1, f"B bank {i}: independent read valid mismatch"

    dut._log.info("Reset During Stall Blocks Writes")
    await FallingEdge(dut.clk)
    dut.rst.value = 1
    dut.step.value = 0
    for i in range(4):
        dut.a_rd_en[i].value = 0
        dut.b_rd_en[i].value = 0
        dut.a_wr_en[i].value = 1
        dut.b_wr_en[i].value = 1
        dut.a_wr_addr[i].value = 0
        dut.b_wr_addr[i].value = 0
        dut.a_wr_data[i].value = 99
        dut.b_wr_data[i].value = -99
    await RisingEdge(dut.clk)
    await ReadOnly()
    for i in range(4):
        assert dut.a_valid[i].value == 0, f"A bank {i}: reset must override held valid"
        assert dut.b_valid[i].value == 0, f"B bank {i}: reset must override held valid"

    dut._log.info("Stored Operands Survive Reset")
    await FallingEdge(dut.clk)
    dut.rst.value = 0
    dut.step.value = 1
    for i in range(4):
        dut.a_wr_en[i].value = 0
        dut.b_wr_en[i].value = 0
        dut.a_rd_en[i].value = 1
        dut.b_rd_en[i].value = 1
        dut.a_rd_addr[i].value = 0
        dut.b_rd_addr[i].value = 0
    await RisingEdge(dut.clk)
    await ReadOnly()
    for i in range(4):
        assert dut.a_rd_data[i].value.to_signed() == 10 + i, f"A bank {i}: reset-time write corrupted address 0"
        assert dut.b_rd_data[i].value.to_signed() == 20 + i, f"B bank {i}: reset-time write corrupted address 0"
        assert dut.a_valid[i].value == 1, f"A bank {i}: post-reset read valid mismatch"
        assert dut.b_valid[i].value == 1, f"B bank {i}: post-reset read valid mismatch"
