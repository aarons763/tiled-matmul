module tiled_matmul #(
    parameter int DOUBLE_BUFFER = 0,
    parameter int ROWS = 4,
    parameter int COLS = 4,
    parameter int DEPTH = 16,
    parameter int ADDR_WIDTH = (DEPTH > 1) ? $clog2(DEPTH) : 1,
    parameter int K_WIDTH = $clog2(DEPTH + 1),
    parameter int DIM_WIDTH = 16,
    parameter int ROW_COUNT_WIDTH = (ROWS > 1) ? $clog2(ROWS + 1) : 1,
    parameter int COL_COUNT_WIDTH = (COLS > 1) ? $clog2(COLS + 1) : 1
) (
    input logic clk,
    input logic rst,
    input logic start,
    input logic step,
    input logic [DIM_WIDTH-1:0] m_len,
    input logic [DIM_WIDTH-1:0] n_len,
    input logic [16:0] total_k,
    input logic load_done,
    input logic result_ready,
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
    output wire [DIM_WIDTH-1:0] tile_row,
    output wire [DIM_WIDTH-1:0] tile_col,
    output wire [ROW_COUNT_WIDTH-1:0] valid_rows,
    output wire [COL_COUNT_WIDTH-1:0] valid_cols,
    output wire result_valid,
    output wire signed [31:0] acc_outputs [0:ROWS-1][0:COLS-1]
);

    logic [16:0] k_total;
    wire engine_start;
    wire engine_done;
    // Completion drives the parent controller; child busy is not needed.
    wire unused_engine_busy;

    // All output tiles use the K length accepted with the matrix command.
    always_ff @(posedge clk) begin
        if (rst) begin
            k_total <= 0;
        end
        else if (start && !busy) begin
            k_total <= total_k;
        end
    end

    output_tile_controller #(
        .ROWS (ROWS),
        .COLS (COLS),
        .DIM_WIDTH (DIM_WIDTH),
        .ROW_COUNT_WIDTH (ROW_COUNT_WIDTH),
        .COL_COUNT_WIDTH (COL_COUNT_WIDTH)
    ) output_tile_controller_inst (
        .clk (clk),
        .rst (rst),
        .start (start),
        .m_len (m_len),
        .n_len (n_len),
        .engine_done (engine_done),
        .result_ready (result_ready),
        .busy (busy),
        .done (done),
        .engine_start (engine_start),
        .tile_row (tile_row),
        .tile_col (tile_col),
        .valid_rows (valid_rows),
        .valid_cols (valid_cols),
        .result_valid (result_valid)
    );

    generate
        if (DOUBLE_BUFFER != 0) begin : double_buffered
            double_buffered_tile_engine #(
                .ROWS (ROWS),
                .COLS (COLS),
                .DEPTH (DEPTH),
                .ADDR_WIDTH (ADDR_WIDTH),
                .K_WIDTH (K_WIDTH)
            ) engine_inst (
                .clk (clk),
                .rst (rst),
                .step (step),
                .start (engine_start),
                .total_k (k_total),
                .load_done (load_done),
                .a_wr_en (a_wr_en),
                .b_wr_en (b_wr_en),
                .a_wr_addr (a_wr_addr),
                .b_wr_addr (b_wr_addr),
                .a_wr_data (a_wr_data),
                .b_wr_data (b_wr_data),
                .busy (unused_engine_busy),
                .done (engine_done),
                .load_req (load_req),
                .k_offset (k_offset),
                .chunk_len (chunk_len),
                .acc_outputs (acc_outputs)
            );
        end
        else begin : single_buffered
            chunked_tile_engine #(
                .ROWS (ROWS),
                .COLS (COLS),
                .DEPTH (DEPTH),
                .ADDR_WIDTH (ADDR_WIDTH),
                .K_WIDTH (K_WIDTH)
            ) chunked_tile_engine_inst (
                .clk (clk),
                .rst (rst),
                .step (step),
                .start (engine_start),
                .total_k (k_total),
                .load_done (load_done),
                .a_wr_en (a_wr_en),
                .b_wr_en (b_wr_en),
                .a_wr_addr (a_wr_addr),
                .b_wr_addr (b_wr_addr),
                .a_wr_data (a_wr_data),
                .b_wr_data (b_wr_data),
                .busy (unused_engine_busy),
                .done (engine_done),
                .load_req (load_req),
                .k_offset (k_offset),
                .chunk_len (chunk_len),
                .acc_outputs (acc_outputs)
            );
        end
    endgenerate

endmodule
