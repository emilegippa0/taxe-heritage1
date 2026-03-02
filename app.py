import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# --- CONFIGURATION ---
st.set_page_config(page_title="Simulateur Héritage Boétie", layout="wide")
st.title("⚖️ Simulateur de Justice Patrimoniale")

# --- DONNÉES D'ENTRÉE  ---
data = {
    "Groupe": ["D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9", "D10 (9%)", "Top 1%"],
    "Patrimoine_au_deces": [3100, 10600, 25000, 57500, 115000, 190000, 275000, 385000, 538000, 1450000, 5200000],
    "Donations_vie": [0, 0, 0, 0, 5000, 15000, 45000, 95000, 180000, 480000, 2100000],
    "Part_heritee": [0.10, 0.15, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.85, 0.92],
    "Nb_successions": [12000, 20000, 31000, 39000, 45000, 48000, 51000, 52000, 41000, 31000, 4000]
}
df_base = pd.DataFrame(data)

# --- BARRE LATÉRALE ---
with st.sidebar:
    st.header("🛠️ Options du Système")
    
    mode_cumul = st.toggle("Fin de l'amnésie fiscale (Cumul vie entière)", value=True)
    mode_distinction = st.toggle("Distinguer Créé / Hérité", value=True)
    
    st.divider()
    
    abattement = st.number_input("Abattement (Crédit unique)", value=100000, step=10000)
    contrib_etat = st.number_input("Contribution État (Md€)", value=0.0) * 1e9

    with st.expander("📊 Seuils des 10 tranches (€)"):
        seuils = []
        defauts = [10000, 50000, 75000, 100000, 150000, 250000, 500000, 1000000, 2000000]
        for i in range(9):
            s = st.number_input(f"Seuil {i+1}", value=defauts[i], step=10000, key=f"s{i}")
            seuils.append(s)
        seuils.append(1e12)

    with st.expander("📉 Taux Patrimoine CRÉÉ"):
        taux_c = [st.slider(f"Taux C T{i+1}", 0.0, 1.0, 0.05 + (i*0.05), key=f"c{i}") for i in range(10)]

    with st.expander("📈 Taux Patrimoine HÉRITÉ"):
        taux_h = [st.slider(f"Taux H T{i+1}", 0.0, 1.0, 0.50 + (i*0.05) if i < 9 else 0.99, key=f"h{i}") for i in range(10)]

# --- CALCULS ---
df = df_base.copy()

# 1. Gestion du cumul (Amnésie ou non)
if mode_cumul:
    df["Stock_total_transmis"] = df["Patrimoine_au_deces"] + df["Donations_vie"]
else:
    df["Stock_total_transmis"] = df["Patrimoine_au_deces"]

# 2. Gestion de la distinction
if mode_distinction:
    df["Hérité_total"] = df["Stock_total_transmis"] * df["Part_heritee"]
    df["Créé_total"] = df["Stock_total_transmis"] - df["Hérité_total"]
else:
    # Si on ne distingue pas, tout est considéré comme une seule masse (on applique le barème 'Crée')
    df["Créé_total"] = df["Stock_total_transmis"]
    df["Hérité_total"] = 0

# 3. Impôts
def calculer_impot(montant, seuils, taux):
    impot, bas = 0, 0
    for i in range(len(seuils)):
        taxable = max(0, min(montant, seuils[i]) - bas)
        impot += taxable * taux[i]
        bas = seuils[i]
    return impot

ratio_h = df["Hérité_total"] / df["Stock_total_transmis"].replace(0, 1)
ratio_c = df["Créé_total"] / df["Stock_total_transmis"].replace(0, 1)

df["Impôt_sur_vie"] = df["Hérité_total"].apply(lambda x: calculer_impot(max(0, x - abattement*ratio_h.iloc[0]), seuils, taux_h)) + \
                      df["Créé_total"].apply(lambda x: calculer_impot(max(0, x - abattement*ratio_c.iloc[0]), seuils, taux_c))

df["Taux_effectif_cumulé"] = (df["Impôt_sur_vie"] / df["Stock_total_transmis"]).fillna(0)
df["Recettes_totales"] = df["Impôt_sur_vie"] * df["Nb_successions"]

# --- AFFICHAGE ---
total_mrd = df["Recettes_totales"].sum() / 1e9
dotation = (df["Recettes_totales"].sum() - contrib_etat) / 800000

m1, m2 = st.columns(2)
m1.metric("Recettes Fiscales", f"{total_mrd:.2f} Md€")
m2.metric("Dotation / Jeune", f"{dotation:,.0f} €")

# GRAPHIQUE DE PROGRESSIVITÉ
st.subheader("📈 Progressivité de l'impôt")
fig = px.line(df, x="Groupe", y="Taux_effectif_cumulé", 
              title="Taux d'imposition effectif par décile",
              markers=True, line_shape="spline")
fig.update_yaxes(tickformat=".0%")
st.plotly_chart(fig, use_container_width=True)

# TABLEAU FINAL 
st.subheader("📋 Tableau détaillé des flux")
st.dataframe(
    df[["Groupe", "Patrimoine_au_deces", "Donations_vie", "Stock_total_transmis", "Impôt_sur_vie", "Taux_effectif_cumulé", "Recettes_totales"]].style.format({
        "Patrimoine_au_deces": "{:,.0f} €",
        "Donations_vie": "{:,.0f} €",
        "Stock_total_transmis": "{:,.0f} €",
        "Impôt_sur_vie": "{:,.0f} €",
        "Taux_effectif_cumulé": "{:.1%}",
        "Recettes_totales": "{:,.0f} €"
    }), use_container_width=True
)


