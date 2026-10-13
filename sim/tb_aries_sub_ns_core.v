`timescale 1ns/1ps
module tb_aries_sub_ns_core;
  reg clk_4ghz = 0;
  reg rst_n = 0;
  reg [63:0] raw_stream = 0;
  reg trigger_valid = 0;
  wire [63:0] resolved_out;
  wire sub_ns_lock;
  integer failures = 0;

  always #0.125 clk_4ghz = ~clk_4ghz;

  aries_sub_ns_core dut (
    .clk_4ghz(clk_4ghz), .rst_n(rst_n), .raw_stream(raw_stream),
    .trigger_valid(trigger_valid), .resolved_out(resolved_out),
    .sub_ns_lock(sub_ns_lock)
  );

  initial begin
    #0.5;
    if (resolved_out !== 64'd0 || sub_ns_lock !== 1'b0) begin
      $display("FAIL: reset values incorrect"); failures = failures + 1;
    end
    rst_n = 1;
    raw_stream = 64'h1234_5678_9ABC_DEF0;
    trigger_valid = 1;
    @(posedge clk_4ghz); #0.01;
    if (resolved_out !== 64'h1234_5678_9ABC_DEF0 || sub_ns_lock !== 1'b1) begin
      $display("FAIL: valid input not captured"); failures = failures + 1;
    end
    trigger_valid = 0;
    @(posedge clk_4ghz); #0.01;
    if (sub_ns_lock !== 1'b0) begin
      $display("FAIL: lock did not clear without trigger"); failures = failures + 1;
    end
    if (failures == 0) $display("PASS: ARIES RTL smoke tests");
    else $display("FAIL: %0d check(s) failed", failures);
    $finish(failures != 0);
  end
endmodule
