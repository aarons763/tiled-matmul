module output_tile_controller #(
    parameter int ROWS = 4,
    parameter int COLS = 4,
    parameter int DIM_WIDTH = 16,
    parameter int ROW_COUNT_WIDTH = (ROWS > 1) ? $clog2(ROWS + 1) : 1,
    parameter int COL_COUNT_WIDTH = (COLS > 1) ? $clog2(COLS + 1) : 1
) (
    input logic clk,
    input logic rst,
    input logic start,
    input logic [DIM_WIDTH-1:0] m_len,
    input logic [DIM_WIDTH-1:0] n_len,
    input logic engine_done,
    input logic result_ready,
    output logic busy,
    output logic done,
    output logic engine_start,
    output logic [DIM_WIDTH-1:0] tile_row,
    output logic [DIM_WIDTH-1:0] tile_col,
    output logic [ROW_COUNT_WIDTH-1:0] valid_rows,
    output logic [COL_COUNT_WIDTH-1:0] valid_cols,
    output logic result_valid
);

    typedef enum logic [1:0] {
        IDLE,
        START,
        WAIT_ENGINE,
        RESULT
    } state_t;

    state_t state;
    logic [DIM_WIDTH-1:0] m_total, n_total;
    wire [DIM_WIDTH:0] next_row, next_col;

    // Positive dimensions and positive tile sizes are caller requirements.
    // ROWS and COLS must each fit within DIM_WIDTH bits.
    // The extra bit prevents tile-boundary addition from wrapping.
    assign next_row = {1'b0, tile_row} + ROWS;
    assign next_col = {1'b0, tile_col} + COLS;

    always_comb begin
        busy = (state != IDLE);
        engine_start = 0;
        result_valid = 0;
        valid_rows = 0;
        valid_cols = 0;

        if (!rst && state != IDLE) begin
            if (m_total - tile_row > ROWS) begin
                valid_rows = ROWS;
            end
            else begin
                valid_rows = m_total - tile_row;
            end

            if (n_total - tile_col > COLS) begin
                valid_cols = COLS;
            end
            else begin
                valid_cols = n_total - tile_col;
            end

            case (state)
                START: engine_start = 1;
                RESULT: result_valid = 1;
                default: begin
                end
            endcase
        end
    end

    always_ff @(posedge clk) begin
        if (rst) begin
            state <= IDLE;
            done <= 0;
            m_total <= 0;
            n_total <= 0;
            tile_row <= 0;
            tile_col <= 0;
        end
        else begin
            done <= 0;

            case (state)
                IDLE: begin
                    if (start) begin
                        m_total <= m_len;
                        n_total <= n_len;
                        tile_row <= 0;
                        tile_col <= 0;
                        state <= START;
                    end
                end

                START: begin
                    state <= WAIT_ENGINE;
                end

                WAIT_ENGINE: begin
                    if (engine_done) begin
                        state <= RESULT;
                    end
                end

                RESULT: begin
                    // Advance only on a result_valid/result_ready handshake.
                    if (result_ready) begin
                        if (next_col < {1'b0, n_total}) begin
                            tile_col <= next_col[DIM_WIDTH-1:0];
                            state <= START;
                        end
                        else if (next_row < {1'b0, m_total}) begin
                            tile_row <= next_row[DIM_WIDTH-1:0];
                            tile_col <= 0;
                            state <= START;
                        end
                        else begin
                            state <= IDLE;
                            done <= 1;
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
