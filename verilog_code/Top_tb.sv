module Top_tb;

  bit clk, reset;
  wire done;
  parameter D = 6, A = 2;

  Top t1(
    .Clk  (clk),
    .Reset(reset),
    .Done (done)
  );

  always begin
    #5ns clk = 1;
    #5ns clk = 0;
  end

  initial begin
    for(int i=0; i<4; i++)
      t1.RF1.Core[i] = i;
    #10ns reset = 1;
    #10ns reset = 0;
    #2000ns $stop;
  end

endmodule
