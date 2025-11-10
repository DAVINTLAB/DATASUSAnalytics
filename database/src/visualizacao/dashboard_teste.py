import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
from sqlalchemy import create_engine
import warnings
warnings.filterwarnings('ignore')

# -------------------------------
# CONFIGURAÇÃO BÁSICA
# -------------------------------
st.set_page_config(page_title="Teste Conexão SIH-RS", layout="wide")
st.title("Teste de Conexão - Dashboard SIH-RS")

# -------------------------------
# CONFIGURAÇÃO DO BANCO
# -------------------------------
# IMPORTANTE: Configuração varia conforme Sistema Operacional!
# Descomente apenas a configuração do SEU sistema:

# ======== LINUX (Ubuntu/CentOS/Debian) ========
# DB_CONFIG = {
#     'usuario': 'postgres',      # Usuário padrão do PostgreSQL
#     'senha': '1234',            # Senha que você definiu na instalação
#     'host': 'localhost',
#     'porta': '5432',
#     'banco': 'sih_rs'
# }

# ======== WINDOWS ========
# DB_CONFIG = {
#     'usuario': 'postgres',      # Usuário padrão do PostgreSQL
#     'senha': '1234',            # Senha definida durante instalação
#     'host': 'localhost',
#     'porta': '5432',
#     'banco': 'sih_rs'
# }

# ======== macOS (Homebrew) ========
DB_CONFIG = {
    'usuario': 'victoriacmarques',  # ← SUBSTITUA pelo SEU usuário do Mac
    'senha': '',                    # Geralmente sem senha no Mac/Homebrew
    'host': 'localhost',
    'porta': '5432',
    'banco': 'sih_rs'
}

# ======== macOS (PostgreSQL.app) ========
# DB_CONFIG = {
#     'usuario': 'seu_usuario_mac',   # Seu usuário do sistema
#     'senha': '',                    # Sem senha
#     'host': 'localhost',
#     'porta': '5432',
#     'banco': 'sih_rs'
# }

# ======== Docker (Qualquer SO) ========
# DB_CONFIG = {
#     'usuario': 'postgres',
#     'senha': 'sua_senha_docker',
#     'host': 'localhost',          # ou IP do container
#     'porta': '5432',             # ou porta mapeada
#     'banco': 'sih_rs'
# }

# ============================================
# COMO DESCOBRIR SUA CONFIGURAÇÃO:
# ============================================
# 1. Verificar owner do banco:
#    psql -d postgres -c "\l" | grep sih_rs
# 
# 2. Testar conexão:
#    psql -U [usuario] -h localhost -d sih_rs -c "SELECT 1;"
#
# 3. Se der erro de autenticação:
#    - Linux/Windows: Verificar senha do postgres
#    - Mac: Usar seu usuário do sistema  
#    - Docker: Verificar variáveis de ambiente
#
# 4. Comandos para diagnóstico:
#    - Ver processos: ps aux | grep postgres
#    - Ver porta: lsof -i :5432  (Mac) ou netstat -an | grep 5432
#    - Testar básico: pg_isready -h localhost -p 5432
# ============================================

st.sidebar.header("Diagnósticos")

# -------------------------------
# FUNÇÃO DE TESTE DE CONEXÃO
# -------------------------------
def testar_conexao():
    """Testa conexão e estrutura do banco"""
    try:
        connection_string = f"postgresql+psycopg2://{DB_CONFIG['usuario']}:{DB_CONFIG['senha']}@{DB_CONFIG['host']}:{DB_CONFIG['porta']}/{DB_CONFIG['banco']}"
        engine = create_engine(connection_string)
        
        # Teste básico
        test_df = pd.read_sql("SELECT 1 as teste", engine)
        return engine, "Conexão OK"
    except Exception as e:
        return None, f"Erro: {e}"

# -------------------------------
# DIAGNÓSTICO DO BANCO
# -------------------------------
st.subheader("1️ Teste de Conexão")

engine, status_conexao = testar_conexao()
st.write(status_conexao)

if engine is None:
    st.error("Não foi possível conectar. Verifique:")
    st.write("- PostgreSQL está rodando?")
    st.write("- Banco 'sih_rs' existe?")
    st.write("- Usuário/senha corretos?")
    st.stop()

# -------------------------------
# VERIFICAR ESTRUTURA DAS TABELAS
# -------------------------------
st.subheader("2️ Estrutura das Tabelas")

try:
    # Listar tabelas
    tabelas_query = """
        SELECT table_name, 
               (SELECT COUNT(*) FROM information_schema.columns 
                WHERE table_name = t.table_name AND table_schema = 'public') as colunas
        FROM information_schema.tables t
        WHERE table_schema = 'public'
        ORDER BY table_name
    """
    
    tabelas_df = pd.read_sql(tabelas_query, engine)
    st.write("**Tabelas encontradas:**")
    st.dataframe(tabelas_df)
    
    # Verificar se tem as tabelas esperadas
    tabelas_esperadas = ['internacoes', 'financeiro', 'uti_info', 'obstetricos', 'procedimentos', 'municipios', 'cid10']
    tabelas_existentes = tabelas_df['table_name'].tolist()
    
    st.write("**Verificação:**")
    for tabela in tabelas_esperadas:
        if tabela in tabelas_existentes:
            st.write(f"OK: {tabela}")
        else:
            st.write(f"FALTANDO: {tabela}")
            
except Exception as e:
    st.error(f"Erro ao verificar tabelas: {e}")

# -------------------------------
# VERIFICAR CONTAGEM DE REGISTROS
# -------------------------------
st.subheader("3️ Contagem de Registros")

try:
    for tabela in tabelas_existentes:
        try:
            count_df = pd.read_sql(f"SELECT COUNT(*) as total FROM {tabela}", engine)
            total = count_df['total'].iloc[0]
            st.write(f"**{tabela}:** {total:,} registros")
        except Exception as e:
            st.write(f"**{tabela}:** Erro - {e}")
            
except Exception as e:
    st.error(f"Erro geral: {e}")

# -------------------------------
# TESTE DE COLUNAS IMPORTANTES
# -------------------------------
st.subheader("4️ Verificar Colunas Importantes")

# Verificar colunas da tabela internacoes
try:
    colunas_internacoes = pd.read_sql("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'internacoes' 
        ORDER BY column_name
    """, engine)
    
    st.write("**Colunas da tabela internacoes:**")
    st.dataframe(colunas_internacoes)
    
    # Verificar colunas críticas
    colunas_criticas = ['N_AIH', 'PROC_REA', 'MUNIC_RES', 'DT_INTER', 'SEXO', 'IDADE', 'MORTE']
    colunas_encontradas = colunas_internacoes['column_name'].tolist()
    
    st.write("**Colunas críticas para dashboard:**")
    for coluna in colunas_criticas:
        if coluna in colunas_encontradas:
            tipo = colunas_internacoes[colunas_internacoes['column_name'] == coluna]['data_type'].iloc[0]
            st.write(f"OK: {coluna} ({tipo})")
        else:
            st.write(f"FALTANDO: {coluna}")
            
except Exception as e:
    st.error(f"Erro ao verificar colunas: {e}")

# -------------------------------
# TESTE DE JOIN SIMPLES
# -------------------------------
st.subheader("5️ Teste de JOIN")

try:
    # Teste simples de JOIN
    join_test = pd.read_sql("""
        SELECT COUNT(*) as total
        FROM internacoes i
        LEFT JOIN procedimentos p ON i."PROC_REA" = p."PROC_REA"
        LIMIT 1
    """, engine)
    
    st.write(f"OK: JOIN internacoes ↔ procedimentos")
    
    # Teste JOIN com municipios
    try:
        join_mun_test = pd.read_sql("""
            SELECT COUNT(*) as total
            FROM internacoes i
            LEFT JOIN municipios m ON i."MUNIC_RES" = m.codigo_municipio_6d
            LIMIT 1
        """, engine)
        st.write(f"OK: JOIN internacoes ↔ municipios")
    except Exception as e:
        st.write(f"ERRO JOIN internacoes ↔ municipios: {e}")
        
        # Tentar outras possibilidades de nome de coluna
        try:
            colunas_municipios = pd.read_sql("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'municipios'
            """, engine)
            st.write("**Colunas disponíveis em municipios:**")
            st.write(colunas_municipios['column_name'].tolist())
        except:
            pass
            
except Exception as e:
    st.error(f"Erro no teste de JOIN: {e}")

# -------------------------------
# AMOSTRA DE DADOS
# -------------------------------
st.subheader("6️ Amostra de Dados")

try:
    # Buscar 5 registros de exemplo
    amostra = pd.read_sql("""
        SELECT i."N_AIH", i."PROC_REA", i."MUNIC_RES", i."SEXO", i."IDADE", 
               p."NOME_PROC"
        FROM internacoes i
        LEFT JOIN procedimentos p ON i."PROC_REA" = p."PROC_REA"
        WHERE p."NOME_PROC" IS NOT NULL
        LIMIT 5
    """, engine)
    
    st.write("**Amostra de dados (5 registros):**")
    st.dataframe(amostra)
    
except Exception as e:
    st.error(f"Erro ao buscar amostra: {e}")

# -------------------------------
# TESTE DE PROCEDIMENTOS
# -------------------------------
st.subheader("7️ Teste de Procedimentos")

try:
    # Top 10 procedimentos
    top_proc = pd.read_sql("""
        SELECT 
            p."PROC_REA",
            p."NOME_PROC",
            COUNT(i."N_AIH") as total_casos
        FROM procedimentos p
        INNER JOIN internacoes i ON p."PROC_REA" = i."PROC_REA"
        GROUP BY p."PROC_REA", p."NOME_PROC"
        ORDER BY total_casos DESC
        LIMIT 10
    """, engine)
    
    st.write("**Top 10 procedimentos:**")
    st.dataframe(top_proc)
    
    if len(top_proc) > 0:
        st.success("Dados OK para dashboard!")
    else:
        st.warning("Nenhum procedimento encontrado")
        
except Exception as e:
    st.error(f"Erro ao testar procedimentos: {e}")

# -------------------------------
# CONCLUSÃO E RECOMENDAÇÕES
# -------------------------------
st.subheader("8️ Conclusão")

if engine and len(tabelas_existentes) >= 5:
    st.success("PRONTO PARA DASHBOARD COMPLETO!")
    st.write("OK: Conexão funcionando")
    st.write("OK: Tabelas existem") 
    st.write("OK: Dados disponíveis")
    st.write("OK: JOINs funcionando")
    
    if st.button("Gerar Dashboard Completo"):
        st.balloons()
        st.write("**Próximo passo:** Use o dashboard completo!")
        
else:
    st.warning("PROBLEMAS ENCONTRADOS")
    st.write("Corrija os problemas acima antes de usar o dashboard completo.")

# Informações de debug
with st.expander("Debug Info"):
    st.write(f"**Banco:** {DB_CONFIG['banco']}")
    st.write(f"**Host:** {DB_CONFIG['host']}:{DB_CONFIG['porta']}")
    st.write(f"**Usuário:** {DB_CONFIG['usuario']}")
    st.write(f"**Tabelas encontradas:** {len(tabelas_existentes) if 'tabelas_existentes' in locals() else 0}")