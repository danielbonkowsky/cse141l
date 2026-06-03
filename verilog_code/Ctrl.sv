module Ctrl(
  input        [8:0] mach_code,
  output logic [1:0] Aluop,
                     Jptr,
  output logic [1:0] Ra,
                     Rb,
                     Wd,
  output logic       WenR,
                     WenD,
                     Ldr,
                     Str
);

  always_comb begin
    Aluop = mach_code[1:0];		// ALU
    Jptr  = mach_code[3:2];		// jump pointer
    Ra	  = mach_code[5:4];		// reg file addr A
    Rb    = 2'b0;
    Wd    = mach_code[5:4];
    WenR  = mach_code[6];		 // reg file write enable
    WenD  = !mach_code[6];	 // data mem write enable
    Ldr   =	mach_code[7];		 // load
    Str	  = !mach_code[6];	 // store
    // case(mach_code)
    // endcase
  end

endmodule
