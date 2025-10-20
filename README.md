# SIH Governance Framework

This repository serves as the **main entry point** for the *Data Governance Framework* developed for the **Brazilian Hospital Information System (SIH-RD/SUS)**. 
It includes two independent components: a **relational data warehouse (PostgreSQL + dbt)** and a **Text-to-SQL LLM agent** designed exclusively for **data querying** through **natural language interaction**.

---

## Purpose

This repository aims to provide:
- A unified structure that organizes both the **data warehouse** and the **LLM agent** under a shared governance approach. 
- An implementation guided by the **pillars of data governance**, such as **architecture**, **modeling**, **integration**, and **data quality**. 
- Independent execution of both components, ensuring modularity and flexibility for development and testing.

---

## Repository Structure

```bash
DATASUSAnalytics/
├── database/      # Complete ETL pipeline and dbt project for the data warehouse
└── llm/           # Text-to-SQL agent for querying in natural language

