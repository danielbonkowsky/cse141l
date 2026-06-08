module DMem(
  input             Clk,
                    Wen,
  input[7:0]        WDat,
                    Addr,
  output logic[7:0] Rdat
);

  logic[7:0] core[256];

  always @(posedge Clk)
    if (Wen) core[Addr] <= WDat;

  assign Rdat = core[Addr];

endmodule
