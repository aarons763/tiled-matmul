module chunked_tile_engine #(
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
    input logic [16:0] total_k,
    input logic load_done,
    input logic a_wr_en [0:ROWS-1],
    input logic b_wr_en [0:COLS-1],
    input logic [ADDR_WIDTH-1:0] a_wr_addr [0:ROWS-1],
    input logic [ADDR_WIDTH-1:0] b_wr_addr [0:COLS-1],
    input logic signed [7:0] a_wr_data [0:ROWS-1],
    input logic signed [7:0] b_wr_data [0:COLS-1],
    output wire busy,
    output wire done,
    output wire load_req,
    output wire [16:0] k_offset,
    output wire [K_WIDTH-1:0] chunk_len,
    output wire signed [31:0] acc_outputs [0:ROWS-1][0:COLS-1]
);

    wire engine_start;
    wire engine_clear;
    wire engine_done;
    // Completion drives the parent controller; child busy is not needed.
    wire unused_engine_busy;
    wire a_wr_en_gated [0:ROWS-1], b_wr_en_gated [0:COLS-1];

    genvar i, j;
    generate
        for (i = 0; i < ROWS; i++) begin : gate_a_writes
            assign a_wr_en_gated[i] = a_wr_en[i] && load_req && !rst;
        end
        for (j = 0; j < COLS; j++) begin : gate_b_writes
            assign b_wr_en_gated[j] = b_wr_en[j] && load_req && !rst;
        end
    endgenerate

    chunk_controller #(
        .DEPTH (DEPTH),
        .K_WIDTH (K_WIDTH)
    ) chunk_controller_inst (
        .clk (clk),
        .rst (rst),
        .start (start),
        .total_k (total_k),
        .load_done (load_done),
        .engine_done (engine_done),
        .busy (busy),
        .done (done),
        .load_req (load_req),
        .k_offset (k_offset),
        .chunk_len (chunk_len),
        .engine_start (engine_start),
        .engine_clear (engine_clear)
    );

    tile_engine #(
        .ROWS (ROWS),
        .COLS (COLS),
        .DEPTH (DEPTH),
        .ADDR_WIDTH (ADDR_WIDTH),
        .K_WIDTH (K_WIDTH)
    ) tile_engine_inst (
        .clk (clk),
        .rst (rst),
        .step (step),
        .start (engine_start),
        .clear (engine_clear),
        .k_len (chunk_len),
        .a_wr_en (a_wr_en_gated),
        .b_wr_en (b_wr_en_gated),
        .a_wr_addr (a_wr_addr),
        .b_wr_addr (b_wr_addr),
        .a_wr_data (a_wr_data),
        .b_wr_data (b_wr_data),
        .busy (unused_engine_busy),
        .done (engine_done),
        .acc_outputs (acc_outputs)
    );

endmodule
