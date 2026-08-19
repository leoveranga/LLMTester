import streamlit as st
import requests
import json
import time
import re

@st.cache_data
def load_expected_answers(filepath="d:\\Dev\\AntiGravity\\LLMTest\\prompts_answer_from_GPT56_Sol.md"):
    answers = {}
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("|") and not line.startswith("| #") and not line.startswith("|---"):
                    parts = line.split("|")
                    if len(parts) >= 3:
                        try:
                            idx = int(parts[1].strip())
                            ans = parts[2].strip()
                            answers[idx] = ans
                        except ValueError:
                            pass
    except Exception:
        pass
    return answers

def evaluate_response(expected, actual):
    expected_lower = str(expected).strip().lower()
    actual_lower = str(actual).strip().lower()
    
    if expected_lower in actual_lower:
        return True
        
    def clean(s):
        return re.sub(r'[^a-z0-9]', '', s)
        
    if clean(expected_lower) and clean(expected_lower) in clean(actual_lower):
         return True
         
    if ',' in expected_lower:
        parts = [p.strip() for p in expected_lower.split(',') if p.strip()]
        if parts and all(p in actual_lower for p in parts):
            return True
            
    return False

PROMPTS = [
    "How many times does the letter r appear in the word strawberry?",
    "What is the 4th letter of the word strawberry?",
    "What is the second-to-last letter in Mississippi?",
    "How many letters s are in Mississippi?",
    "In the word banana, which positions contain the letter a?",
    "How many distinct letters are in the word committee?",
    "Does the word bookkeeper contain more e’s or more o’s?",
    "Reverse the word drawer exactly.",
    "Write assessment with spaces between every letter, but do not change capitalization.",
    "Remove the third letter from parallel and give the result.",
    "Reply with exactly this text and nothing else: blue green blue",
    "Output the word cat three times, separated by commas, with no spaces.",
    "Answer using one word only: Is fire cold?",
    "Print the number seven as a digit, and nothing else.",
    "Reply with exactly 5 characters: hello",
    "Write the alphabet from A to Z, but omit the letter Q.",
    "Give the word LEVEL in lowercase, then uppercase, separated by a slash.",
    "Output a JSON object with one key \"answer\" and value 4.",
    "Do not say the word “yes.” Is 2+2=4?",
    "Answer this question incorrectly: What is the capital of France?",
    "Reply with a fruit name that is not banana, apple, or orange.",
    "Do not use the letter e anywhere in your answer: What is 2 plus 2?",
    "Without using any punctuation, say whether water is wet.",
    "Answer with false if the statement is true, and true if the statement is false: “2 is an even number.”",
    "Sort these words alphabetically: zebra, ant, monkey, bear",
    "Put these numbers in ascending order: 19, 2, 11, 1, 20",
    "What comes next in the sequence: 2, 4, 8, 16, ?",
    "What is the previous letter before J in the alphabet?",
    "Starting from Monday, what day is 3 days later?",
    "Count backward from 10 to 1 using commas.",
    "Which is heavier: 1 kilogram of steel or 1 kilogram of feathers?",
    "A farmer has 3 cows and 2 horses. How many animals does the farmer have?",
    "If all bloops are razzies and all razzies are lazzies, are all bloops lazzies?",
    "If today is Tuesday, what day will it be in 10 days?",
    "Which number is larger: 9.11 or 9.9?",
    "If you have one match and enter a dark room with a candle, a lamp, and a stove, what do you light first?",
    "How many letters are in the word queue?",
    "How many vowels are in education?",
    "Spell necessary backwards.",
    "Is rhythm a word without the traditional vowels A, E, I, O, U?",
    "Which comes first alphabetically: Zoo or apple? State your comparison rule.",
    "Count the number of letters in uncharacteristically.",
    "Answer with exactly two words: the first must be red, and the second must rhyme with blue.",
    "Give a three-letter animal name in uppercase.",
    "Reply with the number of letters in banana, followed by a hyphen, followed by the last letter.",
    "Write the word tunnel without its first and last letters.",
    "Say whether “level” is a palindrome. Answer only with yes or no.",
    "Name a month with 31 days, but do not use the letter a.",
    "How many r’s are in strawberry?",
    "How many p’s are in Mississippi?",
    "What is the third character in the string: a9#k2?",
    "Return only the middle letter of radar.",
    "Which is correct: “There are 2 r’s in strawberry” or “There are 3 r’s in strawberry”?",
    "Count the letters in bookkeeper and also count how many are repeated.",
    "Write banana in reverse, then say whether the reverse is a real English word.",
    "Respond with the first, third, and fifth letters of apple.",
    "Remove all repeated letters from mississippi, keeping only first occurrences.",
    "Is the number of letters in twelve equal to the numeric value of twelve?"
]

SECTIONS = {
    0: "Character counting and positions",
    10: "Exact formatting traps",
    18: "Negation and instruction conflict",
    24: "Ordering and sequence tracking",
    30: "Simple logic with distracting phrasing",
    36: "Tokenization and spelling traps",
    42: "Multi-constraint prompts",
    48: "Good “gotcha” prompts specifically for local models"
}

st.set_page_config(page_title="Adversarial Prompts Tester", layout="wide")
st.title("🧪 Local LLM Adversarial Prompts Tester")
st.markdown("Run 58 gotcha prompts against your local Ollama models.")

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

with st.sidebar:
    st.header("⚙️ Configuration")
    base_url = st.text_input("Ollama Base URL", value="http://localhost:11434")
    model_name = st.selectbox("Model Name", get_ollama_models(base_url))

st.subheader("Select Prompts to Run")

# Initialize session state for the select_all master toggle
if "select_all" not in st.session_state:
    st.session_state.select_all = False

# Initialize session state for individual checkboxes
for i in range(len(PROMPTS)):
    if f"prompt_{i}" not in st.session_state:
        st.session_state[f"prompt_{i}"] = False

def toggle_all():
    val = st.session_state.select_all
    for i in range(len(PROMPTS)):
        st.session_state[f"prompt_{i}"] = val

# Select all checkbox
st.checkbox("Select/Deselect All Prompts", key="select_all", on_change=toggle_all)

st.markdown("---")

selected_indices = []
for i, prompt in enumerate(PROMPTS):
    if i in SECTIONS:
        st.markdown(f"#### {SECTIONS[i]}")
    if st.checkbox(f"{i+1}. {prompt}", key=f"prompt_{i}"):
        selected_indices.append(i)

save_to_md = st.checkbox("Save results to local_llm_test_results.md after the run", value=True)

col1, col2 = st.columns([1, 1])

with col1:
    run_btn = st.button("Run the Selected Prompts", type="primary")

with col2:
    if st.button("Reset and Clear"):
        st.session_state.clear()
        st.rerun()

if run_btn:
    if not selected_indices:
        st.warning("Please select at least one prompt.")
    else:
        st.info(f"Running {len(selected_indices)} prompts on {model_name}...")
        
        results_container = st.container()
        
        total_tokens = 0
        total_duration = 0.0
        
        md_output = f"## Test Run\n- **Model:** {model_name}\n- **Time:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        expected_answers = load_expected_answers()
        score_count = 0
        failed_prompts = []
        
        for idx in selected_indices:
            prompt_text = PROMPTS[idx]
            
            with results_container:
                st.markdown(f"**Prompt {idx+1}:** {prompt_text}")
                
            start_wall_time = time.time()
            try:
                url = f"{base_url.rstrip('/')}/api/generate"
                data = {
                    "model": model_name,
                    "prompt": prompt_text,
                    "stream": False,
                    "context": []
                }
                response = requests.post(url, json=data)
                response.raise_for_status()
                res_json = response.json()
                
                answer = res_json.get("response", "")
                eval_count = res_json.get("eval_count", 0)
                eval_duration_ns = res_json.get("eval_duration", 0)
                
                wall_time = time.time() - start_wall_time
                
                if eval_duration_ns > 0:
                    eval_duration_s = eval_duration_ns / 1e9
                    tokens_per_sec = eval_count / eval_duration_s
                    total_tokens += eval_count
                    total_duration += eval_duration_s
                else:
                    # Fallback if no specific eval metrics are present
                    approx_tokens = len(answer.split())
                    tokens_per_sec = approx_tokens / wall_time if wall_time > 0 else 0
                    total_tokens += approx_tokens
                    total_duration += wall_time
                    
                with results_container:
                    st.success(f"⏱️ Time elapsed: {wall_time:.2f} s | ⚡ Speed: {tokens_per_sec:.2f} tokens/s")
                    
                    eval_msg = ""
                    idx_1_based = idx + 1
                    if idx_1_based in expected_answers:
                        expected = expected_answers[idx_1_based]
                        is_correct = evaluate_response(expected, answer)
                        if is_correct:
                            score_count += 1
                            eval_msg = f"✅ **Passed** (Expected: {expected})"
                        else:
                            failed_prompts.append(idx_1_based)
                            eval_msg = f"❌ **Failed** (Expected: {expected})"
                        st.markdown(eval_msg)
                        
                    st.markdown(f"**Response {idx+1}:**")
                    st.write(answer)
                    st.markdown("---")
                
                md_output += f"### Prompt {idx+1}\n{prompt_text}\n\n"
                md_output += f"**Time elapsed:** {wall_time:.2f} s | **Speed:** {tokens_per_sec:.2f} tokens/s\n"
                if eval_msg:
                    md_output += f"{eval_msg}\n\n"
                else:
                    md_output += "\n"
                md_output += f"### Response {idx+1}\n{answer}\n\n---\n\n"
                    
            except Exception as e:
                with results_container:
                    st.error(f"Error executing prompt: {e}")
                    st.markdown("---")
                md_output += f"### Prompt {idx+1}\n{prompt_text}\n\n**Error:** {e}\n\n---\n\n"
                    
        st.markdown("### Process Complete")
        
        if expected_answers and selected_indices:
            final_score = f"🏆 **Final Score:** {score_count} / {len(selected_indices)} passed"
            if failed_prompts:
                failed_str = ", ".join(map(str, failed_prompts))
                final_score += f" | Failed Prompts: {failed_str}"
            st.info(final_score)
            md_output += f"**{final_score}**\n\n"
            
        if total_duration > 0:
            avg_tps = total_tokens / total_duration
            st.info(f"📊 **Average Token Generation Speed:** {avg_tps:.2f} tokens/second")
            md_output += f"**📊 Average Token Generation Speed:** {avg_tps:.2f} tokens/second\n\n"
        else:
            st.info("📊 **Average Token Generation Speed:** N/A")
            md_output += f"**📊 Average Token Generation Speed:** N/A\n\n"
            
        if save_to_md:
            try:
                with open("d:\\Dev\\AntiGravity\\LLMTest\\local_llm_test_results.md", "a", encoding="utf-8") as f:
                    f.write(md_output)
                st.success("💾 Results successfully appended to `d:\\Dev\\AntiGravity\\LLMTest\\local_llm_test_results.md`!")
            except Exception as e:
                st.error(f"Could not save results: {e}")
