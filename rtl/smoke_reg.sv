module smoke_reg (
    input wire clk,
    input wire rst,
    input wire [7:0] d,
    output reg [7:0] q
);

  always @(posedge clk) begin
    if (rst) begin
      q <= 0;
    end else begin
      q <= d;
    end
  end
endmodule
