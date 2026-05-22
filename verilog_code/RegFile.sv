`define ACC 15

module RegFile(
  input       Clk,	   // clock
              Wen,     // write enable
  input[1:0]  Ra,      // read address pointer
  input[7:0]  Wdat,    // write data in
  output[7:0] RdatAcc, // read data out acc
              RdatReg  // read data out reg
);

  logic[7:0] Core[16]; // reg file itself (16*8 array)

  always_ff @(posedge Clk)
    if (Wen) Core[ACC] <= Wdat;

  assign RdatAcc = Core[ACC];
  assign RdatReg = Core[Ra];

endmodule
