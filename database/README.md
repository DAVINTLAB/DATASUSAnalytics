SIH-RD RS Data (2008-2023) 🏥
Este repositório contém a base de dados do Sistema de Informações Hospitalares (SIH-RD) do Rio Grande do Sul, estruturada para consulta via LLM. Os dados abrangem o período de 2008 a 2023.

🚀 Como Iniciar
1. Requisitos e Download
PostgreSQL 13+ instalado.

Acesso ao terminal (Linux/Bash recomendado).

Download dos Dados: Baixe o arquivo de dump através do link abaixo:

📥 Baixar Base de Dados 
* **Banco de Dados (Dump):** [📥 Clique aqui para baixar o arquivo](https://brpucrs-my.sharepoint.com/:u:/g/personal/isadora_figueiredo_edu_pucrs_br/IQCrKgYEvqJ1QKEETZYXnnYJAdrvqzK4jjRGz6hwjYoXvDM?e=6fgv5e)
```
# 1. Descompactar o arquivo de dump
unzip sih_rs_dump.zip

# 2. Criar a base de dados no PostgreSQL
PGPASSWORD=1234 createdb -U postgres -h localhost sih_rs_test

# 3. Restaurar os dados a partir do arquivo .dump
PGPASSWORD=1234 pg_restore -U postgres -h localhost -d sih_rs_test sih_rs_dump.dump
```


