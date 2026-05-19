module tb_program_counter;

    logic       clk, start;
    logic       z_flag, s_flag, c_flag;  // ← added c_flag
    logic [8:0] instr;
    logic [7:0] reg_out;
    logic       done;
    logic [7:0] pc;

    program_counter dut (
        .clk     (clk),
        .start   (start),
        .z_flag  (z_flag),
        .s_flag  (s_flag),
        .c_flag  (c_flag),              // ← added
        .instr   (instr),
        .reg_out (reg_out),
        .done    (done),
        .pc      (pc)
    );

    initial clk = 0;
    always #5 clk = ~clk;

    task apply_instr(
        input [8:0] i,
        input       z, s, c,
        input [7:0] reg_val,
        input string label
    );
        instr   = i;
        z_flag  = z;
        s_flag  = s;
        c_flag  = c;
        reg_out = reg_val;
        @(posedge clk); #1;
        $display("[%s] PC = %0d | done = %b", label, pc, done);
    endtask

    initial begin
        $display("=== PC Testbench ===");

        // reset
        start = 1; instr = 9'b0; z_flag = 0; s_flag = 0; c_flag = 0; reg_out = 0;
        @(posedge clk); #1;
        $display("[RESET] PC = %0d (expect 0)", pc);
        start = 0;

        // normal increment (R-type ADD)
        apply_instr(9'b00_0011_010, 0, 0, 0, 8'd0, "INCREMENT"); // PC=1
        apply_instr(9'b00_0011_010, 0, 0, 0, 8'd0, "INCREMENT"); // PC=2
        apply_instr(9'b00_0011_010, 0, 0, 0, 8'd0, "INCREMENT"); // PC=3

        // BEQ not taken (z=0): 1_00_000101 = beq +5
        apply_instr(9'b1_00_000101, 0, 0, 0, 8'd0, "BEQ NOT TAKEN"); // PC=4

        // BEQ taken (z=1): from PC=4, +5 -> PC=9
        apply_instr(9'b1_00_000101, 1, 0, 0, 8'd0, "BEQ TAKEN"); // PC=9

        // BEQ backward (z=1): -3 in 6-bit 2's comp = 111101, from PC=9 -> PC=6
        apply_instr(9'b1_00_111101, 1, 0, 0, 8'd0, "BEQ BACKWARD"); // PC=6

        // BLT not taken (s=0): 1_01_000100 = blt +4
        apply_instr(9'b1_01_000100, 0, 0, 0, 8'd0, "BLT NOT TAKEN"); // PC=7

        // BLT taken (s=1): from PC=7, +4 -> PC=11
        apply_instr(9'b1_01_000100, 0, 1, 0, 8'd0, "BLT TAKEN"); // PC=11

        // BCS not taken (c=0): 1_10_000011 = bcs +3
        apply_instr(9'b1_10_000011, 0, 0, 0, 8'd0, "BCS NOT TAKEN"); // PC=12

        // BCS taken (c=1): from PC=12, +3 -> PC=15
        apply_instr(9'b1_10_000011, 0, 0, 1, 8'd0, "BCS TAKEN"); // PC=15

        // JMP: reg_out=10, from PC=15 -> PC=25
        apply_instr(9'b00_1010_011, 0, 0, 0, 8'd10, "JMP"); // PC=25

        // JMP backward: reg_out=-5=8'hFB, from PC=25 -> PC=20
        apply_instr(9'b00_1010_011, 0, 0, 0, 8'hFB, "JMP BACKWARD"); // PC=20

        // done flag: 1_00_000000
        instr = 9'b1_00_000000; z_flag=0; s_flag=0; c_flag=0; reg_out=0;
        @(posedge clk); #1;
        $display("[DONE FLAG] done = %b (expect 1)", done);

        // start resets PC
        start = 1;
        @(posedge clk); #1;
        $display("[START RESET] PC = %0d (expect 0)", pc);
        start = 0;

        $display("=== Done ===");
        $finish;
    end

endmodule
