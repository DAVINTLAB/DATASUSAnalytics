# DATASUS Analytics Framework

---


This repository serves as the **main entry point** for the *Data Governance Framework* developed for the **Brazilian Hospital Information System (SIH-RD/SUS)**. 
It contains two independent components: a **relational data warehouse (PostgreSQL + dbt)**, which implements the governance and ETL processes, and a **Text-to-SQL LLM agent**, designed exclusively for **data querying** through **Datural Language**.
---

## Purpose

This repository aims to provide:
- A modular architecture that separates the **data governance and ETL processes** from the **LLM agent**. 
- A data pipeline guided by the **pillars of data governance**, including **architecture**, **modeling**, **integration**, and **data quality**. 
- A read-only LLM agent that queries the governed data without altering or persisting information.

---

## Repository Structure

```bash
DATASUSAnalytics/
├── database/      # Complete ETL pipeline and dbt project for the data warehouse
└── llm/           # Text-to-SQL agent for querying in natural language

