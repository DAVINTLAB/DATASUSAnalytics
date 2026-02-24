# SIH-RD RS Data 
Este repositório contém o banco para consulta da LLM. São dados do RS de 2008-2023

### Como Iniciar
1. Requisitos
PostgreSQL 13+

2. Restauração do Banco de Dados
O banco de dados é fornecido via dump compactado. Siga os comandos abaixo para preparar o ambiente local:

```
# 1. Descompactar o arquivo de dump
unzip sih_rs_dump.zip

# 2. Criar a base de dados no PostgreSQL
PGPASSWORD=1234 createdb -U postgres -h localhost sih_rs_test

# 3. Restaurar os dados a partir do arquivo .dump
PGPASSWORD=1234 pg_restore -U postgres -h localhost -d sih_rs_test sih_rs_dump.dump
```
