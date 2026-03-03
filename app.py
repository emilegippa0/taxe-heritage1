import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# --- CONFIGURATION ---
st.set_page_config(page_title="Simulateur Héritage Boétie", layout="wide")

# --- TITRE ET INTRODUCTION ---
st.title(" Simulateur de réforme sur l'impôt sur les successions")
st.markdown("""
    Ce simulateur modélise une réforme de la fiscalité des transmissions destinée à financer un **Héritage Universel**.
    
    **Axes de la simulation :**
    * **Flux cumulé** : Intégration des donations et successions sur la vie entière.
    * **Dualité du patrimoine** : Distinction entre patrimoine *créé* (effort) et *hérité* (reproduction).
    * **Dotation d'autonomie** : Versement étalé pour accompagner l'entrée dans l'âge adulte.
""")

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
    st.header("⚙️ Paramètres de la Réforme")
    mode_cumul = st.toggle("Fin de l'amnésie fiscale (Cumul)", value=True, help="Si activé, on taxe la somme des donations passées et du patrimoine au décès.")
    mode_distinction = st.toggle("Distinguer Créé / Hérité", value=True, help="Permet d'appliquer des taux plus faibles sur le patrimoine issu du travail.")
    
    st.divider()
    abattement = st.number_input("Abattement (Tranche à 0% par enfant)", value=100000, step=10000)
    contrib_etat = st.number_input("Prélèvement État (Md€)", value=0.0, help="Part des recettes conservée par le budget général.") * 1e9

    with st.expander("📊 Barème : Seuils des tranches marginales"):
        seuils = []
        defauts = [10000, 50000, 75000, 100000, 150000, 250000, 500000, 1000000, 2000000]
        for i in range(9):
            s = st.number_input(f"Seuil {i+1} (€)", value=defauts[i], step=10000, key=f"s{i}")
            seuils.append(s)
        seuils.append(1e12)

    with st.expander("📉 Taux sur le Patrimoine CRÉÉ"):
        taux_c = [st.slider(f"Taux C T{i+1}", 0.0, 1.0, 0.05 + (i*0.05), key=f"c{i}") for i in range(10)]

    with st.expander("📈 Taux sur le Patrimoine HÉRITÉ"):
        taux_h = [st.slider(f"Taux H T{i+1}", 0.0, 1.0, 0.50 + (i*0.05) if i < 9 else 0.99, key=f"h{i}") for i in range(10)]
# --- CALCULS ---
def calculer_impot_marginal(montant, abattement_partiel, seuils_loc, taux_loc):
    taxable = max(0, montant - abattement_partiel)
    if taxable <= 0: return 0
    impot, bas = 0, 0
    for i in range(len(seuils_loc)):
        haut = seuils_loc[i]
        if taxable > bas:
            portion = min(taxable, haut) - bas
            impot += portion * taux_loc[i]
        bas = haut
    return impot

df = df_base.copy()
df["Masse_parent"] = (df["Patrimoine_au_deces"] + df["Donations_vie"]) if mode_cumul else df["Patrimoine_au_deces"]
df["Part_enfant"] = df["Masse_parent"] / df["Enfants_par_menage"]

if mode_distinction:
    df["H_enfant"] = df["Part_enfant"] * df["Part_heritee"]
    df["C_enfant"] = df["Part_enfant"] - df["H_enfant"]
else:
    df["C_enfant"] = df["Part_enfant"]
    df["H_enfant"] = 0

def appliquer_fiscalite(row):
    ratio_h = row["H_enfant"] / row["Part_enfant"] if row["Part_enfant"] > 0 else 1
    ratio_c = 1 - ratio_h
    imp_h = calculer_impot_marginal(row["H_enfant"], abattement * ratio_h, seuils, taux_h)
    imp_c = calculer_impot_marginal(row["C_enfant"], abattement * ratio_c, seuils, taux_c)
    return imp_h + imp_c

df["Impôt_enfant"] = df.apply(appliquer_fiscalite, axis=1)
df["Recettes_totales"] = df["Impôt_enfant"] * df["Enfants_par_menage"] * df["Nb_successions"]
df["Taux_effectif"] = (df["Impôt_enfant"] / df["Part_enfant"]).fillna(0)

# --- RÉSULTATS ---
total_mrd = df["Recettes_totales"].sum() / 1e9
dotation_totale = max(0, (df["Recettes_totales"].sum() - contrib_etat) / 800000)
annuite = dotation_totale / 7

c1, c2 = st.columns(2)
c1.metric("Recettes Fiscales Totales", f"{total_mrd:.2f} Md€")
c2.metric("Héritage Universel (Total)", f"{dotation_totale:,.0f} €")
st.info(f"💡 Soit un versement de **{annuite:,.0f} € par an** pour chaque jeune entre 18 et 25 ans.")

st.plotly_chart(px.line(df, x="Groupe", y="Taux_effectif", markers=True, title="Progressivité de l'impôt (Taux effectif par enfant)").update_yaxes(tickformat=".0%"), use_container_width=True)

# --- TABLEAU COMPLET ---
st.subheader(" Détail des flux par décile")

# Ici on prépare les colonnes pour qu'elles soient lisibles sans scroll horizontal
df_display = df[["Groupe", "Part_enfant", "H_enfant", "C_enfant", "Impôt_enfant", "Taux_effectif", "Recettes_totales"]].copy()
df_display.columns = ["Groupe", "Capital/enf.", "Hérité", "Créé", "Impôt/enf.", "Taux Eff.", "Total (Md€)"]

st.dataframe(
    df_display.style.format({
        "Capital/enf.": "{:,.0f} €", "Hérité": "{:,.0f} €", "Créé": "{:,.0f} €",
        "Impôt/enf.": "{:,.0f} €", "Taux Eff.": "{:.1%}", "Total (Md€)": "{:,.0f} €"
    }), 
    use_container_width=True, 
    height=450,
    hide_index=True # Supprime la colonne 0, 1, 2...
)

# Bouton de téléchargement
csv = df.to_csv(index=False).encode('utf-8')
st.download_button(" Télécharger les données (CSV)", data=csv, file_name="simulation_boetie.csv", mime="text/csv")
