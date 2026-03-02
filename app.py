import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# Configuration de la page
st.set_page_config(page_title="Simulateur de Justice Patrimoniale", layout="wide")

# Données de base (Seniors 70+)
data_base = {
    "Groupe": ["D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9", "D10 (9%)", "Top 1%"],
    "Pat_Décès": [3100, 10600, 25000, 57500, 115000, 190000, 275000, 385000, 538000, 1450000, 5200000],
    "Donations": [0, 0, 0, 0, 5000, 15000, 45000, 95000, 180000, 480000, 2100000],
    "Part_H": [0.10, 0.15, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.85, 0.92],
    "Nb": [12000, 20000, 31000, 39000, 45000, 48000, 51000, 52000, 41000, 31000, 4000]
}

# --- INTERFACE ---
st.title("⚖️ Simulateur de Justice Patrimoniale")
st.markdown("Outil de micro-simulation des flux successoraux (Institut La Boétie)")

with st.sidebar:
    st.header("Configuration")
    mode_cumul = st.toggle("Fin de l'amnésie (Tirole-Blanchard)", value=True)
    mode_distinction = st.toggle("Distinguer Créé / Hérité", value=True)
    st.divider()
    scenario = st.selectbox("Scénario", ["Justice de Rupture", "Social-Démocrate", "Personnalisé"])

    if scenario == "Justice de Rupture":
        abatt_val, t_h_max, t_c_max = 150000, 0.99, 0.15
    elif scenario == "Social-Démocrate":
        abatt_val, t_h_max, t_c_max = 100000, 0.45, 0.25
    else:
        abatt_val, t_h_max, t_c_max = 100000, 0.50, 0.30

with st.expander("🛠️ Paramètres experts"):
    col_c, col_h = st.columns(2)
    with col_c:
        taux_c = st.slider("Taux max sur le Créé", 0.0, 1.0, t_c_max)
    with col_h:
        taux_h = st.slider("Taux max sur l'Hérité", 0.0, 1.0, t_h_max)
    abattement = st.number_input("Abattement unique", value=abatt_val)

# --- CALCULS ---
df = pd.DataFrame(data_base)
df["Stock_Total"] = df["Pat_Décès"] + (df["Donations"] if mode_cumul else 0)

if mode_distinction:
    df["Assiette_H"] = df["Stock_Total"] * df["Part_H"]
    df["Assiette_C"] = df["Stock_Total"] * (1 - df["Part_H"])
else:
    df["Assiette_H"] = df["Stock_Total"]
    df["Assiette_C"] = 0

df["Impot"] = np.maximum(0, (df["Assiette_H"] - abattement/2) * taux_h + (df["Assiette_C"] - abattement/2) * taux_c)
df["Recettes"] = df["Impot"] * df["Nb"]

# --- RÉSULTATS ---
m1, m2 = st.columns(2)
total_mrd = df["Recettes"].sum() / 1e9
dotation = (df["Recettes"].sum()) / 800000

m1.metric("Recettes Fiscales", f"{total_mrd:.1f} Md€")
m2.metric("Dotation / Jeune", f"{dotation:,.0f} €")

fig = px.bar(df, x="Groupe", y=["Stock_Total", "Impot"], 
             barmode="overlay", color_discrete_map={"Stock_Total": "#cbd5e0", "Impot": "#e53e3e"})
st.plotly_chart(fig, use_container_width=True)
st.dataframe(df.style.format("{:,.0f}"))