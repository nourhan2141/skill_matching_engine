CV_BASE_PARSING_PROMPT = """
You are an expert technical recruiter and career coach. Your task is to parse the following CV text and extract the candidate's base profile into a structured JSON format.

IMPORTANT PRIVACY RULE: Disregard private personal data (like the actual name, email, and phone number) to protect PII. However, you must acknowledge that they exist in the document.
- For "name", output "[PROVIDED]" if a name exists, otherwise null.
- For "contact" object values, output "[PROVIDED]" if the email or phone is present, otherwise null. Do not extract the actual email or phone number.

Extract the following fields:
- "name": string (follow privacy rule)
- "contact": object with email and phone (follow privacy rule)
- "experience_years": float (Calculate total years of experience by summing the durations of all roles. For roles marked "present", assume the current year is {current_year})
- "education": list of objects (e.g., [{"degree": "BSc Computer Science", "institution": "Cairo University", "year": "2019"}])
- "preferences": object with keys "roles" (list), "locations" (list), and "remote" (string) (e.g., {"roles": ["Backend Developer"], "locations": ["Cairo", "Remote"], "remote": "hybrid"})

CV Text:
{cv_text}

Output ONLY valid JSON.
"""

CV_SKILLS_PARSING_PROMPT = """
You are an expert technical recruiter. Your ONLY task is to meticulously extract every single skill from the following CV text.

Extract the following field:
- "skills": list of strings. You MUST meticulously extract EVERY SINGLE programming language, framework, database, tool, and soft skill mentioned anywhere in the CV (e.g., Python, Django, React, PostgreSQL). Do not generalize; list each specific technology. Pay special attention to short-named languages that are easy to miss, such as 'Go' (or 'Golang'), 'R', 'C', and 'C++'.

CRITICAL INSTRUCTION: You MUST scan every single section of the resume. Do NOT just look for a dedicated "Skills" section. You must extract skills mentioned in the Summary, within every Work Experience bullet point, inside Project descriptions, and Certifications. Leave no skill behind.

CV Text:
{cv_text}

Output ONLY valid JSON.
"""

JOB_PARSING_PROMPT = """
You are an expert technical recruiter. Your task is to parse the following Job Description text and extract the requirements into a structured JSON format.

CRITICAL INSTRUCTIONS FOR UNFORMATTED TEXT:
The input text may have lost its original line breaks, bullet points, and formatting (appearing as a single run-on paragraph). You MUST rely on lexical and semantic cues rather than layout to distinguish requirement tiers:
- MANDATORY CUES: "required", "must have", "minimum", "essential", "needs", "proficient in" -> Extract to "mandatory_skills".
- PREFERRED CUES: "nice to have", "preferred", "a plus", "bonus", "ideally", "advantage" -> Extract to "nice_to_have_skills".
- FALLBACK RULE: If no lexical cue exists for a given skill mention (i.e. it is just listed with no qualifying language), you MUST default it to "mandatory_skills" rather than "nice_to_have_skills".

Extract the following fields:
- "title": string
- "mandatory_skills": list of strings (strict must-have skills, excluding experience/education)
- "nice_to_have_skills": list of strings (bonus/preferred skills, e.g., "strong plus", "preferred", "nice to have")
- "experience_years_required": float (minimum years required)
- "education_required": string
- "logistics": object with keys "location" (string), "remote" (string), and "timezone" (string) (e.g., {"location": "Cairo", "remote": "hybrid", "timezone": "GMT+2"})

FEW-SHOT EXAMPLE (Handling unformatted text):
Input: "We are looking for a Senior Developer proficient in Python and React. 5 years of experience required. AWS is a strong plus. Must have experience with PostgreSQL."
Output:
{
  "title": "Senior Developer",
  "mandatory_skills": ["Python", "React", "PostgreSQL"],
  "nice_to_have_skills": ["AWS"],
  "experience_years_required": 5.0,
  "education_required": "",
  "logistics": {"location": "", "remote": "", "timezone": ""}
}

Job Description Text:
{job_text}

Output ONLY valid JSON.
"""

JOB_MATCHING_PROMPT = """
You are an expert Principal Technical Recruiter and Career Coach. 
Your objective is to evaluate a candidate's profile against a target job description and provide a strictly structured, objective scoring analysis.

You will be provided with:
1. `Candidate Profile`: A structured JSON representation of the candidate's skills, experience, and preferences.
2. `Job Profile`: A structured JSON representation of the target role requirements.

Candidate Profile (JSON):
{candidate_profile}

Job Profile (JSON):
{job_profile}

## Evaluation Rubric (100 Points Total)

You MUST score the candidate using the exact point allocations below. You cannot exceed the max points per category.

### 1. Hard Skills Fit (Max 40 points)
- **Full Match (40 pts):** Candidate possesses all mandatory technical skills and core tools.
- **Partial Match (20-39 pts):** Missing 1-2 core skills, but possesses highly transferable skills.
- **Poor Match (0-19 pts):** Missing the majority of mandatory core technical skills.

### 2. Experience Level Fit (Max 30 points)
- **Full Match (30 pts):** Total years of relevant domain experience meets or exceeds the requirement.
- **Partial Match (15-29 pts):** Experience is slightly below the requirement, or high but in an adjacent domain.
- **Poor Match (0-14 pts):** Experience is far below the requirement or completely irrelevant.

### 3. Soft Skills & Domain Knowledge (Max 20 points)
- **Full Match (20 pts):** Explicit evidence of required leadership, communication, or industry domain knowledge.
- **Partial Match (10-19 pts):** Implicit or vague evidence of soft skills.
- **Poor Match (0-9 pts):** No evidence of requested soft skills.

### 4. Career Preferences & Logistics (Max 10 points)
- **Full Match (10 pts):** Explicit alignment with job model (e.g., remote, timezone) and career trajectory.
- **Mismatch (0 pts):** Explicit conflict (e.g., candidate wants remote, job is strictly on-site).

## Final Score Calculation
Your final total score MUST EXACTLY equal the sum of the four categories:
`Total Score = Hard Skills + Experience + Soft Skills + Logistics`

## Evaluation Process
Before scoring, you MUST provide a detailed step-by-step analysis in the `match_analysis` field:
1. Compare the candidate's `experience_years` against the job's `experience_years_required` and state whether it meets/exceeds the requirement or falls short.
2. Explicitly compare the candidate's skills list against BOTH the job's mandatory skills AND nice-to-have skills step-by-step. You MUST map synonyms, abbreviations, and closely related functional skills to each other (e.g., "K8s" matches "Kubernetes", "Node" matches "Node.js", "Go" matches "Golang"). Treat highly related concepts, abbreviations, and synonyms as full matches rather than missing skills. Do not hallucinate missing skills if they exist in the candidate's profile.
3. When populating the `key_matched_skills` array in the JSON, you MUST ONLY include candidate skills that specifically match the job's mandatory or nice-to-have requirements. Do NOT simply list the candidate's entire skill set.
4. When populating the `missing_skills` array, you MUST cross-reference each missing skill against the candidate's skills list. NEVER list a skill in "missing_skills" if it exists in the candidate's profile as a synonym, abbreviation, or slight variation (e.g., do not list "Go" as missing if the candidate has "Golang"). NEVER list experience requirements (e.g., "4+ years") in this array.

## Output Format Constraints

You must output your evaluation strictly as a valid JSON object matching the following schema. Do not include markdown formatting like ```json.
{
  "match_analysis": "Detailed step-by-step comparison of each mandatory skill against candidate skills.",
  "score_details": {
    "hard_skills_score": integer,
    "experience_score": integer,
    "soft_skills_score": integer,
    "logistics_score": integer
  },
  "total_score": integer,
  "explanation": "Detailed paragraph explaining the rationale behind the scores.",
  "key_matched_skills": ["matched_skill_1", "matched_skill_2"],
  "missing_skills": ["missing_skill_1", "missing_skill_2"],
  "recommendation": "One or two actionable steps for the candidate to improve their fit."
}

## Example

**Candidate Profile:** {"skills": ["python", "fastapi"], "experience_years": 2.5}
**Job Profile:** {"mandatory_skills": ["python", "django"], "experience_years_required": 4.0}

**Output:**
{
  "match_analysis": "Candidate has 2.5 years of experience, falling short of the 4.0 required. The candidate possesses 'python' which matches the mandatory 'python' requirement, but completely lacks 'django'.",
  "score_details": {
    "hard_skills_score": 20,
    "experience_score": 15,
    "soft_skills_score": 10,
    "logistics_score": 10
  },
  "total_score": 55,
  "explanation": "The candidate is a partial match. They have Python but lack Django. Experience is 2.5 years, short of the required 4.",
  "key_matched_skills": ["python"],
  "missing_skills": ["django"],
  "recommendation": "Build a project in Django to meet the core framework requirement."
}
"""

from datetime import datetime

class PromptBuilder:
    @staticmethod
    def build_cv_base_parsing_prompt(cv_text: str) -> str:
        current_year = str(datetime.now().year)
        # Replace trusted/specific tokens first to prevent user input from overriding them
        prompt = CV_BASE_PARSING_PROMPT.replace("{current_year}", current_year)
        return prompt.replace("{cv_text}", cv_text)

    @staticmethod
    def build_cv_skills_parsing_prompt(cv_text: str) -> str:
        return CV_SKILLS_PARSING_PROMPT.replace("{cv_text}", cv_text)

    @staticmethod
    def build_job_parsing_prompt(job_text: str) -> str:
        return JOB_PARSING_PROMPT.replace("{job_text}", job_text)

    @staticmethod
    def build_job_matching_prompt(candidate_profile: str, job_profile: str) -> str:
        prompt = JOB_MATCHING_PROMPT.replace("{job_profile}", job_profile)
        return prompt.replace("{candidate_profile}", candidate_profile)
