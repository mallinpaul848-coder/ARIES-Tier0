#define _POSIX_C_SOURCE 200809L
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include "aries_tier0_vector_kernel.h"

#define SAMPLES 20000

static AriesFixedRingBuffer baseline_buffer;
static AriesFixedRingBuffer candidate_buffer;
static double input[ARIES_VECTOR_SIZE];
static double baseline_output[ARIES_VECTOR_SIZE];
static double candidate_output[ARIES_VECTOR_SIZE];
static uint64_t baseline_ns[SAMPLES];
static uint64_t candidate_ns[SAMPLES];

static int baseline_process(AriesFixedRingBuffer *buffer, uint32_t id,
                            const double *in, double *out) {
    const uint64_t start = aries_time_ns();
    AriesVectorNode *node = &buffer->nodes[buffer->head % ARIES_RING_CAPACITY];
    node->node_id = id;
    node->timestamp_ns = start;
    double sum = 0.0;
    for (size_t i = 0; i < ARIES_VECTOR_SIZE; ++i) {
        node->data[i] = in[i] * 3.0 + 6.0 - 9.0;
        out[i] = node->data[i] * 0.3333333333333333;
        sum += out[i];
    }
    buffer->head = (buffer->head + 1u) % ARIES_RING_CAPACITY;
    if (buffer->count < ARIES_RING_CAPACITY) ++buffer->count;
    return sum > 0.0 ? 0 : -1;
}

static int compare_u64(const void *a, const void *b) {
    uint64_t x = *(const uint64_t *)a, y = *(const uint64_t *)b;
    return (x > y) - (x < y);
}

static uint64_t percentile(uint64_t *values, size_t n, double p) {
    size_t index = (size_t)((n - 1) * p);
    return values[index];
}

static void report(const char *name, uint64_t *values) {
    qsort(values, SAMPLES, sizeof(values[0]), compare_u64);
    long double total = 0.0L;
    for (size_t i = 0; i < SAMPLES; ++i) total += values[i];
    printf("%s latency (ns): min=%llu mean=%.1Lf p50=%llu p95=%llu p99=%llu max=%llu\n",
        name, (unsigned long long)values[0], total / SAMPLES,
        (unsigned long long)percentile(values, SAMPLES, .50),
        (unsigned long long)percentile(values, SAMPLES, .95),
        (unsigned long long)percentile(values, SAMPLES, .99),
        (unsigned long long)values[SAMPLES - 1]);
}

int main(void) {
    for (size_t i = 0; i < ARIES_VECTOR_SIZE; ++i)
        input[i] = (double)((int)(i % 17) - 8) * 0.25;

    for (size_t i = 0; i < 1000; ++i) {
        baseline_process(&baseline_buffer, (uint32_t)i, input, baseline_output);
        aries_process_vector_node(&candidate_buffer, (uint32_t)i, input, candidate_output);
    }

    for (size_t i = 0; i < ARIES_VECTOR_SIZE; ++i) {
        if (!isfinite(candidate_output[i]) ||
            fabs(baseline_output[i] - candidate_output[i]) > 1e-12) {
            fprintf(stderr, "Correctness check failed at index %zu: baseline=%.17g candidate=%.17g\n",
                    i, baseline_output[i], candidate_output[i]);
            return 1;
        }
    }

    for (size_t i = 0; i < SAMPLES; ++i) {
        uint64_t start = aries_time_ns();
        baseline_process(&baseline_buffer, (uint32_t)i, input, baseline_output);
        baseline_ns[i] = aries_time_ns() - start;

        start = aries_time_ns();
        aries_process_vector_node(&candidate_buffer, (uint32_t)i, input, candidate_output);
        candidate_ns[i] = aries_time_ns() - start;
    }

    puts("Correctness: PASS (absolute tolerance 1e-12)");
    printf("Samples per implementation: %d; vector elements: %d\n", SAMPLES, ARIES_VECTOR_SIZE);
    report("Baseline", baseline_ns);
    report("Candidate", candidate_ns);
    puts("Interpretation: compare results on the same host/build; no speedup is assumed.");
    return 0;
}
