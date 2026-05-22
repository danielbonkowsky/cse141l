module Top(
  input        Clk,
               Reset,
  output logic Done
);

  wire[5:0] Jump,
            PC;
  wire[1:0] Aluop,
            Ra,
            Rb,
            Wd,
            Jptr;
  wire[8:0] mach_code;
  wire[7:0] DatA,	     // ALU data in
            DatB,
            Rslt,      // ALU data out
            RdatA,     // RF data out
            RdatB,
            WdatR,     // RF data in
            WdatD,     // DM data in
            Rdat,		   // DM data out
            Addr;		   // DM address
  wire      Jen,		   // PC jump enable
            Par,       // ALU parity flag
            SCo,       // ALU shift/carry out
            Zero,      // ALU zero flag
            WenR,      // RF write enable
            WenD,      // DM write enable
            Ldr,       // LOAD
            Str;       // STORE

assign  DatA  = RdatA;
assign  DatB  = RdatB;
assign  WdatR = Rslt;

JLUT JL1(
  .Jptr,
  .Jump
);

ProgCtr PC1(
  .Clk,
  .Reset,
  .Jen,
  .Jump,
  .PC
);

InstROM IR1(
  .PC,
  .mach_code
);

Ctrl C1(
  .mach_code,
  .Aluop,
  .Jptr,
  .Ra,
  .Rb,
  .Wd,
  .WenR,
  .WenD,
  .Ldr,
  .Str
);

RegFile RF1(
  .Clk,
  .Wen(WenR),
  .Ra,
  .Rb,
  .Wd,
  .Wdat(WdatR),
  .RdatA,
  .RdatB
);

ALU A1(
  .Aluop,
  .DatA,
  .DatB,
  .Rslt,
  .Zero,
  .Par,
  .SCo
);

DMem DM1(
  .Clk,
  .Wen (WenD),
  .WDat(WdatD),
  .Addr,
  .Rdat
);

endmodule
