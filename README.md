Watch the video from youtube.
https://www.youtube.com/watch?v=8JHDeBzVcmo

To run : streamlit run app.py


### New update ###
# Local LLM Adversarial Prompts Tester
To run : streamlit run llmtest.py

This Streamlit application provides a specialized testing interface to run local LLMs (via Ollama) against a curated set of 58 adversarial "gotcha" prompts. The app is designed to evaluate how well local models perform on tricky instructions, format constraints, counting tasks, and logic traps, and then rigorously score their output against expected answers.

## User Interaction Flow

1. **Configuration Setup**: 
    - Upon launching the app, the user configures the backend connection in the sidebar.  
    - They provide the base URL for the local Ollama instance (default: `http://localhost:11434`).
    - A dynamic dropdown automatically fetches and populates available models from the Ollama server. The user selects the model they wish to test.

2. **Prompt Selection**:
    - The main interface displays a categorized list of 58 adversarial prompts (e.g., character counting, exact formatting traps, negation traps).
    - The user can select specific prompts to run using individual checkboxes or use a master "Select/Deselect All Prompts" toggle to run the entire suite at once.

3. **Execution**:
    - The user can toggle whether to append the test results to a local Markdown file (`local_llm_test_results.md`).
    - The user clicks the **"Run the Selected Prompts"** button to start the evaluation.

4. **Monitoring Progress & Results**:
    - As the app executes, it iterates through the selected prompts.
    - Real-time updates appear on the screen, showing the wall-time elapsed and token generation speed (tokens/s) for each prompt.
    - Each model response is instantly evaluated against an expected answer. The UI displays whether the model passed `✅` or failed `❌`, along with the raw response text.
    - At the end of the run, a final score report is generated, displaying the total prompts passed, specific failed prompt numbers, and an overall average token generation speed across the entire run.

## End-to-End Process & Architecture

Behind the scenes, the application orchestrates several components to fetch, evaluate, and record the testing data:

### 1. Initialization and Data Loading
- **Expected Answers Parsing**: On startup, the app calls `load_expected_answers()`, which parses a local reference file (`prompts_answer_from_GPT56_Sol.md`). It uses regular expressions and string splitting to extract prompt numbers and their corresponding expected answers from a Markdown table, caching the outcome for efficiency.
- **Dynamic Model Retrieval**: The sidebar uses the `get_ollama_models()` function to make an HTTP GET request to the Ollama `/api/tags` endpoint. This returns a real-time list of installed model names, populating the Streamlit select box.

### 2. Execution Engine
When the "Run" button is clicked:
- The app iterates through the user's `selected_indices` array.
- For each prompt, it initiates a timer (`time.time()`).
- It constructs a JSON payload containing the selected model name and the prompt text, then makes a synchronous HTTP POST request to the Ollama `/api/generate` endpoint. (Streaming is set to `False` to capture the entire payload for easy timing and metric evaluation).

### 3. Metrics Calculation
- Once the response is received, the app extracts the generated answer, `eval_count` (tokens generated), and `eval_duration` from the JSON payload.
- It calculates the token generation speed (`tokens_per_sec = eval_count / eval_duration_s`).
- If Ollama fails to provide nanosecond evaluation durations, the app falls back to a manual metric calculation based on word counts and wall time.

### 4. Evaluation and Scoring
- The `evaluate_response(expected, actual)` function compares the model's raw string output to the parsed expected answer. 
- It uses a multi-tiered evaluation strategy:
    1. **Direct Substring Match**: Is the expected answer physically within the actual output?
    2. **Alphanumeric Cleaned Match**: Strips punctuation and spaces from both strings and checks for a match to bypass minor formatting inconsistencies.
    3. **Comma-Separated Validation**: If the expected answer implies multiple components, it ensures all required components exist in the actual response.
- Successes increment the `score_count`, while failures push the prompt ID to the `failed_prompts` array.

### 5. Final Compilation and Logging
- All metrics (time elapsed, tokens/s, prompt text, response text, pass/fail status) are iteratively concatenated into a large formatted Markdown string.
- The session is wrapped up by calculating the aggregate token speed and compiling the final scorecard.
- Finally, if `save_to_md` is ticked, the app appends the exhaustive run data directly to `local_llm_test_results.md` on the file system, acting as a permanent and traceable audit log for local model evaluation.
