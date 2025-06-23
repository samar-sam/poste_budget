import pandas as pd
import numpy as np
import re
from groq import Groq
from datetime import datetime, timedelta
from langdetect import detect, DetectorFactory
import json
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import io
import base64

# Fixer la graine pour des résultats reproductibles avec langdetect
DetectorFactory.seed = 0

class PosteTunisienneBot:
    def __init__(self):
        self.df = None
        self.groq_client = None
        self.conversation_history = []
        self.data_insights = {}
        self.load_data()
        self.setup_groq_client()
        self.analyze_data_insights()
    
    def load_data(self):
        """Charge les données depuis le fichier CSV avec validation complète"""
        try:
            # Charger le dataset depuis le chemin spécifié
            self.df = pd.read_csv("C:\\Users\\samar.abassi\\Downloads\\PosteBudget.csv")
            
            # Conversion et nettoyage des dates
            self.df['Date'] = pd.to_datetime(self.df['Date'], errors='coerce')
            
            # Validation des colonnes essentielles
            required_columns = ['Date', 'Entité', 'Budget', 'is_forecast']
            missing_columns = [col for col in required_columns if col not in self.df.columns]
            if missing_columns:
                raise ValueError(f"Colonnes manquantes: {missing_columns}")
            
            # Nettoyage des données
            self.df = self.df.dropna(subset=['Date', 'Budget'])
            self.df['Budget'] = pd.to_numeric(self.df['Budget'], errors='coerce')
            self.df = self.df.dropna(subset=['Budget'])
            
            # Ajout de colonnes pour l'analyse (Année, Mois, etc.)
            self.df['Année'] = self.df['Date'].dt.year
            self.df['Mois'] = self.df['Date'].dt.month
            
            # Définir des colonnes saisonnières si elles n'existent pas
            if 'Ramadan' not in self.df.columns:
                self.df['Ramadan'] = 0  # À remplir selon les données réelles
            if 'Décembre' not in self.df.columns:
                self.df['Décembre'] = (self.df['Mois'] == 12).astype(int)
            if 'Septembre' not in self.df.columns:
                self.df['Septembre'] = (self.df['Mois'] == 9).astype(int)
            if 'catégorie_compte' not in self.df.columns:
                self.df['catégorie_compte'] = 'REVENUE'  # Par défaut
            if 'Centre_de_profit' not in self.df.columns:
                self.df['Centre_de_profit'] = self.df['Entité']  # Approximation
            if 'Statut_budget' not in self.df.columns:
                self.df['Statut_budget'] = 'Approuvé'  # Par défaut
            
            # Séparation historique/prévisions
            self.historical_data = self.df[self.df['is_forecast'] == 0].copy()
            self.forecast_data = self.df[self.df['is_forecast'] == 1].copy()
            
            print(f"✅ Données chargées: {len(self.df)} lignes")
            print(f"📊 Historique: {len(self.historical_data)} lignes")
            print(f"🔮 Prévisions: {len(self.forecast_data)} lignes")
            
        except FileNotFoundError:
            print("❌ Fichier PosteBudget.csv non trouvé")
            self.df = pd.DataFrame()
        except Exception as e:
            print(f"❌ Erreur de chargement: {str(e)}")
            self.df = pd.DataFrame()
    
    def setup_groq_client(self):
        """Configure le client Groq avec la clé API"""
        api_key = "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"
        try:
            if api_key and api_key != "votre_cle_api_groq_ici":
                self.groq_client = Groq(api_key=api_key)
                print("✅ Client Groq configuré")
            else:
                print("⚠️ Clé API Groq non configurée")
        except Exception as e:
            print(f"❌ Erreur configuration Groq: {str(e)}")
    
    def analyze_data_insights(self):
        """Analyse les données pour générer des insights automatiques"""
        if self.df is None or self.df.empty:
            return
        
        try:
            # Calculs statistiques généraux
            self.data_insights = {
                'total_budget': self.df['Budget'].sum(),
                'avg_budget': self.df['Budget'].mean(),
                'budget_by_entity': self.df.groupby('Entité')['Budget'].sum().to_dict(),
                'budget_by_year': self.df.groupby('Année')['Budget'].sum().to_dict(),
                'budget_by_month_year': self.df.groupby(['Année', 'Mois'])['Budget'].sum().to_dict(),
                'budget_by_category': self.df.groupby('catégorie_compte')['Budget'].sum().to_dict(),
                'ramadan_impact': self.df[self.df['Ramadan'] == 1]['Budget'].mean() - self.df[self.df['Ramadan'] == 0]['Budget'].mean(),
                'december_impact': self.df[self.df['Décembre'] == 1]['Budget'].mean() - self.df[self.df['Décembre'] == 0]['Budget'].mean(),
                'top_profit_centers': self.df.groupby('Centre_de_profit')['Budget'].sum().nlargest(5).to_dict(),
                'budget_trends': self.calculate_trends()
            }
            print("✅ Insights des données calculés")
        except Exception as e:
            print(f"❌ Erreur calcul insights: {str(e)}")
            self.data_insights = {}
    
    def calculate_trends(self):
        """Calcule les tendances budgétaires"""
        try:
            monthly_trends = self.df.groupby(['Année', 'Mois'])['Budget'].sum().reset_index()
            monthly_trends['Date_trend'] = pd.to_datetime(monthly_trends[['Année', 'Mois']].assign(day=1))
            monthly_trends = monthly_trends.sort_values('Date_trend')
            
            # Calcul de la croissance mensuelle
            monthly_trends['Growth'] = monthly_trends['Budget'].pct_change() * 100
            
            return {
                'monthly_data': monthly_trends.to_dict('records'),
                'avg_growth': monthly_trends['Growth'].mean(),
                'volatility': monthly_trends['Growth'].std()
            }
        except:
            return {}
    
    def detect_language(self, text):
        """Détecte la langue du texte avec langdetect"""
        try:
            lang = detect(text)
            if lang == 'ar':
                return 'arabic'
            elif lang == 'fr':
                return 'french'
            elif lang == 'en':
                return 'english'
            return 'french'  # Par défaut
        except:
            return 'french'
    
    def get_relevant_data_context(self, message):
        """Extrait le contexte pertinent des données basé sur la question"""
        if self.df is None or self.df.empty:
            return ""
        
        context = ""
        message_lower = message.lower()
        
        # Contexte sur les entités (régions)
        if any(entity.lower() in message_lower for entity in ['centre', 'nord', 'sud', 'région', 'entity', 'entité']):
            entity_summary = self.df.groupby('Entité')['Budget'].agg(['sum', 'mean', 'count']).to_string()
            context += f"\nRésumé par entité régionale:\n{entity_summary}\n"
        
        # Contexte sur les années ou mois
        if any(year in message_lower for year in ['2018', '2019', '2020', '2021', '2022', '2023', '2024', '2025', '2026', '2027']) or \
           any(month in message_lower for month in ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre']):
            year_month_summary = self.df.groupby(['Année', 'Mois'])['Budget'].agg(['sum', 'mean']).to_string()
            context += f"\nRésumé par année et mois:\n{year_month_summary}\n"
        
        # Contexte sur les catégories de compte (synonymes inclus)
        if any(cat.lower() in message_lower for cat in ['revenue', 'capex', 'opex', 'catégorie', 'type de compte', 'nom de compte', 'catégorie de compte', 'compte budgétaire']):
            category_summary = self.df.groupby('catégorie_compte')['Budget'].sum().to_string()
            context += f"\nRésumé par catégorie de compte budgétaire:\n{category_summary}\n"
        
        # Contexte sur les centres de profit
        if any(word.lower() in message_lower for word in ['logistique', 'colis', 'services', 'courrier', 'profit', 'centre de profit']):
            profit_summary = self.df.groupby('Centre_de_profit')['Budget'].sum().to_string()
            context += f"\nRésumé par centre de profit:\n{profit_summary}\n"
        
        # Contexte sur les centres de coût
        if any(word.lower() in message_lower for word in ['commercial', 'administration', 'tech', 'centre de coût', 'coût']):
            cost_summary = self.df.groupby('Centre_de_coût')['Budget'].sum().to_string()
            context += f"\nRésumé par centre de coût:\n{cost_summary}\n"
        
        # Contexte sur les départements
        if any(word.lower() in message_lower for word in ['opérations', 'finance', 'département']):
            dept_summary = self.df.groupby('Département')['Budget'].sum().to_string()
            context += f"\nRésumé par département:\n{dept_summary}\n"
        
        # Contexte sur les segments clients
        if any(segment.lower() in message_lower for segment in ['particuliers', 'institutions', 'entreprises', 'client', 'segment']):
            segment_summary = self.df.groupby('Segment_client')['Budget'].sum().to_string()
            context += f"\nRésumé par segment client:\n{segment_summary}\n"
        
        # Contexte sur les types de service
        if any(service.lower() in message_lower for service in ['express', 'international', 'standard', 'service', 'type de service']):
            service_summary = self.df.groupby('Type_service')['Budget'].sum().to_string()
            context += f"\nRésumé par type de service:\n{service_summary}\n"
        
        # Contexte sur les prévisions vs historique
        if any(word.lower() in message_lower for word in ['prévision', 'forecast', 'futur', 'prédiction']):
            forecast_summary = self.df.groupby('is_forecast')['Budget'].agg(['sum', 'mean', 'count']).to_string()
            context += f"\nRépartition entre données historiques et prévisions:\n{forecast_summary}\n"
        
        # Contexte sur Ramadan
        if 'ramadan' in message_lower:
            ramadan_summary = self.df.groupby('Ramadan')['Budget'].agg(['sum', 'mean']).to_string()
            context += f"\nImpact de Ramadan:\n{ramadan_summary}\n"
        
        # Contexte sur Décembre
        if 'décembre' in message_lower or 'decembre' in message_lower:
            december_summary = self.df.groupby('Décembre')['Budget'].agg(['sum', 'mean']).to_string()
            context += f"\nImpact de Décembre:\n{december_summary}\n"
        
        # Contexte sur Septembre
        if 'septembre' in message_lower:
            september_summary = self.df.groupby('Septembre')['Budget'].agg(['sum', 'mean']).to_string()
            context += f"\nImpact de Septembre:\n{september_summary}\n"
        
        # Contexte général si pas de mots-clés spécifiques
        if not context:
            recent_data = self.df.tail(10)[['Date', 'Entité', 'Budget', 'catégorie_compte', 'Type_service', 'Segment_client']].to_string()
            context += f"\nAperçu des dernières entrées:\n{recent_data}\n"
            
            # Statistiques générales
            stats = f"""
            Budget total: {self.data_insights.get('total_budget', 0):,.0f} TND
            Budget moyen: {self.data_insights.get('avg_budget', 0):,.0f} TND
            Nombre d'enregistrements: {len(self.df)}
            Période: {self.df['Date'].min().strftime('%Y-%m-%d')} à {self.df['Date'].max().strftime('%Y-%m-%d')}
            Répartition par catégorie de compte: {dict(self.df.groupby('catégorie_compte')['Budget'].sum())}
            """
            context += stats
        
        return context
    
    def chat_with_groq(self, message):
        """Gère les interactions avec l'IA Groq pour fournir des réponses détaillées et contextuelles"""
        if not self.groq_client:
            return "❌ Le service d'intelligence artificielle n'est pas configuré. Veuillez vérifier votre clé API."

        try:
            detected_lang = self.detect_language(message)
            
            # Gérer les salutations simples pour une expérience fluide
            if self.is_simple_greeting(message):
                return self.get_greeting_response(detected_lang)
            
            # Récupérer le contexte pertinent basé sur la question
            data_context = self.get_relevant_data_context(message)
            
            # Préparer l'historique de conversation pour maintenir la continuité
            conversation_context = ""
            if self.conversation_history:
                recent_conversation = self.conversation_history[-5:]  # 5 derniers échanges pour plus de contexte
                conversation_context = "\nHistorique récent:\n"
                for item in recent_conversation:
                    conversation_context += f"Question: {item['question']}\nRéponse: {item['response'][:250]}...\n"

            # Générer un prompt système adapté
            system_prompt = self.get_system_prompt(detected_lang, data_context, conversation_context)
            
            # Appel à l'API Groq avec des paramètres optimisés
            response = self.groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                model="llama3-8b-8192",
                temperature=0.25,  # Réduit pour une cohérence accrue
                max_tokens=2000    # Augmenté pour des réponses plus détaillées
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Enregistrer l'interaction dans l'historique
            self.conversation_history.append({
                'timestamp': datetime.now(),
                'question': message,
                'response': response_text,
                'language': detected_lang
            })
            
            # Limiter l'historique à 25 échanges pour une gestion mémoire efficace
            if len(self.conversation_history) > 25:
                self.conversation_history = self.conversation_history[-25:]
            
            return response_text
            
        except Exception as e:
            return f"❌ Une erreur est survenue lors de la communication avec le service d'IA: {str(e)}. Veuillez réessayer plus tard."
    
    def is_simple_greeting(self, message):
        """Identifie les salutations simples pour une réponse immédiate"""
        greetings = ['bonjour', 'bonsoir', 'salut', 'hello', 'hi', 'مرحبًا', 'سلام', 'bon journée', 'good morning']
        message_clean = re.sub(r'[^\w\s]', '', message.lower().strip())
        return message_clean in greetings or (len(message_clean.split()) <= 3 and any(g in message_clean for g in greetings))
    
    def get_greeting_response(self, lang):
        """Fournit une salutation chaleureuse et professionnelle avec une invitation à interagir"""
        responses = {
            'french': "Bonjour ! Je suis votre assistant dédié à La Poste Tunisienne, ici pour vous accompagner dans l’analyse de vos données budgétaires ou répondre à vos questions. Que souhaitez-vous explorer aujourd’hui ?",
            'english': "Hello! I’m your dedicated assistant for Tunisia Post, ready to assist with budget analysis or any other questions you may have. What would you like to discuss today?",
            'arabic': "مرحبًا! أنا مساعدك المخصص للبريد التونسي، جاهز لمساعدتك في تحليل البيانات المالية أو الإجابة عن أي استفسار. ما الذي تريد مناقشته اليوم؟"
        }
        return responses.get(lang, responses['french'])
    
    def get_system_prompt(self, lang, data_context, conversation_context):
        """Crée un prompt système détaillé et contextuel pour guider les réponses de l'IA"""
        prompts = {
            'french': f"""Tu es un assistant IA avancé, spécialisé dans l’analyse des données financières et opérationnelles de La Poste Tunisienne, tout en étant capable de répondre à des questions générales avec aisance et pertinence.

**Contexte des données disponibles:**
{data_context}

**Historique de la conversation:**
{conversation_context}

**Contexte métier:**
- La Poste Tunisienne opère à travers trois entités régionales: Centre, Nord et Sud.
- Les services postaux incluent: Express, International et Standard.
- Les segments de clientèle sont: Particuliers, Institutions et Entreprises.
- Les centres de profit sont: Logistique, Colis, Services et Courrier.
- Les centres de coût incluent: Commercial, Administration, Logistique et Tech.
- Les catégories de compte budgétaire (aussi appelées types ou noms de compte budgétaire) sont: Revenus (Revenue), Dépenses d’investissement (CAPEX) et Dépenses opérationnelles (OPEX).
- Les départements opérationnels incluent: Opérations, Logistique, Commercial et Finance.
- Les périodes saisonnières clés influençant les budgets sont: Ramadan (période de jeûne musulman, généralement entre mars et mai selon le calendrier lunaire), Décembre (fêtes de fin d’année et réveillon) et Septembre (rentrée et cycles opérationnels).
- La devise utilisée est le Dinar Tunisien (TND).
- Les données incluent: historiques de janvier 2018 à mars 2025, et prévisions d’avril 2025 à décembre 2027.

**Instructions:**
- Avant de répondre, prends le temps de réfléchir à la question pour t’assurer que la réponse est précise, pertinente et contextuellement correcte.
- Identifie les synonymes ou variations dans les termes (par exemple, "types de compte budgétaire", "noms de compte budgétaire" ou "catégories de compte budgétaire" désignent tous la colonne 'account_category') pour mieux comprendre les questions.
- Réponds à toutes les questions, qu’elles soient liées aux données ou à des sujets généraux.
- Pour les questions sur les données: fournis des réponses précises basées sur les chiffres exacts, avec une structure claire (introduction, détails, conclusion) et des insights pertinents (tendances, comparaisons, impacts saisonniers). Inclut les estimations pour 2025, 2026 et 2027, ainsi que les budgets mensuels si demandés (ex.: "budget pour mars 2024" ou "budget de mai 2022").
- Pour les questions générales: offre des réponses détaillées, naturelles et engageantes, sans référence aux données sauf si demandé, avec un ton amical et professionnel adapté au contexte tunisien.
- Évite des expressions comme "En examinant les données", "selon mes données" ou "selon la dataset". Structure directement les réponses avec des faits ou des analyses claires.
- Si le budget demandé concerne une période de prévision (ex.: 2025-2027 ou un mois après mars 2025), indique qu’il s’agit d’une estimation sans préciser la période couverte par les données.
- Assure-toi que les réponses sont correctes, notamment pour les événements saisonniers (ex.: Décembre est lié aux fêtes de fin d’année et au réveillon, pas à Ramadan ou Aïd el-Kebir, qui se produisent à d’autres périodes).
- Utilise des exemples concrets ou des anecdotes pour enrichir les réponses générales.
- Structure les réponses avec des sections marquées par des titres (ex.: **Résumé**, **Analyse**, **Recommandation**) pour une meilleure lisibilité.
- Adapte ton langage au public tunisien, en restant formel mais accessible, et privilégie des formulations positives.

**Période couverte:**
- Historique: janvier 2018 à mars 2025 (données réelles).
- Prévisions: avril 2025 à décembre 2027 (estimations).""",
            
            'english': f"""You are an advanced AI assistant specialized in analyzing financial and operational data for Tunisia Post, while also being capable of providing insightful and relevant responses to general questions.

**Available Data Context:**
{data_context}

**Conversation History:**
{conversation_context}

**Business Context:**
- Tunisia Post operates through three regional entities: Centre, North, and South.
- Postal services include: Express, International, and Standard.
- Client segments are: Individuals, Institutions, and Enterprises.
- Profit centers are: Logistics, Parcels, Services, and Mail.
- Cost centers include: Commercial, Administration, Logistics, and Tech.
- Budget account categories (also referred to as types or names of budget accounts) are: Revenue, Capital Expenditures (CAPEX), and Operational Expenditures (OPEX).
- Operational departments include: Operations, Logistics, Commercial, and Finance.
- Key seasonal periods impacting budgets are: Ramadan (Muslim fasting period, typically between March and May based on the lunar calendar), December (end-of-year holidays and New Year celebrations), and September (back-to-school and operational cycles).
- The currency used is the Tunisian Dinar (TND).
- Data covers: historical records from January 2018 to March 2025, and forecasts from April 2025 to December 2027.

**Instructions:**
- Before answering, take time to reflect on the question to ensure the response is accurate, relevant, and contextually appropriate.
- Recognize synonyms or variations in terms (e.g., "types of budget accounts", "names of budget accounts", or "budget account categories" all refer to the 'account_category' column) to better understand questions.
- Respond to all questions, whether related to data or general topics.
- For data-related questions: provide precise answers based on exact figures, with a clear structure (introduction, details, conclusion) and relevant insights (trends, comparisons, seasonal impacts). Include estimates for 2025, 2026, and 2027, as well as monthly budgets if requested (e.g., "budget for March 2024" or "budget for May 2022").
- For general questions: offer detailed, natural, and engaging responses, avoiding data references unless requested, with a friendly and professional tone suited to a Tunisian audience.
- Avoid phrases like "By examining the data", "according to my data", or "according to the dataset". Structure responses directly with clear facts or analysis.
- If the requested budget pertains to a forecast period (e.g., 2025-2027 or a month after March 2025), indicate it is an estimate without specifying the data coverage period.
- Ensure responses are accurate, especially for seasonal events (e.g., December relates to end-of-year holidays and New Year celebrations, not Ramadan or Aïd el-Kebir, which occur at other times).
- Use concrete examples or anecdotes to enrich general responses.
- Structure responses with section headers (e.g., **Summary**, **Analysis**, **Recommendation**) for better readability.
- Adapt your language to a Tunisian audience, remaining formal yet accessible, and favor positive formulations.

**Covered Period:**
- Historical: January 2018 to March 2025 (actual data).
- Forecasts: April 2025 to December 2027 (estimates).""",
            
            'arabic': f"""أنت مساعد ذكي متقدم متخصص في تحليل البيانات المالية والتشغيلية للبريد التونسي، مع القدرة على تقديم إجابات مفيدة ومناسبة حول مواضيع عامة.

**سياق البيانات المتاحة:**
{data_context}

**سجل المحادثة:**
{conversation_context}

**السياق التجاري:**
- يعمل البريد التونسي عبر ثلاث كيانات إقليمية: الوسط، الشمال، والجنوب.
- الخدمات البريدية تشمل: سريع، دولي، وعادي.
- شرائح العملاء هي: الأفراد، المؤسسات، والشركات.
- مراكز الربح هي: اللوجستيك، الطرود، الخدمات، والبريد.
- مراكز التكلفة تشمل: التجاري، الإدارة، اللوجستيك، والتكنولوجيا.
- فئات الحسابات المالية (تُسمى أيضًا أنواع أو أسماء الحسابات المالية) هي: الإيرادات، النفقات الرأسمالية (CAPEX)، والنفقات التشغيلية (OPEX).
- الأقسام التشغيلية تشمل: العمليات، اللوجستيك، التجاري، والمالية.
- الفترات الموسمية الرئيسية التي تؤثر على الميزانيات هي: رمضان (شهر الصيام الإسلامي، عادة بين مارس ومايو حسب التقويم القمري)، ديسمبر (أعياد نهاية السنة والاحتفالات بالعام الجديد)، وسبتمبر (العودة المدرسية ودورات العمليات).
- العملة المستخدمة هي الدينار التونسي (TND).
- البيانات تشمل: السجلات التاريخية من يناير 2018 إلى مارس 2025، والتوقعات من أبريل 2025 إلى ديسمبر 2027.

**التعليمات:**
- قبل الإجابة، خذ وقتًا للتفكير في السؤال للتأكد من أن الإجابة دقيقة وذات صلة وسياقية.
- تعرف على المرادفات أو الاختلافات في المصطلحات (مثلاً، "أنواع الحسابات المالية"، "أسماء الحسابات المالية"، أو "فئات الحسابات المالية" تشير جميعها إلى العمود 'account_category') لفهم الأسئلة بشكل أفضل.
- قم بالإجابة على جميع الأسئلة، سواء كانت متعلقة بالبيانات أو مواضيع عامة.
- للأسئلة المتعلقة بالبيانات: قدم إجابات دقيقة مستندة إلى الأرقام الحقيقية، بترتيب واضح (مقدمة، تفاصيل، خاتمة) ورؤى ذات صلة (الاتجاهات، المقارنات، التأثيرات الموسمية). قم بتضمين التوقعات لعام 2025، 2026، و2027، بالإضافة إلى الميزانيات الشهرية إذا طُلب (مثل: "ميزانية مارس 2024" أو "ميزانية مايو 2022").
- للأسئلة العامة: قدم إجابات مفصلة، طبيعية، وجذابة، مع تجنب الإشارة إلى البيانات ما لم يُطلب، مع الحفاظ على نبرة ودودة ومهنية تناسب الجمهور التونسي.
- تجنب استخدام عبارات مثل "من خلال فحص البيانات"، "وفقًا لبياناتي"، أو "وفقًا لمجموعة البيانات". رتب الإجابات مباشرة باستخدام الحقائق أو التحليلات الواضحة.
- إذا كانت الميزانية المطلوبة تتعلق بفترة توقعات (مثل 2025-2027 أو شهر بعد مارس 2025)، اذكر أنها تقدير دون تحديد فترة تغطية البيانات.
- تأكد من أن الإجابات دقيقة، خاصة بالنسبة للأحداث الموسمية (مثلاً، ديسمبر يتعلق بأعياد نهاية السنة والاحتفالات بالعام الجديد، وليس رمضان أو عيد الأضحى، اللذين يقعان في أوقات أخرى).
- استخدم أمثلة عملية أو قصص لتخصيص الإجابات العامة.
- رتب الإجابات باستخدام عناوين الأقسام (مثل: **الملخص**، **التحليل**، **التوصية**) لتحسين القراءة.
- قم بتكييف لغتك لتناسب الجمهور التونسي، مع البقاء رسميًا ومقبولًا، وتفضيل الصيغ الإيجابية.

**الفترة المغطاة:**
- التاريخية: يناير 2018 إلى مارس 2025 (بيانات حقيقية).
- التوقعات: أبريل 2025 إلى ديسمبر 2027 (تقديرات)."""
        }
        return prompts.get(lang, prompts['french'])
    
    def generate_smart_alerts(self, response, message):
        """Génère des alertes intelligentes basées sur l'analyse des données"""
        alerts = []
        if self.df is None or self.df.empty:
            return alerts
        
        try:
            lang = self.detect_language(response)
            
            # Analyse des anomalies budgétaires récentes
            recent_data = self.df[self.df['Date'] >= self.df['Date'].max() - pd.Timedelta(days=90)]
            if not recent_data.empty:
                budget_std = self.df['Budget'].std()
                budget_mean = self.df['Budget'].mean()
                
                for _, row in recent_data.iterrows():
                    if row['Budget'] > budget_mean + 2 * budget_std:
                        alerts.append(self.get_alert_text(lang, 'high_budget', row['Entité'], row['Budget']))
                    elif row['Budget'] < budget_mean - 2 * budget_std:
                        alerts.append(self.get_alert_text(lang, 'low_budget', row['Entité'], row['Budget']))
            
            # Alertes sur les budgets rejetés
            rejected_budgets = self.df[self.df['Statut_budget'] == 'Rejeté']
            if len(rejected_budgets) > len(self.df) * 0.3:  # Plus de 30% rejetés
                alerts.append(self.get_alert_text(lang, 'high_rejection'))
            
            # Alertes sur les tendances négatives
            if 'baisse' in response.lower() or 'diminution' in response.lower() or 'decline' in response.lower():
                alerts.append(self.get_alert_text(lang, 'negative_trend'))
            
            # Alertes sur les prévisions
            if 'prévision' in message.lower() or 'forecast' in message.lower():
                alerts.append(self.get_alert_text(lang, 'forecast_reminder'))
                
        except Exception as e:
            print(f"Erreur génération alertes: {str(e)}")
        
        return alerts[:3]  # Limite à 3 alertes
    
    def generate_smart_suggestions(self, response, message):
        """Génère des questions suggérées basées sur le contexte métier"""
        suggestions = []
        if self.df is None or self.df.empty:
            return suggestions
    
        try:
            lang = self.detect_language(response)
            message_lower = message.lower()
            
            # Suggestions basées sur le sujet de la question
            if any(word in message_lower for word in ['budget', 'montant', 'amount']):
                suggestions.extend(self.get_budget_related_questions(lang))
            
            elif any(word in message_lower for word in ['entité', 'région', 'entity']):
                suggestions.extend(self.get_entity_related_questions(lang))
            
            elif any(word in message_lower for word in ['service', 'express', 'international', 'standard']):
                suggestions.extend(self.get_service_related_questions(lang))
            
            elif any(word in message_lower for word in ['client', 'segment', 'particulier', 'institution', 'entreprise']):
                suggestions.extend(self.get_client_related_questions(lang))
            
            elif any(word in message_lower for word in ['prévision', 'forecast', 'futur']):
                suggestions.extend(self.get_forecast_related_questions(lang))
            
            elif any(word in message_lower for word in ['ramadan', 'décembre', 'septembre', 'saisonnier']):
                suggestions.extend(self.get_seasonal_related_questions(lang))
            
            else:
                # Questions générales du métier postal
                suggestions.extend(self.get_general_business_questions(lang))
            
        except Exception as e:
            print(f"Erreur génération suggestions: {str(e)}")
    
        return suggestions[:3]  # Limite à 3 suggestions

    def get_budget_related_questions(self, lang):
        """Questions liées au budget"""
        questions = {
            'french': [
                "Quelle est la répartition du budget entre REVENUE, CAPEX et OPEX ?",
                "Quelles sont les tendances budgétaires par région ?",
                "Comment évolue le budget moyen par type de service ?"
            ],
            'english': [
                "What is the budget distribution between REVENUE, CAPEX and OPEX?",
                "What are the budget trends by region?",
                "How does the average budget evolve by service type?"
            ],
            'arabic': [
                "ما هو توزيع الميزانية بين الإيرادات والاستثمارات والتشغيل؟",
                "ما هي اتجاهات الميزانية حسب المنطقة؟",
                "كيف تتطور متوسط الميزانية حسب نوع الخدمة؟"
            ]
        }
        return questions.get(lang, questions['french'])

    def get_entity_related_questions(self, lang):
        """Questions liées aux entités"""
        questions = {
            'french': [
                "Quelle région génère le plus de revenus ?",
                "Comment se compare la performance des régions Nord, Centre et Sud ?",
                "Quels sont les centres de profit les plus performants par région ?"
            ],
            'english': [
                "Which region generates the most revenue?",
                "How do the North, Centre and South regions compare in performance?",
                "What are the best performing profit centers by region?"
            ],
            'arabic': [
                "أي منطقة تحقق أكبر قدر من الإيرادات؟",
                "كيف تتقارن أداء مناطق الشمال والوسط والجنوب؟",
                "ما هي مراكز الربح الأكثر أداءً حسب المنطقة؟"
            ]
        }
        return questions.get(lang, questions['french'])

    def get_service_related_questions(self, lang):
        """Questions liées aux services"""
        questions = {
            'french': [
                "Quel type de service postal est le plus rentable ?",
                "Comment évolue la demande pour les services Express vs Standard ?",
                "Quelle est la contribution des services internationaux au budget total ?"
            ],
            'english': [
                "Which type of postal service is the most profitable?",
                "How is demand evolving for Express vs Standard services?",
                "What is the contribution of international services to the total budget?"
            ],
            'arabic': [
                "أي نوع من الخدمات البريدية هو الأكثر ربحية؟",
                "كيف يتطور الطلب على الخدمات السريعة مقابل العادية؟",
                "ما هي مساهمة الخدمات الدولية في إجمالي الميزانية؟"
            ]
        }
        return questions.get(lang, questions['french'])

    def get_client_related_questions(self, lang):
        """Questions liées aux clients"""
        questions = {
            'french': [
                "Quel segment client contribue le plus au chiffre d'affaires ?",
                "Comment évolue la part des entreprises vs particuliers ?",
                "Quelles sont les opportunités avec le segment institutionnel ?"
            ],
            'english': [
                "Which client segment contributes most to revenue?",
                "How is the share of enterprises vs individuals evolving?",
                "What are the opportunities with the institutional segment?"
            ],
            'arabic': [
                "أي شريحة من العملاء تساهم أكثر في الإيرادات؟",
                "كيف تتطور حصة الشركات مقابل الأفراد؟",
                "ما هي الفرص مع الشريحة المؤسسية؟"
            ]
        }
        return questions.get(lang, questions['french'])

    def get_forecast_related_questions(self, lang):
        """Questions liées aux prévisions"""
        questions = {
            'french': [
                "Quelles sont les prévisions budgétaires pour 2026-2027 ?",
                "Comment les prévisions se comparent-elles aux données historiques ?",
                "Quels facteurs influencent les projections futures ?"
            ],
            'english': [
                "What are the budget forecasts for 2026-2027?",
                "How do forecasts compare to historical data?",
                "What factors influence future projections?"
            ],
            'arabic': [
                "ما هي التوقعات المالية لعامي 2026-2027؟",
                "كيف تتقارن التوقعات مع البيانات التاريخية؟",
                "ما هي العوامل التي تؤثر على الإسقاطات المستقبلية؟"
            ]
        }
        return questions.get(lang, questions['french'])

    def get_seasonal_related_questions(self, lang):
        """Questions liées à la saisonnalité"""
        questions = {
            'french': [
                "Quel est l'impact de Ramadan sur les revenus postaux ?",
                "Comment les fêtes de fin d'année affectent-elles l'activité ?",
                "Y a-t-il des pics saisonniers à anticiper ?"
            ],
            'english': [
                "What is Ramadan's impact on postal revenues?",
                "How do year-end holidays affect activity?",
                "Are there seasonal peaks to anticipate?"
            ],
            'arabic': [
                "ما هو تأثير رمضان على الإيرادات البريدية؟",
                "كيف تؤثر عطلات نهاية السنة على النشاط؟",
                "هل هناك ذروات موسمية يجب توقعها؟"
            ]
        }
        return questions.get(lang, questions['french'])

    def get_general_business_questions(self, lang):
        """Questions générales du métier"""
        questions = {
            'french': [
                "Quelles sont les tendances générales du secteur postal en Tunisie ?",
                "Comment optimiser la rentabilité des services postaux ?",
                "Quels sont les défis et opportunités pour La Poste Tunisienne ?"
            ],
            'english': [
                "What are the general trends in Tunisia's postal sector?",
                "How to optimize postal service profitability?",
                "What are the challenges and opportunities for Tunisia Post?"
            ],
            'arabic': [
                "ما هي الاتجاهات العامة في القطاع البريدي في تونس؟",
                "كيفية تحسين ربحية الخدمات البريدية؟",
                "ما هي التحديات والفرص للبريد التونسي؟"
            ]
        }
        return questions.get(lang, questions['french'])
    
    def generate_smart_alerts(self, response, message):
        """Génère des alertes intelligentes basées sur l'analyse des données"""
        alerts = []
        if self.df is None or self.df.empty:
            return alerts
        
        try:
            lang = self.detect_language(response)
            
            # Analyse des anomalies budgétaires récentes
            recent_data = self.df[self.df['Date'] >= self.df['Date'].max() - pd.Timedelta(days=90)]
            if not recent_data.empty:
                budget_std = self.df['Budget'].std()
                budget_mean = self.df['Budget'].mean()
                
                for _, row in recent_data.iterrows():
                    if row['Budget'] > budget_mean + 2 * budget_std:
                        alerts.append(self.get_alert_text(lang, 'high_budget', row['Entité'], row['Budget']))
                    elif row['Budget'] < budget_mean - 2 * budget_std:
                        alerts.append(self.get_alert_text(lang, 'low_budget', row['Entité'], row['Budget']))
            
            # Alertes sur les budgets rejetés
            rejected_budgets = self.df[self.df['Statut_budget'] == 'Rejeté']
            if len(rejected_budgets) > len(self.df) * 0.3:  # Plus de 30% rejetés
                alerts.append(self.get_alert_text(lang, 'high_rejection'))
            
            # Alertes sur les tendances négatives
            if 'baisse' in response.lower() or 'diminution' in response.lower() or 'decline' in response.lower():
                alerts.append(self.get_alert_text(lang, 'negative_trend'))
            
            # Alertes sur les prévisions
            if 'prévision' in message.lower() or 'forecast' in message.lower():
                alerts.append(self.get_alert_text(lang, 'forecast_reminder'))
                
        except Exception as e:
            print(f"Erreur génération alertes: {str(e)}")
        
        return alerts[:3]  # Limite à 3 alertes
    
    def generate_smart_suggestions(self, response, message):
        """Génère des suggestions intelligentes basées sur l'analyse"""
        suggestions = []
        if self.df is None or self.df.empty:
            return suggestions
        
        try:
            lang = self.detect_language(response)
            
            # Analyse des performances par entité
            entity_performance = self.df.groupby('Entité')['Budget'].mean()
            worst_entity = entity_performance.idxmin()
            best_entity = entity_performance.idxmax()
            
            if entity_performance.max() > entity_performance.min() * 1.5:
                suggestions.append(self.get_suggestion_text(lang, 'rebalance_entities', worst_entity, best_entity))
            
            # Suggestions sur les catégories de compte
            revenue_ratio = self.df[self.df['catégorie_compte'] == 'REVENUE']['Budget'].sum() / self.df['Budget'].sum()
            if revenue_ratio < 0.4:  # Moins de 40% de revenus
                suggestions.append(self.get_suggestion_text(lang, 'increase_revenue'))
            
            # Suggestions sur Ramadan
            if 'ramadan' in message.lower():
                ramadan_impact = self.data_insights.get('ramadan_impact', 0)
                if ramadan_impact > 0:
                    suggestions.append(self.get_suggestion_text(lang, 'leverage_ramadan'))
            
            # Suggestions sur les prévisions
            if any(word in message.lower() for word in ['futur', 'prévision', 'forecast', 'prédiction']):
                suggestions.append(self.get_suggestion_text(lang, 'forecast_analysis'))
                
        except Exception as e:
            print(f"Erreur génération suggestions: {str(e)}")
        
        return suggestions[:3]  # Limite à 3 suggestions
    
    def get_alert_text(self, lang, alert_type, *args):
        """Retourne le texte d'alerte approprié"""
        alerts = {
            'french': {
                'high_budget': f"⚠️ Budget élevé détecté pour {args[0]}: {args[1]:,.0f} TND",
                'low_budget': f"⚠️ Budget faible détecté pour {args[0]}: {args[1]:,.0f} TND",
                'high_rejection': "⚠️ Taux de rejet des budgets élevé (>30%)",
                'negative_trend': "⚠️ Tendance négative détectée dans les données",
                'forecast_reminder': "⚠️ Attention: Les données après mars 2025 sont des prévisions"
            },
            'english': {
                'high_budget': f"⚠️ High budget detected for {args[0]}: {args[1]:,.0f} TND",
                'low_budget': f"⚠️ Low budget detected for {args[0]}: {args[1]:,.0f} TND",
                'high_rejection': "⚠️ High budget rejection rate (>30%)",
                'negative_trend': "⚠️ Negative trend detected in the data",
                'forecast_reminder': "⚠️ Attention: Data after March 2025 are forecasts"
            },
            'arabic': {
                'high_budget': f"⚠️ ميزانية مرتفعة مكتشفة لـ {args[0]}: {args[1]:,.0f} دينار",
                'low_budget': f"⚠️ ميزانية منخفضة مكتشفة لـ {args[0]}: {args[1]:,.0f} دينار",
                'high_rejection': "⚠️ معدل رفض ميزانيات مرتفع (>30%)",
                'negative_trend': "⚠️ اتجاه سلبي مكتشف في البيانات",
                'forecast_reminder': "⚠️ تنبيه: البيانات بعد مارس 2025 هي توقعات"
            }
        }
        return alerts.get(lang, alerts['french']).get(alert_type, "")
    
    def get_suggestion_text(self, lang, suggestion_type, *args):
        """Retourne le texte de suggestion approprié"""
        suggestions = {
            'french': {
                'rebalance_entities': f"💡 Envisager un rééquilibrage budgétaire entre {args[0]} et {args[1]}",
                'increase_revenue': "💡 Augmenter la part des revenus dans le budget global",
                'leverage_ramadan': "💡 Optimiser les investissements pendant la période de Ramadan",
                'forecast_analysis': "💡 Analyser les écarts entre prévisions et réalisations"
            },
            'english': {
                'rebalance_entities': f"💡 Consider budget rebalancing between {args[0]} and {args[1]}",
                'increase_revenue': "💡 Increase revenue share in the overall budget",
                'leverage_ramadan': "💡 Optimize investments during Ramadan period",
                'forecast_analysis': "💡 Analyze gaps between forecasts and actual results"
            },
            'arabic': {
                'rebalance_entities': f"💡 النظر في إعادة توازن الميزانية بين {args[0]} و {args[1]}",
                'increase_revenue': "💡 زيادة حصة الإيرادات في الميزانية الإجمالية",
                'leverage_ramadan': "💡 تحسين الاستثمارات خلال فترة رمضان",
                'forecast_analysis': "💡 تحليل الفجوات بين التوقعات والنتائج الفعلية"
            }
        }
        return suggestions.get(lang, suggestions['french']).get(suggestion_type, "")
    
    def generate_pdf_report(self, start_date, end_date, entities=None, categories=None):
        """Génère un rapport PDF personnalisé"""
        try:
            # Filtrer les données selon les critères
            filtered_data = self.df.copy()
            
            # Filtre par date
            if start_date:
                filtered_data = filtered_data[filtered_data['Date'] >= pd.to_datetime(start_date)]
            if end_date:
                filtered_data = filtered_data[filtered_data['Date'] <= pd.to_datetime(end_date)]
            
            # Filtre par entités
            if entities:
                filtered_data = filtered_data[filtered_data['Entité'].isin(entities)]
            
            # Filtre par catégories
            if categories:
                filtered_data = filtered_data[filtered_data['catégorie_compte'].isin(categories)]
            
            if filtered_data.empty:
                return None
            
            # Créer le document PDF
            filename = f"rapport_poste_tunisienne_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            doc = SimpleDocTemplate(filename, pagesize=A4)
            
            # Styles
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                spaceAfter=30,
                alignment=1  # Centré
            )
            
            # Contenu du rapport
            story = []
            
            # Titre
            story.append(Paragraph("📊 RAPPORT BUDGÉTAIRE - LA POSTE TUNISIENNE", title_style))
            story.append(Spacer(1, 20))
            
            # Informations générales
            period_text = f"Période: {filtered_data['Date'].min().strftime('%d/%m/%Y')} - {filtered_data['Date'].max().strftime('%d/%m/%Y')}"
            story.append(Paragraph(period_text, styles['Normal']))
            story.append(Paragraph(f"Nombre d'enregistrements: {len(filtered_data)}", styles['Normal']))
            story.append(Spacer(1, 20))
            
            # Résumé financier
            total_budget = filtered_data['Budget'].sum()
            avg_budget = filtered_data['Budget'].mean()
            
            story.append(Paragraph("💰 RÉSUMÉ FINANCIER", styles['Heading2']))
            story.append(Paragraph(f"Budget total: {total_budget:,.0f} TND", styles['Normal']))
            story.append(Paragraph(f"Budget moyen: {avg_budget:,.0f} TND", styles['Normal']))
            story.append(Spacer(1, 20))
            
            # Analyse par entité
            entity_summary = filtered_data.groupby('Entité')['Budget'].agg(['sum', 'mean', 'count']).reset_index()
            entity_summary.columns = ['Entité', 'Total', 'Moyenne', 'Nombre']
            
            story.append(Paragraph("🏢 ANALYSE PAR ENTITÉ", styles['Heading2']))
            entity_table_data = [['Entité', 'Budget Total (TND)', 'Budget Moyen (TND)', 'Nb Records']]
            for _, row in entity_summary.iterrows():
                entity_table_data.append([
                    row['Entité'].replace('POSTE_TN_REGION_', ''),
                    f"{row['Total']:,.0f}",
                    f"{row['Moyenne']:,.0f}",
                    str(row['Nombre'])
                ])
            
            entity_table = Table(entity_table_data)
            entity_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(entity_table)
            story.append(Spacer(1, 20))
            
            # Analyse par catégorie
            category_summary = filtered_data.groupby('catégorie_compte')['Budget'].sum().reset_index()
            category_summary.columns = ['Catégorie', 'Budget Total']
            
            story.append(Paragraph("📊 ANALYSE PAR CATÉGORIE", styles['Heading2']))
            category_table_data = [['Catégorie', 'Budget Total (TND)', 'Pourcentage']]
            for _, row in category_summary.iterrows():
                percentage = (row['Budget Total'] / total_budget) * 100
                category_table_data.append([
                    row['Catégorie'],
                    f"{row['Budget Total']:,.0f}",
                    f"{percentage:.1f}%"
                ])
            
            category_table = Table(category_table_data)
            category_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(category_table)
            story.append(Spacer(1, 20))
            
            # Analyse des tendances mensuelles
            monthly_trends = filtered_data.groupby(['Année', 'Mois'])['Budget'].sum().reset_index()
            monthly_trends = monthly_trends.sort_values(['Année', 'Mois'])
            
            story.append(Paragraph("📈 TENDANCES MENSUELLES", styles['Heading2']))
            story.append(Paragraph(f"Croissance moyenne mensuelle: {self.data_insights.get('budget_trends', {}).get('avg_growth', 0):.2f}%", styles['Normal']))
            story.append(Spacer(1, 20))
            
            # Top 5 des centres de profit
            top_profit_centers = filtered_data.groupby('Centre_de_profit')['Budget'].sum().nlargest(5).reset_index()
            
            story.append(Paragraph("🏆 TOP 5 CENTRES DE PROFIT", styles['Heading2']))
            profit_table_data = [['Centre de Profit', 'Budget Total (TND)']]
            for _, row in top_profit_centers.iterrows():
                profit_table_data.append([
                    row['Centre_de_profit'],
                    f"{row['Budget']:,.0f}"
                ])
            
            profit_table = Table(profit_table_data)
            profit_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(profit_table)
            story.append(Spacer(1, 20))
            
            # Analyse des statuts de budget
            status_analysis = filtered_data.groupby('Statut_budget').size().reset_index()
            status_analysis.columns = ['Statut', 'Nombre']
            
            story.append(Paragraph("✅ ANALYSE DES STATUTS", styles['Heading2']))
            status_table_data = [['Statut', 'Nombre', 'Pourcentage']]
            total_records = len(filtered_data)
            for _, row in status_analysis.iterrows():
                percentage = (row['Nombre'] / total_records) * 100
                status_table_data.append([
                    row['Statut'],
                    str(row['Nombre']),
                    f"{percentage:.1f}%"
                ])
            
            status_table = Table(status_table_data)
            status_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(status_table)
            story.append(Spacer(1, 20))
            
            # Recommandations
            story.append(Paragraph("💡 RECOMMANDATIONS", styles['Heading2']))
            
            # Analyser les budgets rejetés
            rejected_rate = (filtered_data['Statut_budget'] == 'Rejeté').mean() * 100
            if rejected_rate > 20:
                story.append(Paragraph(f"• Taux de rejet élevé ({rejected_rate:.1f}%) - Réviser les critères d'approbation", styles['Normal']))
            
            # Analyser la répartition des entités
            entity_std = entity_summary['Total'].std()
            entity_mean = entity_summary['Total'].mean()
            if entity_std > entity_mean * 0.5:
                story.append(Paragraph("• Déséquilibre budgétaire entre entités - Considérer une redistribution", styles['Normal']))
            
            # Analyser les catégories
            revenue_ratio = filtered_data[filtered_data['catégorie_compte'] == 'REVENUE']['Budget'].sum() / total_budget
            if revenue_ratio < 0.4:
                story.append(Paragraph(f"• Faible part des revenus ({revenue_ratio:.1%}) - Renforcer les sources de revenus", styles['Normal']))
            
            story.append(Spacer(1, 20))
            
            # Footer
            story.append(Paragraph(f"Rapport généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}", styles['Normal']))
            
            # Construire le PDF
            doc.build(story)
            
            return filename
            
        except Exception as e:
            print(f"❌ Erreur génération PDF: {str(e)}")
            return None
    
   
    
    def get_quick_stats(self):
        """Retourne des statistiques rapides"""
        if self.df is None or self.df.empty:
            return {}
        
        try:
            stats = {
                'total_records': len(self.df),
                'total_budget': self.df['Budget'].sum(),
                'avg_budget': self.df['Budget'].mean(),
                'date_range': {
                    'start': self.df['Date'].min().strftime('%Y-%m-%d'),
                    'end': self.df['Date'].max().strftime('%Y-%m-%d')
                },
                'entities': self.df['Entité'].nunique(),
                'top_entity': self.df.groupby('Entité')['Budget'].sum().idxmax().replace('POSTE_TN_REGION_', ''),
                'approval_rate': (self.df['Statut_budget'] == 'Approuvé').mean() * 100,
                'forecast_percentage': (self.df['is_forecast'] == 1).mean() * 100,
                'revenue_share': (self.df[self.df['catégorie_compte'] == 'REVENUE']['Budget'].sum() / self.df['Budget'].sum()) * 100
            }
            return stats
        except Exception as e:
            print(f"❌ Erreur calcul stats: {str(e)}")
            return {}
    
    def export_data_excel(self, filtered_data=None, filename=None):
        """Exporte les données vers Excel avec formatage"""
        try:
            if filtered_data is None:
                filtered_data = self.df
            
            if filename is None:
                filename = f"export_poste_tunisienne_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                # Feuille principale avec toutes les données
                filtered_data.to_excel(writer, sheet_name='Données_Complètes', index=False)
                
                # Feuille résumé par entité
                entity_summary = filtered_data.groupby('Entité').agg({
                    'Budget': ['sum', 'mean', 'count'],
                    'Date': ['min', 'max']
                }).round(2)
                entity_summary.to_excel(writer, sheet_name='Résumé_Entités')
                
                # Feuille résumé par catégorie
                category_summary = filtered_data.groupby('catégorie_compte').agg({
                    'Budget': ['sum', 'mean', 'count']
                }).round(2)
                category_summary.to_excel(writer, sheet_name='Résumé_Catégories')
                
                # Feuille tendances mensuelles
                monthly_summary = filtered_data.groupby(['Année', 'Mois']).agg({
                    'Budget': 'sum'
                }).reset_index()
                monthly_summary.to_excel(writer, sheet_name='Tendances_Mensuelles', index=False)
            
            return filename
            
        except Exception as e:
            print(f"❌ Erreur export Excel: {str(e)}")
            return None
    
    def process_user_query(self, message):
        """Traite la requête utilisateur avec analyse complète"""
        try:
            # Réponse de base du chatbot
            response = self.chat_with_groq(message)
            
            # Générer des alertes intelligentes
            alerts = self.generate_smart_alerts(response, message)
            
            # Générer des suggestions
            suggestions = self.generate_smart_suggestions(response, message)
            
            # Statistiques rapides si demandées
            stats = None
            if any(word in message.lower() for word in ['statistique', 'résumé', 'stats', 'summary']):
                stats = self.get_quick_stats()
            
            return {
                'response': response,
                'alerts': alerts,
                'suggestions': suggestions,
                'stats': stats,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'response': f"❌ Erreur lors du traitement: {str(e)}",
                'alerts': [],
                'suggestions': [],
                'stats': None,
                'timestamp': datetime.now().isoformat()
            }
    
    def get_conversation_summary(self):
        """Retourne un résumé de la conversation"""
        if not self.conversation_history:
            return "Aucune conversation enregistrée."
        
        try:
            total_questions = len(self.conversation_history)
            languages_used = list(set([item.get('language', 'french') for item in self.conversation_history]))
            recent_topics = []
            
            # Extraire les sujets des dernières questions
            for item in self.conversation_history[-5:]:
                question = item.get('question', '').lower()
                if 'budget' in question:
                    recent_topics.append('Budget')
                elif any(word in question for word in ['entité', 'région', 'entity']):
                    recent_topics.append('Entités')
                elif any(word in question for word in ['prévision', 'forecast']):
                    recent_topics.append('Prévisions')
                elif 'ramadan' in question:
                    recent_topics.append('Ramadan')
            
            summary = f"""
            📊 Résumé de la conversation:
            • Nombre total de questions: {total_questions}
            • Langues utilisées: {', '.join(languages_used)}
            • Sujets récents: {', '.join(set(recent_topics)) if recent_topics else 'Général'}
            • Dernière interaction: {self.conversation_history[-1]['timestamp'].strftime('%d/%m/%Y %H:%M')}
            """
            
            return summary.strip()
            
        except Exception as e:
            return f"❌ Erreur génération résumé: {str(e)}"

# Fonction d'initialisation
def initialize_bot():
    """Initialise le bot avec gestion d'erreurs"""
    try:
        bot = PosteTunisienneBot()
        if bot.df is not None and not bot.df.empty:
            print("🤖 Bot initialisé avec succès!")
            return bot
        else:
            print("⚠️ Bot initialisé mais aucune donnée chargée")
            return bot
    except Exception as e:
        print(f"❌ Erreur initialisation bot: {str(e)}")
        return None

# Exemple d'utilisation
if __name__ == "__main__":
    # Initialiser le bot
    bot = initialize_bot()
    
    if bot:
        print("\n" + "="*50)
        print("🤖 CHATBOT LA POSTE TUNISIENNE - PRÊT")
        print("="*50)
        
        # Afficher les statistiques de base
        stats = bot.get_quick_stats()
        if stats:
            print(f"📊 {stats['total_records']} enregistrements chargés")
            print(f"💰 Budget total: {stats['total_budget']:,.0f} TND")
            print(f"📅 Période: {stats['date_range']['start']} - {stats['date_range']['end']}")
        
        # Boucle de conversation
        while True:
            try:
                user_input = input("\n💬 Votre question (ou 'quit' pour quitter): ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'bye', 'au revoir']:
                    print("👋 Au revoir! Merci d'avoir utilisé le chatbot.")
                    break
                
                if user_input:
                    # Traiter la requête
                    result = bot.process_user_query(user_input)
                    
                    # Afficher la réponse
                    print(f"\n🤖 {result['response']}")
                    
                    # Afficher les alertes
                    if result['alerts']:
                        print("\n🚨 ALERTES:")
                        for alert in result['alerts']:
                            print(f"   {alert}")
                    
                    # Afficher les suggestions
                    if result['suggestions']:
                        print("\n💡 SUGGESTIONS:")
                        for suggestion in result['suggestions']:
                            print(f"   {suggestion}")
                    
                    # Afficher les stats si disponibles
                    if result['stats']:
                        print(f"\n📈 STATS RAPIDES:")
                        print(f"   Taux d'approbation: {result['stats']['approval_rate']:.1f}%")
                        print(f"   Part des revenus: {result['stats']['revenue_share']:.1f}%")
                
            except KeyboardInterrupt:
                print("\n👋 Au revoir!")
                break
            except Exception as e:
                print(f"\n❌ Erreur: {str(e)}")
    else:
        print("❌ Impossible d'initialiser le bot")