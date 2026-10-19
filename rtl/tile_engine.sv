module tile_engine #(
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
    input logic clear,
    input logic [K_WIDTH-1:0] k_len,
    input logic a_wr_en [0:ROWS-1],
    input logic b_wr_en [0:COLS-1],
    input logic [ADDR_WIDTH-1:0] a_wr_addr [0:ROWS-1],
    input logic [ADDR_WIDTH-1:0] b_wr_addr [0:COLS-1],
    input logic signed [7:0] a_wr_data [0:ROWS-1],
    input logic signed [7:0] b_wr_data [0:COLS-1],
    output wire busy,
    output wire done,
    output wire signed [31:0] acc_outputs [0:ROWS-1][0:COLS-1]
);

    wire scheduler_step;
    wire clear_accept;
    wire datapath_step;
    wire a_rd_en [0:ROWS-1], b_rd_en [0:COLS-1];
    wire [ADDR_WIDTH-1:0] a_rd_addr [0:ROWS-1], b_rd_addr [0:COLS-1];
    wire a_wr_en_gated [0:ROWS-1], b_wr_en_gated [0:COLS-1];

    // Idle clear advances the datapath even when the external step is low.
    assign clear_accept = clear && !busy && !rst;
    assign datapath_step = scheduler_step || clear_accept;

    genvar i, j;
    generate
        for (i = 0; i < ROWS; i++) begin : gate_a_writes
            assign a_wr_en_gated[i] = a_wr_en[i] && !busy && !rst;
        end
        for (j = 0; j < COLS; j++) begin : gate_b_writes
            assign b_wr_en_gated[j] = b_wr_en[j] && !busy && !rst;
        end
    endgenerate

    read_scheduler #(
        .ROWS (ROWS),
        .COLS (COLS),
        .DEPTH (DEPTH),
        .ADDR_WIDTH (ADDR_WIDTH),
        .K_WIDTH (K_WIDTH)
    ) read_scheduler_inst (
        .clk (clk),
        .rst (rst),
        .step (step),
        .start (start && !clear),
        .k_len (k_len),
        .busy (busy),
        .done (done),
        .a_rd_en (a_rd_en),
        .b_rd_en (b_rd_en),
        .a_rd_addr (a_rd_addr),
        .b_rd_addr (b_rd_addr),
        .array_step (scheduler_step)
    );

    buffered_array #(
        .ROWS (ROWS),
        .COLS (COLS),
        .DEPTH (DEPTH),
        .ADDR_WIDTH (ADDR_WIDTH)
    ) buffered_array_inst (
        .clk (clk),
        .rst (rst),
        .step (datapath_step),
        .clear (clear_accept),
        .a_wr_en (a_wr_en_gated),
        .b_wr_en (b_wr_en_gated),
        .a_wr_addr (a_wr_addr),
        .b_wr_addr (b_wr_addr),
        .a_wr_data (a_wr_data),
        .b_wr_data (b_wr_data),
        .a_rd_en (a_rd_en),
        .b_rd_en (b_rd_en),
        .a_rd_addr (a_rd_addr),
        .b_rd_addr (b_rd_addr),
        .acc_outputs (acc_outputs)
    );

endmodule
