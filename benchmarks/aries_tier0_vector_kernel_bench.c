#define _POSIX_C_SOURCE 200809L
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include "aries_tier0_vector_kernel.h"

#define TRIALS 5
#define SAMPLES_PER_TRIAL 4000
#define SAMPLES (TRIALS * SAMPLES_PER_TRIAL)
#define WARMUP_SAMPLES 1000

static AriesFixedRingBuffer baseline_buffer;
static AriesFixedRingBuffer candidate_buffer;
static double input[ARIES_VECTOR_SIZE];
static double baseline_output[ARIES_VECTOR_SIZE];
static double candidate_output[ARIES_VECTOR_SIZE];
static uint64_t baseline_ns[SAMPLES];
static uint64_t candidate_ns[SAMPLES];
static uint32_t order_seed = UINT32_C(0xA71E5);

static uint32_t next_random(void) {
    /* Deterministic xorshift32 makes the execution order reproducible. */
    uint32_t x = order_seed;
    x ^= x << 13;
    x ^= x >> 17;
    x ^= x << 5;
    order_seed = x;
    return x;
}

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
    /* Nearest-rank percentile, using a 1-based rank. */
    size_t rank = (size_t)ceil(p * (double)n);
    if (rank < 1) rank = 1;
    if (rank > n) rank = n;
    return values[rank - 1];
}

static void report(const char *name, const uint64_t *source, size_t n) {
    uint64_t *values = malloc(n * sizeof(*values));
    if (values == NULL) {
        fprintf(stderr, "Allocation failed while reporting %s\n", name);
        exit(EXIT_FAILURE);
    }
    for (size_t i = 0; i < n; ++i) values[i] = source[i];
    qsort(values, n, sizeof(values[0]), compare_u64);
    long double total = 0.0L;
    for (size_t i = 0; i < n; ++i) total += values[i];
    printf("%s latency (ns; n=%zu): min=%llu mean=%.2Lf p50=%llu p95=%llu p99=%llu max=%llu\n",
        name, n, (unsigned long long)values[0], total / (long double)n,
        (unsigned long long)percentile(values, n, .50),
        (unsigned long long)percentile(values, n, .95),
        (unsigned long long)percentile(values, n, .99),
        (unsigned long long)values[n - 1]);
    free(values);
}

static int outputs_match(void) {
    for (size_t i = 0; i < ARIES_VECTOR_SIZE; ++i) {
        if (!isfinite(candidate_output[i]) ||
            fabs(baseline_output[i] - candidate_output[i]) > 1e-12) {
            fprintf(stderr,
                "Correctness check failed at index %zu: baseline=%.17g candidate=%.17g\n",
                i, baseline_output[i], candidate_output[i]);
            return 0;
        }
    }
    return 1;
}

int main(void) {
    size_t baseline_first = 0, candidate_first = 0;

    for (size_t i = 0; i < ARIES_VECTOR_SIZE; ++i)
        input[i] = (double)((int)(i % 17) - 8) * 0.25;

    for (size_t i = 0; i < WARMUP_SAMPLES; ++i) {
        baseline_process(&baseline_buffer, (uint32_t)i, input, baseline_output);
        aries_process_vector_node(&candidate_buffer, (uint32_t)i, input, candidate_output);
    }
    if (!outputs_match()) return EXIT_FAILURE;

    for (size_t trial = 0; trial < TRIALS; ++trial) {
        const size_t offset = trial * SAMPLES_PER_TRIAL;
        for (size_t i = 0; i < SAMPLES_PER_TRIAL; ++i) {
            const size_t index = offset + i;
            /* Randomize which implementation runs first in every matched pair. */
            if ((next_random() & 1u) == 0u) {
                uint64_t start = aries_time_ns();
                baseline_process(&baseline_buffer, (uint32_t)index, input, baseline_output);
                baseline_ns[index] = aries_time_ns() - start;
                start = aries_time_ns();
                aries_process_vector_node(&candidate_buffer, (uint32_t)index, input, candidate_output);
                candidate_ns[index] = aries_time_ns() - start;
                ++baseline_first;
            } else {
                uint64_t start = aries_time_ns();
                aries_process_vector_node(&candidate_buffer, (uint32_t)index, input, candidate_output);
                candidate_ns[index] = aries_time_ns() - start;
                start = aries_time_ns();
                baseline_process(&baseline_buffer, (uint32_t)index, input, baseline_output);
                baseline_ns[index] = aries_time_ns() - start;
                ++candidate_first;
            }
            if ((index % 256u) == 255u && !outputs_match()) return EXIT_FAILURE;
        }
        printf("Trial %zu/%d\n", trial + 1, TRIALS);
        report("  Baseline", baseline_ns + offset, SAMPLES_PER_TRIAL);
        report("  Candidate", candidate_ns + offset, SAMPLES_PER_TRIAL);
    }

    puts("Correctness: PASS (absolute tolerance 1e-12; checked during measurement)");
    printf("Trials: %d independent measurement blocks; samples per implementation per trial: %d\n",
           TRIALS, SAMPLES_PER_TRIAL);
    printf("Vector elements: %d; warmup pairs: %d; order seed: 0x%08x\n",
           ARIES_VECTOR_SIZE, WARMUP_SAMPLES, UINT32_C(0xA71E5));
    printf("Pair order: baseline-first=%zu candidate-first=%zu\n", baseline_first, candidate_first);
    report("OVERALL baseline", baseline_ns, SAMPLES);
    report("OVERALL candidate", candidate_ns, SAMPLES);
    puts("Interpretation: compare same-host/build runs; randomized order reduces ordering bias.");
    puts("Five blocks on one process are not five independent machine/process runs; no speedup is assumed.");
    return EXIT_SUCCESS;
}
