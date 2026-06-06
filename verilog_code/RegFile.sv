module RegFile(
  input        Clk,
               Wen,
  input  [3:0] Ra,       // operand register read address
  input  [3:0] Wd,       // write destination (4'hF = ACC, or Rd for STO)
  input  [7:0] Wdat,     // write data
  output [7:0] RdatAcc,  // always reads ACC (r15)
               RdatReg   // reads register at address Ra
);

  logic [7:0] Core[16];

  always_ff @(posedge Clk)
    if (Wen) Core[Wd] <= Wdat;

  assign RdatAcc = Core[15];
  assign RdatReg = Core[Ra];

endmodule
