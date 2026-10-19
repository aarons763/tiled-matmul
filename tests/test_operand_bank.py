import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge
from cocotb.triggers import FallingEdge
from cocotb.triggers import ReadOnly

@cocotb.test()
async def test_operand_bank(dut):

    dut.clk.value = 0
    dut.rd_en.value = 0
    dut.rd_addr.value = 0
    dut.wr_en.value = 0
    dut.wr_addr.value = 0
    dut.wr_data.value = 0

    clock = Clock(dut.clk, 10, unit="ns")  # Create a clock with a period of 10 ns
    clock.start(start_high=False)

    dut._log.info("Starting test_operand_bank")

    dut._log.info("Load")
    await FallingEdge(dut.clk)
    dut.wr_en.value = 1
    dut.wr_addr.value = 0
    dut.wr_data.value = -128
    await RisingEdge(dut.clk)
    await ReadOnly()
    await FallingEdge(dut.clk)
    dut.wr_addr.value = 7
    dut.wr_data.value = 42
    await RisingEdge(dut.clk)
    await ReadOnly()
    await FallingEdge(dut.clk)
    dut.wr_addr.value = 15
    dut.wr_data.value = 127
    await RisingEdge(dut.clk)
    await ReadOnly()

    dut._log.info("Readback")
    await FallingEdge(dut.clk)
    dut.wr_en.value = 0
    dut.rd_en.value = 1
    dut.rd_addr.value = 0
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert dut.rd_data.value.to_signed() == -128, f"Address {dut.rd_addr.value} should be -128, but got {dut.rd_data.value.to_signed()}"
    await FallingEdge(dut.clk)
    dut.rd_addr.value = 7
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert dut.rd_data.value.to_signed() == 42, f"Address {dut.rd_addr.value} should be 42, but got {dut.rd_data.value.to_signed()}"
    await FallingEdge(dut.clk)
    dut.rd_addr.value = 15
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert dut.rd_data.value.to_signed() == 127, f"Address {dut.rd_addr.value} should be 127, but got {dut.rd_data.value.to_signed()}"

    dut._log.info("Synchronous Timing")
    await FallingEdge(dut.clk)
    dut.rd_addr.value = 0
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert dut.rd_data.value.to_signed() == -128, f"Address {dut.rd_addr.value} should be -128, but got {dut.rd_data.value.to_signed()}"
    await FallingEdge(dut.clk)
    dut.rd_addr.value = 15
    await ReadOnly()
    assert dut.rd_data.value.to_signed() == -128, f"Address {dut.rd_addr.value} should be -128, but got {dut.rd_data.value.to_signed()}"
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert dut.rd_data.value.to_signed() == 127, f"Address {dut.rd_addr.value} should be 127, but got {dut.rd_data.value.to_signed()}"

    dut._log.info("Read Disabled")
    await FallingEdge(dut.clk)
    dut.rd_en.value = 0
    dut.rd_addr.value = 0
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert dut.rd_data.value.to_signed() == 127, f"Address {dut.rd_addr.value} should be 127, but got {dut.rd_data.value.to_signed()}"
    await FallingEdge(dut.clk)
    dut.rd_addr.value = 7
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert dut.rd_data.value.to_signed() == 127, f"Address {dut.rd_addr.value} should be 127, but got {dut.rd_data.value.to_signed()}"

    dut._log.info("Write Disabled")
    await FallingEdge(dut.clk)
    dut.wr_addr.value = 7
    dut.wr_data.value = -5
    await RisingEdge(dut.clk)
    await ReadOnly()
    await FallingEdge(dut.clk)
    dut.rd_en.value = 1
    dut.rd_addr.value = 7
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert dut.rd_data.value.to_signed() == 42, f"Address {dut.rd_addr.value} should be 42, but got {dut.rd_data.value.to_signed()}"

    dut._log.info("Overwrite")
    await FallingEdge(dut.clk)
    dut.wr_en.value = 1
    dut.rd_en.value = 0
    dut.wr_addr.value = 7
    dut.wr_data.value = -5
    await RisingEdge(dut.clk)
    await ReadOnly()
    await FallingEdge(dut.clk)
    dut.wr_en.value = 0
    dut.rd_en.value = 1
    dut.rd_addr.value = 7
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert dut.rd_data.value.to_signed() == -5, f"Address {dut.rd_addr.value} should be -5, but got {dut.rd_data.value.to_signed()}"

    dut._log.info("Neighbour Preservation")
    await FallingEdge(dut.clk)
    dut.rd_addr.value = 0
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert dut.rd_data.value.to_signed() == -128, f"Address {dut.rd_addr.value} should be -128, but got {dut.rd_data.value.to_signed()}"
    await FallingEdge(dut.clk)
    dut.rd_addr.value = 15
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert dut.rd_data.value.to_signed() == 127, f"Address {dut.rd_addr.value} should be 127, but got {dut.rd_data.value.to_signed()}"