module chunk_controller #(
    parameter int DEPTH = 16,
    parameter int K_WIDTH = $clog2(DEPTH + 1)
) (
    input logic clk,
    input logic rst,
    input logic start,
    input logic [16:0] total_k,
    input logic load_done,
    input logic engine_done,
    output logic busy,
    output logic done,
    output logic load_req,
    output logic [16:0] k_offset,
    output logic [K_WIDTH-1:0] chunk_len,
    output logic engine_start,
    output logic engine_clear
);

    typedef enum logic [2:0] {
        IDLE,
        CLEAR,
        LOAD,
        START,
        WAIT_ENGINE
    } state_t;

    state_t state;
    logic [16:0] k_total;
    wire [16:0] remaining_after_chunk;

    // Legal operations have 1 <= total_k <= 131071 and 1 <= DEPTH <= 131071.
    // The caller pulses start while idle and loads each chunk at bank address 0.
    assign remaining_after_chunk = k_total - k_offset - chunk_len;

    always_comb begin
        busy = (state != IDLE);
        load_req = 0;
        engine_start = 0;
        engine_clear = 0;

        if (!rst) begin
            case (state)
                CLEAR: engine_clear = 1;
                LOAD: load_req = 1;
                START: engine_start = 1;
                default: begin
                end
            endcase
        end
    end

    always_ff @(posedge clk) begin
        if (rst) begin
            state <= IDLE;
            done <= 0;
            k_total <= 0;
            k_offset <= 0;
            chunk_len <= 0;
        end
        else begin
            done <= 0;

            case (state)
                IDLE: begin
                    if (start) begin
                        k_total <= total_k;
                        k_offset <= 0;
                        if (total_k > DEPTH) begin
                            chunk_len <= DEPTH;
                        end
                        else begin
                            chunk_len <= total_k;
                        end
                        state <= CLEAR;
                    end
                end

                CLEAR: begin
                    state <= LOAD;
                end

                LOAD: begin
                    if (load_done) begin
                        state <= START;
                    end
                end

                START: begin
                    state <= WAIT_ENGINE;
                end

                WAIT_ENGINE: begin
                    if (engine_done) begin
                        if (remaining_after_chunk == 0) begin
                            state <= IDLE;
                            done <= 1;
                        end
                        else begin
                            k_offset <= k_offset + chunk_len;
                            if (remaining_after_chunk > DEPTH) begin
                                chunk_len <= DEPTH;
                            end
                            else begin
                                chunk_len <= remaining_after_chunk;
                            end
                            state <= LOAD;
                        end
                    end
                end

                default: begin
                    state <= IDLE;
                end
            endcase
        end
    end

endmodule
