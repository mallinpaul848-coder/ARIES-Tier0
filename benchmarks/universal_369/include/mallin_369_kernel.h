#ifndef MALLIN_369_KERNEL_H
#define MALLIN_369_KERNEL_H

#include <stddef.h>
#include <stdint.h>

/*
 * Portable, fixed-work 3-6-9 matrix-vector kernel.
 *
 * This implements the explicit cyclic matrix:
 * [3 6 9; 9 3 6; 6 9 3] * x.
 * It is a deterministic arithmetic microkernel, not a claim of quantum,
 * sub-nanotechnology, or sub-nanosecond performance.
 */

#if defined(__cplusplus)
extern "C" {
#endif

typedef struct {
    double v[3];
} mallin_vec3;

static inline mallin_vec3 mallin_369_transform(mallin_vec3 x) {
    mallin_vec3 y;
    y.v[0] = 3.0 * x.v[0] + 6.0 * x.v[1] + 9.0 * x.v[2];
    y.v[1] = 9.0 * x.v[0] + 3.0 * x.v[1] + 6.0 * x.v[2];
    y.v[2] = 6.0 * x.v[0] + 9.0 * x.v[1] + 3.0 * x.v[2];
    return y;
}

#if defined(__cplusplus)
}
#endif

#endif
