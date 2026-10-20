module systolic_array #(
    parameter int ROWS = 4,
    parameter int COLS = 4
) (
    input logic clk,
    input logic rst,
    input logic step,
    input logic clear,
    input logic signed [7:0] a_in [0:ROWS-1],
    input logic signed [7:0] b_in [0:COLS-1],
    input logic a_valid_in [0:ROWS-1],
    input logic b_valid_in [0:COLS-1],
    output logic signed [31:0] acc [0:ROWS-1] [0:COLS-1]
);

    logic signed [7:0] a_links [0:ROWS-1][0:COLS];
    logic signed [7:0] b_links [0:ROWS][0:COLS-1];
    logic a_valid_links [0:ROWS-1][0:COLS];
    logic b_valid_links [0:ROWS][0:COLS-1];

    for (genvar i = 0; i < ROWS; i++) begin : connect_a
        assign a_links[i][0] = a_in[i];
        assign a_valid_links[i][0] = a_valid_in[i];
    end
    for (genvar j = 0; j < COLS; j++) begin : connect_b
        assign b_links[0][j] = b_in[j];
        assign b_valid_links[0][j] = b_valid_in[j];
    end

    for (genvar i = 0; i < ROWS; i++) begin : pe_rows
        for (genvar j = 0; j < COLS; j++) begin : pe_cols
            pe pe_inst (
                .clk(clk),
                .rst(rst),
                .step(step),
                .clear(clear),
                .a_in(a_links[i][j]),
                .b_in(b_links[i][j]),
                .a_valid_in(a_valid_links[i][j]),
                .b_valid_in(b_valid_links[i][j]),
                .a_out(a_links[i][j+1]),
                .b_out(b_links[i+1][j]),
                .a_valid_out(a_valid_links[i][j+1]),
                .b_valid_out(b_valid_links[i+1][j]),
                .acc(acc[i][j])
            );
        end
    end
endmodule
