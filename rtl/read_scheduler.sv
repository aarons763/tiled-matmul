module read_scheduler #(
    parameter int ROWS = 4,
    parameter int COLS = 4,
    parameter int DEPTH = 16,
    parameter int ADDR_WIDTH = (DEPTH > 1) ? $clog2(DEPTH) : 1,
    parameter int K_WIDTH = $clog2(DEPTH + 1)
) (
    input logic clk,
    input logic rst,
    input logic step,
    input logic start,
    input logic [0:K_WIDTH-1] k_len,
    output logic busy,
    output logic done,
    output logic a_rd_en [0:ROWS-1],
    output logic b_rd_en [0:COLS-1],
    output logic [ADDR_WIDTH-1:0] a_rd_addr [0:ROWS-1],
    output logic [ADDR_WIDTH-1:0] b_rd_addr [0:COLS-1],
    output logic array_step
);

    localparam int T_WIDTH =
    (DEPTH + ROWS + COLS - 1 > 1)
    ? $clog2(DEPTH + ROWS + COLS - 1) : 1;

    logic [K_WIDTH-1:0] k_length;
    logic [T_WIDTH-1:0] t;

    always_ff @(posedge clk) begin
        if (rst) begin
            busy <= 0;
            done <= 0;
            k_length <= 0;
            t <= 0;
        end
        else begin
            done <= 0;
            if (!busy && start) begin
                k_length <= k_len;
                t <= 0;
                busy <= 1;
            end
            else if (busy && step && t < k_length + ROWS + COLS - 2) begin
                t <= t + 1;
            end
            else if (busy && step && t == k_length + ROWS + COLS - 2) begin
                busy <= 0;
                done <= 1;
            end
        end
    end

    assign array_step = busy && step && !rst;

    always_comb begin
        for (int r = 0; r < ROWS; r++) begin
            a_rd_en [r] = 0;
            a_rd_addr [r] = 0;
            if (array_step && t >= r && t-r < k_length) begin
                a_rd_en[r] = 1;
                a_rd_addr[r] = t - r;
            end
        end
        for (int c = 0; c < COLS; c++) begin
            b_rd_en [c] = 0;
            b_rd_addr [c] = 0;
            if (array_step && t >= c && t-c < k_length) begin
                b_rd_en [c] = 1;
                b_rd_addr [c] = t-c;
            end
        end
    end
endmodule