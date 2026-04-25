module tb_alu;

    // inputs
    logic [7:0] acc, alu_in;
    logic [3:0] alu_op;

    // outputs
    logic [7:0] result;
    logic       z_flag, s_flag, c_flag, ov_flag;

    // instantiate
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

    // helper task
    task test_op(
        input [3:0] op,
        input [7:0] a, b,
        input [7:0] exp_result,
        input       exp_z, exp_s, exp_c,
        input string label
    );
        acc    = a;
        alu_in = b;
        alu_op = op;
        #10;
        $display("[%s] acc=%0d in=%0d | result=%0d (exp %0d) | Z=%b S=%b C=%b",
            label, a, b, result, exp_result, z_flag, s_flag, c_flag);
        if (result !== exp_result || z_flag !== exp_z || 
            s_flag !== exp_s || c_flag !== exp_c)
            $display("  *** MISMATCH ***");
    endtask

    initial begin
        $display("=== ALU Testbench ===");

        // --- AND (0000) ---
        test_op(4'b0000, 8'hF0, 8'h0F, 8'h00, 1, 0, 0, "AND zero");
        test_op(4'b0000, 8'hFF, 8'h0F, 8'h0F, 0, 0, 0, "AND nonzero");
        test_op(4'b0000, 8'hFF, 8'h01, 8'h01, 0, 0, 0, "AND isolate LSB");
        test_op(4'b0000, 8'hFF, 8'h80, 8'h80, 0, 0, 0, "AND isolate sign bit");

        // --- XOR (0001) ---
        test_op(4'b0001, 8'hFF, 8'hFF, 8'h00, 1, 0, 0, "XOR same");
        test_op(4'b0001, 8'hF0, 8'h0F, 8'hFF, 0, 0, 0, "XOR all diff");
        test_op(4'b0001, 8'hAA, 8'h55, 8'hFF, 0, 0, 0, "XOR alternating");

        // --- INV (0010) ---
        test_op(4'b0010, 8'hFF, 8'h00, 8'h00, 1, 0, 0, "INV 0xFF");
        test_op(4'b0010, 8'h00, 8'h00, 8'hFF, 0, 0, 0, "INV 0x00");
        test_op(4'b0010, 8'hAA, 8'h00, 8'h55, 0, 0, 0, "INV 0xAA");

        // --- ADD (0011) ---
        test_op(4'b0011, 8'd10,  8'd5,   8'd15,  0, 0, 0, "ADD basic");
        test_op(4'b0011, 8'd0,   8'd0,   8'd0,   1, 0, 0, "ADD zero");
        test_op(4'b0011, 8'hFF,  8'h01,  8'h00,  1, 0, 1, "ADD overflow carry");
        test_op(4'b0011, 8'h80,  8'h80,  8'h00,  1, 0, 1, "ADD carry no result");

        // --- SUB (0100) ---
        test_op(4'b0100, 8'd10,  8'd5,   8'd5,   0, 0, 0, "SUB basic");
        test_op(4'b0100, 8'd5,   8'd5,   8'd0,   1, 0, 0, "SUB equal -> zero");
        test_op(4'b0100, 8'd3,   8'd5,   8'hFE,  0, 1, 0, "SUB negative -> sign");

        // --- MOV (0101) ---
        test_op(4'b0101, 8'd0,   8'd42,  8'd42,  0, 0, 0, "MOV basic");
        test_op(4'b0101, 8'd99,  8'd0,   8'd0,   1, 0, 0, "MOV zero");

        // --- STO (0110) --- result just passes through for reg write
        test_op(4'b0110, 8'd55,  8'd0,   8'd55,  0, 0, 0, "STO passes ACC");

        // --- LD (0111) --- ACC gets mem value via mux, ALU just passes reg_out
        test_op(4'b0111, 8'd0,   8'd99,  8'd99,  0, 0, 0, "LD passes reg_out");

        // --- ST (1000) --- ACC goes to memory, no ALU result needed
        test_op(4'b1000, 8'd77,  8'd0,   8'd77,  0, 0, 0, "ST passes ACC");

        // --- CMP (1001) --- sets flags only, result discarded ---
        test_op(4'b1001, 8'd5,   8'd5,   8'hXX,  1, 0, 0, "CMP equal");
        test_op(4'b1001, 8'd3,   8'd5,   8'hXX,  0, 1, 0, "CMP less than");
        test_op(4'b1001, 8'd5,   8'd3,   8'hXX,  0, 0, 0, "CMP greater than");

        // --- JMP (1010) --- no ALU operation, PC handles it
        // just verify flags aren't disturbed
        test_op(4'b1010, 8'd0,   8'd0,   8'd0,   0, 0, 0, "JMP noop");

        // --- LSH via I-type (imm=shift amount) ---
        // ALU op encoding for LSH: Daniel to confirm
        test_op(4'b1011, 8'b0000_0001, 8'd1, 8'b0000_0010, 0, 0, 0, "LSH 1");
        test_op(4'b1011, 8'b0000_0001, 8'd3, 8'b0000_1000, 0, 0, 0, "LSH 3");
        test_op(4'b1011, 8'b1000_0000, 8'd1, 8'b0000_0000, 1, 0, 1, "LSH overflow");

        // --- RSH ---
        test_op(4'b1100, 8'b0000_1000, 8'd1, 8'b0000_0100, 0, 0, 0, "RSH 1");
        test_op(4'b1100, 8'b0000_0001, 8'd1, 8'b0000_0000, 1, 0, 0, "RSH underflow");

        // --- LDI --- ACC = immediate
        test_op(4'b1101, 8'd0, 8'd7, 8'd7, 0, 0, 0, "LDI 7");
        test_op(4'b1101, 8'd0, 8'd0, 8'd0, 1, 0, 0, "LDI 0");

        // --- ADDI --- ACC += immediate
        test_op(4'b1110, 8'd10, 8'd5, 8'd15, 0, 0, 0, "ADDI basic");
        test_op(4'b1110, 8'hFF, 8'd1, 8'h00, 1, 0, 1, "ADDI overflow");

        // --- SUBI --- ACC -= immediate
        test_op(4'b1111, 8'd10, 8'd3, 8'd7,  0, 0, 0, "SUBI basic");
        test_op(4'b1111, 8'd3,  8'd3, 8'd0,  1, 0, 0, "SUBI zero");
        test_op(4'b1111, 8'd2,  8'd3, 8'hFF, 0, 1, 0, "SUBI negative");

        $display("=== Done ===");
        $finish;
    end

endmodule