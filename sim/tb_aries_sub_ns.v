`timescale 1ns/1ps
module tb_aries_sub_ns;
  reg clk = 0; reg rst_n = 0; reg [63:0] raw_stream = 0; reg trigger_valid = 0;
  wire [63:0] resolved_out; wire sub_ns_lock;
  aries_sub_ns_core dut (.clk_4ghz(clk), .rst_n(rst_n), .raw_stream(raw_stream), .trigger_valid(trigger_valid), .resolved_out(resolved_out), .sub_ns_lock(sub_ns_lock));
  // Simulation clock only; this does NOT prove physical 4 GHz operation.
  always #0.125 clk = ~clk;
  reg [63:0] ref_s1 = 0, ref_s2 = 0, ref_out = 0; reg ref_lock = 0; integer cycles = 0;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin ref_s1 <= 0; ref_s2 <= 0; ref_out <= 0; ref_lock <= 0; end
    else if (trigger_valid) begin
      ref_s1 <= raw_stream ^ 64'h9A3B_5C1D_E7F8_2468;
      ref_s2 <= {ref_s1[31:0] * 3, ref_s1[63:32] * 6};
      ref_out <= ref_s2 ^ 64'h3693_6936_9369_3693; ref_lock <= 1;
    end else ref_lock <= 0;
  end
  task check_outputs; begin #0.01;
    if (resolved_out !== ref_out) begin $display("FAIL cycle=%0d output expected=%h got=%h", cycles, ref_out, resolved_out); $fatal(1); end
    if (sub_ns_lock !== ref_lock) begin $display("FAIL cycle=%0d lock expected=%b got=%b", cycles, ref_lock, sub_ns_lock); $fatal(1); end
    cycles = cycles + 1;
  end endtask
  initial begin
    $dumpfile("aries_sub_ns.vcd"); $dumpvars(0, tb_aries_sub_ns);
    repeat (2) begin @(posedge clk); check_outputs(); end
    rst_n = 1; @(negedge clk); trigger_valid = 1; raw_stream = 64'h0123_4567_89AB_CDEF;
    repeat (6) begin @(posedge clk); check_outputs(); end
    @(negedge clk); raw_stream = 64'hFEDC_BA98_7654_3210; repeat (4) begin @(posedge clk); check_outputs(); end
    @(negedge clk); trigger_valid = 0; repeat (3) begin @(posedge clk); check_outputs(); end
    @(negedge clk); trigger_valid = 1; raw_stream = 64'hA5A5_5A5A_1122_3344; @(posedge clk); check_outputs();
    @(negedge clk); trigger_valid = 0; repeat (3) begin @(posedge clk); check_outputs(); end
    rst_n = 0; @(posedge clk); check_outputs();
    $display("PASS: %0d cycle-by-cycle checks completed.", cycles); $finish;
  end
endmodule
