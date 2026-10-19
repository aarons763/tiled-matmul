def matmul_reference(a, b):

    for name, matrix in (("a", a), ("b", b)):
        if not isinstance(matrix, list) or not matrix:
            raise ValueError(f"Matrix {name} must be a nonempty list.")

        width = None

        for row in matrix:
            if not isinstance(row, list) or not row:
                raise ValueError(
                    f"Each row in matrix {name} must be a nonempty list."
                )

            if width is None:
                width = len(row)
            elif len(row) != width:
                raise ValueError(
                    f"All rows in matrix {name} must have the same length."
                )

            for value in row:
                if type(value) is not int or not (-128 <= value <= 127):
                    raise ValueError(
                        f"Matrix {name} elements must be integers from -128 to 127."
                    )

    if len(a[0]) != len(b):
        raise ValueError("A's column count must equal B's row count.")

    M = len(a)
    K = len(a[0])
    N = len(b[0])

    result = []

    for i in range(M):
        row = []
        for j in range(N):
            total = 0
            for k in range(K):
                total += a[i][k] * b[k][j]
            row.append(total)
        result.append(row)
    return result