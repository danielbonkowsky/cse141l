// alu_tb.sv
// Testbench for DelicateArch ALU
// Updated for revised ISA: SHF (signed shift), ADDI (signed imm), no SUBI

module tb_alu;

    // inputs
    logic [7:0] acc, alu_in;
    logic [3:0] alu_op;

    // outputs
    logic [7:0] result;
    logic       z_flag, s_flag, c_flag, ov_flag;

    // instantiate ALU
    alu dut (
        .acc     (acc),
        .alu_in  (alu_in),
        .alu_op  (alu_op),
        .result  (result),
        .z_flag  (z_flag),
        .s_flag  (s_flag),
        .c_flag  (c_flag),
        .ov_flag (ov_flag)
    );

    // helper task: apply inputs, wait, check outputs
    // note: CMP/JMP discard result so pass exp_result=8'hxx and set skip_result=1
    task test_op(
        input [3:0]  op,
        input [7:0]  a, b,
        input [7:0]  exp_result,
        input        exp_z, exp_s, exp_c,
        input logic  skip_result,
        input string label
    );
        acc    = a;
        alu_in = b;
        alu_op = op;
        #10;
        $display("[%s] acc=%0d in=%0d | result=%0d | Z=%b S=%b C=%b OV=%b",
            label, a, b, result, z_flag, s_flag, c_flag, ov_flag);
        if (!skip_result && result !== exp_result)
            $display("  *** RESULT MISMATCH: got %0d, expected %0d ***", result, exp_result);
        if (z_flag !== exp_z)
            $display("  *** Z FLAG MISMATCH: got %b, expected %b ***", z_flag, exp_z);
        if (s_flag !== exp_s)
            $display("  *** S FLAG MISMATCH: got %b, expected %b ***", s_flag, exp_s);
        if (c_flag !== exp_c)
            $display("  *** C FLAG MISMATCH: got %b, expected %b ***", c_flag, exp_c);
    endtask

    initial begin
        $display("=== ALU Testbench ===");

        // -----------------------------------------------------------------
        // AND (opcode 0000): ACC &= alu_in
        // clears carry and overflow; sets zero and sign
        // -----------------------------------------------------------------
        $display("--- AND ---");
        test_op(4'b0000, 8'hF0, 8'h0F, 8'h00, 1, 0, 0, 0, "AND -> zero");
        test_op(4'b0000, 8'hFF, 8'h0F, 8'h0F, 0, 0, 0, 0, "AND -> nonzero");
        test_op(4'b0000, 8'hFF, 8'h01, 8'h01, 0, 0, 0, 0, "AND -> isolate LSB");
        test_op(4'b0000, 8'hFF, 8'h80, 8'h80, 0, 1, 0, 0, "AND -> isolate sign bit");

        // -----------------------------------------------------------------
        // XOR (opcode 0001): ACC ^= alu_in
        // clears carry and overflow; sets zero and sign
        // -----------------------------------------------------------------
        $display("--- XOR ---");
        test_op(4'b0001, 8'hFF, 8'hFF, 8'h00, 1, 0, 0, 0, "XOR -> same inputs");
        test_op(4'b0001, 8'hF0, 8'h0F, 8'hFF, 0, 1, 0, 0, "XOR -> all different");
        test_op(4'b0001, 8'hAA, 8'h55, 8'hFF, 0, 1, 0, 0, "XOR -> alternating");
        test_op(4'b0001, 8'h00, 8'h00, 8'h00, 1, 0, 0, 0, "XOR -> both zero");

        // -----------------------------------------------------------------
        // INV (opcode 0010): ACC = ~ACC
        // preserves flags; alu_in unused
        // -----------------------------------------------------------------
        $display("--- INV ---");
        test_op(4'b0010, 8'hFF, 8'h00, 8'h00, 1, 0, 0, 0, "INV 0xFF -> 0x00");
        test_op(4'b0010, 8'h00, 8'h00, 8'hFF, 0, 1, 0, 0, "INV 0x00 -> 0xFF");
        test_op(4'b0010, 8'hAA, 8'h00, 8'h55, 0, 0, 0, 0, "INV 0xAA -> 0x55");

        // -----------------------------------------------------------------
        // ADD (opcode 0011): ACC += alu_in
        // carry set on unsigned overflow; overflow set on signed overflow
        // -----------------------------------------------------------------
        $display("--- ADD ---");
        test_op(4'b0011, 8'd10,  8'd5,  8'd15,  0, 0, 0, 0, "ADD basic");
        test_op(4'b0011, 8'd0,   8'd0,  8'd0,   1, 0, 0, 0, "ADD -> zero");
        test_op(4'b0011, 8'hFF,  8'h01, 8'h00,  1, 0, 1, 0, "ADD -> unsigned overflow");
        test_op(4'b0011, 8'h80,  8'h80, 8'h00,  1, 0, 1, 0, "ADD -> carry, signed overflow");
        test_op(4'b0011, 8'h7F,  8'h01, 8'h80,  0, 1, 0, 0, "ADD -> signed overflow only");

        // -----------------------------------------------------------------
        // SUB (opcode 0100): ACC -= alu_in
        // carry set on unsigned borrow; sign flag = MSB of result
        // -----------------------------------------------------------------
        $display("--- SUB ---");
        test_op(4'b0100, 8'd10,  8'd5,  8'd5,   0, 0, 0, 0, "SUB basic");
        test_op(4'b0100, 8'd5,   8'd5,  8'd0,   1, 0, 0, 0, "SUB -> equal -> zero");
        test_op(4'b0100, 8'd3,   8'd5,  8'hFE,  0, 1, 1, 0, "SUB -> borrow, sign set");
        test_op(4'b0100, 8'h80,  8'h01, 8'h7F,  0, 0, 0, 0, "SUB -> signed overflow");

        // -----------------------------------------------------------------
        // MOV (opcode 0101): ACC = alu_in (register value)
        // preserves flags
        // -----------------------------------------------------------------
        $display("--- MOV ---");
        test_op(4'b0101, 8'd0,  8'd42, 8'd42, 0, 0, 0, 0, "MOV basic");
        test_op(4'b0101, 8'd99, 8'd0,  8'd0,  1, 0, 0, 0, "MOV -> zero");
        test_op(4'b0101, 8'd0,  8'hFF, 8'hFF, 0, 1, 0, 0, "MOV -> sign set");

        // -----------------------------------------------------------------
        // STO (opcode 0110): passes ACC through for register write
        // result = ACC; preserves flags
        // -----------------------------------------------------------------
        $display("--- STO ---");
        test_op(4'b0110, 8'd55, 8'd0,  8'd55,  0, 0, 0, 0, "STO passes ACC");
        test_op(4'b0110, 8'd0,  8'd99, 8'd0,   1, 0, 0, 0, "STO ignores alu_in");

        // -----------------------------------------------------------------
        // LD (opcode 0111): result = alu_in (mem data routed via mux)
        // ALU just passes alu_in through; actual mem read handled by mux_acc_src
        // -----------------------------------------------------------------
        $display("--- LD ---");
        test_op(4'b0111, 8'd0,  8'd99, 8'd99, 0, 0, 0, 0, "LD passes mem data");
        test_op(4'b0111, 8'd0,  8'hAB, 8'hAB, 0, 1, 0, 0, "LD sign from mem data");

        // -----------------------------------------------------------------
        // ST (opcode 1000): ACC written to memory; no ALU result needed
        // result = ACC (for completeness); preserves flags
        // -----------------------------------------------------------------
        $display("--- ST ---");
        test_op(4'b1000, 8'd77, 8'd0, 8'd77, 0, 0, 0, 0, "ST passes ACC");

        // -----------------------------------------------------------------
        // CMP (opcode 1001): ACC - alu_in, flags set, result discarded
        // -----------------------------------------------------------------
        $display("--- CMP ---");
        test_op(4'b1001, 8'd5,  8'd5,  8'h00, 1, 0, 0, 1, "CMP equal -> Z set");
        test_op(4'b1001, 8'd3,  8'd5,  8'h00, 0, 1, 1, 1, "CMP less -> S and C set");
        test_op(4'b1001, 8'd5,  8'd3,  8'h00, 0, 0, 0, 1, "CMP greater -> no flags");
        test_op(4'b1001, 8'h00, 8'hFF, 8'h00, 0, 0, 1, 1, "CMP unsigned borrow");

        // -----------------------------------------------------------------
        // JMP (opcode 1010): handled entirely by PC; ALU is a noop
        // flags should not be disturbed
        // -----------------------------------------------------------------
        $display("--- JMP (noop in ALU) ---");
        test_op(4'b1010, 8'd0, 8'd0, 8'd0, 0, 0, 0, 1, "JMP noop");

        // -----------------------------------------------------------------
        // SHF (opcode 1011): signed shift
        // positive alu_in = left shift; negative alu_in = right shift
        // carry = last bit shifted out; overflow = sign bit changed (shift by 1)
        // -----------------------------------------------------------------
        $display("--- SHF (signed shift) ---");
        // left shifts (positive immediate)
        test_op(4'b1011, 8'b0000_0001, 8'd1,  8'b0000_0010, 0, 0, 0, 0, "SHF left 1");
        test_op(4'b1011, 8'b0000_0001, 8'd3,  8'b0000_1000, 0, 0, 0, 0, "SHF left 3");
        test_op(4'b1011, 8'b0100_0000, 8'd1,  8'b1000_0000, 0, 1, 0, 0, "SHF left 1 -> sign changes, overflow");
        test_op(4'b1011, 8'b1000_0000, 8'd1,  8'b0000_0000, 1, 0, 1, 0, "SHF left 1 -> carry, sign changes");
        // right shifts (negative immediate, 4-bit 2's comp: -1=1111, -2=1110 etc)
        test_op(4'b1011, 8'b0000_1000, 8'hFF, 8'b0000_0100, 0, 0, 0, 0, "SHF right 1 (-1)");
        test_op(4'b1011, 8'b0000_1000, 8'hFE, 8'b0000_0010, 0, 0, 0, 0, "SHF right 2 (-2)");
        test_op(4'b1011, 8'b0000_0001, 8'hFF, 8'b0000_0000, 1, 0, 1, 0, "SHF right 1 -> carry");
        // shift by 0 = noop
        test_op(4'b1011, 8'b1010_1010, 8'd0,  8'b1010_1010, 0, 1, 0, 0, "SHF by 0 -> noop");

        // -----------------------------------------------------------------
        // LDI (opcode 1101): ACC = immediate (0-15 unsigned)
        // preserves flags
        // -----------------------------------------------------------------
        $display("--- LDI ---");
        test_op(4'b1101, 8'd0, 8'd7,  8'd7,  0, 0, 0, 0, "LDI 7");
        test_op(4'b1101, 8'd0, 8'd0,  8'd0,  1, 0, 0, 0, "LDI 0 -> zero flag");
        test_op(4'b1101, 8'd0, 8'd15, 8'd15, 0, 0, 0, 0, "LDI 15 (max)");

        // -----------------------------------------------------------------
        // ADDI (opcode 1110): ACC += signed immediate (-8 to +7)
        // same flag behavior as ADD
        // -----------------------------------------------------------------
        $display("--- ADDI (signed immediate) ---");
        // positive immediate
        test_op(4'b1110, 8'd10, 8'd4,  8'd14,  0, 0, 0, 0, "ADDI +4");
        test_op(4'b1110, 8'd0,  8'd7,  8'd7,   0, 0, 0, 0, "ADDI +7 (max positive imm)");
        test_op(4'b1110, 8'hFF, 8'd1,  8'h00,  1, 0, 1, 0, "ADDI +1 -> unsigned overflow");
        // negative immediate (4-bit 2's comp: -1=1111, -2=1110, ..., -8=1000)
        test_op(4'b1110, 8'd10, 8'hFF, 8'd9,   0, 0, 0, 0, "ADDI -1 (0xF)");
        test_op(4'b1110, 8'd10, 8'hFE, 8'd8,   0, 0, 0, 0, "ADDI -2 (0xE)");
        test_op(4'b1110, 8'd5,  8'hFB, 8'd0,   1, 0, 0, 0, "ADDI -5 -> zero");
        test_op(4'b1110, 8'd3,  8'hFB, 8'hFE,  0, 1, 1, 0, "ADDI -5 -> borrow, sign set");

        $display("=== ALU Testbench Complete ===");
        $finish;
    end

endmodule
