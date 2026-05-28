import streamlit as st
import pandas as pd
import numpy as np
from math import comb
import plotly.graph_objects as go

st.set_page_config(page_title="Perudo Calculator", page_icon="🎲", layout="wide")

st.title("🎲 Perudo — Calculateur de probabilités")
st.markdown("Renseigne ta main et le contexte de la partie pour connaître tes chances sur chaque annonce.")

# ─── Fonctions ───────────────────────────────────────────────────────────────

def prob_au_moins_k(n, k, paco=False):
    p = 1/6 if paco else 1/3
    if k > n:
        return 0.0
    if k <= 0:
        return 100.0
    return sum(comb(n, i) * (p**i) * ((1-p)**(n-i)) for i in range(k, n+1)) * 100

def count_in_hand(hand, face, include_pacos=True):
    """Compte combien de dés dans la main correspondent à la face (+ pacos si non-paco)"""
    count = hand.count(face)
    if include_pacos and face != 1:
        count += hand.count(1)
    return count

def prob_avec_main(hand, n_total, k, face):
    """Probabilité conditionnelle : on sait ce qu'on a en main"""
    is_paco = (face == 1)
    n_others = n_total - len(hand)

    # Combien j'ai déjà dans ma main
    in_hand = count_in_hand(hand, face, include_pacos=not is_paco)

    # Il faut trouver (k - in_hand) parmi les dés adverses
    needed = k - in_hand

    if needed <= 0:
        return 100.0
    if n_others <= 0:
        return 0.0

    return prob_au_moins_k(n_others, needed, paco=is_paco)

# ─── Sidebar : configuration ──────────────────────────────────────────────────

with st.sidebar:
    st.header("⚙️ Configuration")

    n_total = st.slider("🎲 Nombre total de dés en jeu", min_value=2, max_value=30, value=15)
    n_ma_main = st.slider("✋ Nombre de dés dans ta main", min_value=1, max_value=6, value=5)

    st.markdown("---")
    st.subheader("🎯 Ta main")
    st.markdown("Clique sur les faces de tes dés :")

    hand = []
    cols = st.columns(n_ma_main)
    face_emoji = {1: "🦜", 2: "2️⃣", 3: "3️⃣", 4: "4️⃣", 5: "5️⃣", 6: "6️⃣"}

    for i, col in enumerate(cols):
        with col:
            val = st.selectbox(
                f"Dé {i+1}",
                options=[1, 2, 3, 4, 5, 6],
                format_func=lambda x: face_emoji[x],
                key=f"die_{i}",
                index=i % 6
            )
            hand.append(val)
            st.markdown(f"<div style='text-align:center;font-size:2rem'>{face_emoji[val]}</div>", unsafe_allow_html=True)

# ─── Résumé de la main ────────────────────────────────────────────────────────

st.markdown("---")
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("✋ Ta main")
    hand_str = "  ".join([face_emoji[d] for d in sorted(hand)])
    st.markdown(f"<div style='font-size:2.5rem;text-align:center;padding:10px'>{hand_str}</div>", unsafe_allow_html=True)

    st.markdown("**Décompte (avec Pacos) :**")
    for face in range(2, 7):
        count = count_in_hand(hand, face, include_pacos=True)
        pacos = hand.count(1)
        direct = hand.count(face)
        if count > 0:
            detail = f"{direct} × {face_emoji[face]}"
            if pacos > 0:
                detail += f" + {pacos} 🦜"
            st.markdown(f"- **{face_emoji[face]}** : {count} dés ({detail})")

    pacos_in_hand = hand.count(1)
    if pacos_in_hand > 0:
        st.markdown(f"- **🦜 Pacos** : {pacos_in_hand} dés")

with col2:
    st.subheader("📊 Probabilités par annonce")

    faces = [2, 3, 4, 5, 6]
    face_labels = ["2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣"]

    tab1, tab2 = st.tabs(["🎯 Faces normales (2-6)", "🦜 Pacos (1)"])

    with tab1:
        max_k = min(n_total, 15)

        # Tableau de probabilités
        data = {}
        for face, label in zip(faces, face_labels):
            probs = []
            for k in range(1, max_k + 1):
                p = prob_avec_main(hand, n_total, k, face)
                probs.append(round(p, 1))
            data[label] = probs

        df = pd.DataFrame(data, index=[f"k={k}" for k in range(1, max_k + 1)])

        def color_cell(val):
            if val >= 70:
                return "background-color: #1a9850; color: white; font-weight:bold"
            elif val >= 50:
                return "background-color: #91cf60; color: black"
            elif val >= 30:
                return "background-color: #fee08b; color: black"
            elif val >= 15:
                return "background-color: #fc8d59; color: black"
            else:
                return "background-color: #d73027; color: white"

        styled = df.style.applymap(color_cell).format("{:.1f}%")
        st.dataframe(styled, use_container_width=True, height=420)

        st.caption("🟢 ≥70% safe | 🟡 30-50% risqué | 🔴 <15% très risqué")

    with tab2:
        max_k_paco = min(n_total // 2 + 1, 10)
        paco_data = {"🦜 Pacos": []}
        for k in range(1, max_k_paco + 1):
            p = prob_avec_main(hand, n_total, k, face=1)
            paco_data["🦜 Pacos"].append(round(p, 1))

        df_paco = pd.DataFrame(paco_data, index=[f"k={k}" for k in range(1, max_k_paco + 1)])
        styled_paco = df_paco.style.applymap(color_cell).format("{:.1f}%")
        st.dataframe(styled_paco, use_container_width=True)
        st.caption("Pour les Pacos, p=1/6 — les annonces de Pacos sont ~2× plus rares")

# ─── Section : Analyser une annonce adverse ───────────────────────────────────

st.markdown("---")
st.subheader("🔍 Analyser une annonce adverse")
st.markdown("Quelqu'un vient d'annoncer quelque chose — quelle est la probabilité qu'il ait raison ?")

col_a, col_b, col_c = st.columns(3)
with col_a:
    annonce_face = st.selectbox("Face annoncée", options=[1,2,3,4,5,6], format_func=lambda x: face_emoji[x], index=3)
with col_b:
    annonce_k = st.number_input("Quantité annoncée (k)", min_value=1, max_value=n_total, value=4)
with col_c:
    st.markdown("<br>", unsafe_allow_html=True)
    analyser = st.button("📊 Analyser", use_container_width=True)

if analyser or True:
    p_adverse = prob_avec_main(hand, n_total, annonce_k, annonce_face)
    p_sans_main = prob_au_moins_k(n_total, annonce_k, paco=(annonce_face==1))

    col_r1, col_r2, col_r3 = st.columns(3)
    with col_r1:
        color = "green" if p_adverse >= 50 else ("orange" if p_adverse >= 25 else "red")
        st.metric(
            label=f"P(≥{annonce_k} × {face_emoji[annonce_face]}) avec ta main",
            value=f"{p_adverse:.1f}%",
            help="Probabilité que l'annonce soit vraie, sachant ce que tu as en main"
        )
    with col_r2:
        st.metric(
            label="P(≥k) sans info de main",
            value=f"{p_sans_main:.1f}%",
            help="Probabilité brute sans connaître ta main"
        )
    with col_r3:
        diff = p_adverse - p_sans_main
        conseil = "✅ Laisser passer" if p_adverse >= 50 else ("⚠️ Hésiter" if p_adverse >= 25 else "❌ Dire DUDO !")
        st.metric(
            label="Conseil",
            value=conseil,
            delta=f"{diff:+.1f}% vs sans info",
        )

    # Jauge visuelle
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=p_adverse,
        number={"suffix": "%", "font": {"size": 36}},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": "#2196F3"},
            "steps": [
                {"range": [0, 25], "color": "#d73027"},
                {"range": [25, 50], "color": "#fc8d59"},
                {"range": [50, 70], "color": "#fee08b"},
                {"range": [70, 85], "color": "#91cf60"},
                {"range": [85, 100], "color": "#1a9850"},
            ],
            "threshold": {"line": {"color": "black", "width": 4}, "thickness": 0.75, "value": 50}
        },
        title={"text": f"Probabilité que l'annonce {annonce_k}×{face_emoji[annonce_face]} soit vraie"}
    ))
    fig.update_layout(height=280, margin=dict(t=60, b=20, l=40, r=40))
    st.plotly_chart(fig, use_container_width=True)
