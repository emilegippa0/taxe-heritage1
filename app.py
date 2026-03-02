import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# --- CONFIGURATION ---
st.set_page_config(page_title="Simulateur Héritage Boétie", layout="wide")

# --- TITRE ET INTRODUCTION ---
st.title(" Simulateur de réforme sur l'impot sur les successions")
st.markdown("""
    Ce simulateur modélise une réforme de la fiscalité des transmissions destinée à financer un Héritage Universel.
    
    **Axes de la simulation :**
    * **Flux cumulé** : Intégration des donations et successions sur la vie entière.
    * **Dualité du patrimoine** : Distinction entre patrimoine *créé* et *hérité*.
""")

st.divider()

# --- DONNÉES D'ENTRÉE (Sources : Insee / IPP / DGFiP) ---
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
    st.header("⚙️ Paramètres")
    mode_cumul = st.toggle("Fin de l'amnésie fiscale (Cumul)", value=True)
    mode_distinction = st.toggle("Distinguer Créé / Hérité", value=True)
    
    st.divider()
    abattement = st.number_input("Abattement (Par enfant)", value=100000, step=10000)
    contrib_etat = st.number_input("Prélèvement État (Md€)", value=0.0) * 1e9

    with st.expander("Barème des taux"):
        seuils = [10000, 50000, 75000, 100000, 150000, 250000, 500000, 1000000, 2000000, 1e12]
        taux_c = [st.slider(f"Taux Créé T{i+1}", 0.0, 1.0, 0.05 + (i*0.05), key=f"c{i}") for i in range(10)]
        taux_h = [st.slider(f"Taux Hérité T{i+1}", 0.0, 1.0, 0.50 + (i*0.05) if i < 9 else 0.99, key=f"h{i}") for i in range(10)]

# --- CALCULS ---
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

df = df_base.copy()
df["Masse_parent"] = (df["Patrimoine_au_deces"] + df["Donations_vie"]) if mode_cumul else df["Patrimoine_au_deces"]
df["Part_enfant"] = df["Masse_parent"] / df["Enfants_par_menage"]

def appliquer_fiscalite(row):
    ratio_h = row["H_enfant"] / row["Part_enfant"] if row["Part_enfant"] > 0 else 1
    ratio_c = 1 - ratio_h
    imp_h = calculer_impot_marginal(row["H_enfant"], abattement * ratio_h, seuils, taux_h)
    imp_c = calculer_impot_marginal(row["C_enfant"], abattement * ratio_c, seuils, taux_c)
    return imp_h + imp_c

if mode_distinction:
    df["H_enfant"] = df["Part_enfant"] * df["Part_heritee"]
    df["C_enfant"] = df["Part_enfant"] - df["H_enfant"]
else:
    df["H_enfant"] = df["Part_enfant"]
    df["C_enfant"] = 0

df["Impôt_enfant"] = df.apply(appliquer_fiscalite, axis=1)
df["Recettes_totales"] = df["Impôt_enfant"] * df["Enfants_par_menage"] * df["Nb_successions"]
df["Taux_effectif"] = (df["Impôt_enfant"] / df["Part_enfant"]).fillna(0)

# --- RÉSULTATS ---
total_mrd = df["Recettes_totales"].sum() / 1e9
dotation = max(0, (df["Recettes_totales"].sum() - contrib_etat) / 800000)

c1, c2 = st.columns(2)
c1.metric("Recettes Fiscales Totales", f"{total_mrd:.2f} Md€")
c2.metric("Héritage Universel", f"{dotation:,.0f} € / jeune")

st.plotly_chart(px.line(df, x="Groupe", y="Taux_effectif", markers=True, title="Progressivité de l'impôt (Taux effectif par enfant)").update_yaxes(tickformat=".0%"), use_container_width=True)

# --- TABLEAU COMPLET ---
st.subheader("📋 Détail des flux par décile")
st.dataframe(
    df[["Groupe", "Part_enfant", "H_enfant", "C_enfant", "Impôt_enfant", "Taux_effectif", "Recettes_totales"]].style.format({
        "Part_enfant": "{:,.0f} €", "H_enfant": "{:,.0f} €", "C_enfant": "{:,.0f} €",
        "Impôt_enfant": "{:,.0f} €", "Taux_effectif": "{:.1%}", "Recettes_totales": "{:,.0f} €"
    }), 
    use_container_width=True, 
    height=450  # 450 pixels est la hauteur parfaite pour 11 lignes sans scroll
)

# Bouton de téléchargement
csv = df.to_csv(index=False).encode('utf-8')
st.download_button("📥 Télécharger les données (CSV)", data=csv, file_name="simulation_boetie.csv", mime="text/csv")

# --- SOURCES ET RÉFÉRENCES ---
st.divider()
st.subheader(" Sources et Fondements")
col_a, col_b = st.columns(2)
with col_a:
    st.markdown("""
    **Données Statistiques :**
    * **Insee (2024)** : Enquête *Patrimoine* et comptes nationaux.
    * **IPP (2025)** : Note sur la concentration des héritages en France.
    * **DGFiP** : Données sur les transmissions et donations déclarées.
    """)
with col_b:
    st.markdown("""
    **Cadre Théorique :**
    * **Tirole & Blanchard (2021)** : Rapport sur les défis économiques (Chapitre Inégalités).
    * **Piketty & Zucman** : Travaux sur le capitalisme et la reproduction patrimoniale.
    """)
