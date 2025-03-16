import streamlit as st # type: ignore
import google.generativeai as genai # type: ignore
import time
import os
import apiDrive
import html
from google.oauth2.credentials import Credentials # type: ignore
from google_auth_oauthlib.flow import InstalledAppFlow # type: ignore
from google.auth.transport.requests import Request # type: ignore
from googleapiclient.discovery import build # type: ignore

# ------------------------------ CONFIGURAÇÃO INICIAL ------------------------------ #
st.set_page_config(
    page_title="Assistente Nutricional",
    layout="centered",
    page_icon="🍏"
)

if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []

if "dieta_limpa" not in st.session_state:
    st.session_state.dieta_limpa = False

DIETA_FILE = r"D:\\Projetos\\SitemaInformacao\\chatbot\\ChatBotFitness-main\\temp\\dieta.txt"
SCOPES = ['https://www.googleapis.com/auth/drive']

file_path = "apiKey.txt"

with open(file_path, "r") as file:
    api_key = file.read().strip()

genai.configure(api_key=api_key)

mensagem_area = st.empty()

# ------------------------------ FUNÇÕES AUXILIARES ------------------------------ #
def authenticate_google_drive(config):
    creds = None
    TOKEN_FILE = 'token.json'

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_config({
                "installed": {
                    "client_id": config['client_id'],
                    "client_secret": config['client_secret'],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": config['redirect_uris']
                }
            }, SCOPES)
            creds = flow.run_local_server(port=0)
            with open(TOKEN_FILE, 'w') as token_file:
                token_file.write(creds.to_json())
    return creds

def ler_contexto_do_drive(file_name='contexto.txt'):
    try:
        config = apiDrive.load_config('config_drive.json')
        creds = authenticate_google_drive(config)
        service = build('drive', 'v3', credentials=creds)

        results = service.files().list(q=f"name='{file_name}'",
                                       fields="files(id, name)").execute()
        items = results.get('files', [])

        if not items:
            mensagem_area.error("❌ Arquivo contexto.txt não encontrado no Google Drive.")
            return ""

        file_id = items[0]['id']
        request = service.files().get_media(fileId=file_id)

        file_content = request.execute().decode('utf-8')
        return file_content

    except Exception as e:
        mensagem_area.error(f"❌ Erro ao ler o arquivo contexto.txt: {e}")
        return ""
    
def ler_dieta_do_drive(file_name='dieta.txt'):
    try:
        config = apiDrive.load_config('config_drive.json')
        creds = authenticate_google_drive(config)
        service = build('drive', 'v3', credentials=creds)

        results = service.files().list(q=f"name='{file_name}'",
                                       fields="files(id, name)").execute()
        items = results.get('files', [])

        if not items:
            mensagem_area.error("❌ Arquivo contexto.txt não encontrado no Google Drive.")
            return ""

        file_id = items[0]['id']
        request = service.files().get_media(fileId=file_id)

        file_content = request.execute().decode('utf-8')
        return file_content

    except Exception as e:
        mensagem_area.error(f"❌ Erro ao ler o arquivo contexto.txt: {e}")
        return ""


# ------------------------------
# FUNÇÕES AUXILIARES
# ------------------------------
def display_chat():
    for entry in st.session_state.conversation_history:
        role = entry["role"]
        message = html.escape(entry["message"])
        timestamp = entry.get("timestamp", "")

        if role == "user":
            st.markdown(
                f"""
                <div style='text-align: right; margin: 10px;'>
                    <div style='color: #666; font-size: 0.8em;'>{timestamp}</div>
                    <div style='background: #4CAF50; color: white; padding: 12px 18px; border-radius: 20px; display: inline-block; max-width: 70%;'>
                        {message}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"""
                <div style='text-align: left; margin: 10px;'>
                    <div style='color: #666; font-size: 0.8em;'>{timestamp}</div>
                    <div style='background: #f8f8f8; color: #333; padding: 12px 18px; border-radius: 20px; display: inline-block; max-width: 70%;'>
                        {message}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

@st.cache_resource
def load_gemini():
    return genai.GenerativeModel('gemini-2.0-flash')

model = load_gemini()

def generate_response(user_input):
    try:
        contexto = ler_contexto_do_drive('contexto.txt')
        dieta_existente = ler_dieta_do_drive('dieta.txt')

        if dieta_existente.strip():
            contexto += f"\n\nO usuário já possui essa dieta: {dieta_existente.strip()}"

        context = f"{contexto}\n\nPergunta do usuário: {user_input}\nResposta:"
        
        response = model.generate_content(
            context,
            generation_config=genai.types.GenerationConfig(
                temperature=0.0,
                max_output_tokens=8192 
            )
        )
        resposta_gerada = response.text.strip()
        return {"text": resposta_gerada} if resposta_gerada else {"text": "Desculpe, não consegui entender sua pergunta. Tente novamente."}
    except Exception as e:
        return {"text": f"Erro no sistema: {str(e)}"}
 
def salvar_dieta_no_txt(dieta_conteudo):
    try:
        os.makedirs(os.path.dirname(DIETA_FILE), exist_ok=True)
        with open(DIETA_FILE, 'w', encoding='utf-8') as f:
            f.write(dieta_conteudo)
        mensagem_area.success("✅ Dieta salva ou atualizada com sucesso!")
    except Exception as e:
        mensagem_area.error(f"❌ Erro ao salvar dieta: {e}")

def enviar_dieta_para_drive():
    try:
        if not os.path.exists(DIETA_FILE):
            mensagem_area.error(f"❌ Arquivo não encontrado no caminho: {DIETA_FILE}")
            return
        config = apiDrive.load_config('config_drive.json')
        apiDrive.upload_file_to_drive(config, os.path.basename(DIETA_FILE))
        mensagem_area.success("✅ Dieta enviada ou atualizada com sucesso!")
    except Exception as e:
        mensagem_area.error(f"❌ Erro ao enviar dieta, tente novamente mais tarde: {e}")

def contem_palavra_chave_dieta(texto):
    palavras_chave = ['dieta', 'plano alimentar', 'alimentação', 'refeição', 'cardápio', 'nutrição']
    texto = texto.lower()
    return any(palavra in texto for palavra in palavras_chave)

def dieta_existe():
    return os.path.exists(DIETA_FILE) and os.path.getsize(DIETA_FILE) > 0

def limpar_dieta():
    try:
        with open(DIETA_FILE, 'w', encoding='utf-8') as f:
            f.write('')
        mensagem_area.success("✅ Dieta limpa com sucesso!")
        enviar_dieta_para_drive()
        st.session_state.dieta_limpa = True
    except Exception as e:
        mensagem_area.error(f"❌ Erro ao limpar dieta: {e}")

# ------------------------------
# INTERFACE
# ------------------------------
col1, col2 = st.columns([1, 4])
with col1:
    st.image("img/maca.png", width=200)
with col2:
    st.title("Assistente Fitness")
    st.markdown("<h4 style='font-size: 16px; color: #7ED957;'>Seu assistente para dicas de treino e planos alimentares!</h4>", unsafe_allow_html=True)

with st.container():
    st.markdown("<hr>", unsafe_allow_html=True)
    display_chat()
    st.markdown("<hr>", unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.session_state.conversation_history:
            st.button("Limpar Conversa 🗑️", key="limpar_conversa", use_container_width=True, on_click=lambda: st.session_state.update({"conversation_history": []}))
    with col2:
        if dieta_existe():
            st.button("Limpar Dieta 🗑️", key="limpar_dieta", use_container_width=True, on_click=limpar_dieta)

with st.form(key="unique_form", clear_on_submit=True):
    user_input = st.text_area(
        "Digite sua pergunta:", 
        placeholder="Ex: Monte um plano alimentar para minha altura e peso", 
        max_chars=1000, 
        height=150
    )
    submit_button = st.form_submit_button("Enviar ➤")

if submit_button and user_input:
    with st.spinner("Buscando resposta..."):
        st.session_state.conversation_history.append({
            "role": "user",
            "message": user_input,
            "timestamp": time.strftime("%H:%M")
        })

        resposta = generate_response(user_input)
        resposta_texto = resposta["text"]

        st.session_state.conversation_history.append({
            "role": "assistant",
            "message": resposta_texto,
            "timestamp": time.strftime("%H:%M")
        })

        if contem_palavra_chave_dieta(user_input):
            salvar_dieta_no_txt(resposta_texto)
            enviar_dieta_para_drive()

        st.rerun()

# Forçar o scroll para o final após limpar dieta
if st.session_state.dieta_limpa:
    st.markdown("""
        <script>
            setTimeout(() => {
                window.scrollTo(0, document.body.scrollHeight);
            }, 500);
        </script>
    """, unsafe_allow_html=True)
    st.session_state.dieta_limpa = False

# Rodapé
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown(
    f"""
    <div style='text-align: center; font-size: 0.9em; color: #666; padding: 15px;'>
        <p>Desenvolvido para promover saúde e bem-estar. • {time.strftime('%d/%m/%Y')}</p>
    </div>
    """,
    unsafe_allow_html=True
)
