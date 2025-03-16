import streamlit as st
import google.generativeai as genai
import time

# ------------------------------
# CONFIGURAÇÃO INICIAL
# ------------------------------
st.set_page_config(
    page_title="Assistente Nutricional",
    layout="centered",
    page_icon="🍏"
)

if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []

# ------------------------------
# CSS PERSONALIZADO PARA CADA BOTÃO
# ------------------------------
st.markdown("""
    <style>
        /* Botão Enviar (Verde) */
        .st-emotion-cache-1xw8zd0.e10yg2by1 button:first-child {
            background-color: #4CAF50 !important;
            color: white !important;
            padding: 10px 20px;
            border-radius: 5px;
            border: none;
            font-size: 16px;
            cursor: pointer;
            transition: background-color 0.3s ease-in-out, transform 0.2s ease-in-out;
        }

  .st-emotion-cache-1xw8zd0.e10yg2by1 button:first-child:hover {
            background-color: #2E7D32 !important;
            transform: scale(1.05);
        }

      
    </style>
""", unsafe_allow_html=True)

# ------------------------------
# INICIALIZAÇÕES
# ------------------------------
# Substitua pela sua chave de API
file_path = "apiKey.txt"

# Ler a chave de API do arquivo
with open(file_path, "r") as file:
    api_key = file.read().strip()

# Configurar a chave da API
genai.configure(api_key=api_key) 


# ------------------------------
# FUNÇÕES AUXILIARES
# ------------------------------
def display_chat():
    for entry in st.session_state.conversation_history:
        role = entry["role"]
        message = entry["message"]
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
        context = f"""
        Você é um assistente fitness, 
        dedicado a ajudar seus usuários a atingirem seus objetivos de saúde e bem-estar. 
        Oferece conselhos personalizados sobre nutrição, 
        cria planos de treino adaptados ao nível de fitness de cada pessoa e fornece dicas para otimizar os resultados.
        Qual é o objetivo fitness do usuário hoje?

        Pergunta do usuário: {user_input}
        Resposta:
        """

        response = model.generate_content(
            context,
            generation_config=genai.types.GenerationConfig(
                temperature=0.0,
                max_output_tokens=8192 
            )
        )

        resposta_gerada = response.text.strip()

        if not resposta_gerada:
            return {"text": "Desculpe, não consegui entender sua pergunta. Tente novamente."}

        return {"text": resposta_gerada}

    except Exception as e:
        return {"text": f"Erro no sistema: {str(e)}"}

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

    # Botão customizado para limpar conversa
    if st.session_state.conversation_history:
        if st.button("Limpar Conversa 🗑️"):
            st.session_state.conversation_history = []
            st.rerun()
            
with st.form(key="unique_form", clear_on_submit=True):
    user_input = st.text_input(
        "Digite sua pergunta:", 
        placeholder="Ex: Monte um plano alimentar para minha altura e peso", 
        max_chars=100
    )
    submit_button = st.form_submit_button("Enviar ➤")

if submit_button and user_input:
    with st.spinner("Buscando resposta..."):
        st.session_state.conversation_history.append({
            "role": "user",
            "message": user_input,
            "timestamp": time.strftime("%H:%M:%S")
        })
        
        resposta = generate_response(user_input)
        
        st.session_state.conversation_history.append({
            "role": "assistant",
            "message": resposta["text"],
            "timestamp": time.strftime("%H:%M:%S")
        })
        
        st.rerun()

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
