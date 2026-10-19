import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge
from cocotb.triggers import FallingEdge
from cocotb.triggers import ReadOnly

from matmul_reference import matmul_reference


@cocotb.test()
async def test_buffered_array(dut):
    a = [[1, -2, 3], [0, 4, -1], [-3, 2, 1], [2, 0, -2]]
    b = [[2, 1, -1, 3], [-1, 3, 2, 0], [4, -2, 1, -1]]
    expected = matmul_reference(a, b)
    rows = len(a)
    cols = len(b[0])
    K = len(a[0])

    dut.clk.value = 0
    dut.rst.value = 1
    dut.step.value = 0
    dut.clear.value = 0
    for r in range(rows):
        dut.a_wr_en[r].value = 0
        dut.a_wr_addr[r].value = 0
        dut.a_wr_data[r].value = 0
        dut.a_rd_en[r].value = 0
        dut.a_rd_addr[r].value = 0
    for c in range(cols):
        dut.b_wr_en[c].value = 0
        dut.b_wr_addr[c].value = 0
        dut.b_wr_data[c].value = 0
        dut.b_rd_en[c].value = 0
        dut.b_rd_addr[c].value = 0

    clock = Clock(dut.clk, 10, unit="ns")
    clock.start(start_high=False)

    dut._log.info("Reset")
    await RisingEdge(dut.clk)
    await ReadOnly()
    for r in range(rows):
        for c in range(cols):
            assert dut.acc_outputs[r * cols + c].value.to_signed() == 0, (
                f"Reset: accumulator [{r}][{c}] must be zero"
            )

    dut._log.info("Load A Rows And B Columns While Paused")
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
        for r in range(rows):
            for c in range(cols):
                assert dut.acc_outputs[r * cols + c].value.to_signed() == 0, (
                    f"Load address {k}: accumulator [{r}][{c}] changed"
                )

    # Reuse the loaded operands after clearing, without resetting memory.
    for with_stalls in (False, True):
        dut._log.info(f"Compute With Stalls={with_stalls}")
        # One memory-read edge plus K + rows + cols - 2 array advances.
        enabled_edges = K + rows + cols - 1
        for t in range(enabled_edges):
            if with_stalls and t in (1, 5):
                held = []
                for r in range(rows):
                    for c in range(cols):
                        held.append(dut.acc_outputs[r * cols + c].value.to_signed())

                dut._log.info(f"Two-Edge Stall Before Request Step {t}")
                for stall_edge in range(2):
                    await FallingEdge(dut.clk)
                    dut.step.value = 0
                    for r in range(rows):
                        dut.a_rd_en[r].value = stall_edge
                        dut.a_rd_addr[r].value = (r + stall_edge) % K
                    for c in range(cols):
                        dut.b_rd_en[c].value = 1 - stall_edge
                        dut.b_rd_addr[c].value = (c + stall_edge) % K
                    await RisingEdge(dut.clk)
                    await ReadOnly()
                    for r in range(rows):
                        for c in range(cols):
                            actual = dut.acc_outputs[r * cols + c].value.to_signed()
                            assert actual == held[r * cols + c], (
                                f"Stall before step {t}, edge {stall_edge}: "
                                f"accumulator [{r}][{c}] changed to {actual}"
                            )

            await FallingEdge(dut.clk)
            dut.step.value = 1
            dut.clear.value = 0
            for r in range(rows):
                dut.a_wr_en[r].value = 0
                k = t - r
                dut.a_rd_en[r].value = int(0 <= k < K)
                dut.a_rd_addr[r].value = k if 0 <= k < K else 0
            for c in range(cols):
                dut.b_wr_en[c].value = 0
                k = t - c
                dut.b_rd_en[c].value = int(0 <= k < K)
                dut.b_rd_addr[c].value = k if 0 <= k < K else 0
            await RisingEdge(dut.clk)
            await ReadOnly()

            if t == 0:
                for r in range(rows):
                    for c in range(cols):
                        actual = dut.acc_outputs[r * cols + c].value.to_signed()
                        assert actual == 0, (
                            f"First read edge: [{r}][{c}] computed too early: {actual}"
                        )
            if t == 1:
                for r in range(rows):
                    for c in range(cols):
                        first = a[0][0] * b[0][0] if r == 0 and c == 0 else 0
                        actual = dut.acc_outputs[r * cols + c].value.to_signed()
                        assert actual == first, (
                            f"First MAC edge: [{r}][{c}] expected {first}, got {actual}"
                        )
            if t == enabled_edges - 2:
                # This workload's bottom-right final product is nonzero.
                actual = dut.acc_outputs[rows * cols - 1].value.to_signed()
                before_last = expected[-1][-1] - a[-1][-1] * b[-1][-1]
                assert actual == before_last, (
                    f"Before final edge: bottom-right expected {before_last}, got {actual}"
                )

        dut._log.info("Check All Final Results")
        for r in range(rows):
            for c in range(cols):
                actual = dut.acc_outputs[r * cols + c].value.to_signed()
                assert actual == expected[r][c], (
                    f"Stalls={with_stalls}: [{r}][{c}] "
                    f"expected {expected[r][c]}, got {actual}"
                )

        dut._log.info("Drain With Invalid Requests And Hold Results")
        for hold_edge in range(2):
            await FallingEdge(dut.clk)
            for r in range(rows):
                dut.a_rd_en[r].value = 0
            for c in range(cols):
                dut.b_rd_en[c].value = 0
            await RisingEdge(dut.clk)
            await ReadOnly()
            for r in range(rows):
                for c in range(cols):
                    actual = dut.acc_outputs[r * cols + c].value.to_signed()
                    assert actual == expected[r][c], (
                        f"Hold edge {hold_edge}: [{r}][{c}] "
                        f"expected {expected[r][c]}, got {actual}"
                    )

        dut._log.info("Clear After Drain")
        await FallingEdge(dut.clk)
        dut.clear.value = 1
        await RisingEdge(dut.clk)
        await ReadOnly()
        for r in range(rows):
            for c in range(cols):
                assert dut.acc_outputs[r * cols + c].value.to_signed() == 0, (
                    f"Clear: accumulator [{r}][{c}] must be zero"
                )
