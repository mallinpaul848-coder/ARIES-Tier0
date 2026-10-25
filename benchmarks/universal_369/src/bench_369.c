#define _POSIX_C_SOURCE 200809L
#include <inttypes.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include "mallin_369_kernel.h"

static uint64_t now_ns(void) {
    struct timespec ts;
    if (clock_gettime(CLOCK_MONOTONIC, &ts) != 0) {
        perror("clock_gettime");
        exit(EXIT_FAILURE);
    }
    return (uint64_t)ts.tv_sec * UINT64_C(1000000000) + (uint64_t)ts.tv_nsec;
}

static int cmp_u64(const void *a, const void *b) {
    uint64_t x = *(const uint64_t *)a, y = *(const uint64_t *)b;
    return (x > y) - (x < y);
}

static uint64_t percentile(const uint64_t *sorted, size_t n, double p) {
    size_t i = (size_t)ceil(p * (double)n);
    if (i == 0) i = 1;
    if (i > n) i = n;
    return sorted[i - 1];
}

int main(int argc, char **argv) {
    uint64_t iterations = UINT64_C(10000000);
    if (argc > 1) {
        char *end = NULL;
        unsigned long long parsed = strtoull(argv[1], &end, 10);
        if (!end || *end != '\0' || parsed == 0) {
            fprintf(stderr, "Usage: %s [iterations>0]\n", argv[0]);
            return EXIT_FAILURE;
        }
        iterations = (uint64_t)parsed;
    }

    const size_t samples = 101;
    uint64_t times[samples];
    volatile double sink = 0.0;
    mallin_vec3 x = {{1.0, 2.0, 3.0}};

    for (size_t s = 0; s < samples; ++s) {
        uint64_t start = now_ns();
        for (uint64_t i = 0; i < iterations; ++i) {
            x.v[0] += 0.0000001;
            if (x.v[0] > 1000.0) x.v[0] = 1.0;
            mallin_vec3 y = mallin_369_transform(x);
            sink += y.v[i % 3] * 0.000000001;
        }
        uint64_t stop = now_ns();
        times[s] = stop - start;
    }

    qsort(times, samples, sizeof(times[0]), cmp_u64);
    uint64_t total = 0;
    for (size_t i = 0; i < samples; ++i) total += times[i];
    double mean_ns = (double)total / (double)samples;
    double mean_op_ns = mean_ns / (double)iterations;
    double ops_s = mean_op_ns > 0.0 ? 1.0e9 / mean_op_ns : 0.0;

    printf("kernel=mallin_369_transform\n");
    printf("iterations_per_sample=%" PRIu64 "\n", iterations);
    printf("samples=%zu\n", samples);
    printf("sample_min_ns=%" PRIu64 "\n", times[0]);
    printf("sample_mean_ns=%.2f\n", mean_ns);
    printf("sample_p50_ns=%" PRIu64 "\n", percentile(times, samples, 0.50));
    printf("sample_p95_ns=%" PRIu64 "\n", percentile(times, samples, 0.95));
    printf("sample_p99_ns=%" PRIu64 "\n", percentile(times, samples, 0.99));
    printf("sample_max_ns=%" PRIu64 "\n", times[samples - 1]);
    printf("mean_ns_per_transform=%.6f\n", mean_op_ns);
    printf("estimated_transforms_per_second=%.2f\n", ops_s);
    printf("sink=%.12f\n", sink);
    printf("note=single-process microbenchmark; not third-party validation\n");
    return EXIT_SUCCESS;
}
