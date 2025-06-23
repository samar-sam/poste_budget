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

# CSS optimisé
CSS_STYLES = f"""
<style>
    .main-header {{
        background: linear-gradient(135deg, {POSTE_BLUE} 0%, {LIGHT_BLUE} 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.15);
    }}
    .welcome-text {{
        color: white;
        font-size: 2.8rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 1rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }}
    .subtitle {{
        color: {POSTE_GOLD};
        font-size: 1.3rem;
        text-align: center;
        margin-bottom: 0;
        font-weight: 500;
    }}
    .logo-container {{
        text-align: center;
        margin-bottom: 1.5rem;
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 1rem;
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
        margin-top: 1rem;
        box-shadow: 0 3px 6px rgba(0,0,0,0.1);
    }}
    .stButton > button {{
        background: linear-gradient(135deg, {POSTE_BLUE} 0%, {LIGHT_BLUE} 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.7rem 1.5rem !important;
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
        background: linear-gradient(135deg, #e8f4fd 0%, #cce7ff 100%) !important;
        color: {POSTE_BLUE} !important;
        border: 1px solid {LIGHT_BLUE} !important;
        border-radius: 8px !important;
        padding: 0.5rem 1rem !important;
        font-size: 0.9rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05) !important;
    }}
    .suggestion-button > button:hover {{
        background: linear-gradient(135deg, {LIGHT_BLUE} 0%, {POSTE_GOLD} 100%) !important;
        color: white !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1) !important;
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
    }}
    .stTextInput > div > div > input:focus {{
        border-color: {POSTE_GOLD} !important;
        box-shadow: 0 0 0 2px rgba(255, 184, 28, 0.2) !important;
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
    .decorative-footer {{
        background: linear-gradient(135deg, {POSTE_BLUE} 0%, {LIGHT_BLUE} 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-top: 2rem;
        text-align: center;
        color: white;
        animation: pulse 3s infinite;
    }}
    @keyframes pulse {{
        0% {{ transform: scale(1); }}
        50% {{ transform: scale(1.02); }}
        100% {{ transform: scale(1); }}
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
    .auth-container {{
        background: linear-gradient(135deg, {POSTE_BLUE} 0%, {LIGHT_BLUE} 100%);
        padding: 2rem;
        border-radius: 15px;
        margin: 2rem auto;
        max-width: 400px;
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.15);
        text-align: center;
    }}
    .auth-title {{
        color: white;
        font-size: 2rem;
        font-weight: bold;
        margin-bottom: 1rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }}
    .auth-subtitle {{
        color: {POSTE_GOLD};
        font-size: 1rem;
        margin-bottom: 1.5rem;
        font-weight: 500;
    }}
    .auth-input {{
        border-radius: 10px !important;
        border: 2px solid {POSTE_BLUE} !important;
        padding: 0.7rem !important;
        margin-bottom: 1rem !important;
        width: 100% !important;
    }}
    .auth-input:focus {{
        border-color: {POSTE_GOLD} !important;
        box-shadow: 0 0 0 2px rgba(255, 184, 28, 0.2) !important;
    }}
</style>
"""
st.markdown(CSS_STYLES, unsafe_allow_html=True)

# Gestion de la connexion
authenticator.login("main")

if st.session_state["authentication_status"]:
    st.success(f"Bienvenue {st.session_state['name']} 👋")
    st.sidebar.title(f"Utilisateur : {st.session_state['username']}")
    authenticator.logout("Se déconnecter", "sidebar")

    # Initialisation du bot
    with st.spinner("🔄 Chargement du chatbot..."):
        if 'bot' not in st.session_state:
            st.session_state.bot = initialize_bot()

    # Sidebar
    with st.sidebar:
        st.markdown("""
        <div class="sidebar-logo">
            <img src="assets/logo.png" style="width: 80px; height: auto; margin-bottom: 0.5rem;">
            <img src="assets/tun.png" style="width: 60px; height: 40px;">
            <h2 style="color: white; margin: 0.2rem 0; font-size: 1.3rem;">La Poste</h2>
            <h3 style="color: #ffb81c; margin: 0; font-size: 1.1rem;">Tunisienne</h3>
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
            <div style="color: white; font-size: 0.85rem;">
                <p><strong>Période:</strong> {stats['date_range']['start']} - {stats['date_range']['end']}</p>
                <p><strong>Entités:</strong> {stats['entities']} régions</p>
                <p><strong>Budget:</strong> {stats['total_budget']/1e9:.2f}B TND</p>
                <p><strong>IA:</strong> Groq LLaMA</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

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
        st.markdown("""
        <div class="main-header">
            <div class="logo-container">
                <img src="assets/logo.png" style="width: 100px; height: auto;">
                <img src="assets/tun.png" style="width: 80px; height: 50px;">
            </div>
            <div class="welcome-text">Bienvenue à La Poste Tunisienne</div>
            <div class="subtitle">Votre Solution Budgétaire Intelligente</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### Accès Rapide")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Tableau de Bord", key="quick_dashboard", use_container_width=True):
                st.session_state.current_page = "dashboard"
                st.rerun()
        with col2:
            if st.button("Assistant IA", key="quick_assistant", use_container_width=True):
                st.session_state.current_page = "assistant"
                st.rerun()
        with col3:
            if st.button("Workflow SAP", key="quick_sap", use_container_width=True):
                st.success("Redirection vers SAP Analytics Cloud")
        
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
        
        st.markdown("""
        <div class="decorative-footer">
            <h3>Optimisez Votre Gestion Budgétaire</h3>
            <p style="font-size: 1rem; margin: 0.5rem 0;">Des analyses puissantes et des insights en temps réel</p>
            <div style="display: flex; justify-content: center; gap: 1rem; margin-top: 1rem;">
                <span style="font-size: 2rem;">📈</span>
                <span style="font-size: 2rm;">🔍</span>
                <span style="font-size: 2rem;">💼</span>
            </div>
            <p style="font-size: 0.9rem; color: #ffb81c; margin-top: 1rem;">
                Propulsé par IA • © 2025 La Poste Tunisienne
            </p>
        </div>
        """, unsafe_allow_html=True)

    # Page Dashboard
    elif st.session_state.current_page == 'dashboard':
        st.markdown("""
        <div class="main-header">
            <div class="logo-container">
                <img src="assets/logo.png" style="width: 100px; height: auto;">
                <img src="assets/tun.png" style="width: 80px; height: 50px;">
            </div>
            <div class="welcome-text">Tableau de Bord Budgétaire</div>
            <div class="subtitle">Insights pour une gestion financière optimisée</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Filtres interactifs
        st.markdown("### Filtres de Données")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            selected_years = st.multiselect("Années", sorted(st.session_state.bot.df['Année'].unique()), default=sorted(st.session_state.bot.df['Année'].unique()))
        with col2:
            selected_entities = st.multiselect("Régions", st.session_state.bot.df['Entité'].unique(), default=st.session_state.bot.df['Entité'].unique())
        with col3:
            selected_categories = st.multiselect("Catégories de compte", st.session_state.bot.df['catégorie_compte'].unique(), default=st.session_state.bot.df['catégorie_compte'].unique())
        with col4:
            selected_services = st.multiselect(
                "Types de service",
                st.session_state.bot.df['Type_service'].unique() if 'Type_service' in st.session_state.bot.df.columns else [],
                default=st.session_state.bot.df['Type_service'].unique() if 'Type_service' in st.session_state.bot.df.columns else []
            )
        
        filtered_data = st.session_state.bot.df[
            (st.session_state.bot.df['Année'].isin(selected_years)) &
            (st.session_state.bot.df['Entité'].isin(selected_entities)) &
            (st.session_state.bot.df['catégorie_compte'].isin(selected_categories))
        ]
        if 'Type_service' in st.session_state.bot.df.columns and selected_services:
            filtered_data = filtered_data[filtered_data['Type_service'].isin(selected_services)]
        
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
            fig.update_layout(plot_bgcolor='white', paper_bgcolor='white', font_color=POSTE_BLUE)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("### Budget par Entité")
            entity_data = filtered_data.groupby('Entité')['Budget'].sum().reset_index()
            fig = px.bar(entity_data, x='Entité', y='Budget',
                         color_discrete_sequence=[POSTE_GOLD])
            fig.update_layout(plot_bgcolor='white', paper_bgcolor='white', font_color=POSTE_BLUE)
            st.plotly_chart(fig, use_container_width=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### Tendance Budgétaire")
            trend_data = filtered_data.groupby('Date')['Budget'].sum().reset_index()
            fig = px.line(trend_data, x='Date', y='Budget',
                          color_discrete_sequence=[POSTE_BLUE])
            fig.update_layout(plot_bgcolor='white', paper_bgcolor='white', font_color=POSTE_BLUE)
            st.plotly_chart(fig, use_container_width=True)

    # Page Assistant IA
    elif st.session_state.current_page == 'assistant':
        st.markdown("""
        <div class="main-header">
            <div class="logo-container">
                <img src="assets/logo.png" style="width: 100px; height: auto;">
                <img src="assets/tun.png" style="width: 80px; height: 50px;">
            </div>
            <div class="welcome-text">Assistant Budgétaire Intelligent</div>
            <div class="subtitle">Analyses personnalisées et recommandations en temps réel</div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown("### 💬 Interagir avec l'Assistant")
            st.markdown('<div class="chat-container">', unsafe_allow_html=True)
            if not st.session_state.chat_history:
                st.markdown(f"""
                <div class="chat-message-bot">
                    <strong>🤖 Assistant:</strong><br>
                    Bonjour! Hello!<br>
                    Je suis votre assistant IA pour optimiser la gestion budgétaire de La Poste Tunisienne.<br>
                    Posez vos questions (par ex., "Budget 2026 par région") pour des analyses détaillées.
                </div>
                """, unsafe_allow_html=True)
            
            for chat in st.session_state.chat_history:
                text_class = "rtl-text" if st.session_state.bot.detect_language(chat['user']) == 'arabic' else ""
                st.markdown(f"""
                <div class="chat-message-user {text_class}">
                    <strong>👤 Vous ({chat['timestamp'].strftime('%H:%M')}):</strong><br>{chat['user']}
                </div>
                <div class="chat-message-bot {text_class}">
                    <strong>🤖 Assistant:</strong><br>{chat['assistant']}
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            with st.form(key="chat_form"):
                user_input = st.text_input(
                    "Posez votre question :",
                    placeholder="Ex: Quel est le budget prévu pour 2026 dans la région Nord ?",
                    key="chat_input"
                )
                submit_button = st.form_submit_button("Envoyer")
                
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
                        st.session_state.last_input = user_input
                        # Gestion des suggestions de reformulation
                        if "Suggestions :" in response_text:
                            suggestions = response_text.split("Suggestions :")[-1].split("|")
                            st.markdown("### Suggestions de Reformulation")
                            for suggestion in suggestions:
                                suggestion_clean = suggestion.strip()
                                if suggestion_clean and st.button(suggestion_clean, key=f"rephrase_{hash(suggestion_clean)}"):
                                    logging.info(f"Rephrased query: {suggestion_clean}")
                                    rephrase_result = st.session_state.bot.process_user_query(suggestion_clean)
                                    st.session_state.chat_history.append({
                                        'user': suggestion_clean,
                                        'assistant': rephrase_result['response'],
                                        'timestamp': datetime.now()
                                    })
                                    st.session_state.current_alerts = rephrase_result['alerts']
                                    st.session_state.current_suggestions = rephrase_result['suggestions']
                                    st.rerun()
                        st.rerun()
            
            # Suggestions interactives sous le bouton "Envoyer"
            if st.session_state.current_suggestions:
                st.markdown("### Questions Suggérées")
                for suggestion in st.session_state.current_suggestions:
                    text_class = "rtl-text" if st.session_state.bot.detect_language(suggestion) == 'arabic' else ""
                    st.markdown(f"<div class='suggestion-box {text_class}'><p style='margin: 0; font-size: 0.9rem;'>{suggestion}</p></div>", unsafe_allow_html=True)
                    if st.button(f"Poser cette question", key=f"suggestion_{hash(suggestion)}", use_container_width=True, help=suggestion):
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

    # Page Rapports
    elif st.session_state.current_page == 'reports':
        st.markdown("""
        <div class="main-header">
            <div class="logo-container">
                <img src="assets/logo.png" style="width: 100px; height: auto;">
                <img src="assets/tun.png" style="width: 80px; height: 50px;">
            </div>
            <div class="welcome-text">Rapports Budgétaires</div>
            <div class="subtitle">Générez des analyses détaillées en PDF</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### 📄 Générer un Rapport Personnalisé")
        with st.container():
            st.markdown('<div class="report-box">', unsafe_allow_html=True)
            st.markdown("**Créer un rapport budgétaire détaillé**")
            col1, col2, col3 = st.columns(3)
            with col1:
                start_year = st.selectbox("Année de début", range(2018, 2028), index=0)
                start_month = st.selectbox("Mois de début", range(1, 13), format_func=lambda x: datetime(2025, x, 1).strftime('%B'))
            with col2:
                end_year = st.selectbox("Année de fin", range(2018, 2028), index=9)
                end_month = st.selectbox("Mois de fin", range(1, 13), format_func=lambda x: datetime(2025, x, 1).strftime('%B'))
            with col3:
                selected_entities = st.multiselect("Régions", st.session_state.bot.df['Entité'].unique(), default=st.session_state.bot.df['Entité'].unique())
                selected_categories = st.multiselect("Catégories de compte", st.session_state.bot.df['catégorie_compte'].unique(), default=st.session_state.bot.df['catégorie_compte'].unique())
            
            if st.button("Générer et Télécharger PDF", use_container_width=True):
                start_date = f"{start_year}-{start_month:02d}-01"
                end_date = f"{end_year}-{end_month:02d}-31"
                filename = st.session_state.bot.generate_pdf_report(start_date, end_date, entities=selected_entities, categories=selected_categories)
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

    # Footer
    st.markdown("""
    <div class="decorative-footer">
        <div style="display: flex; justify-content: center; gap: 1rem;">
            <img src="assets/logo.png" style="width: 80px; height: auto;">
            <img src="assets/tun.png" style="width: 60px; height: 40px;">
        </div>
        <h3>La Poste Tunisienne</h3>
        <p style="font-size: 0.9rem;">Système d'Analyse Budgétaire Intelligent • © 2025</p>
    </div>
    """, unsafe_allow_html=True)

elif st.session_state["authentication_status"] is False:
    st.error("Nom d'utilisateur ou mot de passe incorrect.")

elif st.session_state["authentication_status"] is None:
    st.warning("Veuillez entrer vos identifiants.")