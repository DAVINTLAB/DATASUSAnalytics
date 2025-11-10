import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# -------------------------------
# CONFIGURAÇÃO DO APP
# -------------------------------
st.set_page_config(page_title="Análise de Procedimentos SIH-RS", layout="wide")
st.sidebar.header("Filtros")

# -------------------------------
# LEITURA DOS DADOS
# -------------------------------
@st.cache_data
def load_data():
    # Carrega dados principais
    df_main = pd.read_parquet("../../banco/parquet_unificado/sih_rs_tratado.parquet")
    
    # Carrega tabelas auxiliares
    try:
        df_procedimentos = pd.read_csv("../../banco/procedimentos.csv")
        df_municipios = pd.read_csv("../../banco/municipios_cod.csv")
        df_cid10 = pd.read_csv("../../banco/cid10.csv")
        
        # Merge com nomes dos procedimentos
        df_main = df_main.merge(df_procedimentos, on='PROC_REA', how='left')
        
        # Merge com coordenadas dos municípios (usando MUNIC_RES)
        df_main = df_main.merge(
            df_municipios, 
            left_on='MUNIC_RES', 
            right_on='codigo_6d', 
            how='left'
        )
        
        # Remove procedimentos sem nome (conforme instrução da Isadora)
        df_main = df_main.dropna(subset=['NOME_PROC'])
        
        return df_main, df_procedimentos, df_municipios, df_cid10
        
    except FileNotFoundError as e:
        st.error(f"Arquivo não encontrado: {e}")
        return df_main, None, None, None

# Carrega os dados
df, df_proc, df_mun, df_cid = load_data()

# Verifica se os dados foram carregados
if df is None or len(df) == 0:
    st.error("Erro ao carregar os dados!")
    st.stop()

# Converte datas
df['DT_INTER'] = pd.to_datetime(df['DT_INTER'], errors='coerce')
df['DT_SAIDA'] = pd.to_datetime(df['DT_SAIDA'], errors='coerce')

# -------------------------------
# FILTROS NA SIDEBAR
# -------------------------------
st.sidebar.subheader("Filtros de Dados")

# Filtro por procedimento
procedimentos_com_nome = df.dropna(subset=['NOME_PROC'])['PROC_REA'].unique()
procedimentos_disponiveis = sorted(procedimentos_com_nome)

codigo_procedimento = st.sidebar.selectbox(
    "Escolha o código do procedimento", 
    procedimentos_disponiveis,
    format_func=lambda x: f"{x} - {df[df['PROC_REA']==x]['NOME_PROC'].iloc[0][:50]}..."
)

# Filtro por ano
anos_disponiveis = sorted(df['DT_INTER'].dt.year.dropna().unique(), reverse=True)
anos_selecionados = st.sidebar.multiselect(
    "Selecionar anos:",
    anos_disponiveis,
    default=anos_disponiveis[:3] if len(anos_disponiveis) >= 3 else anos_disponiveis
)

# Filtro por município (top 20 mais frequentes)
top_municipios = df['nome'].value_counts().head(20).index.tolist()
municipios_selecionados = st.sidebar.multiselect(
    "Filtrar por municípios (top 20):",
    top_municipios,
    default=[]
)

# Aplicar filtros
df_filtrado = df[df['PROC_REA'] == codigo_procedimento].copy()

if anos_selecionados:
    df_filtrado = df_filtrado[df_filtrado['DT_INTER'].dt.year.isin(anos_selecionados)]

if municipios_selecionados:
    df_filtrado = df_filtrado[df_filtrado['nome'].isin(municipios_selecionados)]

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
# Remove registros com idade muito baixa (conforme código original)
df_filtrado = df_filtrado[df_filtrado['IDADE'] >= 10]

# Faixas etárias
bins = list(range(10, 90, 5)) + [200]
labels = [f"{i}-{i+4}" for i in range(10, 85, 5)] + ["85+"]
df_filtrado['faixa_etaria'] = pd.cut(df_filtrado['IDADE'], bins=bins, labels=labels, right=False)

# Mapeamento de sexo
sexo_map = {1: 'Masculino', 3: 'Feminino'}
df_filtrado['sexo'] = df_filtrado['SEXO'].map(sexo_map)

# Indicadores
df_filtrado['dias_internado'] = (df_filtrado['DT_SAIDA'] - df_filtrado['DT_INTER']).dt.days

# Calcula métricas
percentual_obito = (df_filtrado['MORTE'].sum() / len(df_filtrado) * 100) if len(df_filtrado) > 0 else 0
media_gasto = df_filtrado['VAL_TOT'].mean() if 'VAL_TOT' in df_filtrado.columns else 0
media_dias = df_filtrado['dias_internado'].mean() if len(df_filtrado) > 0 else 0
total_internacoes = len(df_filtrado)

# -------------------------------
# INDICADORES GERAIS
# -------------------------------
st.markdown("### Indicadores Gerais")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total de Internações", f"{total_internacoes:,}")

with col2:
    st.metric("Percentual de Óbito", f"{percentual_obito:.1f}%")

with col3:
    if not pd.isna(media_gasto) and media_gasto > 0:
        st.metric("Valor Médio Gasto", f"R$ {media_gasto:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    else:
        st.metric("Valor Médio Gasto", "N/A")

with col4:
    if not pd.isna(media_dias) and media_dias > 0:
        st.metric("Dias Médios de Internação", f"{media_dias:.1f} dias")
    else:
        st.metric("Dias Médios de Internação", "N/A")

# -------------------------------
# GRÁFICOS: PIRÂMIDE E HEATMAP
# -------------------------------
col5, col6 = st.columns(2)

# Pirâmide etária
with col5:
    st.markdown("#### Pirâmide Etária por Sexo")
    
    # Remove valores nulos de sexo e faixa etária
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
with col6:
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
    tendencia = df_temporal.groupby('ano_mes').size().reset_index(name='quantidade')

    if len(tendencia) > 1:
        fig3, ax3 = plt.subplots(figsize=(12, 6))
        sns.lineplot(data=tendencia, x='ano_mes', y='quantidade', marker='o', ax=ax3)
        ax3.set_title("Evolução Mensal da Quantidade de Procedimentos")
        ax3.set_xlabel("Período")
        ax3.set_ylabel("Quantidade de Internações")
        
        # Formatação do eixo X
        import matplotlib.dates as mdates
        ax3.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax3.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        st.pyplot(fig3)
    else:
        st.info("Dados insuficientes para análise temporal")
else:
    st.warning("Sem dados de data para análise temporal")

# -------------------------------
# ANÁLISE POR MUNICÍPIO
# -------------------------------
st.markdown("### Análise Geográfica")

col7, col8 = st.columns(2)

with col7:
    st.markdown("#### Top 10 Municípios")
    
    if 'nome' in df_filtrado.columns:
        top_municipios_proc = df_filtrado.groupby('nome').agg({
            'N_AIH': 'count',
            'VAL_TOT': 'mean',
            'MORTE': 'sum'
        }).round(2)
        
        top_municipios_proc.columns = ['Internações', 'Valor Médio', 'Óbitos']
        top_municipios_proc = top_municipios_proc.sort_values('Internações', ascending=False).head(10)
        
        if len(top_municipios_proc) > 0:
            st.dataframe(top_municipios_proc)
        else:
            st.warning("Dados de município não disponíveis")

with col8:
    st.markdown("#### Distribuição de Valores")
    
    if 'VAL_TOT' in df_filtrado.columns and df_filtrado['VAL_TOT'].notna().sum() > 0:
        valores_validos = df_filtrado['VAL_TOT'].dropna()
        
        if len(valores_validos) > 0:
            fig4, ax4 = plt.subplots(figsize=(8, 6))
            ax4.hist(valores_validos, bins=30, alpha=0.7, color='skyblue', edgecolor='black')
            ax4.set_title("Distribuição dos Valores das Internações")
            ax4.set_xlabel("Valor (R$)")
            ax4.set_ylabel("Frequência")
            
            plt.tight_layout()
            st.pyplot(fig4)
    else:
        st.warning("Dados de valores não disponíveis")

# -------------------------------
# MAPA DE LOCALIZAÇÃO
# -------------------------------
st.markdown("### Mapa de Localização dos Pacientes")

# Criar dados para o mapa
if 'latitude' in df_filtrado.columns and 'longitude' in df_filtrado.columns:
    mapa_dados = df_filtrado.groupby(['nome', 'latitude', 'longitude']).size().reset_index(name='quantidade')
    mapa_dados = mapa_dados.dropna(subset=['latitude', 'longitude'])
    
    if len(mapa_dados) > 0:
        # Renomear colunas para o formato esperado pelo st.map
        mapa_dados = mapa_dados.rename(columns={'latitude': 'lat', 'longitude': 'lon'})
        
        # Filtrar coordenadas válidas
        mapa_dados = mapa_dados[
            (mapa_dados['lat'].between(-90, 90)) & 
            (mapa_dados['lon'].between(-180, 180))
        ]
        
        if len(mapa_dados) > 0:
            st.map(mapa_dados, size='quantidade', zoom=6)
            
            # Estatísticas do mapa
            col9, col10, col11 = st.columns(3)
            with col9:
                st.metric("Municípios no Mapa", len(mapa_dados))
            with col10:
                st.metric("Total Internações", mapa_dados['quantidade'].sum())
            with col11:
                st.metric("Média por Município", f"{mapa_dados['quantidade'].mean():.1f}")
        else:
            st.warning("Coordenadas inválidas nos dados")
    else:
        st.warning("Sem dados de coordenadas válidos para o mapa")
else:
    st.warning("Dados de localização não disponíveis")

# -------------------------------
# INFORMAÇÕES ADICIONAIS
# -------------------------------
with st.expander("Estatísticas Detalhadas"):
    st.write("**Dados do Procedimento:**")
    st.write(f"- Código: {codigo_procedimento}")
    st.write(f"- Nome: {nome_procedimento}")
    st.write(f"- Total de registros analisados: {len(df_filtrado):,}")
    
    if anos_selecionados:
        st.write(f"- Anos incluídos: {', '.join(map(str, anos_selecionados))}")
    
    if municipios_selecionados:
        st.write(f"- Municípios filtrados: {', '.join(municipios_selecionados)}")
    
    st.write("**Qualidade dos Dados:**")
    st.write(f"- Registros com data válida: {df_filtrado['DT_INTER'].notna().sum():,}")
    st.write(f"- Registros com sexo válido: {df_filtrado['sexo'].notna().sum():,}")
    st.write(f"- Registros com valor financeiro: {df_filtrado['VAL_TOT'].notna().sum():,}")
    st.write(f"- Registros com coordenadas: {df_filtrado[['latitude', 'longitude']].notna().all(axis=1).sum():,}")

# Rodapé
st.markdown("---")
st.markdown("**Fonte:** Sistema de Informações Hospitalares (SIH) - Rio Grande do Sul")
st.markdown("*Dashboard adaptado para análise de procedimentos hospitalares*")