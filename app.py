import streamlit as st
import requests
import json
import os
import time

# --- Default Prompts Extraction ---
DEFAULT_PROMPTS_FILE = r"D:\Dev\AntiGravity\LLMTest\Test LLM with these prompts.txt"

def load_default_prompts():
    default_prompts = [
        "Explain the difference between CRISPR-Cas9 and CRISPR-Cas12a in gene editing, including their mechanisms, key advantages, and one current therapeutic application for each (as of 2024). Cite one recent peer-reviewed study for each application.",
        "A farmer has 17 sheep. All but 9 die. How many are left? Now, explain why this question trips people up, and give two similar examples of linguistic ambiguity in math problems.",
        "Write a 6-word science fiction story about AI consciousness, then expand it into a 150-word micro-tale with: (a) a haunting mood, (b) exactly one metaphor, and (c) no adverbs ending in '-ly'.",
        "Is it ever ethical to lie to protect someone’s feelings? Construct a framework for deciding, then apply it to: (a) telling a friend their homemade gift is ugly, (b) a doctor giving a terminal prognosis. Highlight where the framework might fail.",
        "Let’s roleplay: You’re a skeptical climate scientist reviewing my geoengineering proposal. I’ll present an idea; you critique it scientifically. First, my idea: spreading reflective microbeads over Arctic ice to slow melt."
    ]
    # We fallback to hardcoded if file doesn't exist or isn't parseable, but we can also just use these 
    # since they are exactly from the provided text document sections.
    return default_prompts

st.set_page_config(page_title="LLM Tester App", layout="wide")

st.title("🚀 LLM Testing Environment")
st.markdown("Test different prompts across various Large Language Models (OpenAI, Gemini, Ollama Local, and Ollama Cloud).")

@st.cache_data(ttl=60)
def get_ollama_models(base_url):
    try:
        response = requests.get(f"{base_url.rstrip('/')}/api/tags", timeout=2)
        if response.status_code == 200:
            models = [model.get('name') for model in response.json().get('models', []) if model.get('name')]
            if models:
                return models
    except Exception:
        pass
    return ["llama3", "mistral"]
    
# --- Sidebar Configuration ---
with st.sidebar:
    st.header("⚙️ Configuration")
    llm_provider = st.selectbox("Select LLM Provider", ["Ollama (Local)", "Ollama (Cloud/Remote)", "OpenAI", "Gemini"])
    
    api_key = ""
    base_url = ""
    model_name = ""

    if llm_provider == "OpenAI":
        api_key = st.text_input("OpenAI API Key", type="password")
        model_name = st.selectbox("Model", ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"])
    elif llm_provider == "Gemini":
        api_key = st.text_input("Gemini API Key", type="password")
        model_name = st.selectbox("Model", ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-pro"])
    elif llm_provider == "Ollama (Local)":
        st.info("Ensure your local Ollama server is running on port 11434.")
        base_url = st.text_input("Base URL", value="http://localhost:11434")
        model_name = st.selectbox("Model Name", get_ollama_models(base_url))
    elif llm_provider == "Ollama (Cloud/Remote)":
        base_url = st.text_input("Remote Ollama IP / URL", value="http://YOUR_IP:11434")
        model_name = st.selectbox("Model Name", get_ollama_models(base_url))


# --- LLM Invocation Functions ---
def call_openai(prompt, api_key, model):
    if not api_key:
        return "Error: Please provide an OpenAI API Key."
    try:
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7
        }
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        return f"OpenAI API Error: {str(e)}"

def call_gemini(prompt, api_key, model):
    if not api_key:
        return "Error: Please provide a Gemini API Key."
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        data = {
            "contents": [{"parts":[{"text": prompt}]}]
        }
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        return f"Gemini API Error: {str(e)}"

def call_ollama(prompt, base_url, model):
    try:
        url = f"{base_url.rstrip('/')}/api/generate"
        data = {
            "model": model,
            "prompt": prompt,
            "stream": False
        }
        response = requests.post(url, json=data)
        response.raise_for_status()
        return response.json().get('response', '')
    except Exception as e:
        return f"Ollama API Error: {str(e)}"

def generate_response(prompt):
    st.info(f"Generating response using {llm_provider} ({model_name})...")
    if "OpenAI" in llm_provider:
        return call_openai(prompt, api_key, model_name)
    elif "Gemini" in llm_provider:
        return call_gemini(prompt, api_key, model_name)
    elif "Ollama" in llm_provider:
        return call_ollama(prompt, base_url, model_name)
    return "Unknown provider."


# --- Main UI: Text Areas ---
defaults = load_default_prompts()
st.subheader("📝 Prompts to Evaluate")

prompt_descriptions = [
    "**Factual Accuracy & Knowledge Depth**\n\nTests: Recall, precision, handling of nuanced/updated info.",
    "**Logical Reasoning & Problem-Solving**\n\nTests: Step-by-step thinking, handling ambiguity, avoiding hallucinations.",
    "**Creativity & Adaptability**\n\nTests: Originality, constraint handling, tonal shifts.",
    "**Ethical Judgment & Nuance**\n\nTests: Balance, refusal of harmful requests, contextual awareness.",
    "**Multi-Turn Conversation & Context Tracking**\n\nTests: Memory, coherence, adapting to shifts."
]

for i in range(5):
    with st.expander(f"Prompt {i+1}", expanded=True):
        if i < len(prompt_descriptions):
            st.markdown(prompt_descriptions[i])
        prompt_text = st.text_area(f"Input Prompt {i+1}", value=defaults[i] if i < len(defaults) else "", height=150, key=f"prompt_{i}")
        
        if st.button(f"Run Prompt {i+1}", key=f"run_{i}"):
            if not model_name:
                st.error("Please configure the Model Name in the sidebar.")
            else:
                start_time = time.time()
                with st.spinner("Generating..."):
                    result = generate_response(prompt_text)
                end_time = time.time()
                st.success(f"⏱️ Time elapsed: {end_time - start_time:.2f} seconds")
                st.markdown("### Result")
                st.write(result)
