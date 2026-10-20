module double_buffer_controller #(
    parameter int DEPTH = 16,
    parameter int K_WIDTH = $clog2(DEPTH + 1)
) (
    input logic clk,
    input logic rst,
    input logic start,
    input logic [16:0] total_k,
    input logic load_done,
    input logic engine_done,
    output wire busy,
    output logic done,
    output wire load_req,
    output logic [16:0] k_offset,
    output logic [K_WIDTH-1:0] chunk_len,
    output wire engine_start,
    output wire engine_clear,
    output logic [K_WIDTH-1:0] engine_k_len,
    output logic read_bank,
    output logic write_bank
);

    typedef enum logic [2:0] {
        IDLE, CLEAR, LOAD_FIRST, START, RUN, WAIT_NEXT
    } state_t;

    state_t state;
    logic [16:0] k_total;
    logic request_pending;
    logic next_ready;
    logic active_last;
    wire [16:0] remaining;
    wire load_accept;

    // Metadata describes the loader's chunk, independently of engine_k_len.
    assign remaining = k_total - k_offset - 17'(chunk_len);
    assign busy = (state != IDLE);
    assign engine_clear = (state == CLEAR) && !rst;
    assign engine_start = (state == START) && !rst;
    assign load_req = !rst && ((state == LOAD_FIRST) || request_pending);
    assign load_accept = load_req && load_done;

    always_ff @(posedge clk) begin
        if (rst) begin
            state <= IDLE;
            done <= 0;
            k_total <= 0;
            k_offset <= 0;
            chunk_len <= 0;
            engine_k_len <= 0;
            read_bank <= 0;
            write_bank <= 0;
            request_pending <= 0;
            next_ready <= 0;
            active_last <= 0;
        end
        else begin
            done <= 0;
            case (state)
                IDLE: begin
                    if (start) begin
                        k_total <= total_k;
                        k_offset <= 0;
                        chunk_len <= (32'(total_k) > DEPTH)
                            ? K_WIDTH'(DEPTH) : K_WIDTH'(total_k);
                        read_bank <= 0;
                        write_bank <= 0;
                        request_pending <= 0;
                        next_ready <= 0;
                        active_last <= 0;
                        state <= CLEAR;
                    end
                end

                CLEAR: state <= LOAD_FIRST;

                LOAD_FIRST: begin
                    if (load_accept) begin
                        engine_k_len <= chunk_len;
                        active_last <= (remaining == 0);
                        state <= START;
                    end
                end

                START: begin
                    // The scheduler accepts the current chunk on this edge.
                    // Only the opposite bank is then offered to the loader.
                    if (!active_last) begin
                        k_offset <= k_offset + 17'(chunk_len);
                        chunk_len <= (32'(remaining) > DEPTH)
                            ? K_WIDTH'(DEPTH) : K_WIDTH'(remaining);
                        write_bank <= !read_bank;
                        request_pending <= 1;
                    end
                    state <= RUN;
                end

                RUN: begin
                    if (load_accept) begin
                        request_pending <= 0;
                        next_ready <= 1;
                    end
                    if (engine_done) begin
                        if (active_last) begin
                            state <= IDLE;
                            done <= 1;
                        end
                        else if (next_ready || load_accept) begin
                            read_bank <= write_bank;
                            engine_k_len <= chunk_len;
                            active_last <= (remaining == 0);
                            next_ready <= 0;
                            state <= START;
                        end
                        else begin
                            state <= WAIT_NEXT;
                        end
                    end
                end

                WAIT_NEXT: begin
                    // Computation drained first. Keep ownership until loading
                    // completes; an early loader likewise waits in RUN.
                    if (load_accept) begin
                        request_pending <= 0;
                        next_ready <= 0;
                        read_bank <= write_bank;
                        engine_k_len <= chunk_len;
                        active_last <= (remaining == 0);
                        state <= START;
                    end
                end

                default: state <= IDLE;
            endcase
        end
    end
endmodule
