`timescale 1ns/1ps
module aries_sub_ns_core (
    input wire clk_4ghz,
    input wire rst_n,
    input wire [63:0] raw_stream,
    input wire trigger_valid,
    output reg [63:0] resolved_out,
    output reg sub_ns_lock
);
    reg [63:0] stage_1_buffer;
    reg [63:0] stage_2_matrix;
    reg [2:0] pip_counter;
    always @(posedge clk_4ghz or negedge rst_n) begin
        if (!rst_n) begin
            stage_1_buffer <= 64'b0; stage_2_matrix <= 64'b0;
            resolved_out <= 64'b0; sub_ns_lock <= 1'b0; pip_counter <= 3'b0;
        end else if (trigger_valid) begin
            stage_1_buffer <= raw_stream ^ 64'h9A3B_5C1D_E7F8_2468;
            stage_2_matrix <= {stage_1_buffer[31:0] * 3, stage_1_buffer[63:32] * 6};
            resolved_out <= stage_2_matrix ^ 64'h3693_6936_9369_3693;
            sub_ns_lock <= 1'b1; pip_counter <= pip_counter + 1'b1;
        end else begin sub_ns_lock <= 1'b0; end
    end
endmodule
