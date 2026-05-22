module DMem(
  input             Clk,
                    Wen,
  input[7:0]        WDat,
                    Addr,
  output logic[7:0] Rdat
);

  logic[7:0] Core[256];

  always_ff @(posedge Clk)
    if (Wen) Core[Addr] <= WDat;

  assign Rdat = Core[Addr];

endmodule
