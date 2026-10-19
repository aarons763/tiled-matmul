module buffered_array #(
    parameter int ROWS = 4,
    parameter int COLS = 4,
    parameter int DEPTH = 16,
    parameter int ADDR_WIDTH = (DEPTH > 1) ? $clog2(DEPTH) : 1
) (
    input logic clk,
    input logic rst,
    input logic step,
    input logic clear,
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
    output wire signed [31:0] acc_outputs [0:ROWS-1][0:COLS-1]
);

    wire signed [7:0] a_rd_data [0:ROWS-1], b_rd_data [0:COLS-1];
    wire a_valid [0:ROWS-1], b_valid [0:COLS-1];

    operand_buffer #(
        .ROWS (ROWS),
        .COLS (COLS),
        .DEPTH (DEPTH),
        .ADDR_WIDTH (ADDR_WIDTH)
    ) operand_buffer_inst (
        .clk (clk),
        .rst (rst),
        .step (step),
        .a_wr_en (a_wr_en),
        .b_wr_en (b_wr_en),
        .a_wr_addr (a_wr_addr),
        .b_wr_addr (b_wr_addr),
        .a_wr_data (a_wr_data),
        .b_wr_data (b_wr_data),
        .a_rd_en (a_rd_en),
        .b_rd_en (b_rd_en),
        .a_rd_addr (a_rd_addr),
        .b_rd_addr (b_rd_addr),
        .a_rd_data (a_rd_data),
        .b_rd_data (b_rd_data),
        .a_valid (a_valid),
        .b_valid (b_valid)
    );

    systolic_array #(
        .ROWS (ROWS),
        .COLS (COLS)
    ) systolic_array_inst (
        .clk (clk),
        .rst (rst),
        .step (step),
        .clear (clear),
        .a_in (a_rd_data),
        .b_in (b_rd_data),
        .a_valid_in (a_valid),
        .b_valid_in (b_valid),
        .acc (acc_outputs)
    );
endmodule