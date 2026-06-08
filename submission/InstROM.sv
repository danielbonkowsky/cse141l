module InstROM(
  input[9:0] PC,
  output logic[8:0] mach_code
);

  logic[8:0] Core[1024];

  initial
  $readmemb("program1.mem",Core);

  always_comb mach_code = Core[PC];

endmodule
