# TVCG Resubmission Plan — VERA

Status legend: ⬜ not started · 🔲 in progress · ✅ done

---

## Priority 1: Parameter Sensitivity Analysis

**Raised by:** R1Q4, R2Q1, R2Q2, R2Q4, R3Q4
**Owner:** Pavlin
**Why critical:** All three reviewers flag this. This is the single most-repeated concern and addressing it convincingly will determine whether the paper is accepted.

### Approach

Generate VERA output under varying parameter settings on 2–3 datasets (e.g., Attrition, Abalone, one synthetic). For each parameter, produce 3–5 visualizations showing the effect. Include all of this in the supplementary material. In the paper, state default values with brief justifications and point to the supplementary for the full sensitivity analysis.

### 1.1 Number of bins (R1Q4, R2Q1, R2Q2)

⬜ State the default value in the paper.
⬜ Generate 3–5 VERA outputs per dataset with different bin counts.
⬜ Include visualizations in supplementary with a brief description of the effect.

### 1.2 Binning strategy (R2Q2)

⬜ Document in Section III-A.1 that the strategy is 1D k-means clustering.
⬜ Add brief justification: adapts to data distribution, avoids splitting natural clusters (unlike equidistant), avoids wasting bins on empty ranges. Cite connection to Jenks natural breaks / Fisher's exact 1D optimization.

### 1.3 KDE contour level (R1Q4, R2Q1, R3Q4)

⬜ State the default ($0.25 \times \max D$) and justify: traces the region where density is at least 25% of the peak — a common choice in KDE-based visualization. Cite precedents (splatterplots, DataContextMap, etc.).
⬜ Generate 3–5 VERA outputs per dataset with different contour levels (e.g., 0.1, 0.15, 0.25, 0.4, 0.6).
⬜ Include visualizations in supplementary.

### 1.4 Gaussian bandwidth $\sigma$ (R1Q4, R2Q1, R3Q4)

⬜ State the default (median $k$-NN distance, $k=\sqrt{N}$) and justify with citation to nearest-neighbor bandwidth selection literature.
⬜ Generate 3–5 VERA outputs per dataset with different bandwidth values.
⬜ Include visualizations in supplementary.

### 1.5 Overlap thresholds (R1Q4, R2Q1, R3Q4)

⬜ State the specific numeric values used for post-hoc merge threshold, contrastive "near-perfect" overlap threshold, and descriptive merge threshold.
⬜ Generate 3–5 VERA outputs per dataset varying the overlap thresholds.
⬜ Include visualizations in supplementary.

### 1.6 Ranking-related parameters (R2Q4, R2Q10) — written response only

⬜ In the cover letter, acknowledge that the human-attention score center and ranking weight choices are heuristic and that a systematic ablation is a natural direction for future work.
⬜ No experiments or visualizations needed for these.

### 1.7 Paper and supplementary structure

**Paper:**
⬜ Add one sentence at the end of Section III (Methods) or in Section V (Scalability and Limitations) stating that all parameters were set to reasonable defaults and that a parameter sensitivity analysis is provided in the supplementary material.
⬜ Find the best placement — likely the last paragraph of Section III before Section IV (Usage Scenarios), or the first paragraph of Scalability and Limitations.

**Supplementary — generation phase (working files):**
⬜ One markdown file per dataset collecting all parameter-variation figures for that dataset.

**Supplementary — final presentation:**
⬜ Organize by parameter, not by dataset. One section per parameter (bins, contour level, bandwidth, overlap thresholds), each showing a grid of (dataset × parameter value), e.g., 2–3 rows (datasets) × 3–5 columns (parameter values).
⬜ Add a concluding paragraph per section: "VERA's output is qualitatively stable across reasonable parameter ranges; the primary effect of varying X is Y."

---

## Priority 2: High-Dimensional Scalability — Scope Clarification

**Raised by:** R1Q3, R2Q9, R3Q3
**Owner:** Pavlin + Blaž
**Why addressed:** The introduction claims relevance for "tens of thousands of features" but VERA's descriptive annotations become cluttered and unreadable at high dimensionality. This is already acknowledged in the Scalability and Limitations section, but the introduction overpromises.

### Approach — writing fixes only, no new experiments

⬜ **Narrow the scope in the Introduction.** Tone down or remove the "tens of thousands of features" framing. Reframe VERA as targeting datasets with interpretable, moderate-dimensional feature sets (tens to low hundreds of features). Acknowledge that higher-dimensional data requires feature selection or summarization as a preprocessing step.
⬜ **Strengthen the Scalability and Limitations section.** Ensure it clearly states that descriptor length grows with dimensionality and that this is a practical limitation. Verify the existing LLM summarization discussion is prominent enough.
⬜ **Cover letter responses.** For R1Q3, R2Q9, R3Q3: point to the Scalability and Limitations section, acknowledge the limitation honestly, and note that the introduction has been revised to better reflect the method's scope. Mention LLM-based summarization and feature pre-filtering as concrete future directions.

---

## Priority 3: Positioning vs. Related Work (esp. Sohns et al.)

**Raised by:** R1Q1, R1Q2a, R1Q2b, R3Q2
**Owner:** Blaž (writing), Pavlin (implementation)

### 3.1 Abstract & Introduction uniqueness (R1Q1)

⬜ Revise the abstract to explicitly state what makes VERA different: automated explanation *generation* (filtering, ranking, selection), not just visual encoding.
⬜ Add 1–2 sentences to the introduction explicitly contrasting VERA with feature-encoding approaches like Sohns et al.
⬜ Emphasize the key differentiator: VERA automates the full pipeline (region construction → filtering → merging → ranking → layout), whereas prior work primarily provides visual encodings that leave pattern selection to the user.

### 3.2 Systematic comparison table in Related Work (R3Q2)

⬜ Add a comparison table (or structured prose) to Related Work covering ~5–8 key methods, with columns for:
  - Automation level (manual, semi-automatic, fully automatic)
  - Explanation type (contrastive, descriptive, both)
  - Requires clustering? (yes/no)
  - Handles continuous structures? (yes/no)
  - Output format (interactive, static, both)
  - DR-method agnostic? (yes/no)

### 3.3 Rangeset integration examples (already done partially)

⬜ Verify that the rangeset variant is implemented and generates good output.
⬜ Include 2–3 rangeset-based VERA examples in supplementary.
⬜ Ensure the paper text in Section III-A.2 references these examples.

---

## Priority 4: User Study Clarifications

**Raised by:** R2Q6, R2Q7, R3Q5

### 4.1 Supplement the user study materials (R2Q6)

⬜ Verify that supplementary materials include full question catalog, visualizations, and questionnaires.
⬜ Add example Orange workflows to supplementary (already mentioned in response).

### 4.2 Reframe the user study contribution (R3Q5)

⬜ Add a sentence in the User Evaluation results emphasizing that the main contribution is not a "slight improvement in accuracy" but rather *comparable accuracy with 33% less time*. This is already partially addressed in the cover letter response — make sure the paper text is equally clear.

---

## Priority 5: Remaining Individual Concerns

### 5.1 Misleading descriptive annotations (R2Q3) — Pavlin

⬜ Add a clarifying note (in Section III-C or in a figure caption) explaining that descriptive annotations characterize what is *enriched* in a region, not that the feature value is *exclusive* to that region.
⬜ Consider adding a visual cue (e.g., proportion bar, purity indicator) in the annotation to make this distinction clearer.

### 5.2 Occlusion problem (R2Q5) — Pavlin

⬜ Acknowledge the issue explicitly in the paper (Scalability/Limitations section).
⬜ Discuss potential solutions: transparency, outline-only regions, or showing non-colored points in a separate layer.
⬜ Optionally implement a simple fix (e.g., alpha blending) and show the improvement.

### 5.3 Projection artifacts in category merging (R2Q8) — Pavlin

⬜ Clarify the concern: if two categories overlap due to projection artifacts (not real similarity), the merge may be misleading.
⬜ Note that VERA's distortion-weighting mechanism (Section III-A.2) partially mitigates this.
⬜ Add a sentence acknowledging the limitation for cases where distortion measures are unavailable.

### 5.4 Class label used as feature — Iris/Penguins (R2Q11) — Pavlin

⬜ Add a sentence clarifying that the class label was *not* used as an input feature for dimensionality reduction, only as an explanatory feature for VERA.
⬜ Explain briefly why this is appropriate in an EDA context (checking how well the embedding separates known classes is a standard use case).

### 5.5 Multiple visualizations needed (R1Q7) — Pavlin

⬜ Acknowledge that VERA still produces multiple panels (e.g., Fig 8a–d), but argue this is by design: each panel conveys a different aspect of the embedding (contrastive vs. descriptive, different features).
⬜ Compare to the alternative: without VERA, the user would need to inspect *many more* individual feature-colored scatter plots.
⬜ Mention that the number of panels is user-configurable.

### 5.6 Merged vs. separate visualizations (R1Q5) — Pavlin

⬜ Write the cover letter response explaining the benefit of merged panels (space reduction, reveals correlations, including nonlinear ones).
⬜ Optionally add a brief discussion in the paper.

### 5.7 KDE motivation (R3Q1) — Pavlin

⬜ Strengthen the KDE justification in Section III-A.2:
  - Cite precedent (splatterplots, DataContextMap, etc.)
  - List advantages: cluster-free, scalable (linear time via FFT), naturally incorporates distortion weighting
  - Mention modularity (rangesets as alternative)

### 5.8 Long descriptions / LLM summarization (R1Q6)

✅ Response is already written. No further action needed unless the high-dimensional demo (Priority 2) makes this more urgent.

---

## Execution Order

The recommended order of work, accounting for dependencies:

1. **Parameter catalog & justification** (1.1–1.2) — needed before any experiments
2. **Binning strategy** (1.3) — may affect downstream experiments
3. **Sensitivity sweep** (1.5) + **Ranking ablation** (1.4) — can be run together
4. **High-dimensional demo** (2.1–2.4) — independent of above, can be parallelized
5. **Related work positioning** (3.1–3.3) — mostly writing, can happen in parallel
6. **Individual fixes** (5.1–5.7) — small, independent, do last or in gaps
7. **User study supplements** (4.1–4.2) — quick, do anytime

Target: complete experimental work (items 1–4) first, then writing (items 3, 5, 6, 7).
