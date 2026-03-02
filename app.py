import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# --- CONFIGURATION ---
st.set_page_config(page_title="Simulateur Héritage Boétie", layout="wide")
st.title("⚖️ Simulateur de Justice Patrimoniale (Version Finale)")

# --- DONNÉES D'ENTRÉE ---
data = {
    "Groupe": ["D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9", "D10 (9%)", "Top 1%"],
    "Patrimoine_au_deces": [3100, 10600, 25000, 57500, 115000, 190000, 275000, 385000, 538000, 1450000, 5200000],
    "Donations_vie": [0, 0, 0, 0, 5000, 15000, 45000, 95000, 180000, 480000, 2100000],
    "Part_heritee": [0.10, 0.15, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.85, 0.92],
    "Nb_successions": [12000, 20000, 31000, 39000, 45000, 48000, 51000, 52000, 41000, 31000, 4000],
    "Enfants_par_menage": [2.2, 2.1, 2.0, 1.9, 1.9, 1.8, 1.8, 1.8, 1.9, 1.9, 2.0]
}
df_base = pd.DataFrame(data)

# --- BARRE LATÉRALE ---
with st.sidebar:
    st.header("🛠️ Options du Système")
    mode_cumul = st.toggle("Fin de l'amnésie fiscale (Cumul)", value=True)
    mode_distinction = st.toggle("Distinguer Créé / Hérité", value=True)
    
    st.divider()
    abattement = st.number_input("Abattement (Par enfant)", value=100000, step=10000)
    contrib_etat = st.number_input("Contribution État (Md€)", value=0.0) * 1e9

    with st.expander("📊 Seuils des 10 tranches (€)"):
        seuils = []
        defauts = [10000, 50000, 75000, 100000, 150000, 250000, 500000, 1000000, 2000000]
        for i in range(9):
            s = st.number_input(f"Seuil {i+1}", value=defauts[i], step=10000, key=f"s{i}")
            seuils.append(s)
        seuils.append(1e12) # Tranche finale (infinie)

    with st.expander("📉 Taux Patrimoine CRÉÉ"):
        taux_c = [st.slider(f"Taux C T{i+1}", 0.0, 1.0, 0.05 + (i*0.05), key=f"c{i}") for i in range(10)]

    with st.expander("📈 Taux Patrimoine HÉRITÉ"):
        taux_h = [st.slider(f"Taux H T{i+1}", 0.0, 1.0, 0.50 + (i*0.05) if i < 9 else 0.99, key=f"h{i}") for i in range(10)]

# --- FONCTION DE CALCUL MARGINAL ---
def calculer_impot_marginal(montant, abattement_partiel, seuils, taux):
    taxable = max(0, montant - abattement_partiel)
    if taxable <= 0: return 0
    impot, bas = 0, 0
    for i in range(len(seuils)):
        haut = seuils[i]
        if taxable > bas:
            portion = min(taxable, haut) - bas
            impot += portion * taux[i]
        bas = haut
    return impot

# --- LOGIQUE DE SIMULATION ---
df = df_base.copy()

# 1. Masse par enfant
df["Masse_parent"] = (df["Patrimoine_au_deces"] + df["Donations_vie"]) if mode_cumul else df["Patrimoine_au_deces"]
df["Part_enfant"] = df["Masse_parent"] / df["Enfants_par_menage"]

# 2. Distinction Créé/Hérité
if mode_distinction:
    df["H_enfant"] = df["Part_enfant"] * df["Part_heritee"]
    df["C_enfant"] = df["Part_enfant"] - df["H_enfant"]
else:
    df["H_enfant"] = df["Part_enfant"]
    df["C_enfant"] = 0

# 3. Calcul de l'impôt (Ligne par ligne pour les ratios)
def appliquer_fiscalite(row):
    # On répartit l'abattement au prorata
    ratio_h = row["H_enfant"] / row["Part_enfant"] if row["Part_enfant"] > 0 else 1
    ratio_c = 1 - ratio_h
    
    impot_h = calculer_impot_marginal(row["H_enfant"], abattement * ratio_h, seuils, taux_h)
    impot_c = calculer_impot_marginal(row["C_enfant"], abattement * ratio_c, seuils, taux_c)
    return impot_h + impot_c

df["Impôt_enfant"] = df.apply(appliquer_fiscalite, axis=1)

# 4. Agrégation
df["Recettes_totales"] = df["Impôt_enfant"] * df["Enfants_par_menage"] * df["Nb_successions"]
df["Taux_effectif"] = (df["Impôt_enfant"] / df["Part_enfant"]).fillna(0)

# --- AFFICHAGE ---
total_mrd = df["Recettes_totales"].sum() / 1e9
dotation = max(0, (df["Recettes_totales"].sum() - contrib_etat) / 800000)

c1, c2 = st.columns(2)
c1.metric("Recettes Fiscales", f"{total_mrd:.2f} Md€")
c2.metric("Dotation / Jeune", f"{dotation:,.0f} €")

# Graphique
st.subheader("📈 Progressivité de l'impôt (Taux effectif par enfant)")
fig = px.line(df, x="Groupe", y="Taux_effectif", markers=True, line_shape="spline")
fig.update_yaxes(tickformat=".0%")
st.plotly_chart(fig, use_container_width=True)

# Tableau
st.subheader("📋 Détail des flux (Unité : Enfant)")
st.dataframe(df[["Groupe", "Part_enfant", "H_enfant", "C_enfant", "Impôt_enfant", "Taux_effectif", "Recettes_totales"]].style.format({
    "Part_enfant": "{:,.0f} €", "H_enfant": "{:,.0f} €", "C_enfant": "{:,.0f} €",
    "Impôt_enfant": "{:,.0f} €", "Taux_effectif": "{:.1%}", "Recettes_totales": "{:,.0f} €"
}), use_container_width=True)
