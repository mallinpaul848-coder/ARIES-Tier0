# ARIES/MALLIN Auditable Learning System

## Goal

Provide the foundations for broad, ongoing knowledge acquisition and evaluation-driven
software improvement across mathematics, computer science, engineering, physical and
life sciences, health, psychology, language, history, social sciences, law/civics,
arts, business, environment, and other explicitly registered subjects.

## Architecture

- **Subject registry:** an extensible taxonomy. A subject entry is not evidence of coverage or mastery.
- **Knowledge records:** content paired with a source name, source URL/reference, evidence label, review status, and tags.
- **Provenance-aware retrieval:** returns matching records with citations so a calling model can distinguish source material from unsupported recall.
- **Evaluation feedback:** records pass/fail/partial/needs-review outcomes.
- **Improvement proposals:** groups failures into reviewable work items, recommending root-cause analysis and held-out regression tests.
- **Audit log:** records additions, subject registration, and feedback timestamps.

## Self-improvement loop

1. Ingest only authorized source material and preserve provenance.
2. Validate schema, source accessibility, licensing, freshness, and trustworthiness in the ingesting application.
3. Index records and retrieve relevant passages for a task.
4. Evaluate answers against held-out references and safety checks.
5. Store failures and identify repeated patterns.
6. Propose code, prompt, retrieval, or training-data changes for review.
7. Test on separate regression and adversarial sets.
8. Require explicit approval before merge, deployment, or model-weight updates.
9. Monitor regressions and roll back when necessary.

This is controlled improvement, not unrestricted self-modification. The reference module does
not browse the web, download or execute arbitrary code, train weights, persist a database,
or deploy itself. Those require separate, permissioned integrations.

## About self-awareness

The system may maintain an inspectable operational self-model (available tools, model ID,
latency, confidence estimates, known limitations, and recent evaluation outcomes). That
is software state and self-monitoring; it does not establish subjective experience or
consciousness. Do not claim that ARIES is conscious or has human-like self-awareness.

## Validation

```bash
python -m unittest discover -s tests -p "test_learning_system.py" -v
```

Evaluate retrieval precision/recall, source attribution, freshness, citation correctness,
subject coverage, held-out task accuracy, calibration, abstention, safety regressions,
latency, and resource cost. Compare each change with a fixed baseline and report confidence
intervals. Do not claim general intelligence gains from code presence or passing unit tests alone.
