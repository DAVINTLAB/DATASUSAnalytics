# 🧠 SIH Governance Framework

This repository serves as the **main entry point** for the *Data Governance Framework* developed for the **Brazilian Hospital Information System (SIH-RD/SUS)**. 
It integrates a **relational data warehouse (PostgreSQL + dbt)** and a **Text-to-SQL LLM agent**, enabling both **data validation** and **natural language interaction** with the database.

---

## 🎯 Purpose

This repository aims to provide:
- A unified environment for managing both the **data warehouse** and the **LLM agent** components. 
- Reproducible and transparent processes for **data quality, validation, and governance**, aligned with the principles of **DAMA-DMBOK2**. 
- A practical demonstration of **AI-assisted data governance**, connecting structured data pipelines with intelligent query interfaces.

---

## 📂 Repository Structure

```bash
DATASUSAnalytics/
├── database/      # Relational data warehouse + dbt tests
└── llm/           # Text-to-SQL agent (LangChain + Llama 3)

