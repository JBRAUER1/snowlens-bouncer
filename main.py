import os
import json
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
from dotenv import load_dotenv

# Clean, synced imports
from models import StyleRequest, CoachPreflightRequest, CoachMainRequest, PassRequest, AdjudicatorRequest
from prompts import get_agent1_prompts, get_agent2_prompts, get_adjudicator_prompts

load_dotenv()

# --- CLOUD SECRETS ---
MASTER_OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")

# We are hardcoding the fallback URL right here. 
# Replace the https link with your actual Supabase URL.
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://your-project.supabase.co")

SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") 

# Add this print statement so we can spy on Railway's logs
if not SUPABASE_SERVICE_KEY:
    print("CRITICAL DIAGNOSTIC: Railway is completely failing to inject the secret variables!")

# Initialize Supabase Client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# TEMPORARY BYPASS FOR SPRINT 3 TESTING
# Replace this string with the actual UID from Supabase
TEST_USER_ID = "09183802-6dde-46e2-bae5-c7bbdb871f5a"

app = FastAPI(title="Snow Lens Rosenbridge Proxy")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 66% PROFIT MARGIN MATH ---
MODEL_PRICING = {
    "anthropic/claude-3.5-sonnet": {"in": 3.00, "out": 15.00},
    "openai/gpt-4o": {"in": 2.50, "out": 10.00},
    "mistralai/mistral-large-2407": {"in": 2.00, "out": 6.00},
    "google/gemini-1.5-pro": {"in": 1.25, "out": 5.00},
    "meta-llama/llama-3.1-405b-instruct": {"in": 3.00, "out": 3.00}
}

def verify_and_deduct_credits(login_key: str, prompt_tokens: int, completion_tokens: int, ai_model: str):
    """Checks user balance, calculates the 66% marked-up cost, and deducts the float."""
    # BYPASS: Ignore frontend login_key, force lookup by hardcoded TEST_USER_ID
    user_res = supabase.table("users").select("id, compute_balance").eq("id", TEST_USER_ID).execute()
    if not user_res.data:
        raise HTTPException(status_code=401, detail="Invalid Login Key.")
    
    user = user_res.data[0]
    current_balance = float(user['compute_balance'])
    
    if current_balance <= 0:
        raise HTTPException(status_code=402, detail="Insufficient Compute Credits. Please refill.")

    rates = MODEL_PRICING.get(ai_model, {"in": 3.00, "out": 15.00})
    cost_in = (prompt_tokens / 1000000) * rates["in"]
    cost_out = (completion_tokens / 1000000) * rates["out"]
    raw_cost_dollars = cost_in + cost_out

    credits_to_deduct = (raw_cost_dollars * 100) * 3.0 

    new_balance = max(0.0, current_balance - credits_to_deduct)
    supabase.table("users").update({"compute_balance": new_balance}).eq("id", user['id']).execute()

def repair_broken_json(content: str) -> str:
    if not content: return "{}"
    content = content.strip()
    if content.startswith("```json"): content = content.replace("```json", "", 1)
    if content.endswith("```"): content = content[::-1].replace("```", "", 1)[::-1]
    content = content.strip()
    if content.rstrip().endswith(','): content = content.rstrip(',')
    
    if '"suggestions": [' in content:
        if not content.endswith('}'):
            if not content.endswith(']'): content += ']'
            content += '}'
    elif content.startswith('[') and not content.endswith(']'):
        last_brace = content.rfind('}')
        if last_brace != -1: content = content[:last_brace+1] + ']'
            
    return content

def extract_valid_json_objects(text: str) -> list:
    results = []
    decoder = json.JSONDecoder()
    pos = 0
    while True:
        pos = text.find('{', pos)
        if pos == -1: break
        try:
            obj, next_pos = decoder.raw_decode(text, pos)
            results.append(obj)
            pos = next_pos
        except json.JSONDecodeError:
            pos += 1
    return results

def call_openrouter(ai_model: str, messages: list, login_key: str, **kwargs):
    """The central routing tunnel. Handles OpenRouter call AND financial math."""
    # BYPASS: Ignore frontend login_key, force lookup by hardcoded TEST_USER_ID
    user_res = supabase.table("users").select("compute_balance").eq("id", TEST_USER_ID).execute()
    if not user_res.data or float(user_res.data[0]['compute_balance']) <= 0:
        raise HTTPException(status_code=402, detail="Insufficient Compute Credits or Invalid Key.")

    headers = {
        "Authorization": f"Bearer {MASTER_OPENROUTER_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://snowlensapp.com",
        "X-Title": "SnowLens Bouncer"
    }
    
    payload = {"model": ai_model, "messages": messages, **kwargs}
    res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
    
    if res.status_code != 200:
        raise HTTPException(status_code=res.status_code, detail=res.text)
        
    data = res.json()
    
    usage = data.get('usage', {})
    prompt_tokens = usage.get('prompt_tokens', 0)
    completion_tokens = usage.get('completion_tokens', 0)
    
    verify_and_deduct_credits(login_key, prompt_tokens, completion_tokens, ai_model)
    
    return data['choices'][0]['message']['content']

# ==========================================
# AGENT 1: STYLE MANIFESTO ENDPOINT
# ==========================================
@app.post("/api/v1/proxy/analyze_style")
def proxy_analyze_style(req: StyleRequest):
    try:
        prompts = get_agent1_prompts(req.ai_model, req.stats, req.genre_tags, req.profile)
        
        manifesto_raw = call_openrouter(
            ai_model=req.ai_model,
            messages=[{"role": "user", "content": prompts["prompt_a"]}],
            login_key=req.api_key
        )
        
        final_prompt_b = prompts["prompt_b"].format(manifesto=manifesto_raw)
        compressed_raw = call_openrouter(
            ai_model=req.ai_model,
            messages=[{"role": "user", "content": final_prompt_b}],
            login_key=req.api_key,
            max_tokens=600
        )
        
        return {
            "manifesto": manifesto_raw,
            "compressed_tags": compressed_raw
        }
    except HTTPException:
        raise
    except Exception as e:
        return {"error": "Pipeline Failure", "details": str(e)}

# ==========================================
# AGENT 2: COACH 2-PASS ENDPOINTS
# ==========================================
@app.post("/api/v1/proxy/coach-preflight")
def proxy_coach_preflight(req: CoachPreflightRequest):
    prompts = get_agent2_prompts("coach", req.ai_model, "", 0, "")
    idx_task = prompts.get("idx_task", "Summarize narrative context.")
    
    messages = [{"role": "user", "content": f"{req.chunk_text}\n\nTASK: {idx_task}"}]
    try:
        res_text = call_openrouter(req.ai_model, messages, req.api_key, response_format={"type": "json_object"})
        context = json.dumps(json.loads(res_text))
        return {"narrative_context": context}
    except HTTPException:
        raise
    except:
        return {"narrative_context": "Summary unavailable."}

@app.post("/api/v1/proxy/coach-main")
def proxy_coach_main(req: CoachMainRequest):
    prompts = get_agent2_prompts("coach", req.ai_model, req.constraints, req.limit, "", None, req.narrative_context)
    
    messages = [
        {"role": "system", "content": prompts["sys_prompt"]},
        {"role": "user", "content": f"{req.chunk_text}\n\n====================\nCURRENT TASK:\n{prompts['task_discovery']}"}
    ]
    
    try:
        res_text = call_openrouter(req.ai_model, messages, req.api_key, response_format={"type": "json_object"})
        res_text = repair_broken_json(res_text)
        
        try:
            data = json.loads(res_text)
        except json.JSONDecodeError:
            data = {"suggestions": extract_valid_json_objects(res_text)}

        suggestions = data if isinstance(data, list) else data.get("suggestions", [])
        if not suggestions:
            for val in data.values():
                if isinstance(val, list):
                    suggestions = val
                    break
        return {"suggestions": suggestions}
    except HTTPException:
        raise
    except Exception as e:
        print(f"--- [BOUNCER CRASH REPORT] --- {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# AGENT 2: STANDARD PASS ENDPOINT
# ==========================================
@app.post("/api/v1/proxy/run-pass")
def proxy_run_pass(req: PassRequest):
    prompts = get_agent2_prompts(req.active_tool, req.ai_model, req.constraints, req.limit, req.exclusion)
    
    messages = [
        {"role": "system", "content": prompts["sys_prompt"]},
        {"role": "user", "content": f"{req.chunk_text}\n\n====================\nCURRENT TASK:\n{prompts['task_discovery']}"}
    ]
    
    try:
        res_text = call_openrouter(req.ai_model, messages, req.api_key, response_format={"type": "json_object"})
        res_text = repair_broken_json(res_text)
        
        try:
            data = json.loads(res_text)
        except json.JSONDecodeError:
            data = {"suggestions": extract_valid_json_objects(res_text)}

        suggestions = data if isinstance(data, list) else data.get("suggestions", [])
        if not suggestions:
            for val in data.values():
                if isinstance(val, list):
                    suggestions = val
                    break
        return {"suggestions": suggestions}
    except HTTPException:
        raise
    except Exception as e:
        print(f"--- [BOUNCER CRASH REPORT] --- {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# ADJUDICATOR: COMPOUND SYNTHESIS ENDPOINT
# ==========================================
@app.post("/api/v1/proxy/adjudicator")
def proxy_adjudicator(req: AdjudicatorRequest):
    prompts = get_adjudicator_prompts(req.ai_model, req.manuscript_snippet, req.critiques_list)
    
    messages = [
        {"role": "system", "content": prompts["sys_syn"]},
        {"role": "user", "content": prompts["base_prompt"]}
    ]
    
    try:
        res_text = call_openrouter(req.ai_model, messages, req.api_key, response_format={"type": "json_object"})
        res_text = repair_broken_json(res_text)
        
        try:
            data = json.loads(res_text)
        except json.JSONDecodeError:
            # Adjudicator returns a single object, so we extract the first valid object found
            extracted = extract_valid_json_objects(res_text)
            data = extracted[0] if extracted else {"suggested": "", "critique": "Failed to parse adjudicator response."}
            
        return data
    except HTTPException:
        raise
    except Exception as e:
        print(f"--- [BOUNCER CRASH REPORT] --- {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))