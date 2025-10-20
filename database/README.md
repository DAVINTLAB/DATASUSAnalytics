# Database Module

This module contains the complete **ETL pipeline** and **data governance layer** for the SIH-RD/SUS dataset. 
It is responsible for extracting, cleaning, transforming, validating, and loading data into a **PostgreSQL relational data warehouse**, following the principles of **data governance** defined in the DAMA-DMBOK2 framework.

---

## Overview

The ETL process is implemented in **Python** using the **Polars** library for efficient in-memory data manipulation and parallelized processing. 
After transformation, the data is loaded into a **PostgreSQL** database, where relational integrity and business rules are validated through **dbt** tests written in **YAML** (for structure and metadata) and **SQL** (for complex logic).

---

## Workflow Summary

1. **Extract** 
   - Download raw data from DATASUS in `.parquet` format. 
   - Store files in `data/raw/`.

2. **Transform** 
   - Clean, unify, and standardize datasets using Polars. 
   - Process intermediate data stored in `data/interim/`. 
   - Generate final ready-to-load datasets in `data/processed/`.

3. **Load** 
   - Use `psycopg2` to insert processed data into the PostgreSQL database. 
   - Define schemas, constraints, and foreign keys in `src/database/schema.py`. 

4. **Validate** 
   - Apply **YAML-based dbt tests** for structure validation (e.g., `not_null`, `unique`, `relationships`). 
   - Use **SQL tests** for advanced business rules and cross-table validations.

---

## Repository Structure

```bash
database/
├─ data/
│  ├─ raw/             # Raw parquet files downloaded from DATASUS
│  ├─ interim/         # Unified and preprocessed parquet files
│  ├─ processed/       # Final datasets ready to load into PostgreSQL
│  └─ support/         # Lookup CSVs (CID10, municipalities, procedures)
│
├─ sih_analytics/      # dbt project for validation and governance
│  ├─ models/          # Staging, marts, and intermediate layers
│  ├─ tests/           # YAML + SQL tests
│  ├─ macros/          # Reusable SQL or Jinja macros
│  ├─ analyses/        # Exploratory SQL analyses
│  ├─ seeds/           # Static reference data
│  ├─ snapshots/       # Historical snapshots for audit
│  ├─ dbt_project.yml  # Main dbt configuration
│  └─ profiles.yml     # Local dbt connection profile
│
├─ docs/
│  ├─ diagrams/        # ETL and schema diagrams
│  ├─ decisions/       # Architecture decision records (ADR)
│  └─ database/        # Database documentation (dictionary, schema, constraints)
│
├─ reports/
│  └─ logs/            # Execution logs from ETL and dbt runs
│
├─ src/
│  ├─ config/
│  │  └── settings.py  # Global parameters (paths, DB credentials, year filters)
│  │
│  ├─ data/
│  │  ├─ download.py   # EXTRACT: Download DATASUS → parquet
│  │  ├─ unify.py      # TRANSFORM 1: Merge parquet files
│  │  ├─ preprocess.py # TRANSFORM 2: Clean & standardize
│  │  ├─ aggregate.py  # TRANSFORM 3: Contract or enrich data
│  │  └─ split.py      # TRANSFORM 4: Split into fact/dim tables
│  │
│  ├─ database/
│  │  ├─ schema.py     # Table structure, PK, FK definitions
│  │  └─ load.py       # LOAD: Insert processed data into PostgreSQL
│  │
│  └─ main.py          # Orchestration script for ETL execution
│
├─ requirements.txt     # Python dependencies
├─ .gitignore           # Ignore data and sensitive files
└─ README.md            # This document

