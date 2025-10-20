

# SIH Governance Framework


This repository serves as the **main entry point** for the *Data Governance Framework* developed for the **Brazilian Hospital Information System (SIH/SUS)**. 
It integrates a **relational data warehouse (PostgreSQL + dbt)** and a **Text-to-SQL LLM agent**, enabling both **data validation** and **natural language interaction** with the database.

---
##  Purpose

This repository aims to provide:
- A unified environment for managing both the **data warehouse** and the **LLM agent** components. 
- Reproducible and transparent processes for **data quality, validation, and governance**, aligned with the principles of **DAMA-DMBOK2**. 
- A practical demonstration of **AI-assisted data governance**, connecting structured data pipelines with intelligent query interfaces.

---

##  Repository Structure

```bash
DATASUSAnalytics/
<<<<<<< HEAD
├─ datasus-sih/                   # ETL pipeline for SIH/SUS data
│
├─ llm/                           # LLM-based module (RAG, agents, NLP)
│
├─ viz/                           # Dashboards and visualizations (Streamlit, Power BI)
│
├─ ml/                            # Predictive models
│
├─ dbt/                           # Data quality tests and transformations with dbt
│
├─ rules/                         # Association rules (Apriori, FP-Growth)
│
├─ docs/                          # Global documentation for the whole project
│  ├─ diagrams/                   # Architecture and workflow diagrams
│  ├─ decisions/                  # Global architecture decision records (ADRs)
│  └─ reports/                    # General reports or executive summaries
│
├─ reports/                       # Auto-generated reports (logs, summaries)
│  ├─ logs/                       # Logs for orchestration and monitoring
│
├─ .gitignore                     # Ignore rules (exclude raw data, temp files, etc.)
├─ requirements.txt               # Global dependencies (dbt, psycopg2, streamlit, etc.)
└─ README.md                      # Main navigation guide and instructions
>>>>>>> 0619b3e (refresh structure)
=======
├── database/      # Relational data warehouse + dbt tests
└── llm/           # Text-to-SQL agent (LangChain + Llama 3)
>>>>>>> ffc7962 (add readme)

