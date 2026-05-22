# 4 Solution Model

This section demonstrates and explains the solution model proposed in this study.

## 4.1 Overview

This study does not focus on technical cybersecurity detection (e.g., network logs or intrusion detection), but rather on organizational risk signals derived from communication, governance processes, and decision-making contexts.

### Model Architecture

The C2M model is conceptualized as a multi-agent system designed to support probabilistic inference of cyber crisis emergence.

![Figure 2 - Model for Cyber Crisis Management](figures/c2m_model.png)

**Figure 2.** Model for cyber crisis management (C2M).

The model contains three supervisory agents:

1. Organizational Environment
2. Risk Management
3. Disaster and Recovery

Each supervisory agent is responsible for coordinating subordinate agents.

---

## 4.2 Organizational Data Acquisition and Communication Levels

Communication is a fundamental principle within a business.

The model explores three communication levels:

- Interactive communication (meetings)
- Active communication (reports and e-mails)
- Passive communication (policies and governance documents)

![Figure 4 - PMBOK Communication Levels](figures/pmbok_communication.png)

**Figure 4.** Communication according to PMBOK 7th Edition.

---

## 4.3 Semantic Representation and Conformity Factor

After textual extraction, the system transforms organizational content into dense vector embeddings.

### Cosine Similarity

$$
Similarity(t,d_i)=\frac{E(t)\cdot E(d_i)}
{\|E(t)\|\|E(d_i)\|}
$$

where:

- $t$ = meeting transcript
- $d_i$ = organizational document

### Conformity Factor

$$
CF = 1 - Similarity
$$

where:

- CF ≈ 0 → strong governance alignment
- CF ≈ 1 → governance divergence

---

## 4.4 Decision-Making: Initial Filtering

The decision tree considers:

- Sentiment polarity
- Alert words
- Similarity to previous crises
- Human feedback
- Governance context

---

## 4.5 Monte Carlo Crisis Inference Model

The model performs Monte Carlo simulation using 50,000 scenarios.

### 4.5.1 Stochastic Variables

| Variable | Symbol | Distribution |
|-----------|----------|--------------|
| Organizational Sentiment | SS | Triangular |
| Organizational Maturity | MM | Truncated Normal |
| Continuity Plan | PP | Bernoulli |
| Historical Events | HH | Poisson |
| Governance Conformity | CC | Fixed Semantic Factor |

### Sentiment

$$
SS \sim Triangular(a,b,c)
$$

### Organizational Maturity

$$
MM \sim N(\mu,\sigma)
$$

### Historical Events

$$
HH \sim Poisson(\lambda)
$$

---

## 4.5.2 Crisis Probability Function

The probability of cyber crisis is calculated as:

$$
P=
w_1SS+
w_2MM+
w_3PP+
w_4HH+
w_5CC
$$

Subject to:

$$
0 \le P \le 1
$$

---

## 4.5.3 Statistical Aggregation

Mean probability:

$$
\bar P =
\frac{1}{N}
\sum_{i=1}^{N}
P_i
$$

Standard deviation:

$$
\sigma=
\sqrt{
\frac{\sum(P_i-\bar P)^2}
{N-1}
}
$$

95% confidence interval:

$$
CI_{95\%}
=
[P_{2.5},P_{97.5}]
$$

---

## 4.5.4 Contributing Factors Analysis

Pearson correlation:

$$
r=
\frac{
\sum (x_i-\bar x)(y_i-\bar y)
}{
\sigma_x\sigma_y
}
$$

---

## 4.6 ISO 22324 Crisis Classification

| Probability | Level | Action |
|------------|--------|---------|
| 0.00 – 0.20 | Green | Monitor |
| 0.20 – 0.40 | Yellow | Prepare |
| 0.40 – 0.70 | Orange | Activate Crisis Committee |
| ≥ 0.70 | Red | Declare Crisis |

---

## 4.7 Feedback and Continuous Learning

The model applies Reinforcement Learning from Human Feedback (RLHF).

Managers evaluate:

- Correctness
- Usefulness
- Timeliness
- Relevance

Feedback is incorporated into future assessments.

---

## 4.8 System Implementation

The implementation includes:

- FastAPI REST APIs
- PostgreSQL
- Redis
- FAISS (optional)
- Sentence Transformers
- NumPy Monte Carlo Engine
- ISO Classification Services

### Main Components

```text
/app/services/monte_carlo.py
/app/services/vector_search.py
/app/ml/embedder.py