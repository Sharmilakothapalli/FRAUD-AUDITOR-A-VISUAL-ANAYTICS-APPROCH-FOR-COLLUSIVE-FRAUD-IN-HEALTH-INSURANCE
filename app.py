import uvicorn
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
import pandas as pd
import networkx as nx
import os
import io
import random
from typing import List, Dict, Any
from datetime import datetime, timedelta

app = FastAPI(title="Fraud Auditor - Health Insurance Collusion Detection")

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static Files
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# InMemory Storage for the loaded dataset
CURRENT_DATASET = None

@app.get("/")
async def read_index():
    return FileResponse("static/index.html")

def generate_detailed_synthetic_data(num_claims=3500):
    """Generates rich synthetic claims data with embedded, disjoint collusion patterns."""
    
    data = []
    
    # -------------------------------------------------------------
    # 1. POOL SEPARATION (Crucial for Distinct Rings)
    # -------------------------------------------------------------
    # Total: 60 Docs, 600 Patients
    
    # Pool A: Honest (50 Docs, 500 Patients)
    honest_docs = [f"Dr. {i}" for i in range(1, 51)]
    honest_patients = [f"Patient_{i}" for i in range(1, 501)]
    
    # Pool B: Corrupt (10 Docs, 100 Patients) - Completely separate IDs
    corrupt_docs = [f"Dr. {i}" for i in range(51, 61)]
    corrupt_patients = [f"Patient_{i}" for i in range(501, 601)]
    
    # Resources
    procedures = {
        "99213": {"desc": "Office Visit", "cost": 150},
        "99214": {"desc": "Detailed Visit", "cost": 250},
        "71045": {"desc": "J Chest X-Ray", "cost": 100},
        "85025": {"desc": "Complete Blood Count", "cost": 60},
        "72148": {"desc": "MRI Lumbar Spine", "cost": 1200}, 
        "29881": {"desc": "Knee Arthroscopy", "cost": 5000},
        "A0427": {"desc": "Ambulance Life Support", "cost": 600},
        "J3010": {"desc": "Fentanyl Injection", "cost": 40},
        "97110": {"desc": "Therapeutic Exercise", "cost": 130}
    }
    cpt_codes = list(procedures.keys())
    
    diagnoses = [
        "J00 (Common Cold)", "I10 (Hypertension)", "E11 (Type 2 Diabetes)", 
        "M54.5 (Low Back Pain)", "S83.2 (Meniscus Tear)", "F11.20 (Opioid Dependence)"
    ]
    
    base_date = datetime(2023, 1, 1)

    # -------------------------------------------------------------
    # 2. HONEST TRAFFIC (The "Haystack")
    # -------------------------------------------------------------
    # Random noise between Honest Docs and Honest Patients
    for _ in range(num_claims):
        cpt = random.choice(cpt_codes)
        proc = procedures[cpt]
        svc_date = base_date + timedelta(days=random.randint(0, 365))
        
        data.append({
            "ServiceDate": svc_date.strftime("%Y-%m-%d"),
            "Provider": random.choice(honest_docs),
            "Patient": random.choice(honest_patients),
            "ProcedureCode": cpt,
            "Description": proc["desc"],
            "Diagnosis": random.choice(diagnoses),
            "Cost": proc["cost"] + random.randint(-15, 15)
        })
        
    # -------------------------------------------------------------
    # 3. FRAUD RINGS (The "Needles")
    # -------------------------------------------------------------
    # We create multiple rings using the Corrupt Pools.
    # Since they use IDs NOT in the Honest Pool, they appear as isolated islands.
    
    # RING 1: The "Kickback Surgeons" (2 Docs sharing 10 Patients)
    # High Cost, High Density
    r1_docs = random.sample(corrupt_docs, 2)
    r1_pats = random.sample(corrupt_patients, 10)
    for _ in range(120):
        data.append({
            "ServiceDate": (base_date + timedelta(days=random.randint(0, 365))).strftime("%Y-%m-%d"),
            "Provider": random.choice(r1_docs),
            "Patient": random.choice(r1_pats),
            "ProcedureCode": "29881", # Knee Surgery
            "Description": "Knee Arthroscopy",
            "Diagnosis": "S83.2 (Meniscus Tear)",
            "Cost": 5000
        })
        
    # RING 2: The "Phantom Billing" Ring (1 Doc, 20 Patients, MANY small claims)
    # Low Individual Cost, Massive Volume
    rem_docs = [d for d in corrupt_docs if d not in r1_docs]
    rem_pats = [p for p in corrupt_patients if p not in r1_pats]
    
    r2_doc = random.sample(rem_docs, 1) # Just 1 doc
    r2_pats = random.sample(rem_pats, 20)
    for _ in range(300): # Huge volume
        data.append({
            "ServiceDate": (base_date + timedelta(days=random.randint(0, 365))).strftime("%Y-%m-%d"),
            "Provider": r2_doc[0],
            "Patient": random.choice(r2_pats),
            "ProcedureCode": "99214", 
            "Description": "Detailed Visit",
            "Diagnosis": "I10 (Hypertension)",
            "Cost": 250
        })

    # RING 3: "Ambulance Chasers" (1 Doc, 1 Ambulance Co, 8 Patients)
    # Circular flow: Patient -> Ambulance -> Doc
    rem_docs = [d for d in rem_docs if d not in r2_doc]
    rem_pats = [p for p in rem_pats if p not in r2_pats]
    
    if len(rem_docs) >= 2:
        r3_docs = random.sample(rem_docs, 2) 
        r3_pats = random.sample(rem_pats, 8)
        
        for _ in range(80):
            pat = random.choice(r3_pats)
            # Ambulance Ride
            data.append({
                "ServiceDate": "2023-05-20", 
                "Provider": r3_docs[0], # The Ambulance Co
                "Patient": pat,
                "ProcedureCode": "A0427", "Description": "Ambulance Life Support", "Diagnosis": "S83.2 (Meniscus Tear)", "Cost": 600
            })
            # Surgery next day
            data.append({
                "ServiceDate": "2023-05-21", 
                "Provider": r3_docs[1], # The Surgeon
                "Patient": pat,
                "ProcedureCode": "29881", "Description": "Knee Arthroscopy", "Diagnosis": "S83.2 (Meniscus Tear)", "Cost": 5000
            })
            
    # RING 4: "Therapy Mill" (2 Docs, 30 Patients, Recurring small charges)
    # Very high connectivity
    rem_docs = [d for d in rem_docs if d not in r3_docs] # Refresh pool ref
    rem_pats = [p for p in rem_pats if p not in r3_pats] # Refresh pool ref
    
    if len(rem_docs) >= 2:
        r4_docs = random.sample(rem_docs, min(2, len(rem_docs)))
        r4_pats = random.sample(rem_pats, min(15, len(rem_pats)))
        
        for _ in range(200):
            data.append({
                "ServiceDate": (base_date + timedelta(days=random.randint(0, 365))).strftime("%Y-%m-%d"),
                "Provider": random.choice(r4_docs),
                "Patient": random.choice(r4_pats),
                "ProcedureCode": "97110", 
                "Description": "Therapeutic Exercise",
                "Diagnosis": "M54.5 (Low Back Pain)",
                "Cost": 130
            })

    return pd.DataFrame(data)

@app.get("/load_data")
async def load_data():
    """Generates and loads the dataset into memory."""
    global CURRENT_DATASET
    df = generate_detailed_synthetic_data()
    CURRENT_DATASET = df
    
    # Return preview (first 20 rows) and stats
    preview = df.head(20).to_dict(orient="records")
    return {
        "message": "Dataset Loaded Successfully",
        "total_records": len(df),
        "total_providers": df['Provider'].nunique(),
        "total_patients": df['Patient'].nunique(),
        "preview": preview
    }

@app.post("/audit_network")
async def audit_network():
    """Analyzes the loaded dataset for collusion."""
    global CURRENT_DATASET
    if CURRENT_DATASET is None:
        raise HTTPException(status_code=400, detail="No data loaded. Please load dataset first.")
        
    df = CURRENT_DATASET
    
    try:
        # Build Graph
        G = nx.Graph()
        
        # Nodes & Edges
        # Calculate individual stats for tooltips
        prov_stats = df.groupby('Provider')['Cost'].sum().to_dict()
        pat_stats = df.groupby('Patient')['Cost'].sum().to_dict()
        
        # Group by Provider-Patient to count interactions
        interactions = df.groupby(['Provider', 'Patient']).size().reset_index(name='count')
        
        # Add Nodes with Metadata
        for p in df['Provider'].unique(): 
            G.add_node(str(p), type="Provider", color="#FF5733", value=prov_stats.get(p, 0)) 
        for p in df['Patient'].unique(): 
            G.add_node(str(p), type="Patient", color="#33FF57", value=pat_stats.get(p, 0))
            
        # Add Edges
        for _, row in interactions.iterrows():
            G.add_edge(str(row['Provider']), str(row['Patient']), weight=int(row['count']))
            
        # --- DETECTION ---
        components = list(nx.connected_components(G))
        flagged_communities = []
        
        for comp in components:
            if len(comp) > 3:
                subgraph = G.subgraph(comp)
                density = nx.density(subgraph)
                
                # Dynamic Thresholds
                if density > 0.08: # Slightly relaxed threshold for larger graph
                    
                    # Calculate Risk Score based on Cost & Density
                    total_risk_value = 0
                    members = list(comp)
                    for m in members:
                        total_risk_value += prov_stats.get(m, 0) + pat_stats.get(m, 0)
                    
                    risk_score = min(100, int(density * 100) + (total_risk_value // 10000))
                    
                    flagged_communities.append({
                        "id": f"Ring_{len(flagged_communities)+1}",
                        "nodes": members,
                        "density": round(density, 2),
                        "risk_score": risk_score,
                        "total_value": total_risk_value,
                        "reason": "High Density & Volume"
                    })

        # Visualization Data (Top Risk Rings + Context)
        vis_nodes = []
        vis_edges = []
        added_nodes = set()
        
        # Helper to add node
        def add_vis_node(n):
            if n in added_nodes: return
            ntype = G.nodes[n]['type']
            lbl = str(n)
            # Detailed Tooltip
            if ntype == 'Provider':
                title = f"<b>{lbl}</b><br>Role: Provider<br>Total Billed: ${prov_stats.get(n,0):,}"
            else:
                title = f"<b>{lbl}</b><br>Role: Patient<br>Total Claims: ${pat_stats.get(n,0):,}"
                
            vis_nodes.append({
                "id": n, 
                "group": ntype, 
                "label": lbl, 
                "title": title,
                "value": G.nodes[n].get('value', 1)  # Size by money involved
            })
            added_nodes.add(n)

        # 1. Add ALL Flagged Communities
        for comm in flagged_communities:
             for node in comm['nodes']:
                 add_vis_node(node)
                 
        # 2. Add Edges for these
        sub = G.subgraph(added_nodes)
        for u, v, d in sub.edges(data=True):
            vis_edges.append({"from": u, "to": v, "value": d.get('weight', 1)})
            
        return {
            "status": "Audit Complete",
            "flagged_rings": len(flagged_communities),
            "communities": flagged_communities,
            "graph_data": {"nodes": vis_nodes, "edges": vis_edges}
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
