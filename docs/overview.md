# Ziz Project – Summary for Coding Agent

## Background & Motivation

The rapid growth of GenAI applications created a gap: startups lack lightweight tools to evaluate and improve AI outputs based on **real user experience**. Existing solutions focus on enterprise-grade evaluation or offline metrics, leaving small teams without practical ways to measure satisfaction, detect failure patterns, and run improvement cycles.

**Ziz** addresses this gap by building a **user-experience-driven evaluation framework** that turns user interactions (likes, edits, retries, etc.) into actionable insights. The ultimate goal is to help small AI teams **ship with confidence** by continuously validating and improving their AI outputs.

---

## Main Goals

1. **Low-friction integration** – Simple SDKs and APIs to log outputs and user interactions with minimal code changes.
2. **Real-time feedback ingestion** – Collect implicit and explicit UX signals from production use.
3. **Automated feature discovery** – Suggest which new metrics to track when satisfaction predictions are weak.
4. **Correlation → Causation** – Identify not just correlations but run experiments/natural tests to confirm drivers of satisfaction.
5. **Actionable analytics** – Provide dashboards and alerts that clearly explain where issues are and how to fix them.

---

## Product Components

### 1. **SDKs (Python, JavaScript)**

* Drop-in client libraries for logging outputs, user actions, and metadata.
* Patterns: decorators, context managers, or wrapper clients for minimal code change.
* Support environment-based configuration for quick setup.

### 2. **API for Uploading Outputs/Interactions**

* REST endpoints for submitting:

  * AI outputs (text, metadata)
  * User interactions (thumbs up/down, edits, re-prompts, copy/paste)
  * Session data (context, model version, latency)
* Batch and real-time modes.

### 3. **Ingestion System**

* Validates and stores incoming events.
* Handles schema, session enrichment, and queues for downstream processing.
* Scales horizontally to support many apps sending data.

### 4. **Analysis System**

* Correlation engine: detects patterns in dissatisfaction.
* Feature recommendation engine: suggests what new signals to track.
* Experiment manager: generates A/B tests or uses natural experiments to confirm causation.
* Stores validated causal graphs and improvement history.

### 5. **Frontend (Dashboards & Alerts)**

* Metrics dashboard: regen rate, satisfaction trends, edit ratios, etc.
* Alerts: notify when thresholds (e.g. dissatisfaction >20%) are crossed.
* Insights: prioritized recommendations in plain language, with implementation snippets.

---

## Current Focus

The team is currently working on the **core infrastructure**:

* **API + SDKs** for receiving outputs and interactions.
* **Storage layer** for structured event and session data.

This foundation will enable downstream analytics, feature discovery, and dashboards in later phases.
