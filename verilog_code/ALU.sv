module ALU(
  input [1:0]       Aluop,
  input [7:0]       DatA,
                    DatB,
  output logic[7:0] Rslt,
  output logic      Zero,
                    Par,
			              SCo
);

always_comb begin
  Rslt = 8'b0;
  SCo  = 8'b0;
  case(Aluop)
    2'b00: {SCo,Rslt} = DatA + DatB;   // add
    2'b01: {SCo,Rslt} = DatA<<1'b1;    // left shift
	  2'b10: Rslt       = DatA & DatB;   // bitwise AND
	  2'b11: Rslt       = DatA ^ DatB;   // bitwise XOR
  endcase
end

  assign Zero = !Rslt;
  assign Par  = ^Rslt;

endmodule
