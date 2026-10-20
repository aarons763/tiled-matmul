module operand_bank #(
    parameter int DEPTH = 16,
    parameter int ADDR_WIDTH = (DEPTH > 1) ? $clog2(DEPTH) : 1
) (
    input logic clk,
    input logic wr_en,
    input logic [ADDR_WIDTH-1:0] wr_addr,
    input logic signed [7:0] wr_data,
    input logic rd_en,
    input logic [ADDR_WIDTH-1:0] rd_addr,
    output logic signed [7:0] rd_data
);

    logic signed [7:0] mem [0:DEPTH-1];

    always_ff @(posedge clk) begin
        if (wr_en) begin
            mem[wr_addr] <= wr_data;
        end
        if (rd_en) begin
            rd_data <= mem[rd_addr];
        end
    end
endmodule
