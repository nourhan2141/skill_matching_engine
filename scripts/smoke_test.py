import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000/match/upload")
API_KEY = os.getenv("APP_API_KEY", "your_app_api_key_here")

def main():
    print(f"Starting smoke test against {API_URL}...")
    for i in range(1, 6):
        cv_file = f"tests/data/cvs/cv_{i}.pdf"
        jd_file = f"tests/data/jobs/jd_{i}.txt"
        
        print("\n" + "="*80)
        print(f"RUNNING SMOKE TEST PAIR {i}")
        print("="*80)
        
        if os.path.exists(cv_file) and os.path.exists(jd_file):
            try:
                with open(jd_file, 'r', encoding='utf-8') as f:
                    job_text = f.read()
                    
                with open(cv_file, 'rb') as pdf_file:
                    files = {'cv_file': (cv_file, pdf_file, 'application/pdf')}
                    data = {'job_description': job_text}
                    headers = {"X-API-Key": API_KEY}
                    
                    response = requests.post(API_URL, headers=headers, files=files, data=data)
                    
                if response.status_code == 200:
                    resp_json = response.json()
                    match_res = resp_json.get("match_result", {})
                    total_score = match_res.get("total_score")
                    missing = match_res.get("missing_skills", [])
                    print(f"[SUCCESS] Status 200 | Total Score: {total_score}")
                    print(f"          Missing Skills identified: {missing}")
                else:
                    print(f"[FAILED] Status {response.status_code} | Response: {response.text}")
                    
            except Exception as e:
                print(f"[-] Connection or request failed. Is the server running? Error: {e}")
        else:
            print(f"[-] Missing files for Pair {i} (checked {cv_file} and {jd_file})")

if __name__ == "__main__":
    main()
