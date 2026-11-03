# Benchmark evidence

## Luna Fast latency

The matched HTTP benchmark alternated baseline and Fast order over two rounds of nine synthetic fixtures. Both arms received identical semantic inputs. The benchmark recorded HTTP request time separately from CLI startup and confirmed the provider actually served Fast for all 18 candidate responses. The baseline used the production-style request with no explicit tier and did not report its served tier.

| Measure | Baseline | Fast |
| --- | ---: | ---: |
| Requests passing quality checks | 18/18 | 18/18 |
| Median HTTP latency | 1,135.5 ms | 971.5 ms |
| p95 HTTP latency | 2,131 ms | 1,457 ms |

The overall median decreased 14.4%. The median of the per-pair gains was 245.5 ms. An earlier nine-trial native measurement using generated speech recorded a median 1,427 ms from release to simulated insertion, including 1,315 ms of service wait. The two benchmarks measured different parts of the path.

## Recognition prompt decision

The new prompt explicitly asked for abandoned-start removal and contextually clear sound-alike repair. The candidate ran through Nalu’s native client against a staged service.

| Check | Candidate result |
| --- | --- |
| Budget sound-alike and a second clear mishearing | Both corrected |
| Literal “spinning,” a direct quote, and ambiguous wording | Preserved |
| Abandoned start and a restart containing a price and negation | Cleaned up, with facts preserved |
| Conditional wording | Preserved |
| Broader 24-case reference suite | 20 passed, 1 failed, 3 unrun |

The failing fixture contained explicit paragraphs. The candidate preserved normalized words and returned the expected line count, but differed from the exact reference. A separate run on the live prompt reproduced that mismatch. The live prompt also passed the budget sound-alike case in a separate run. The candidate stayed in staging.

These are synthetic tests. They provide evidence about the measured inputs and checks. Real-world edit rate and meaning preservation across speakers remain unmeasured.

[Sanitized latency rows](latency-results.json) · [Sanitized prompt results](prompt-results.json)
