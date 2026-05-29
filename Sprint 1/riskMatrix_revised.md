# Risk and Opportunity Matrix – Sprint 1 (Revised)

## Introduction

In Sprint 1, the group developed the initial risk and opportunity matrix for the Bayer Decision Agriculture project.

This stage focuses on mapping the primary uncertainties regarding the analysis of the ~320k rows dataset, the integration of public APIs (INMET/NOAA), the business problem framing, and the macro-environmental analysis (PESTEL). The risk assessment aligns with the project deliverables and the specific task distribution among the team members.

The matrix below presents the identified risks and opportunities, the fundamental justifications for their ratings, and the concrete action plans established to control them throughout the sprint.

This revision responds to the Sprint 1 evaluation feedback: action plans for R4 and R6 were rewritten to address the specific failure mode of each risk rather than defaulting to coordination activities, and a dedicated Top 3 Risks prioritization section was added between the register and the conclusion.

## Risks

| Risk | Prob. (%) | Impact | Grade / Intensity | Fundamental Justification | Risk Response | Action Plan (Summary) | Owner / Function | Date Identified |
|---|---|---|---|---|---|---|---|---|
| **Inconsistencies in the core dataset (R1)** | 60% | Very High | Critical | The ~320k rows dataset may contain missing values or outliers in crucial variables (e.g., singulation, CV%), which directly compromises the simulator's logic. | Mitigate | Execute strict EDA to identify nulls and establish clear statistical dropping or imputation rules. | Arthur Almeida & João Cauê / Data Analysis | 29/Apr/2026 |
| **API rate limits or downtime (R2)** | 40% | High | Elevated | Relying on external public sources (INMET/Sentinel) introduces a technical dependency on third-party uptime for the simulator's inputs. | Mitigate | Download a static historical sample to serve as a local cache/mock backend during the development phases. | Yan Kruziski / Risk Matrix | 29/Apr/2026 |
| **Misalignment in Problem Framing (R3)** | 30% | Very High | Critical | Framing the wrong decision variables could render the final simulator impractical for Bayer's Farmers Insights Squad. | Mitigate | Validate the specific decision thresholds directly with Bayer stakeholders during the initial alignment workshop. | João Agmont / Problem Framing | 29/Apr/2026 |
| **Superficial PESTEL Analysis (R4)** | 40% | Moderate | Relevant | Delivering generic macro factors without mathematically connecting them to the ROI of the planting strategy reduces the artifact's utility. | Avoid | Enforce a depth standard before submission: each PESTEL factor must include (1) a quantified market sizing (e.g., R$ value of the Brazilian soybean/corn segment affected), (2) at least one specific regulatory citation (law, normative instruction, or ANVISA/MAPA reference where applicable), and (3) a financial impact estimate tied to Bayer's planting strategy ROI (e.g., expected cost or revenue delta in R$/ha). Cross-review with the Framing team is kept as a secondary check, executed only after the depth criteria are met. | Rafael Skitch / PESTEL | 29/Apr/2026 |
| **Retroactive GitLab management penalties (R5)** | 50% | High | Elevated | Inteli's evaluation strictly penalizes retroactive issue tracking, directly lowering the individual performance factor score. | Mitigate | Implement a daily check to ensure all artifact tasks are updated in the "Doing" and "Testing" columns. | Miguel Almeida / PESTEL | 29/Apr/2026 |
| **Scope creep toward legacy systems (R6)** | 20% | High | Relevant | The team might waste resources attempting to integrate the prototype with Bayer's internal systems, which is expressly out of scope. | Avoid | **Prevention:** explicitly document the out-of-scope boundaries within the Problem Framing deliverable. **Contingency** (if a scope addition request from Bayer arrives mid-sprint before the boundaries are formally documented): (1) the receiving member logs the request immediately in GitLab as a `scope-evaluation` issue, with no commitment to delivery; (2) the Problem Framing owner runs a same-day go/no-go check against the current scope skeleton and documents the decision in the issue; (3) any item that cannot be accepted within the current sprint scope is deferred to the next sprint planning with a written rationale, preserving the audit trail required by Inteli's evaluation. | João Agmont / Problem Framing | 29/Apr/2026 |

## Opportunities

| Opportunity | Prob. (%) | Impact | Grade / Intensity | Fundamental Justification | Opportunity Response | Action Plan (Summary) | Owner / Function | Date Identified |
|---|---|---|---|---|---|---|---|---|
| **High correlation findings in EDA (O1)** | 70% | High | Elevated | Finding strong statistical correlations early between public weather data and planting efficiency creates a solid base for the decision tree. | Exploit | Highlight specific variable correlations in the EDA report to directly guide the logic of Sprint 3. | João Cauê / Data Analysis | 29/Apr/2026 |
| **Strategic differentiation via PESTEL (O2)** | 60% | High | Elevated | A deep, quantified analysis of Brazilian agribusiness volatility provides a unique angle for the subsequent Payoff Matrix. | Enhance | Quantify market sizes and regulatory impacts within the PESTEL document instead of just listing qualitative factors. | Ariel Mouadeb / PESTEL | 29/Apr/2026 |
| **Establishing a reusable Risk Framework (O3)** | 80% | Moderate | Relevant | Building a highly structured matrix now accelerates the mandatory update process required in all subsequent sprints. | Exploit | Keep the matrix mapping directly tied to the workflow, allowing rapid status updates for Sprint 2. | Yan Kruziski / Risk Matrix | 29/Apr/2026 |

## Top 3 Risks – Prioritization

Severity grade alone does not capture how a risk will behave across the remaining sprints. The three risks below were prioritized using two additional criteria beyond probability × impact: (a) **propagation cost** — how many downstream deliverables inherit the failure if the risk materializes, and (b) **recovery asymmetry** — whether the failure is gradual and partially recoverable, or categorical and unrecoverable without rework.

### 1. R1 — Inconsistencies in the core dataset

**Why it leads the priority list.** R1 has the highest combined severity (60% × Very High = Critical) and sits at the top of the propagation chain: every quantitative deliverable in the project consumes the cleaned dataset. Feature engineering in Sprint 2, the decision-tree logic in Sprint 3, the payoff matrix, and the final simulator all inherit any defect introduced (or missed) during the Sprint 1 EDA.

**Cross-sprint impact if not mitigated.** A corrupted variable is invisible in summary slides but distorts the simulator's recommendations downstream. Detection cost grows exponentially across sprints — fixing an outlier rule in Sprint 1 is cheap; fixing it after the decision tree has been trained means re-running every dependent artifact. There is no compensating control later in the pipeline that can recover a silently wrong input.

### 2. R3 — Misalignment in Problem Framing

**Why it ranks second despite a lower probability.** R3's probability (30%) is lower than R1's, but the failure mode is *categorical* rather than gradual: if the decision variables encode the wrong question, no amount of downstream technical quality can recover the artifact. R3 has the highest rework cost of any item on the register — realizing this risk in Sprint 2 or Sprint 3 effectively resets the project. Bayer's Farmers Insights Squad is explicitly named as the stakeholder whose expectations define correctness, so the failure is also externally visible and not recoverable by internal iteration alone.

**Cross-sprint impact if not mitigated.** PESTEL ROI would be tied to the wrong outcome variable; the decision tree would learn a target the customer does not value; the final simulator would deliver an answer the squad cannot act on. Recovery requires returning to Sprint 1 deliverables and re-validating with Bayer — a cost the remaining sprint budget cannot absorb.

### 3. R5 — Retroactive GitLab management penalties

**Why it is in the top three despite an Elevated (not Critical) grade.** R5 is structurally different from the other risks: its failure mode is *recurring across every sprint of the module*, not contained to a single deliverable. The 50% probability reflects how routine the slip is, and the impact compounds because Inteli's individual performance factor is evaluated cumulatively. R2 sits at the same severity tier but its mitigation (static cache) is a one-time investment whose payoff persists; R5 requires sustained daily discipline and degrades silently if neglected.

**Cross-sprint impact if not mitigated.** Each sprint's individual evaluation factor is lowered, and the deficit compounds across the module because there is no retroactive recovery — once a sprint window closes, evidence cannot be backfilled. Unlike technical risks, R5 cannot be fixed by a single deliverable; it requires a daily routine that must be in place before Sprint 2 begins.

### Why these three, and not R2

R2 (API rate limits) is tied with R5 on severity grade but was placed below the cut. The mitigation for R2 is a bounded, one-time engineering action (download a static historical sample, ship a mock backend), and once executed it neutralizes the risk for the remainder of the project. R5, by contrast, is open-ended and recurring. Concentrating top-three attention on R1, R3, and R5 covers the three failure modes whose realization would be hardest to undo: a corrupted dataset, a misframed problem, and a sustained process penalty.

## Visual Map

The risk and opportunity heat map from the original artifact (Probability rows 1–5 × Impact columns A–J) remains valid: none of the probability or impact ratings were changed in this revision — only the action-plan content for R4 and R6 was rewritten. Refer to the heat map in `riskMatrix.pdf` for the visual placement of R1–R6 and O1–O3.

## Conclusion

Sprint 1 establishes the analytical and strategic foundation for the decision-making simulator. The primary risks identified relate to data integrity within the EDA phase and the accuracy of the strategic alignment in the Problem Framing, with retroactive GitLab management representing the principal process risk that will recur across every subsequent sprint.

The application of action plans by the respective artifact owners ensures that technical dependencies (such as external APIs) and internal agile management (GitLab tracking) are controlled early. Parallelly, the depth required in the PESTEL and EDA deliverables opens clear opportunities to strengthen the mathematical and business logic that will be demanded in upcoming sprints.

This matrix is a living document and will be reviewed at the beginning of Sprint 2. The Sprint 2 review will, in addition to status updates on R1–R6 and O1–O3, introduce at least one new risk under the **team and communication** category — a gap identified by the Sprint 1 evaluation — addressing coordination and quality-standard consistency across sub-teams working on parallel deliverables.
