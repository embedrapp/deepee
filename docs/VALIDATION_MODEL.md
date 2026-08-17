# Deterministic validation model

DeepEE evaluates declared engineering contracts, not visual similarity to a reference answer. A task passes only when every critical requirement passes. Compilation, ERC, and DRC are feasibility gates; they are never treated as proof of functional completeness by themselves.

## Evidence layers

1. **Deliverable:** required native files exist and are parseable.
2. **Integrity:** protected APIs, headers, and project rules are unchanged.
3. **Behavior:** verifier-owned vectors exercise normal, boundary, and regression behavior.
4. **Build:** the declared target toolchain produces the required output.
5. **Logical:** components, values, pin roles, and electrical connectivity satisfy the public contract.
6. **Electrical:** KiCad ERC validates the completed schematic.
7. **Physical:** pad nets, copper presence, track widths, routing metrics, board outline, and any stated pair constraints satisfy the public contract.
8. **Manufacturability:** KiCad DRC validates the completed board with warnings treated as violations.

Not every task uses every layer. A task may claim only properties that its requirements and oracles actually measure.

## Deterministic result

Each score contains a binary benchmark decision and a diagnostic vector. Requirement IDs are stable across a release. Leaf structural checks carry their measured evidence, and `metadata.hashes.decision` hashes only deterministic decision fields. Timestamps, host paths, and tool output do not affect that hash.

The binary result protects Pass@1 from partial-credit ambiguity. `quality_score` and `score_vector` are diagnostics; they do not rescue a critical failure.

## Verifier adequacy

The known-good solution for every task must pass. The release gate then creates a separate mutant for each critical requirement, runs the exact offline verifier, and requires the mapped requirement to fail. The benchmark cannot release if any supported critical mutant survives.

Mutations cover missing artifacts, protected-file tampering, restoration of buggy starter code, target-build failures, schematic component-contract violations, malformed ERC inputs, incomplete PCB repairs, and malformed DRC inputs. Physical PCB tests additionally include thin-copper and length-skew regression fixtures.

Mutation score measures the verifier, not the agent. A score of 100% means every declared critical requirement has at least one demonstrated negative case; it does not imply universal coverage of unspecified defects.

## Fairness and alternatives

- Every requirement affecting pass/fail is visible in `manifest.yaml` and described in the task prompt.
- Numerical tolerances and units are explicit.
- Validators inspect semantic connectivity and measured geometry instead of comparing whole files with a golden answer.
- A different implementation or layout passes when it satisfies the same contract.
- Tool versions, container platform, network policy, benchmark hash, task hash, and verifier image identity are recorded or pinned.

## Open-source threat model

Reference fixtures and mutation logic are public for auditability but excluded from both runtime images. The agent image has no task/verifier tree, each run receives only its prompt and starter, direct internet access is blocked, and allowed OpenAI traffic passes through the restricted proxy. Public availability still permits prior study or training contamination; published results must therefore state the agent version, benchmark hash, run policy, and first-attempt status.
