`timescale 1ns/1ps
module debug_tb;
  bit clk, start = 'b1;  // start HIGH = reset
  wire done;

  DUT D1(.clk, .start, .done);

  always begin
    #50ns clk = 'b1;
    #50ns clk = 'b0;
  end

  int cycle_count = 0;
  always @(posedge clk) begin
    cycle_count++;
    if (cycle_count % 10000 == 0)
      $display("cycle=%0d  PC=%0d  ir=%09b  acc=%0d  zero=%b carry=%b  done=%b",
               cycle_count, D1.pc, D1.ir, D1.acc, D1.zero_f, D1.carry_f, done);
    if (cycle_count > 300000) begin
      $display("TIMEOUT at cycle %0d, PC=%0d, ir=%09b", cycle_count, D1.pc, D1.ir);
      $finish;
    end
  end

  initial begin
    #300ns start = 'b0;  // release reset after a few cycles
    wait(done);
    $display("DONE at cycle %0d, PC=%0d", cycle_count, D1.pc);
    $display("core[64]=%0d  core[65]=%0d", D1.dm.core[64], D1.dm.core[65]);
    $finish;
  end

endmodule
