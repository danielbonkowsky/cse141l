// data memory module
module dat_mem(
  input       clk,
              wen,
  input [7:0] addr,
              dat_in,
  output[7:0] dat_out);

  logic[7:0] core[256];

  always_ff @(posedge clk)
	if(wen) core[addr] <= dat_in;

  assign dat_out = core[addr];

endmodule