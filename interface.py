import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
import plotly.express as px
from datetime import datetime
from chatbot import PosteTunisienneBot, initialize_bot
import warnings
import logging
import os
import yaml
from yaml.loader import SafeLoader
import base64

warnings.filterwarnings('ignore')

# Configuration de la page
st.set_page_config(
    page_title="La Poste Tunisienne - Assistant IA",
    page_icon="📬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuration de la journalisation
if not os.path.exists('logs'):
    os.makedirs('logs')
logging.basicConfig(
    filename='logs/app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Chargement du fichier config.yaml
with open("config.yaml") as file:
    config = yaml.load(file, Loader=SafeLoader)

# Initialisation de l'authentificateur
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

# Couleurs de La Poste Tunisienne
POSTE_BLUE = "#003d82"
POSTE_GOLD = "#ffb81c"
LIGHT_BLUE = "#4a90e2"
BACKGROUND_COLOR = "#f8f9fa"

# Conversion des images en base64
def get_base64_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()

logo_base64 = get_base64_image("assets/logo.png") if os.path.exists("assets/logo.png") else ""
tun_base64 = get_base64_image("assets/tun.png") if os.path.exists("assets/tun.png") else ""

# CSS optimisé avec ajouts demandés
CSS_STYLES = f"""
<style>
    .main-header {{
        background: linear-gradient(135deg, {POSTE_BLUE} 0%, {LIGHT_BLUE} 100%);
        padding: 1rem;
        border-radius: 15px;
        margin-bottom: 1.5rem;
        margin-top: 1rem; /* Décollé du haut */
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.15);
    }}
    .welcome-text {{
        color: white;
        font-size: 1.8rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 0.5rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }}
    .subtitle {{
        color: {POSTE_GOLD};
        font-size: 1rem;
        text-align: center;
        margin-bottom: 0;
        font-weight: 500;
    }}
    .logo-container {{
        text-align: center;
        margin-bottom: 1rem;
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 1rem;
    }}
    .logo-equal {{
        width: 80px !important;
        height: 60px !important;
        object-fit: contain;
    }}
    .kpi-card {{
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 5px solid {POSTE_BLUE};
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
        transition: transform 0.3s ease;
    }}
    .kpi-card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
    }}
    .kpi-value {{
        font-size: 2.2rem;
        font-weight: bold;
        color: {POSTE_BLUE};
        margin: 0;
    }}
    .kpi-label {{
        font-size: 0.95rem;
        color: #666;
        margin: 0;
        font-weight: 500;
    }}
    .sidebar {{
        background: linear-gradient(180deg, {POSTE_BLUE} 0%, {LIGHT_BLUE} 100%);
    }}
    .chat-container {{
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        margin-bottom: 1.5rem;
        border: 1px solid #e0e0e0;
        max-height: 500px;
        overflow-y: auto;
    }}
    .chat-message-user {{
        background: linear-gradient(135deg, {POSTE_BLUE} 0%, {LIGHT_BLUE} 100%);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 20px 20px 5px 20px;
        margin: 0.5rem 0;
        margin-left: 2rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }}
    .chat-message-bot {{
        background: #f8f9fa;
        color: {POSTE_BLUE};
        padding: 1rem 1.5rem;
        border-radius: 20px 20px 20px 5px;
        margin: 0.5rem 0;
        margin-right: 2rem;
        border-left: 4px solid {POSTE_GOLD};
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }}
    .alert-box {{
        background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
        border: 1px solid {POSTE_GOLD};
        border-radius: 12px;
        padding: 1.2rem;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }}
    .suggestion-box {{
        background: linear-gradient(135deg, #e8f4fd 0%, #cce7ff 100%);
        border: 1px solid {LIGHT_BLUE};
        border-radius: 8px;
        padding: 0.8rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }}
    .report-box {{
        background: white;
        border: 1px solid {POSTE_BLUE};
        border-radius: 10px;
        padding: 1.5rem;
        margin-top: 0;
        box-shadow: 0 3px 6px rgba(0,0,0,0.1);
    }}
    .stButton > button {{
        background: linear-gradient(135deg, {POSTE_BLUE} 0%, {LIGHT_BLUE} 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.5rem 1.2rem !important; /* Minimisé */
        font-weight: bold !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1) !important;
    }}
    .stButton > button:hover {{
        background: linear-gradient(135deg, {LIGHT_BLUE} 0%, {POSTE_GOLD} 100%) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2) !important;
    }}
    .suggestion-button > button {{
        background: linear-gradient(135deg, {POSTE_BLUE} 0%, {LIGHT_BLUE} 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.5rem 1.5rem !important;
        font-weight: bold !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1) !important;
        margin: 0.2rem !important;
        width: 100% !important;
    }}
    .suggestion-button > button:hover {{
        background: linear-gradient(135deg, {LIGHT_BLUE} 0%, {POSTE_GOLD} 100%) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2) !important;
    }}
    .masque-button {{
        background: white;
        border: 2px solid {POSTE_BLUE};
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s ease;
        color: {POSTE_BLUE};
        font-weight: bold;
        width: 100%;
    }}
    .masque-button:hover {{
        background: {POSTE_BLUE};
        color: white;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
    }}
    .stTextInput > div > div > input {{
        border-radius: 10px !important;
        border: 2px solid {POSTE_BLUE} !important;
        padding: 0.7rem !important;
        color: {POSTE_BLUE} !important;
    }}
    .stTextInput > div > div > input:focus {{
        border-color: {POSTE_GOLD} !important;
        box-shadow: 0 0 0 2px rgba(255, 184, 28, 0.2) !important;
    }}
    .stSelectbox > div > div > div, .stMultiselect > div > div > div {{
        background-color: {POSTE_BLUE} !important;
        color: white !important;
    }}
    .stSelectbox > div > div > div[data-selected="true"], 
    .stMultiselect > div > div > div[data-selected="true"] {{
        background-color: {POSTE_BLUE} !important;
        color: white !important;
    }}
    .stSelectbox > div > div, .stMultiselect > div > div {{
        background: white !important;
        border: 2px solid {POSTE_BLUE} !important;
        border-radius: 10px !important;
        padding: 0.5rem !important;
        color: {POSTE_BLUE} !important;
        font-weight: 500 !important;
        transition: all 0.3s ease !important;
    }}
    .stSelectbox > div > div:hover, .stMultiselect > div > div:hover {{
        border-color: {POSTE_GOLD} !important;
        box-shadow: 0 0 0 2px rgba(255, 184, 28, 0.2) !important;
    }}
    .sidebar-logo {{
        text-align: center;
        padding: 1.5rem;
        background: rgba(255,255,255,0.1);
        border-radius: 15px;
        margin-bottom: 1.5rem;
        border: 2px solid {POSTE_GOLD};
    }}
    .nav-title {{
        color: {POSTE_GOLD};
        font-size: 1.1rem;
        font-weight: bold;
        margin-bottom: 0.8rem;
        text-align: center;
    }}
    .info-card {{
        background: rgba(255,255,255,0.1);
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 3px solid {POSTE_GOLD};
    }}
    .info-card p {{
        color: {POSTE_BLUE};
        font-size: 0.85rem;
    }}
    .decorative-footer {{
        background: linear-gradient(135deg, {POSTE_BLUE} 0%, {LIGHT_BLUE} 100%);
        padding: 1.5rem;
        border-radius: 15px;
        margin-top: 2rem;
        text-align: center;
        color: white;
    }}
    .rtl-text {{
        direction: rtl;
        text-align: right;
    }}
    .suggestion-rephrase-box {{
        background: linear-gradient(135deg, #e8f4fd 0%, #cce7ff 100%);
        border: 1px solid {LIGHT_BLUE};
        border-radius: 8px;
        padding: 0.8rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }}
    /* Styles pour les filtres */
    .stMultiSelect [data-baseweb="select"] {{
        border: 2px solid #1e3a8a !important;
        border-radius: 10px !important;
        background-color: white !important;
    }}

    .stMultiSelect [data-baseweb="tag"] {{
        background-color: #1e3a8a !important;
        color: white !important;
        border-radius: 5px !important;
    }}

    .stSelectbox [data-baseweb="select"] > div {{
        background-color: white !important;
        color: #1e3a8a !important;
        border: 2px solid #1e3a8a !important;
        border-radius: 10px !important;
    }}

    /* Style pour le bouton Envoyer du chat */
    .stForm [data-testid="stFormSubmitButton"] > button {{
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.5rem 1.2rem !important; /* Minimisé */
        font-weight: bold !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15) !important;
        width: auto !important; /* Ajusté pour ne pas être trop large */
        font-size: 1.1rem !important;
    }}

    .stForm [data-testid="stFormSubmitButton"] > button:hover {{
        background: linear-gradient(135deg, #3b82f6 0%, #f59e0b 100%) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.25) !important;
    }}

    /* Page d'authentification améliorée */
    .auth-form-container {{
        padding: 2rem;
        max-width: 450px;
        margin: 2rem auto;
        text-align: center;
    }}

    .auth-title-main {{
        color: #1e3a8a;
        font-size: 2.2rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }}

    .auth-title-arabic {{
        color: #f59e0b;
        font-size: 1.3rem;
        margin-bottom: 0.5rem;
        font-weight: 600;
    }}

    .auth-subtitle-main {{
        color: #6b7280;
        font-size: 1rem;
        margin-bottom: 2rem;
    }}

    /* Boutons de suggestions améliorés */
    .suggestion-container button {{
        background: linear-gradient(135deg, {POSTE_BLUE} 0%, {LIGHT_BLUE} 100%) !important; /* Aligné au design des autres boutons */
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.5rem 1.2rem !important; /* Minimisé */
        font-weight: bold !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1) !important;
        margin: 0.2rem !important;
        width: 100% !important;
        font-size: 0.95rem !important;
    }}

    .suggestion-container button:hover {{
        background: linear-gradient(135deg, {LIGHT_BLUE} 0%, {POSTE_GOLD} 100%) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2) !important;
    }}
    .block-container {{
        padding-top: 0rem !important;
        padding-bottom: 0rem !important;
    }}
    .main .block-container {{
        max-width: 100% !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }}
</style>
"""
st.markdown(CSS_STYLES, unsafe_allow_html=True)

# Gestion de la connexion
if not st.session_state.get("authentication_status"):
    

    # Ajouter la logique d'authentification Streamlit
    fields = {
        'Form name': '',
        'Username': 'Nom d\'utilisateur',
        'Password': 'Mot de passe',
        'Login': 'Connexion'
    }
    authenticator.login(fields=fields, location='main')

if st.session_state["authentication_status"]:
    st.sidebar.title("")  # Supprime "Utilisateur : admin"

    # Initialisation du bot
    with st.spinner("🔄 Chargement du chatbot..."):
        if 'bot' not in st.session_state:
            st.session_state.bot = initialize_bot()

    # Sidebar
    with st.sidebar:
        st.markdown(f"""
        <div class="sidebar-logo">
            {'<img src="data:image/png;base64,' + logo_base64 + '" style="width: 80px; height: auto; margin-bottom: 0.5rem; display: block; margin-left: auto; margin-right: auto;">' if logo_base64 else '<div style="font-size: 3rem; color: white; text-align: center;">📬</div>'}
            <h2 style="color: {POSTE_BLUE}; margin: 0.2rem 0; font-size: 1.3rem; text-align: center;">La Poste</h2> <!-- Changé en bleu -->
            <h3 style="color: {POSTE_GOLD}; margin: 0; font-size: 1.1rem; text-align: center;">Tunisienne</h3>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="nav-title">Navigation</div>', unsafe_allow_html=True)
        pages = [("Accueil", "home"), ("Dashboard", "dashboard"), ("Assistant IA", "assistant"), ("Rapports", "reports")]
        for page_name, page_key in pages:
            if st.button(page_name, key=f"nav_{page_key}", use_container_width=True):
                st.session_state.current_page = page_key
        
        st.markdown('<div class="nav-title">Informations Système</div>', unsafe_allow_html=True)
        stats = st.session_state.bot.get_quick_stats()
        st.markdown(f"""
        <div class="info-card">
            <div>
                <p><strong>Période:</strong> {stats['date_range']['start']} - {stats['date_range']['end']}</p>
                <p><strong>Entités:</strong> {stats['entities']} régions</p>
                <p><strong>Budget:</strong> {stats['total_budget']/1e9:.2f}B TND</p>
                <p><strong>IA:</strong> Groq LLaMA</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Bouton déconnexion en bas
        st.markdown('<div class="logout-button">', unsafe_allow_html=True)
        authenticator.logout("Se déconnecter", location="sidebar")
        st.markdown('</div>', unsafe_allow_html=True)

    # Initialisation de l'état de session
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'current_alerts' not in st.session_state:
        st.session_state.current_alerts = []
    if 'current_suggestions' not in st.session_state:
        st.session_state.current_suggestions = []
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'home'
    if 'last_input' not in st.session_state:
        st.session_state.last_input = None

    # Vérification des données
    if st.session_state.bot.df is None or st.session_state.bot.df.empty:
        st.error("Erreur : Aucun fichier de données valide trouvé. Vérifiez PosteBudget.csv.")
        st.stop()

    # Page Accueil
    if st.session_state.current_page == 'home':
        st.markdown(f"""
<div class="main-header">
    <div class="logo-container">
        {'<img src="data:image/png;base64,' + logo_base64 + '" class="logo-equal">' if logo_base64 else '<div style="font-size: 3rem; color: white;">📬</div>'}
        {'<img src="data:image/png;base64,' + tun_base64 + '" class="logo-equal">' if tun_base64 else ''}
    </div>
    <div class="welcome-text">أهلا وسهلا - BIENVENUE - WELCOME</div>
    <div class="subtitle">Votre Solution Budgétaire Intelligente</div>
</div>
""", unsafe_allow_html=True)
        
        st.markdown("### Masques de Saisie")
        col1, col2, col3, col4 = st.columns(4)
        masques = [
            ("CAPEX", "Dépenses d'investissement", "CAPEX"),
            ("OPEX", "Dépenses opérationnelles", "OPEX"),
            ("États financiers", "Rapports financiers", "ETATS"),
            ("Consolidation", "Consolidation des comptes", "CONSOLIDATION")
        ]
        for i, (masque, description, key) in enumerate(masques):
            with [col1, col2, col3, col4][i]:
                if st.button(masque, key=f"masque_{key}", use_container_width=True):
                    st.success(f"Redirection vers SAP Analytics Cloud - {description}")
                    st.info("Module de saisie activé")
        
        st.markdown("### Workflow Budgétaire")
        if st.button("Accéder au workflow budgétaire", key="workflow_budget", use_container_width=True):
            st.success("Redirection vers SAP Analytics Cloud - Workflow Budgétaire")
            st.info("Module de workflow activé")
        
        st.markdown("""
        <div class="decorative-footer">
            <h3>La Poste Tunisienne - البريد التونسي</h3>
            <p style="font-size: 0.9rem;">Système d'Analyse Budgétaire Intelligent • © 2025</p>
        </div>
        """, unsafe_allow_html=True)

    # Page Dashboard
    elif st.session_state.current_page == 'dashboard':
        st.markdown(f"""
<div class="main-header">
    <div class="logo-container">
        {'<img src="data:image/png;base64,' + logo_base64 + '" class="logo-equal">' if logo_base64 else '<div style="font-size: 3rem; color: white;">📬</div>'}
        {'<img src="data:image/png;base64,' + tun_base64 + '" class="logo-equal">' if tun_base64 else ''}
    </div>
    <div class="welcome-text">Tableau de Bord Budgétaire</div>
    <div class="subtitle">Insights pour une gestion financière optimisée</div>
</div>
""", unsafe_allow_html=True)
        
        # Filtres interactifs
        st.markdown("### Filtres de Données")
        col1, col2 = st.columns(2)
        with col1:
            selected_years = st.multiselect("Années", sorted(st.session_state.bot.df['Année'].unique()), default=sorted(st.session_state.bot.df['Année'].unique()))
        with col2:
            selected_entities = st.multiselect("Régions", st.session_state.bot.df['Entité'].unique(), default=st.session_state.bot.df['Entité'].unique())
        
        # Logique de filtrage CORRIGÉE - afficher toutes les données par défaut
        filtered_data = st.session_state.bot.df.copy()

        # Appliquer les filtres seulement si des éléments spécifiques sont sélectionnés
        all_years = sorted(st.session_state.bot.df['Année'].unique())
        all_entities = st.session_state.bot.df['Entité'].unique()

        if selected_years and len(selected_years) < len(all_years):
            filtered_data = filtered_data[filtered_data['Année'].isin(selected_years)]
        if selected_entities and len(selected_entities) < len(all_entities):
            filtered_data = filtered_data[filtered_data['Entité'].isin(selected_entities)]
        
        # KPIs
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            total_budget = filtered_data['Budget'].sum()
            st.markdown(f"""
            <div class="kpi-card">
                <p class="kpi-value">{total_budget/1e9:.2f}B</p>
                <p class="kpi-label">Budget Total (TND)</p>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            avg_budget = filtered_data['Budget'].mean() if not filtered_data.empty else 0
            st.markdown(f"""
            <div class="kpi-card">
                <p class="kpi-value">{avg_budget/1e6:.2f}M</p>
                <p class="kpi-label">Moyenne Mensuelle</p>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            forecast_budget = filtered_data[filtered_data['is_forecast'] == 1]['Budget'].sum()
            st.markdown(f"""
            <div class="kpi-card">
                <p class="kpi-value">{forecast_budget/1e9:.2f}B</p>
                <p class="kpi-label">Prévisions</p>
            </div>
            """, unsafe_allow_html=True)
        with col4:
            approval_rate = (filtered_data[filtered_data['Statut_budget'] == 'Approuvé']['Budget'].sum() / total_budget * 100) if total_budget > 0 else 0
            st.markdown(f"""
            <div class="kpi-card">
                <p class="kpi-value">{approval_rate:.1f}%</p>
                <p class="kpi-label">Taux d'Approbation</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Visualisations
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### Budget par Catégorie de Compte")
            category_data = filtered_data.groupby('catégorie_compte')['Budget'].sum().reset_index()
            fig = px.pie(category_data, values='Budget', names='catégorie_compte',
                         color_discrete_sequence=[POSTE_BLUE, LIGHT_BLUE, POSTE_GOLD, '#0288D1'])
            fig.update_layout(plot_bgcolor='white', paper_bgcolor='white', font_color=POSTE_BLUE, height=300, title_font_size=14)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("### Budget par Type de Service")
            service_data = filtered_data.groupby('Type_service')['Budget'].sum().reset_index()
            fig = px.bar(service_data, x='Type_service', y='Budget',
                         color_discrete_sequence=[POSTE_GOLD])
            fig.update_layout(plot_bgcolor='white', paper_bgcolor='white', font_color=POSTE_BLUE, height=300, title_font_size=14)
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("### Budget par Type de Client")
        if 'Type_client' in filtered_data.columns:
            client_data = filtered_data.groupby('Type_client')['Budget'].sum().reset_index()
            fig = px.pie(client_data, values='Budget', names='Type_client',
                         color_discrete_sequence=[POSTE_BLUE, LIGHT_BLUE, POSTE_GOLD, '#0288D1'],
                         title="Répartition du Budget par Type de Client")
            fig.update_layout(plot_bgcolor='white', paper_bgcolor='white', font_color=POSTE_BLUE, height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Données 'Type_client' non disponibles dans le dataset")
        
        st.markdown("### Tendance Budgétaire")
        trend_data = filtered_data.groupby('Date')['Budget'].sum().reset_index()
        fig = px.line(trend_data, x='Date', y='Budget',
                      color_discrete_sequence=[POSTE_BLUE])
        fig.update_layout(plot_bgcolor='white', paper_bgcolor='white', font_color=POSTE_BLUE, height=600, title_font_size=14)
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("""
        <div class="decorative-footer">
            <h3>La Poste Tunisienne - البريد التونسي</h3>
            <p style="font-size: 0.9rem;">Système d'Analyse Budgétaire Intelligent • © 2025</p>
        </div>
        """, unsafe_allow_html=True)

    # Page Assistant IA
    elif st.session_state.current_page == 'assistant':
        st.markdown(f"""
<div class="main-header">
    <div class="logo-container">
        {'<img src="data:image/png;base64,' + logo_base64 + '" class="logo-equal">' if logo_base64 else '<div style="font-size: 3rem; color: white;">📬</div>'}
        {'<img src="data:image/png;base64,' + tun_base64 + '" class="logo-equal">' if tun_base64 else ''}
    </div>
    <div class="welcome-text">Assistant Budgétaire Intelligent</div>
    <div class="subtitle">Analyses personnalisées et recommandations en temps réel</div>
</div>
""", unsafe_allow_html=True)
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown('<div class="chat-container">', unsafe_allow_html=True)
            if not st.session_state.chat_history:
                st.markdown(f"""
                <div class="chat-message-bot">
                    <strong> Assistant:</strong><br>
                    Bonjour! Hello!<br>
                    Je suis votre assistant IA pour optimiser la gestion budgétaire de La Poste Tunisienne.<br>
                    Posez vos questions (par ex., "Budget 2026 par région") pour des analyses détaillées.
                </div>
                """, unsafe_allow_html=True)
            
            for chat in st.session_state.chat_history:
                text_class = "rtl-text" if st.session_state.bot.detect_language(chat['user']) == 'arabic' else ""
                st.markdown(f"""
                <div class="chat-message-user {text_class}">
                    <strong> Vous ({chat['timestamp'].strftime('%H:%M')}):</strong><br>{chat['user']}
                </div>
                <div class="chat-message-bot {text_class}">
                    <strong>  Assistant:</strong><br>{chat['assistant']}
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            with st.form(key="chat_form"):
                user_input = st.text_input(
                    "Posez votre question :",
                    placeholder="Ex: Quel est le budget prévu pour 2026 dans la région Nord ?",
                    key="chat_input",
                    value=""
                )
                st.markdown('<div class="stButton">', unsafe_allow_html=True)
                submit_button = st.form_submit_button("Envoyer")
                st.markdown('</div>', unsafe_allow_html=True)
                
                if submit_button and user_input and user_input.strip():
                    if user_input == st.session_state.last_input:
                        st.warning("Question déjà posée. Veuillez poser une nouvelle question.")
                    else:
                        logging.info(f"User query: {user_input}")
                        result = st.session_state.bot.process_user_query(user_input)
                        response_text = result['response']
                        if st.session_state.bot.detect_language(user_input) == 'arabic':
                            response_text = "⚠️ Les réponses en arabe ne sont pas prises en charge. Voici la réponse en français :\n" + response_text
                        logging.info(f"Response: {response_text}")
                        st.session_state.chat_history.append({
                            'user': user_input,
                            'assistant': response_text,
                            'timestamp': datetime.now()
                        })
                        st.session_state.current_alerts = result['alerts']
                        st.session_state.current_suggestions = result['suggestions']
                        st.session_state.last_input = None  # Réinitialise l'input
                        st.rerun()
            
            # Suggestions interactives sous le bouton "Envoyer" comme boutons
            if st.session_state.current_suggestions:
                st.markdown("### Questions Suggérées")
                st.markdown('<div class="suggestion-container">', unsafe_allow_html=True)
                for suggestion in st.session_state.current_suggestions:
                    text_class = "rtl-text" if st.session_state.bot.detect_language(suggestion) == 'arabic' else ""
                    if st.button(suggestion, key=f"suggestion_{hash(suggestion)}", use_container_width=True, help=suggestion):
                        logging.info(f"Suggestion query: {suggestion}")
                        result = st.session_state.bot.process_user_query(suggestion)
                        st.session_state.chat_history.append({
                            'user': suggestion,
                            'assistant': result['response'],
                            'timestamp': datetime.now()
                        })
                        st.session_state.current_alerts = result['alerts']
                        st.session_state.current_suggestions = result['suggestions']
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown("### ⚙️ Paramètres")
            st.markdown(f"""
            <div style="background: white; padding: 1rem; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <p><strong>Messages:</strong> {len(st.session_state.chat_history)}</p>
                <p><strong>Alertes:</strong> {len(st.session_state.current_alerts)}</p>
                <p><strong>Suggestions:</strong> {len(st.session_state.current_suggestions)}</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("Réinitialiser la conversation", use_container_width=True):
                st.session_state.chat_history = []
                st.session_state.current_alerts = []
                st.session_state.current_suggestions = []
                st.session_state.last_input = None
                logging.info("Conversation reset by user")
                st.rerun()
            
            if st.button("Voir le Résumé de la Conversation", use_container_width=True):
                summary = st.session_state.bot.get_conversation_summary()
                st.markdown(f"<div class='report-box'>{summary}</div>", unsafe_allow_html=True)
            
            if st.button("Exporter la Conversation", use_container_width=True):
                conversation_df = pd.DataFrame([
                    {'Question': chat['user'], 'Réponse': chat['assistant'], 'Date': chat['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}
                    for chat in st.session_state.chat_history
                ])
                if not conversation_df.empty:
                    csv = conversation_df.to_csv(index=False)
                    st.download_button(
                        "Télécharger CSV",
                        csv,
                        "conversation.csv",
                        "text/csv",
                        use_container_width=True
                    )
                    logging.info("Conversation exported to CSV")
                else:
                    st.warning("Aucune conversation à exporter.")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 🚨 Alertes Actives")
            if st.session_state.current_alerts:
                for alert in st.session_state.current_alerts:
                    text_class = "rtl-text" if st.session_state.bot.detect_language(alert) == 'arabic' else ""
                    st.markdown(f"""
                    <div class="alert-box {text_class}">
                        <p>{alert}</p>
                        <p style="font-size: 0.8rem; color: #555;">{datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown('<div class="alert-box"><p>Aucune alerte pour le moment.</p></div>', unsafe_allow_html=True)

        st.markdown("""
        <div class="decorative-footer">
            <h3>La Poste Tunisienne - البريد التونسي</h3>
            <p style="font-size: 0.9rem;">Système d'Analyse Budgétaire Intelligent • © 2025</p>
        </div>
        """, unsafe_allow_html=True)

    # Page Rapports
    elif st.session_state.current_page == 'reports':
        st.markdown(f"""
<div class="main-header">
    <div class="logo-container">
        {'<img src="data:image/png;base64,' + logo_base64 + '" class="logo-equal">' if logo_base64 else '<div style="font-size: 3rem; color: white;">📬</div>'}
        {'<img src="data:image/png;base64,' + tun_base64 + '" class="logo-equal">' if tun_base64 else ''}
    </div>
    <div class="welcome-text">Rapports Budgétaires</div>
    <div class="subtitle">Générez des analyses détaillées en PDF</div>
</div>
""", unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="report-box">
            <h3 style="color: {POSTE_BLUE}; font-weight: bold; text-align: center; margin-bottom: 1.5rem; border-bottom: 2px solid {POSTE_GOLD}; padding-bottom: 0.5rem;">
                Génération de Rapport Budgétaire
            </h3>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**Date de début**")
            start_date = st.date_input(
                "Date de début",
                value=datetime(2025, 1, 1),
                min_value=datetime(2018, 1, 1),
                max_value=datetime(2027, 12, 31),
                key="start_date_report",
                label_visibility="collapsed"
            )
        
        with col2:
            st.markdown("**Date de fin**")
            end_date = st.date_input(
                "Date de fin",
                value=datetime(2025, 12, 31),
                min_value=datetime(2018, 1, 1),
                max_value=datetime(2027, 12, 31),
                key="end_date_report",
                label_visibility="collapsed"
            )
        
        with col3:
            st.markdown("**Régions**")
            selected_entities_report = st.multiselect(
                "Sélectionner les régions",
                st.session_state.bot.df['Entité'].unique(),
                default=list(st.session_state.bot.df['Entité'].unique()[:5]),
                key="entities_report",
                label_visibility="collapsed"
            )

        if st.button("Générer et Télécharger PDF", use_container_width=True):
            start_date_str = start_date.strftime("%Y-%m-%d")
            end_date_str = end_date.strftime("%Y-%m-%d")
            filename = st.session_state.bot.generate_pdf_report(start_date_str, end_date_str, entities=selected_entities_report)
            if filename:
                with open(filename, "rb") as f:
                    st.download_button(
                        "Télécharger le Rapport PDF",
                        data=f,
                        file_name=filename,
                        mime="application/pdf",
                        use_container_width=True
                    )
                logging.info(f"PDF report generated: {filename}")
            else:
                st.error("Échec de la génération du rapport PDF.")
                logging.error("Failed to generate PDF report")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("""
        <div class="decorative-footer">
            <h3>La Poste Tunisienne - البريد التونسي</h3>
            <p style="font-size: 0.9rem;">Système d'Analyse Budgétaire Intelligent • © 2025</p>
        </div>
        """, unsafe_allow_html=True)

elif st.session_state["authentication_status"] is False:
    st.error("Nom d'utilisateur ou mot de passe incorrect.")

elif st.session_state["authentication_status"] is None:
    st.warning("Veuillez entrer vos identifiants.")