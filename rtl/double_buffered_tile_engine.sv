module double_buffered_tile_engine #(
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

    wire engine_start, engine_clear, engine_done;
    wire read_bank, write_bank;
    wire [K_WIDTH-1:0] engine_k_len;
    wire scheduler_step, datapath_step;
    wire unused_scheduler_busy;
    wire a_rd_en [0:ROWS-1], b_rd_en [0:COLS-1];
    wire [ADDR_WIDTH-1:0] a_rd_addr [0:ROWS-1], b_rd_addr [0:COLS-1];
    wire signed [7:0] a_data [0:1][0:ROWS-1], b_data [0:1][0:COLS-1];
    wire a_valid [0:1][0:ROWS-1], b_valid [0:1][0:COLS-1];
    wire signed [7:0] selected_a [0:ROWS-1], selected_b [0:COLS-1];
    wire selected_a_valid [0:ROWS-1], selected_b_valid [0:COLS-1];

    assign datapath_step = scheduler_step || engine_clear;

    double_buffer_controller #(
        .DEPTH (DEPTH),
        .K_WIDTH (K_WIDTH)
    ) controller_inst (
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
        .engine_clear (engine_clear),
        .engine_k_len (engine_k_len),
        .read_bank (read_bank),
        .write_bank (write_bank)
    );

    read_scheduler #(
        .ROWS (ROWS),
        .COLS (COLS),
        .DEPTH (DEPTH),
        .ADDR_WIDTH (ADDR_WIDTH),
        .K_WIDTH (K_WIDTH)
    ) scheduler_inst (
        .clk (clk),
        .rst (rst),
        .step (step),
        .start (engine_start),
        .k_len (engine_k_len),
        .busy (unused_scheduler_busy),
        .done (engine_done),
        .a_rd_en (a_rd_en),
        .b_rd_en (b_rd_en),
        .a_rd_addr (a_rd_addr),
        .b_rd_addr (b_rd_addr),
        .array_step (scheduler_step)
    );

    genvar bank, r, c;
    generate
        for (bank = 0; bank < 2; bank++) begin : buffers
            wire signed [7:0] bank_a_data [0:ROWS-1], bank_b_data [0:COLS-1];
            wire bank_a_valid [0:ROWS-1], bank_b_valid [0:COLS-1];
            wire bank_a_wr_en [0:ROWS-1], bank_b_wr_en [0:COLS-1];
            wire bank_a_rd_en [0:ROWS-1], bank_b_rd_en [0:COLS-1];
            for (r = 0; r < ROWS; r++) begin : a_controls
                assign a_data[bank][r] = bank_a_data[r];
                assign a_valid[bank][r] = bank_a_valid[r];
                assign bank_a_wr_en[r] = a_wr_en[r] && load_req
                    && (write_bank == 1'(bank));
                assign bank_a_rd_en[r] = a_rd_en[r] && (read_bank == 1'(bank));
            end
            for (c = 0; c < COLS; c++) begin : b_controls
                assign b_data[bank][c] = bank_b_data[c];
                assign b_valid[bank][c] = bank_b_valid[c];
                assign bank_b_wr_en[c] = b_wr_en[c] && load_req
                    && (write_bank == 1'(bank));
                assign bank_b_rd_en[c] = b_rd_en[c] && (read_bank == 1'(bank));
            end

            // Both valid pipelines advance together. Unselected reads are
            // invalid, so a drained bank cannot replay stale valid operands.
            operand_buffer #(
                .ROWS (ROWS),
                .COLS (COLS),
                .DEPTH (DEPTH),
                .ADDR_WIDTH (ADDR_WIDTH)
            ) buffer_inst (
                .clk (clk),
                .rst (rst),
                .step (datapath_step),
                .a_wr_en (bank_a_wr_en),
                .b_wr_en (bank_b_wr_en),
                .a_wr_addr (a_wr_addr),
                .b_wr_addr (b_wr_addr),
                .a_wr_data (a_wr_data),
                .b_wr_data (b_wr_data),
                .a_rd_en (bank_a_rd_en),
                .b_rd_en (bank_b_rd_en),
                .a_rd_addr (a_rd_addr),
                .b_rd_addr (b_rd_addr),
                .a_rd_data (bank_a_data),
                .b_rd_data (bank_b_data),
                .a_valid (bank_a_valid),
                .b_valid (bank_b_valid)
            );
        end

        for (r = 0; r < ROWS; r++) begin : select_a
            assign selected_a[r] = read_bank ? a_data[1][r] : a_data[0][r];
            assign selected_a_valid[r] = read_bank ? a_valid[1][r] : a_valid[0][r];
        end
        for (c = 0; c < COLS; c++) begin : select_b
            assign selected_b[c] = read_bank ? b_data[1][c] : b_data[0][c];
            assign selected_b_valid[c] = read_bank ? b_valid[1][c] : b_valid[0][c];
        end
    endgenerate

    systolic_array #(
        .ROWS (ROWS),
        .COLS (COLS)
    ) array_inst (
        .clk (clk),
        .rst (rst),
        .step (datapath_step),
        .clear (engine_clear),
        .a_in (selected_a),
        .b_in (selected_b),
        .a_valid_in (selected_a_valid),
        .b_valid_in (selected_b_valid),
        .acc (acc_outputs)
    );
endmodule
