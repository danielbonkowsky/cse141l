module tb_program_counter;

    // inputs
    logic       clk, start;
    logic       z_flag, s_flag;
    logic [8:0] instr;
    logic [7:0] reg_out;

    // outputs
    logic       done;
    logic [7:0] pc;

    // instantiate
    program_counter dut (
        .clk     (clk),
        .start   (start),
        .z_flag  (z_flag),
        .s_flag  (s_flag),
        .instr   (instr),
        .reg_out (reg_out),
        .done    (done),
        .pc      (pc)
    );

    // clock: 10ns period
    initial clk = 0;
    always #5 clk = ~clk;

    // helper task to apply one instruction and print result
    task apply_instr(
        input [8:0] i,
        input       z, s,
        input [7:0] reg_val,
        input string label
    );
        instr   = i;
        z_flag  = z;
        s_flag  = s;
        reg_out = reg_val;
        @(posedge clk); #1;
        $display("[%s] PC = %0d | done = %b", label, pc, done);
    endtask

    initial begin
        $display("=== PC Testbench ===");

        // --- reset ---
        start   = 1;
        instr   = 9'b0;
        z_flag  = 0;
        s_flag  = 0;
        reg_out = 0;
        @(posedge clk); #1;
        $display("[RESET] PC = %0d (expect 0)", pc);
        start = 0;

        // --- test 1: normal increment ---
        // R-type instruction, no branch
        apply_instr(9'b00_0011_010, 0, 0, 8'd0, "INCREMENT");
        apply_instr(9'b00_0011_010, 0, 0, 8'd0, "INCREMENT");
        apply_instr(9'b00_0011_010, 0, 0, 8'd0, "INCREMENT");
        // expect PC = 3

        // --- test 2: BEQ not taken (z_flag = 0) ---
        // beq +5 = 10_0000101
        apply_instr(9'b10_0000101, 0, 0, 8'd0, "BEQ NOT TAKEN");
        // expect PC = 4 (just increments)

        // --- test 3: BEQ taken (z_flag = 1) ---
        // beq +5 = 10_0000101, from PC=4 -> PC = 4 + 5 = 9
        apply_instr(9'b10_0000101, 1, 0, 8'd0, "BEQ TAKEN");
        // expect PC = 9

        // --- test 4: BEQ negative offset (backward branch) ---
        // beq -3 = 10_1111101 (7-bit two's complement of -3)
        // from PC=9 -> PC = 9 + (-3) = 6
        apply_instr(9'b10_1111101, 1, 0, 8'd0, "BEQ BACKWARD");
        // expect PC = 6

        // --- test 5: BLT not taken (s_flag = 0) ---
        // blt +4 = 11_0000100, from PC=6
        apply_instr(9'b11_0000100, 0, 0, 8'd0, "BLT NOT TAKEN");
        // expect PC = 7

        // --- test 6: BLT taken (s_flag = 1) ---
        // blt +4 = 11_0000100, from PC=7 -> PC = 7 + 4 = 11
        apply_instr(9'b11_0000100, 0, 1, 8'd0, "BLT TAKEN");
        // expect PC = 11

        // --- test 7: JMP via register ---
        // jmp R3 = 00_1010_011, reg_out = 10 -> PC = 11 + 10 = 21
        apply_instr(9'b00_1010_011, 0, 0, 8'd10, "JMP");
        // expect PC = 21

        // --- test 8: JMP negative (backward) ---
        // reg_out = -5 = 8'hFB -> PC = 21 + (-5) = 16
        apply_instr(9'b00_1010_011, 0, 0, 8'hFB, "JMP BACKWARD");
        // expect PC = 16

        // --- test 9: done flag (beq 0) ---
        // beq 0 = 10_0000000
        instr   = 9'b10_0000000;
        z_flag  = 0;
        s_flag  = 0;
        reg_out = 0;
        @(posedge clk); #1;
        $display("[DONE FLAG] done = %b (expect 1)", done);
        // expect done = 1, PC halts

        // --- test 10: start mid-program resets PC ---
        start = 1;
        @(posedge clk); #1;
        $display("[START RESET] PC = %0d (expect 0)", pc);
        start = 0;

        $display("=== Done ===");
        $finish;
    end

endmodule