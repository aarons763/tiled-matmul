module matmul_host #(
    parameter int ROWS = 4,
    parameter int COLS = 4,
    parameter int DEPTH = 16,
    parameter int ADDR_WIDTH = (DEPTH > 1) ? $clog2(DEPTH) : 1,
    parameter int K_WIDTH = $clog2(DEPTH + 1),
    parameter int DIM_WIDTH = 16,
    parameter int ROW_COUNT_WIDTH = (ROWS > 1) ? $clog2(ROWS + 1) : 1,
    parameter int COL_COUNT_WIDTH = (COLS > 1) ? $clog2(COLS + 1) : 1,
    parameter int BANK_WIDTH = ((ROWS > COLS ? ROWS : COLS) > 1)
        ? $clog2(ROWS > COLS ? ROWS : COLS) : 1
) (
    input logic clk,
    input logic rst,
    input logic step,
    input logic cmd_valid,
    output wire cmd_ready,
    input logic [DIM_WIDTH-1:0] cmd_m,
    input logic [DIM_WIDTH-1:0] cmd_n,
    input logic [16:0] cmd_k,
    output wire busy,
    output wire done,
    output logic error,
    output wire load_req,
    output wire [DIM_WIDTH-1:0] tile_row,
    output wire [DIM_WIDTH-1:0] tile_col,
    output wire [ROW_COUNT_WIDTH-1:0] valid_rows,
    output wire [COL_COUNT_WIDTH-1:0] valid_cols,
    output wire [16:0] k_offset,
    output wire [K_WIDTH-1:0] chunk_len,
    input logic wr_valid,
    output wire wr_ready,
    input logic wr_is_b,
    input logic [BANK_WIDTH-1:0] wr_bank,
    input logic [ADDR_WIDTH-1:0] wr_addr,
    input logic signed [7:0] wr_data,
    input logic load_complete_valid,
    output wire load_complete_ready,
    output wire result_valid,
    input logic result_ready,
    output logic signed [31:0] result_data,
    output logic [DIM_WIDTH-1:0] result_row,
    output logic [DIM_WIDTH-1:0] result_col
);

    wire command_legal;
    wire core_start;
    wire write_accept;
    wire core_load_done;
    wire core_result_valid;
    wire core_result_ready;
    wire last_result;
    wire a_wr_en [0:ROWS-1], b_wr_en [0:COLS-1];
    wire [ADDR_WIDTH-1:0] a_wr_addr [0:ROWS-1], b_wr_addr [0:COLS-1];
    wire signed [7:0] a_wr_data [0:ROWS-1], b_wr_data [0:COLS-1];
    wire signed [31:0] acc_outputs [0:ROWS-1][0:COLS-1];
    logic [ROW_COUNT_WIDTH-1:0] read_row;
    logic [COL_COUNT_WIDTH-1:0] read_col;

    assign cmd_ready = !busy && !rst;
    assign command_legal = (cmd_m != 0) && (cmd_n != 0) && (cmd_k != 0);
    assign core_start = cmd_valid && cmd_ready && command_legal;

    // One operand per accepted write. Invalid destinations are not accepted.
    assign wr_ready = load_req && !rst && (wr_addr < chunk_len)
        && (wr_is_b ? (wr_bank < COLS) : (wr_bank < ROWS));
    assign write_accept = wr_valid && wr_ready;
    // Writes take priority; completion must follow the final accepted write.
    assign load_complete_ready = load_req && !rst && !wr_valid;
    assign core_load_done = load_complete_valid && load_complete_ready;

    assign result_valid = core_result_valid && !rst;
    assign last_result = (read_row == valid_rows - 1)
        && (read_col == valid_cols - 1);
    assign core_result_ready = result_valid && result_ready && last_result;

    genvar i, j;
    generate
        for (i = 0; i < ROWS; i++) begin : connect_a_writes
            assign a_wr_en[i] = write_accept && !wr_is_b && (wr_bank == i);
            assign a_wr_addr[i] = wr_addr;
            assign a_wr_data[i] = wr_data;
        end
        for (j = 0; j < COLS; j++) begin : connect_b_writes
            assign b_wr_en[j] = write_accept && wr_is_b && (wr_bank == j);
            assign b_wr_addr[j] = wr_addr;
            assign b_wr_data[j] = wr_data;
        end
    endgenerate

    always_comb begin
        result_data = 0;
        result_row = 0;
        result_col = 0;
        if (result_valid) begin
            result_data = acc_outputs[read_row][read_col];
            result_row = tile_row + read_row;
            result_col = tile_col + read_col;
        end
    end

    always_ff @(posedge clk) begin
        if (rst) begin
            error <= 0;
            read_row <= 0;
            read_col <= 0;
        end
        else begin
            error <= cmd_valid && cmd_ready && !command_legal;

            if (!core_result_valid) begin
                read_row <= 0;
                read_col <= 0;
            end
            else if (result_ready) begin
                if (last_result) begin
                    read_row <= 0;
                    read_col <= 0;
                end
                else if (read_col == valid_cols - 1) begin
                    read_col <= 0;
                    read_row <= read_row + 1;
                end
                else begin
                    read_col <= read_col + 1;
                end
            end
        end
    end

    tiled_matmul #(
        .ROWS (ROWS),
        .COLS (COLS),
        .DEPTH (DEPTH),
        .ADDR_WIDTH (ADDR_WIDTH),
        .K_WIDTH (K_WIDTH),
        .DIM_WIDTH (DIM_WIDTH),
        .ROW_COUNT_WIDTH (ROW_COUNT_WIDTH),
        .COL_COUNT_WIDTH (COL_COUNT_WIDTH)
    ) tiled_matmul_inst (
        .clk (clk),
        .rst (rst),
        .start (core_start),
        .step (step),
        .m_len (cmd_m),
        .n_len (cmd_n),
        .total_k (cmd_k),
        .load_done (core_load_done),
        .result_ready (core_result_ready),
        .a_wr_en (a_wr_en),
        .b_wr_en (b_wr_en),
        .a_wr_addr (a_wr_addr),
        .b_wr_addr (b_wr_addr),
        .a_wr_data (a_wr_data),
        .b_wr_data (b_wr_data),
        .busy (busy),
        .done (done),
        .load_req (load_req),
        .k_offset (k_offset),
        .chunk_len (chunk_len),
        .tile_row (tile_row),
        .tile_col (tile_col),
        .valid_rows (valid_rows),
        .valid_cols (valid_cols),
        .result_valid (core_result_valid),
        .acc_outputs (acc_outputs)
    );

endmodule
