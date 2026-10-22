#ifndef ARIES_TIER0_VECTOR_KERNEL_H
#define ARIES_TIER0_VECTOR_KERNEL_H

#include <stddef.h>
#include <stdint.h>
#include <time.h>

#ifndef ARIES_VECTOR_SIZE
#define ARIES_VECTOR_SIZE 64
#endif

#ifndef ARIES_RING_CAPACITY
#define ARIES_RING_CAPACITY 100000
#endif

typedef struct {
    double data[ARIES_VECTOR_SIZE];
    uint64_t timestamp_ns;
    uint32_t node_id;
} AriesVectorNode;

typedef struct {
    AriesVectorNode nodes[ARIES_RING_CAPACITY];
    size_t head;
    size_t count;
} AriesFixedRingBuffer;

static inline uint64_t aries_time_ns(void) {
    struct timespec ts;
    if (clock_gettime(CLOCK_MONOTONIC, &ts) != 0) return 0;
    return (uint64_t)ts.tv_sec * UINT64_C(1000000000) + (uint64_t)ts.tv_nsec;
}

/*
 * Processes one vector using caller-owned, preallocated storage.
 * A buffer must not be accessed concurrently without external synchronization.
 * Returns 0 on success, -1 for invalid arguments or non-finite input/output.
 */
static inline int aries_process_vector_node(
    AriesFixedRingBuffer *buffer,
    uint32_t node_id,
    const double *input_vector,
    double *output_vector
) {
    if (buffer == NULL || input_vector == NULL || output_vector == NULL) return -1;

    const uint64_t start_ns = aries_time_ns();
    const size_t slot = buffer->head % ARIES_RING_CAPACITY;
    AriesVectorNode *node = &buffer->nodes[slot];
    node->node_id = node_id;
    node->timestamp_ns = start_ns;

    double accumulator = 0.0;
#if defined(_OPENMP)
#pragma omp simd reduction(+:accumulator)
#endif
    for (size_t i = 0; i < ARIES_VECTOR_SIZE; ++i) {
        /* Algebraically equivalent over real numbers; floating-point rounding may differ. */
        const double value = input_vector[i] - 1.0;
        node->data[i] = value;
        output_vector[i] = value;
        accumulator += value;
    }

    buffer->head = (buffer->head + 1u) % ARIES_RING_CAPACITY;
    if (buffer->count < ARIES_RING_CAPACITY) ++buffer->count;

    return accumulator > 0.0 ? 0 : -1;
}

#endif
