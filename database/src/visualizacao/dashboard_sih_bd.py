import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from sqlalchemy import create_engine
import warnings
from datetime import datetime
warnings.filterwarnings('ignore')

# -------------------------------
# CONFIGURAÇÃO DO APP
# -------------------------------
st.set_page_config(page_title="Análise de Procedimentos SIH-RS", layout="wide")
st.sidebar.header("Filtros")

# -------------------------------
# CONFIGURAÇÃO DO BANCO DE DADOS
# -------------------------------
DB_CONFIG = {
    'usuario': 'victoriacmarques',
    'senha': '',
    'host': 'localhost',
    'porta': '5432',
    'banco': 'sih_rs'
}

@st.cache_resource
def get_database_connection():
    """Cria conexão com o banco PostgreSQL"""
    try:
        connection_string = f"postgresql+psycopg2://{DB_CONFIG['usuario']}:{DB_CONFIG['senha']}@{DB_CONFIG['host']}:{DB_CONFIG['porta']}/{DB_CONFIG['banco']}"
        engine = create_engine(connection_string)
        
        # Testa a conexão
        test_query = pd.read_sql("SELECT 1 as test", engine)
        st.sidebar.success("Conectado ao banco PostgreSQL")
        return engine
    except Exception as e:
        st.sidebar.error(f"Erro de conexão: {e}")
        st.error("Não foi possível conectar ao banco de dados. Verifique as configurações.")
        st.stop()

# -------------------------------
# LEITURA DOS DADOS DO BANCO
# -------------------------------
@st.cache_data
def load_data_from_database(_engine):
    """Carrega dados do banco PostgreSQL com JOINs otimizados"""
    try:
        # Query principal com JOINs para trazer todos os dados necessários
        main_query = """
        SELECT 
            i."N_AIH",
            i."PROC_REA",
            i."MUNIC_RES", 
            i."NASC",
            i."SEXO",
            i."DT_INTER",
            i."DT_SAIDA", 
            i."IDADE",
            i."DIAG_PRINC",
            i."MORTE",
            i."DIAS_PERM",
            i."ESPEC",
            
            -- Dados financeiros
            f."VAL_SH",
            f."VAL_SP", 
            f."VAL_TOT",
            f."VAL_UTI",
            
            -- Dados de UTI
            u."UTI_MES_TO",
            u."MARCA_UTI",
            u."UTI_INT_TO",
            u."DIAR_ACOM",
            
            -- Dados obstétricos
            o."GESTRICO",
            o."INSC_PN",
            o."CONTRACEP1",
            o."CONTRACEP2",
            
            -- Nome do procedimento
            p."NOME_PROC",
            
            -- Dados do município
            m.nome as nome_municipio,
            m.uf,
            NULL as latitude,
            NULL as longitude
            
        FROM internacoes i
        LEFT JOIN financeiro f ON i."N_AIH" = f."N_AIH"
        LEFT JOIN uti_info u ON i."N_AIH" = u."N_AIH" 
        LEFT JOIN obstetricos o ON i."N_AIH" = o."N_AIH"
        LEFT JOIN procedimentos p ON i."PROC_REA" = p."PROC_REA"
        LEFT JOIN municipios m ON i."MUNIC_RES" = m.codigo_municipio_6d
        WHERE p."NOME_PROC" IS NOT NULL
        ORDER BY i."DT_INTER" DESC
        """
        
        df_main = pd.read_sql(main_query, _engine)
        
        # Carregar tabelas auxiliares para filtros
        df_procedimentos = pd.read_sql('SELECT "PROC_REA", "NOME_PROC" FROM procedimentos ORDER BY "NOME_PROC"', _engine)
        df_municipios = pd.read_sql('SELECT codigo_municipio_6d, nome, uf FROM municipios ORDER BY nome', _engine)
        df_cid10 = pd.read_sql('SELECT "CID_COD", "CID_NOME" FROM cid10 ORDER BY "CID_COD"', _engine)
        
        return df_main, df_procedimentos, df_municipios, df_cid10
        
    except Exception as e:
        st.error(f"Erro ao carregar dados do banco: {e}")
        st.stop()

@st.cache_data 
def get_procedimento_stats(_engine):
    """Carrega estatísticas rápidas dos procedimentos para o selectbox"""
    try:
        stats_query = """
        SELECT 
            p."PROC_REA",
            p."NOME_PROC",
            COUNT(i."N_AIH") as total_internacoes,
            ROUND(AVG(CAST(f."VAL_TOT" AS NUMERIC)), 2) as valor_medio
        FROM procedimentos p
        INNER JOIN internacoes i ON p."PROC_REA" = i."PROC_REA"
        LEFT JOIN financeiro f ON i."N_AIH" = f."N_AIH"
        GROUP BY p."PROC_REA", p."NOME_PROC"
        HAVING COUNT(i."N_AIH") >= 100
        ORDER BY total_internacoes DESC
        """
        
        return pd.read_sql(stats_query, _engine)
    except Exception as e:
        st.error(f"Erro ao carregar estatísticas: {e}")
        return pd.DataFrame()

# Conectar ao banco
engine = get_database_connection()

# Carregar dados
df, df_proc, df_mun, df_cid = load_data_from_database(engine)
proc_stats = get_procedimento_stats(engine)

# Verifica se os dados foram carregados
if df is None or len(df) == 0:
    st.error("Erro ao carregar os dados do banco!")
    st.stop()

# Converte datas
df['DT_INTER'] = pd.to_datetime(df['DT_INTER'], errors='coerce')
df['DT_SAIDA'] = pd.to_datetime(df['DT_SAIDA'], errors='coerce')

# -------------------------------
# FILTROS NA SIDEBAR
# -------------------------------
st.sidebar.subheader("Filtros de Dados")

# Mostrar estatísticas da conexão
st.sidebar.info(f"Total de registros: {len(df):,}")
st.sidebar.info(f"Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

# Filtro por procedimento com estatísticas
if len(proc_stats) > 0:
    # Criar formato mais informativo para o selectbox
    def format_procedimento(proc_rea):
        row = proc_stats[proc_stats['PROC_REA'] == proc_rea]
        if len(row) > 0:
            nome = row['NOME_PROC'].iloc[0][:50]
            total = row['total_internacoes'].iloc[0]
            valor = row['valor_medio'].iloc[0] if pd.notna(row['valor_medio'].iloc[0]) else 0
            return f"{proc_rea} - {nome}... ({total:,} casos, R${valor:,.0f})"
        return proc_rea
    
    codigo_procedimento = st.sidebar.selectbox(
        "Escolha o procedimento:", 
        proc_stats['PROC_REA'].tolist(),
        format_func=format_procedimento,
        help="Mostrando apenas procedimentos com mais de 100 casos"
    )
else:
    st.sidebar.error("Nenhum procedimento encontrado")
    st.stop()

# Filtro por ano
anos_disponiveis = sorted(df['DT_INTER'].dt.year.dropna().unique(), reverse=True)
anos_selecionados = st.sidebar.multiselect(
    "Selecionar anos:",
    anos_disponiveis,
    default=anos_disponiveis[:3] if len(anos_disponiveis) >= 3 else anos_disponiveis,
    help="Selecione os anos para análise"
)

# Filtro por município (top 20 mais frequentes para este procedimento)
municipios_procedimento = df[df['PROC_REA'] == codigo_procedimento]['nome_municipio'].value_counts().head(20).index.tolist()
municipios_selecionados = st.sidebar.multiselect(
    "Filtrar por municípios:",
    municipios_procedimento,
    default=[],
    help="Top 20 municípios para este procedimento"
)

# Filtro por sexo
sexo_map = {1: 'Masculino', 3: 'Feminino'}
sexos_disponiveis = [1, 3]
sexos_selecionados = st.sidebar.multiselect(
    "Filtrar por sexo:",
    sexos_disponiveis,
    format_func=lambda x: sexo_map.get(x, f'Código {x}'),
    default=sexos_disponiveis
)

# Filtro por faixa de valor (se houver dados financeiros)
if df['VAL_TOT'].notna().sum() > 0:
    valores_validos = df[df['PROC_REA'] == codigo_procedimento]['VAL_TOT'].dropna()
    if len(valores_validos) > 0:
        valor_min, valor_max = float(valores_validos.min()), float(valores_validos.max())
        faixa_valor = st.sidebar.slider(
            "Faixa de valor (R$):",
            min_value=valor_min,
            max_value=valor_max,
            value=(valor_min, valor_max),
            format="R$ %.0f"
        )
    else:
        faixa_valor = None
else:
    faixa_valor = None

# -------------------------------
# APLICAR FILTROS
# -------------------------------
@st.cache_data
def apply_filters(df, codigo_proc, anos, municipios, sexos, faixa_val):
    """Aplica todos os filtros selecionados"""
    df_filtrado = df[df['PROC_REA'] == codigo_proc].copy()
    
    if anos:
        df_filtrado = df_filtrado[df_filtrado['DT_INTER'].dt.year.isin(anos)]
    
    if municipios:
        df_filtrado = df_filtrado[df_filtrado['nome_municipio'].isin(municipios)]
    
    if sexos:
        df_filtrado = df_filtrado[df_filtrado['SEXO'].isin(sexos)]
    
    if faixa_val and 'VAL_TOT' in df_filtrado.columns:
        df_filtrado = df_filtrado[
            (df_filtrado['VAL_TOT'] >= faixa_val[0]) & 
            (df_filtrado['VAL_TOT'] <= faixa_val[1])
        ]
    
    return df_filtrado

df_filtrado = apply_filters(df, codigo_procedimento, anos_selecionados, 
                           municipios_selecionados, sexos_selecionados, faixa_valor)

# Obter nome do procedimento
nome_procedimento = df_filtrado['NOME_PROC'].iloc[0] if len(df_filtrado) > 0 else "Procedimento não encontrado"

st.title(f"Análise do Procedimento {codigo_procedimento}")
st.subheader(f"{nome_procedimento}")

if len(df_filtrado) == 0:
    st.warning("Nenhum dado encontrado com os filtros selecionados!")
    st.stop()

# -------------------------------
# PRÉ-PROCESSAMENTO
# -------------------------------
# Remove registros com idade muito baixa
df_filtrado = df_filtrado[df_filtrado['IDADE'] >= 10]

# Faixas etárias
bins = list(range(10, 90, 5)) + [200]
labels = [f"{i}-{i+4}" for i in range(10, 85, 5)] + ["85+"]
df_filtrado['faixa_etaria'] = pd.cut(df_filtrado['IDADE'], bins=bins, labels=labels, right=False)

# Mapeamento de sexo
df_filtrado['sexo'] = df_filtrado['SEXO'].map(sexo_map)

# Indicadores
df_filtrado['dias_internado'] = (df_filtrado['DT_SAIDA'] - df_filtrado['DT_INTER']).dt.days

# Calcula métricas
percentual_obito = (df_filtrado['MORTE'].sum() / len(df_filtrado) * 100) if len(df_filtrado) > 0 else 0
media_gasto = df_filtrado['VAL_TOT'].mean() if 'VAL_TOT' in df_filtrado.columns else 0
media_dias = df_filtrado['dias_internado'].mean() if len(df_filtrado) > 0 else 0
total_internacoes = len(df_filtrado)
total_obitos = df_filtrado['MORTE'].sum()

# -------------------------------
# INDICADORES GERAIS
# -------------------------------
st.markdown("### Indicadores Gerais")
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Total de Internações", f"{total_internacoes:,}")

with col2:
    st.metric("Total de Óbitos", f"{total_obitos:,}")

with col3:
    st.metric("Taxa de Mortalidade", f"{percentual_obito:.1f}%")

with col4:
    if not pd.isna(media_gasto) and media_gasto > 0:
        st.metric("Valor Médio", f"R$ {media_gasto:,.2f}")
    else:
        st.metric("Valor Médio", "N/A")

with col5:
    if not pd.isna(media_dias) and media_dias > 0:
        st.metric("Dias Médios", f"{media_dias:.1f}")
    else:
        st.metric("Dias Médios", "N/A")

# -------------------------------
# GRÁFICOS: PIRÂMIDE E HEATMAP
# -------------------------------
col6, col7 = st.columns(2)

# Pirâmide etária
with col6:
    st.markdown("#### Pirâmide Etária por Sexo")
    
    df_piramide = df_filtrado.dropna(subset=['sexo', 'faixa_etaria'])
    
    if len(df_piramide) > 0:
        df_grouped = df_piramide.groupby(['faixa_etaria', 'sexo']).size().unstack(fill_value=0)
        df_grouped = df_grouped.reindex(labels, fill_value=0)
        
        # Inverte valores masculinos para criar pirâmide
        if 'Masculino' in df_grouped.columns:
            df_grouped['Masculino'] *= -1

        fig1, ax1 = plt.subplots(figsize=(8, 8))
        cores = {'Masculino': '#5DA5DA', 'Feminino': '#FAA43A'}
        
        if 'Masculino' in df_grouped.columns:
            ax1.barh(df_grouped.index, df_grouped['Masculino'], color=cores['Masculino'], label='Masculino')
        if 'Feminino' in df_grouped.columns:
            ax1.barh(df_grouped.index, df_grouped['Feminino'], color=cores['Feminino'], label='Feminino')
        
        ax1.set_xlabel("Quantidade")
        ax1.set_ylabel("Faixa Etária")
        ax1.set_title(f"Distribuição por Sexo e Idade")
        ax1.legend(title="Sexo")
        
        # Ajustar labels do eixo X para mostrar valores positivos
        ticks = ax1.get_xticks()
        ax1.set_xticklabels([abs(int(tick)) for tick in ticks])
        
        plt.tight_layout()
        st.pyplot(fig1)
    else:
        st.warning("Dados insuficientes para pirâmide etária")

# Heatmap por faixa etária e mês
with col7:
    st.markdown("#### Distribuição por Mês e Faixa Etária")
    
    df_heatmap = df_filtrado.dropna(subset=['DT_INTER', 'faixa_etaria'])
    
    if len(df_heatmap) > 0:
        df_heatmap['mes'] = df_heatmap['DT_INTER'].dt.month
        heatmap_data = df_heatmap.groupby(['faixa_etaria', 'mes']).size().unstack(fill_value=0)
        
        # Garantir que temos todos os meses
        for i in range(1, 13):
            if i not in heatmap_data.columns:
                heatmap_data[i] = 0
        
        heatmap_data = heatmap_data[sorted(heatmap_data.columns)]
        meses_nome = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 
                     'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
        heatmap_data.columns = meses_nome
        heatmap_data = heatmap_data.reindex(labels[::-1], fill_value=0)

        fig2, ax2 = plt.subplots(figsize=(10, 8))
        sns.heatmap(heatmap_data, cmap="OrRd", linewidths=0.5, ax=ax2, annot=False)
        ax2.set_title("Distribuição Mensal por Faixa Etária")
        ax2.set_xlabel("Mês")
        ax2.set_ylabel("Faixa Etária")
        plt.tight_layout()
        st.pyplot(fig2)
    else:
        st.warning("Dados insuficientes para heatmap temporal")

# -------------------------------
# TENDÊNCIA TEMPORAL
# -------------------------------
st.markdown("### Tendência Temporal")

df_temporal = df_filtrado.dropna(subset=['DT_INTER'])

if len(df_temporal) > 0:
    df_temporal['ano_mes'] = df_temporal['DT_INTER'].dt.to_period('M').dt.to_timestamp()
    tendencia = df_temporal.groupby('ano_mes').agg({
        'N_AIH': 'count',
        'MORTE': 'sum',
        'VAL_TOT': 'mean'
    }).reset_index()
    tendencia.columns = ['ano_mes', 'quantidade', 'obitos', 'valor_medio']

    if len(tendencia) > 1:
        fig3, (ax3a, ax3b) = plt.subplots(2, 1, figsize=(12, 10))
        
        # Gráfico de quantidade
        sns.lineplot(data=tendencia, x='ano_mes', y='quantidade', marker='o', ax=ax3a, color='blue')
        ax3a.set_title("Evolução Mensal da Quantidade de Procedimentos")
        ax3a.set_xlabel("Período")
        ax3a.set_ylabel("Quantidade de Internações")
        
        # Gráfico de mortalidade
        if tendencia['obitos'].sum() > 0:
            tendencia['taxa_mortalidade'] = (tendencia['obitos'] / tendencia['quantidade']) * 100
            sns.lineplot(data=tendencia, x='ano_mes', y='taxa_mortalidade', marker='s', ax=ax3b, color='red')
            ax3b.set_title("Evolução da Taxa de Mortalidade (%)")
            ax3b.set_xlabel("Período")
            ax3b.set_ylabel("Taxa de Mortalidade (%)")
        
        # Formatação do eixo X
        import matplotlib.dates as mdates
        for ax in [ax3a, ax3b]:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
            ax.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        st.pyplot(fig3)
    else:
        st.info("Dados insuficientes para análise temporal")
else:
    st.warning("Sem dados de data para análise temporal")

# -------------------------------
# ANÁLISE FINANCEIRA E GEOGRÁFICA
# -------------------------------
col8, col9 = st.columns(2)

with col8:
    st.markdown("#### Top 10 Municípios")
    
    if 'nome_municipio' in df_filtrado.columns:
        top_municipios_proc = df_filtrado.groupby('nome_municipio').agg({
            'N_AIH': 'count',
            'VAL_TOT': 'mean',
            'MORTE': 'sum',
            'IDADE': 'mean'
        }).round(2)
        
        top_municipios_proc.columns = ['Internações', 'Valor Médio (R$)', 'Óbitos', 'Idade Média']
        top_municipios_proc = top_municipios_proc.sort_values('Internações', ascending=False).head(10)
        
        if len(top_municipios_proc) > 0:
            # Formatar valores monetários
            top_municipios_proc['Valor Médio (R$)'] = top_municipios_proc['Valor Médio (R$)'].apply(
                lambda x: f"R$ {x:,.2f}" if pd.notna(x) else "N/A"
            )
            st.dataframe(top_municipios_proc, use_container_width=True)
        else:
            st.warning("Dados de município não disponíveis")

with col9:
    st.markdown("#### Distribuição de Valores")
    
    if 'VAL_TOT' in df_filtrado.columns and df_filtrado['VAL_TOT'].notna().sum() > 0:
        valores_validos = df_filtrado['VAL_TOT'].dropna()
        
        if len(valores_validos) > 10:  # Mínimo para histograma
            fig4, ax4 = plt.subplots(figsize=(8, 6))
            ax4.hist(valores_validos, bins=30, alpha=0.7, color='skyblue', edgecolor='black')
            ax4.set_title("Distribuição dos Valores das Internações")
            ax4.set_xlabel("Valor (R$)")
            ax4.set_ylabel("Frequência")
            
            # Adicionar estatísticas no gráfico
            media_val = valores_validos.mean()
            mediana_val = valores_validos.median()
            ax4.axvline(media_val, color='red', linestyle='--', alpha=0.7, label=f'Média: R$ {media_val:,.0f}')
            ax4.axvline(mediana_val, color='green', linestyle='--', alpha=0.7, label=f'Mediana: R$ {mediana_val:,.0f}')
            ax4.legend()
            
            plt.tight_layout()
            st.pyplot(fig4)
        else:
            st.info("Poucos dados para histograma")
    else:
        st.warning("Dados de valores não disponíveis")

# -------------------------------
# ANÁLISES ESPECIALIZADAS
# -------------------------------
with st.expander("Análises Especializadas"):
    col14, col15 = st.columns(2)
    
    with col14:
        st.subheader("Estatísticas por UTI")
        if df_filtrado['MARCA_UTI'].notna().sum() > 0:
            uti_stats = df_filtrado.groupby('MARCA_UTI').agg({
                'N_AIH': 'count',
                'MORTE': 'sum',
                'UTI_MES_TO': 'mean',
                'VAL_UTI': 'mean'
            }).round(2)
            uti_stats.columns = ['Casos', 'Óbitos', 'Meses UTI Médio', 'Valor UTI Médio']
            st.dataframe(uti_stats)
        else:
            st.info("Sem dados de UTI para este procedimento")
    
    with col15:
        st.subheader("Diagnósticos Principais")
        if df_filtrado['DIAG_PRINC'].notna().sum() > 0:
            diag_counts = df_filtrado['DIAG_PRINC'].value_counts().head(10)
            if len(diag_counts) > 0:
                fig5, ax5 = plt.subplots(figsize=(8, 6))
                diag_counts.plot(kind='barh', ax=ax5)
                ax5.set_title("Top 10 Diagnósticos Principais")
                ax5.set_xlabel("Quantidade")
                plt.tight_layout()
                st.pyplot(fig5)
        else:
            st.info("Sem dados de diagnóstico disponíveis")

# -------------------------------
# EXPORTAÇÃO DE DADOS
# -------------------------------
with st.expander("Exportar Dados"):
    st.write("**Baixar dados filtrados:**")
    
    col16, col17 = st.columns(2)
    
    with col16:
        if st.button("Baixar CSV Completo"):
            csv_data = df_filtrado.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv_data,
                file_name=f"sih_rs_{codigo_procedimento}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    
    with col17:
        if st.button("Baixar Resumo Estatístico"):
            resumo = df_filtrado.describe(include='all')
            resumo_csv = resumo.to_csv()
            st.download_button(
                label="Download Resumo",
                data=resumo_csv,
                file_name=f"resumo_{codigo_procedimento}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )

st.markdown("---")
st.markdown("**Fonte:** Sistema de Informações Hospitalares (SIH) - Rio Grande do Sul")
st.markdown("**Banco de Dados:** PostgreSQL Normalizado - Estrutura otimizada para análises")
st.markdown(f"**Última consulta:** {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}")
st.markdown("*Dashboard conectado diretamente ao banco de dados para análises em tempo real*")