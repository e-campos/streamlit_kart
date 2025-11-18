import pandas as pd
import streamlit as st
import plotly.express as px
from datetime import timedelta, time

st.set_page_config(page_title="Dashboard Corrida Kart", layout="wide")
st.title("🏎️ Dashboard Corrida Kart - Análise de Voltas")

# 📂 Upload do Excel
arquivo = st.file_uploader(
    "📂 Envie o arquivo Excel com colunas: Piloto, Volta, Tempo, Latitude, Longitude, Timestamp",
    type=["xlsx"]
)
if arquivo is None:
    st.stop()

# 📄 Leitura e validação
df = pd.read_excel(arquivo)
colunas_necessarias = {"Piloto", "Volta", "Tempo", "Latitude", "Longitude", "Timestamp"}
if not colunas_necessarias.issubset(df.columns):
    st.error(f"O arquivo deve conter as colunas: {', '.join(colunas_necessarias)}")
    st.stop()

# ⏱️ Conversão de tempo
def converter_tempo(t):
    if isinstance(t, str):
        try:
            return pd.to_timedelta(t)
        except:
            return None
    elif isinstance(t, time):
        return timedelta(hours=t.hour, minutes=t.minute, seconds=t.second, microseconds=t.microsecond)
    elif isinstance(t, pd.Timedelta):
        return t
    else:
        return None

df["Tempo"] = df["Tempo"].apply(converter_tempo)
df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
df = df.dropna(subset=["Tempo", "Latitude", "Longitude", "Timestamp"])
df["Tempo (s)"] = df["Tempo"].dt.total_seconds()

# 🎛️ Filtros
st.sidebar.header("Filtros")
pilotos = st.sidebar.multiselect("👤 Pilotos:", sorted(df["Piloto"].unique()), default=df["Piloto"].unique())
voltas = st.sidebar.multiselect("🔁 Voltas:", sorted(df["Volta"].unique()), default=sorted(df["Volta"].unique()))
df_filtrado = df[df["Piloto"].isin(pilotos) & df["Volta"].isin(voltas)]

# 🏆 Melhor volta
melhor_volta = df_filtrado.loc[df_filtrado["Tempo"].idxmin()]
st.metric("🏁 Melhor Volta", f"{melhor_volta['Piloto']} - Volta {melhor_volta['Volta']}", str(melhor_volta['Tempo']).split(".")[0])

# 📈 Gráfico de tempo por volta (destaque para líderes)
lideres = df_filtrado.loc[df_filtrado.groupby("Volta")["Tempo"].idxmin()]
lideres["É_Líder"] = True
df_filtrado = df_filtrado.merge(lideres[["Volta", "Piloto", "É_Líder"]], on=["Volta", "Piloto"], how="left")
df_filtrado["É_Líder"] = df_filtrado["É_Líder"].fillna(False)

st.subheader("📈 Tempo por Volta com Destaque de Líder")
fig = px.line(
    df_filtrado,
    x="Volta",
    y="Tempo (s)",
    color="Piloto",
    symbol="É_Líder",
    symbol_map={True: "star", False: "circle"},
    hover_data=["Piloto", "Tempo"],
    title="Comparativo de Tempo por Volta"
)
st.plotly_chart(fig, use_container_width=True)

# 📊 Média de tempo por piloto
st.subheader("📊 Média de Tempo por Piloto")
media_tempo = df_filtrado.groupby("Piloto")["Tempo"].mean().reset_index()
media_tempo["Média (s)"] = media_tempo["Tempo"].dt.total_seconds()
media_tempo["Média Formatada"] = media_tempo["Tempo"].apply(lambda x: str(x).split(".")[0])
st.dataframe(media_tempo[["Piloto", "Média Formatada", "Média (s)"]].sort_values("Média (s)"))

# 🏁 Classificação geral por tempo total
st.subheader("🏁 Classificação Geral por Tempo Total")
total_tempo = df_filtrado.groupby("Piloto")["Tempo"].sum().reset_index()
total_tempo["Tempo Total (s)"] = total_tempo["Tempo"].dt.total_seconds()
total_tempo["Tempo Formatado"] = total_tempo["Tempo"].apply(lambda x: str(x).split(".")[0])
total_tempo = total_tempo.sort_values("Tempo Total (s)").reset_index(drop=True)
total_tempo.index += 1
st.dataframe(total_tempo[["Piloto", "Tempo Formatado", "Tempo Total (s)"]])

# 📋 Estatísticas complementares
st.subheader("📋 Estatísticas Complementares")
voltas_por_piloto = df_filtrado.groupby("Piloto")["Volta"].nunique().reset_index(name="Voltas Completadas")
st.dataframe(voltas_por_piloto)
