import streamlit as st
import pandas as pd
import numpy as np

# --- CONFIGURATION ---
st.set_page_config(page_title="Simulateur Héritage Boétie", layout="wide")
st.title("⚖️ Simulateur de Justice Patrimoniale (Tirole-Blanchard)")

# --- DONNÉES D'ENTRÉE ---
data = {
    "Groupe": ["D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9", "D10 (9%)", "Top 1%"],
    "Patrimoine_au_deces": [3100, 10600, 25000, 57500, 115000, 190000, 275000, 385000, 538000, 1450000, 5200000],
    "Donations_vie": [0, 0, 0, 0, 5000, 15000, 45000, 95000, 180000, 480000, 2100000],
    "Part_heritee": [0.10, 0.15, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.85, 0.92],
    "Nb_successions": [12000, 20000, 31000, 39000, 45000, 48000, 51000, 52000, 41000, 31000, 4000]
}
df_base = pd.DataFrame(data)

# --- BARRE LATÉRALE (PARAMÈTRES) ---
with st.sidebar:
    st.header("⚙️ Paramètres Généraux")
    abattement = st.number_input("Abattement (Crédit unique)", value=100000, step=10000)
    contrib_etat = st.number_input("Contribution État (Md€)", value=0.0) * 1e9
    
    st.divider()
    
    with st.expander("📊 Seuils des 10 tranches (€)"):
        seuils = []
        valeurs_defaut = [10000, 50000, 75000, 100000, 150000, 250000, 500000, 1000000, 2000000]
        for i in range(9):
            s = st.number_input(f"Seuil {i+1}", value=valeurs_defaut[i], step=10000)
            seuils.append(s)
        seuils.append(1e12) # Tranche infinie

    with st.expander("📉 Taux sur le Patrimoine CRÉÉ"):
        taux_c = []
        for i in range(10):
            t = st.slider(f"Taux Créé T{i+1}", 0.0, 1.0, 0.05 + (i*0.05), key=f"c{i}")
            taux_c.append(t)

    with st.expander("📈 Taux sur le Patrimoine HÉRITÉ"):
        taux_h = []
        for i in range(10):
            t = st.slider(f"Taux Hérité T{i+1}", 0.0, 1.0, 0.50 + (i*0.05) if i < 9 else 0.99, key=f"h{i}")
            taux_h.append(t)

# --- FONCTION DE CALCUL ---
def calculer_impot(montant, seuils, taux):
    impot = 0
    bas = 0
    for i in range(len(seuils)):
        haut = seuils[i]
        taxable = max(0, min(montant, haut) - bas)
        impot += taxable * taux[i]
        bas = haut
    return impot

# --- LOGIQUE DE SIMULATION ---
df = df_base.copy()
df["Stock_total"] = df["Patrimoine_au_deces"] + df["Donations_vie"]
df["Hérité_total"] = df["Stock_total"] * df["Part_heritee"]
df["Créé_total"] = df["Stock_total"] - df["Hérité_total"]

# Répartition de l'abattement
ratio_cree = df["Créé_total"] / df["Stock_total"].replace(0, 1)
ratio_herite = df["Hérité_total"] / df["Stock_total"].replace(0, 1)

df["C_taxable"] = np.maximum(0, df["Créé_total"] - abattement * ratio_cree)
df["H_taxable"] = np.maximum(0, df["Hérité_total"] - abattement * ratio_herite)

df["Impôt"] = df["C_taxable"].apply(lambda x: calculer_impot(x, seuils, taux_c)) + \
              df["H_taxable"].apply(lambda x: calculer_impot(x, seuils, taux_h))

df["Recettes"] = df["Impôt"] * df["Nb_successions"]
total_recettes = df["Recettes"].sum()
dotation_jeune = max(0, (total_recettes - contrib_etat) / 800000)

# --- AFFICHAGE DES RÉSULTATS ---
col1, col2 = st.columns(2)
col1.metric("Recettes fiscales totales", f"{total_recettes/1e9:.2f} Md€")
col2.metric("Dotation par jeune", f"{dotation_jeune:,.0f} €")

st.divider()
st.subheader("Détail par décile de patrimoine")
cols_finales = ["Groupe", "Stock_total", "Hérité_total", "Créé_total", "Impôt", "Recettes"]
st.dataframe(df[cols_finales].style.format("{:,.0f}"), use_container_width=True)

st.info("Méthode Tirole-Blanchard : L'impôt est calculé sur le stock cumulé (succession + toutes les donations passées) pour mettre fin à l'amnésie fiscale.")
