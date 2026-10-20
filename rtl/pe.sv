module pe (
    input logic clk,
    input logic rst,
    input logic step,
    input logic clear,
    input logic signed [7:0] a_in,
    input logic signed [7:0] b_in,
    input logic a_valid_in,
    input logic b_valid_in,
    output logic signed [7:0] a_out,
    output logic signed [7:0] b_out,
    output logic a_valid_out,
    output logic b_valid_out,
    output logic signed [31:0] acc
);

    logic signed [15:0] intermediate_product;
    logic signed [31:0] extended_product;
    assign intermediate_product = a_in * b_in;
    assign extended_product = {{16{intermediate_product[15]}}, intermediate_product};

    always_ff @(posedge clk) begin
        if (rst) begin
            a_out <= 0;
            b_out <= 0;
            a_valid_out <= 0;
            b_valid_out <= 0;
            acc <= 0;
        end else if (step) begin
            a_out <= a_in;
            b_out <= b_in;
            a_valid_out <= a_valid_in;
            b_valid_out <= b_valid_in;
            if (clear) begin
                acc <= 0;
            end else if (a_valid_in && b_valid_in) begin
                acc <= acc + extended_product;
            end
        end
    end
endmodule
