# FRAUD AUDITOR: VISUAL ANALYTICS FOR COLLUSIVE FRAUD IN HEALTH INSURANCE

## Overview

**Fraud Auditor** is a Visual Analytics system designed to detect **Collusive Fraud** in the health insurance sector. Unlike traditional systems that look at individual claims, Fraud Auditor uses **Graph Theory (Network Analytics)** to identify suspicious connections between Healthcare Providers (Doctors) and Patients.

It detects "Collusion Rings" (Cliques) where a group of patients and providers work together to maximize claim payouts. This system currently demonstrates these capabilities using a sophisticated **Synthetic Data Generator** that embeds specific, complex fraud patterns into a dataset of honest claims.

## Key Features

- **Graph-Based Detection**: Models claims as a network graph (Nodes = Doctors/Patients, Edges = Claims).
- **Community Detection Algorithm**: Automatically identifies dense subgraphs ("Cliques") indicative of collusion.
- **Visual Analytics Dashboard**: Interactive Network Graph using **Vis.js** to visualize connections and zoom into suspicious communities.
- **Advanced Synthetic Data**: Generates realistic "Honest" traffic (the haystack) and embeds 4 distinct "Fraud Rings" (the needles):
  1.  **"Kickback Surgeons"**: High-cost knee surgeries with a small, dense group of patients.
  2.  **"Phantom Billing"**: Massive volume of low-cost visits by a single provider.
  3.  **"Ambulance Chasers"**: Circular flow (Patient -> Ambulance -> Surgeon) for maximizing per-incident billing.
  4.  **"Therapy Mill"**: High connectivity, recurring small charges for therapy sessions.
- **Simple & Fast**: Built with FastAPI and NetworkX for lightweight, efficient analysis.

## Architecture

- **Backend**: Python (FastAPI + NetworkX).
- **Frontend**: HTML5 + Vis.js (Network Visualization).
- **Logic**:
  1.  **Generate Data**: Create a dataframe with 3500+ claims, mixing honest transactions with specific fraud signatures.
  2.  **Build Graph**: Construct a weighted network based on patient-provider interactions and costs.
  3.  **Detect Communities**: Identify isolated components and calculate density/risk scores.
  4.  **Visualize**: Render the high-risk communities for manual auditing.

## Installation & Usage

### 1. Install Dependencies

```bash
pip install -r requirements.txt

./venv/scripts/activate

```

### 2. Run the Application

```bash
uvicorn app:app --reload
```

The server will start at `http://127.0.0.1:8000`.

### 3. Detect Fraud

1.  Open `http://127.0.0.1:8000` in your browser.
2.  Click **"Load Dataset"**:
    - This triggers the synthetic data generator.
    - A preview of the raw claims data will appear.
3.  Click **"Audit Network"**:
    - The system analyzes the 3500+ claims.
    - It identifies the 4 hidden fraud rings.
    - The graph visualization highlights the rings (e.g., Ring 1: Kickback Surgeons).
    - Click on nodes to see detailed stats (Total Billed, Role, etc.).

## Project Structure

```
FraudAuditor/
├── app.py                 # Backend Logic (Data Generation & Graph Visualizer)
├── requirements.txt       # Dependencies (fastapi, networkx, pandas)
├── static/
│   ├── index.html         # Frontend Dashboard (Vis.js logic)
└── README.md              # Documentation
```
