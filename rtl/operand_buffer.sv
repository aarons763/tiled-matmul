module operand_buffer #(
    parameter int ROWS = 4,
    parameter int COLS = 4,
    parameter int DEPTH = 16,
    parameter int ADDR_WIDTH = (DEPTH > 1) ? $clog2(DEPTH) : 1
) (
    input logic clk,
    input logic rst,
    input logic step,
    input logic a_wr_en [0:ROWS-1],
    input logic b_wr_en [0:COLS-1],
    input logic [ADDR_WIDTH-1:0] a_wr_addr [0:ROWS-1],
    input logic [ADDR_WIDTH-1:0] b_wr_addr [0:COLS-1],
    input logic signed [7:0] a_wr_data [0:ROWS-1],
    input logic signed [7:0] b_wr_data [0:COLS-1],
    input logic a_rd_en [0:ROWS-1],
    input logic b_rd_en [0:COLS-1],
    input logic [ADDR_WIDTH-1:0] a_rd_addr [0:ROWS-1],
    input logic [ADDR_WIDTH-1:0] b_rd_addr [0:COLS-1],
    output logic signed [7:0] a_rd_data [0:ROWS-1],
    output logic signed [7:0] b_rd_data [0:COLS-1],
    output logic a_valid [0:ROWS-1],
    output logic b_valid [0:COLS-1]
);

    genvar i, j;

    generate
        for (i = 0; i < ROWS; i++) begin : gen_operand_a_banks
            operand_bank #(
                .DEPTH (DEPTH),
                .ADDR_WIDTH (ADDR_WIDTH)
            ) a_bank_inst (
                .clk (clk),
                .wr_en (a_wr_en [i] && !rst),
                .wr_addr (a_wr_addr [i]),
                .wr_data (a_wr_data [i]),
                .rd_en (a_rd_en [i] && step && !rst),
                .rd_addr (a_rd_addr [i]),
                .rd_data(a_rd_data[i])
            );

            always_ff @(posedge clk) begin
                if (rst) begin
                    a_valid [i] <= 0;
                end
                else if (step) begin
                    a_valid [i] <= a_rd_en [i];
                end
            end
        end

        for (j = 0; j < COLS; j++) begin : gen_operand_b_banks
            operand_bank #(
                .DEPTH (DEPTH),
                .ADDR_WIDTH (ADDR_WIDTH)
            ) b_bank_inst (
                .clk (clk),
                .wr_en (b_wr_en [j] && !rst),
                .wr_addr (b_wr_addr [j]),
                .wr_data (b_wr_data [j]),
                .rd_en (b_rd_en [j]  && step && !rst),
                .rd_addr (b_rd_addr [j]),
                .rd_data(b_rd_data[j])
            );

            always_ff @(posedge clk) begin
                if (rst) begin
                    b_valid [j] <= 0;
                end
                else if (step) begin
                    b_valid [j] <= b_rd_en [j];
                end
            end
        end
    endgenerate
endmodule
