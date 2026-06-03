module ProgCtr(
  input             Clk,
                    Reset,
                    Jen,
  input       [9:0] Jump,
  output logic[9:0] PC
);

  always_ff @(posedge Clk)
    if (Reset)    PC <= 'b0;
    else if (Jen) PC <= Jump;
    else          PC <= PC + 10'd1;

endmodule
