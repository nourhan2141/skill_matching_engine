import argparse
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

def load_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

def main(cv_pdf_path, job_txt_path):
    api_url_base = os.getenv("API_URL", "http://127.0.0.1:8000")
    url = f"{api_url_base}/match/upload"
    
    try:
        job_text = load_file(job_txt_path)
    except Exception as e:
        print(f"[-] Error reading job text file: {e}")
        return
        
    print(f"[*] Evaluating CV (PDF): {cv_pdf_path}")
    print(f"[*] Against Job (TXT):   {job_txt_path}")
    print("[*] Sending request to FastAPI upload endpoint...")
    
    try:
        with open(cv_pdf_path, 'rb') as pdf_file:
            files = {
                'cv_file': (cv_pdf_path, pdf_file, 'application/pdf')
            }
            data = {
                'job_description': job_text
            }
            headers = {
                'X-API-Key': os.getenv("APP_API_KEY", "your_app_api_key_here")
            }
            
            response = requests.post(url, headers=headers, files=files, data=data)
            print(f"[*] Status Code: {response.status_code}")
            
            if response.status_code == 200:
                print("\nSUCCESS! Here is the evaluation report:")
                resp_data = response.json()
                match = resp_data.get("match_result", {})
                scores = match.get("score_details", {})
                
                print("\n" + "="*60)
                print(f"[*] TOTAL MATCH SCORE: {match.get('total_score', 0)} / 100")
                print("="*60)
                
                print("\n[+] SCORE BREAKDOWN:")
                print(f"  - Hard Skills Fit:       {scores.get('hard_skills_score', 0)} / 40")
                print(f"  - Experience Level:      {scores.get('experience_score', 0)} / 30")
                print(f"  - Soft Skills & Domain:  {scores.get('soft_skills_score', 0)} / 20")
                print(f"  - Logistics & Prefs:     {scores.get('logistics_score', 0)} / 10")
                
                print("\n[*] EXPLANATION:")
                print(f"  {match.get('explanation', '')}")
                
                print("\n[+] KEY STRENGTHS:")
                for s in match.get('key_matched_skills', []):
                    print(f"  + {s}")
                    
                print("\n[-] MISSING SKILLS / WEAKNESSES:")
                if match.get('missing_skills'):
                    for m in match.get('missing_skills', []):
                        print(f"  - {m}")
                else:
                    print("  (None identified)")
                    
                print("\n[>] RECOMMENDATION:")
                print(f"  {match.get('recommendation', '')}")
                
                print("\n" + "="*60)
            else:
                print("\nERROR response from server:")
                print(json.dumps(response.json(), indent=2))
            
    except Exception as e:
        print(f"[-] Failed to connect to the server: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test the AI Career Coach matcher with a PDF CV.")
    parser.add_argument("--cv", default="tests/data/cvs/cv_1.pdf", help="Path to CV PDF file")
    parser.add_argument("--job", default="tests/data/jobs/jd_1.txt", help="Path to Job TXT file")
    args = parser.parse_args()
    
    main(args.cv, args.job)
