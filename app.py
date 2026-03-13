import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# CONFIGURATION 
st.set_page_config(page_title="Simulateur de reforme de l'impot sur les successions", layout="wide")

# TITRE ET INTRODUCTION 
st.title("Simulateur de reforme de l'impot sur les successions")
st.markdown("""
    Ce simulateur modelise une reforme de la fiscalite des transmissions destinee a financer un **Heritage Universel**.
    
    **Axes de la simulation :**
    * **Flux cumule** : Integration des donations et successions sur la vie entiere.
    * **Dualite du patrimoine** : Distinction entre patrimoine *cree* (effort) et *herite* (reproduction).
    * **Heritage Universel** : Versement etale pour accompagner l'entree dans l'age adulte.
""")

# DONNEES D'ENTREE 
data = {
    "Groupe": ["D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9", "D10 (9%)", "Top 1%"],
    "Patrimoine_au_deces": [3100, 10600, 25000, 57500, 115000, 190000, 275000, 385000, 538000, 1450000, 5200000],
    "Donations_vie": [0, 0, 0, 0, 5000, 15000, 45000, 95000, 180000, 480000, 2100000],
    "Part_heritee": [0.00, 0.00, 0.00, 0.05, 0.15, 0.35, 0.55, 0.68, 0.75, 0.82, 0.90],
    "Nb_successions": [12000, 20000, 31000, 39000, 45000, 48000, 51000, 52000, 41000, 31000, 4000],
    "Enfants_par_menage": [2.5, 2.2, 2.1, 1.9, 1.9, 2.0, 2.0, 2.1, 2.2, 2.2, 2.2]
}
df_base = pd.DataFrame(data)

# BARRE LATERALE 
with st.sidebar:
    st.header("Parametres de la Reforme")
    mode_cumul = st.toggle("Fin de l'amnesie fiscale (Cumul)", value=True)
    mode_distinction = st.toggle("Distinguer Cree / Herite", value=True)
    
    st.divider()
    contrib_etat = st.number_input("Prelevement Etat (Md EUR)", value=0.0) * 1e9

    with st.expander("Seuils des tranches marginales du Patrimoine CREE"):
        seuils_c = []
        defauts_c = [10000, 50000, 75000, 100000, 150000, 250000, 500000, 1000000, 2000000]
        for i in range(9):
            s = st.number_input(f"Seuil C {i+1} (EUR)", value=defauts_c[i], step=10000, key=f"sc_{i}")
            seuils_c.append(s)
        seuils_c.append(1e15)

    with st.expander("Seuils des tranches marginales du Patrimoine HERITE"):
        seuils_h = []
        defauts_h = [10000, 50000, 75000, 100000, 150000, 250000, 500000, 1000000, 2000000]
        for i in range(9):
            s = st.number_input(f"Seuil H {i+1} (EUR)", value=defauts_h[i], step=10000, key=f"sh_{i}")
            seuils_h.append(s)
        seuils_h.append(1e15)

    with st.expander("Taux sur le Patrimoine CREE"):
        taux_c = [st.slider(f"Taux C T{i+1}", 0.0, 1.0, 0.05 + (i*0.05), key=f"c{i}") for i in range(10)]

    with st.expander("Taux sur le Patrimoine HERITE"):
        taux_h = [st.slider(f"Taux H T{i+1}", 0.0, 1.0, 0.50 + (i*0.05) if i < 9 else 0.99, key=f"h{i}") for i in range(10)]

# CALCULS 
def calculer_impot_marginal(montant, seuils_loc, taux_loc):
    if montant <= 0: return 0
    impot, bas = 0, 0
    for i in range(len(seuils_loc)):
        haut = seuils_loc[i]
        if montant > bas:
            portion = min(montant, haut) - bas
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
    imp_h = calculer_impot_marginal(row["H_enfant"], seuils_h, taux_h)
    imp_c = calculer_impot_marginal(row["C_enfant"], seuils_c, taux_c)
    return imp_h + imp_c

# On utilise bien le nom 'Impot_enfant' pour la suite
df["Impot_enfant"] = df.apply(appliquer_fiscalite, axis=1)
df["Recettes_totales"] = df["Impot_enfant"] * df["Enfants_par_menage"] * df["Nb_successions"]
df["Taux_effectif"] = (df["Impot_enfant"] / df["Part_enfant"]).fillna(0)

# RESULTATS 
total_mrd = df["Recettes_totales"].sum() / 1e9
dotation_totale = max(0, (df["Recettes_totales"].sum() - contrib_etat) / 800000)
annuite = dotation_totale / 8

c1, c2 = st.columns(2)
c1.metric("Recettes Fiscales Totales", f"{total_mrd:.2f} Md EUR")
c2.metric("Heritage Universel (Total)", f"{dotation_totale:,.0f} EUR")
st.info(f"Soit un versement de {annuite:,.0f} EUR par an pour chaque jeune entre 18 et 25 ans.")

st.plotly_chart(px.line(df, x="Groupe", y="Taux_effectif", markers=True, title="Progressivite de l'impot (Taux effectif par enfant)").update_yaxes(tickformat=".0%"), use_container_width=True)

# TABLEAU COMPLET 
st.subheader("Detail des flux par decile")

df_display = df[["Groupe", "Part_enfant", "H_enfant", "C_enfant", "Impot_enfant", "Taux_effectif", "Recettes_totales"]].copy()
# On transforme les recettes totales en Millions pour raccourcir la colonne
df_display["Recettes_totales"] = df_display["Recettes_totales"] / 1e6
df_display.columns = ["Groupe", "Cap./enf.", "Part Herite", "Part Cree", "Imp./enf.", "Taux Effectif", "Total (M EUR)"]

st.dataframe(
    df_display.style.format({
        "Cap./enf.": "{:,.0f}",
        "Herite": "{:,.0f}",
        "Cree": "{:,.0f}",
        "Imp./enf.": "{:,.0f}",
        "Taux Eff.": "{:.0%}",
        "Total (MEUR)": "{:,.1f}" # Une decimale pour les millions
    }), 
    use_container_width=True, 
    height=450,
    hide_index=True 
)

# BOUTON DE TELECHARGEMENT
csv = df.to_csv(index=False).encode('utf-8')
st.download_button("Telecharger les donnees (CSV)", data=csv, file_name="simulation_boetie.csv", mime="text/csv")




