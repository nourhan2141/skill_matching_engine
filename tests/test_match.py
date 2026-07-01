import pytest
import os
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

# Ensure API key is set for tests before importing the app
os.environ["APP_API_KEY"] = "test-secret-key"
os.environ["GROQ_API_KEY"] = "test-groq-key"

from app.main import app

client = TestClient(app)

MOCK_CV_JSON = {
    "name": "Jane Doe",
    "contact": {"email": "[PROVIDED]"},
    "skills": [" Python ", "python", "Django", "SQL", "pytest"],
    "experience_years": 4.5,
    "education": [{"degree": "BSc Computer Science"}],
    "preferences": {}
}

MOCK_JOB_JSON = {
    "title": "Backend Developer",
    "mandatory_skills": ["python", "django", "SQL"],
    "nice_to_have_skills": ["docker", "AWS"],
    "experience_years_required": 3.0,
    "education_required": "BSc",
    "logistics": {}
}

MOCK_MATCH_JSON = {
    "match_analysis": "Jane meets all requirements...",
    "score_details": {
        "hard_skills_score": 40,
        "experience_score": 30,
        "soft_skills_score": 20,
        "logistics_score": 10
    },
    "total_score": 100,
    "explanation": "Perfect match.",
    "key_matched_skills": ["python", "django", "sql"],
    "missing_skills": [],
    "recommendation": "Hire immediately."
}

async def fake_generate_json(prompt, *args, **kwargs):
    if "extract the candidate's base profile" in prompt:
        return MOCK_CV_JSON
    elif "extract every single skill" in prompt:
        return {"skills": MOCK_CV_JSON["skills"]}
    elif "parse the following Job Description text" in prompt:
        return MOCK_JOB_JSON
    else:
        return MOCK_MATCH_JSON

@pytest.fixture
def mock_dependencies():
    with patch("app.api.routes.match.generate_json", new=AsyncMock(side_effect=fake_generate_json)) as mock_gen, \
         patch("app.api.routes.match.extract_cv_text_robust", return_value="Dummy CV Text") as mock_pdf:
        yield mock_gen, mock_pdf

def test_missing_api_key():
    response = client.post(
        "/match/upload",
        files={"cv_file": ("dummy.pdf", b"dummy content", "application/pdf")},
        data={"job_description": "Dummy JD"}
    )
    assert response.status_code == 403
    assert "Could not validate API key" in response.text

def test_match_endpoint_success(mock_dependencies):
    headers = {"X-API-Key": "test-secret-key"}
    response = client.post(
        "/match/upload",
        headers=headers,
        files={"cv_file": ("test_cv.pdf", b"dummy content", "application/pdf")},
        data={"job_description": "We need a Backend Dev"}
    )

    assert response.status_code == 200, response.text
    data = response.json()
    
    # Assert Score bounds and existence
    match_result = data["match_result"]
    assert match_result["total_score"] == 100
    assert match_result["score_details"]["hard_skills_score"] <= 40
    assert "explanation" in match_result
    
    # Assert Normalization of skills (deduplicated, stripped, preserved casing)
    parsed_candidate = data["parsed_candidate"]
    skills = parsed_candidate["skills"]
    assert "Django" in skills
    assert "django" not in skills
    # " Python " was in list, "python" was in list -> should just have "Python" once
    assert skills.count("Python") == 1
    assert "python" not in skills
    assert parsed_candidate["experience_years"] == 4.5
    
    # Check that education typed model parsed correctly
    assert len(parsed_candidate["education"]) == 1
    assert parsed_candidate["education"][0]["degree"] == "BSc Computer Science"

def test_oversized_cv():
    headers = {"X-API-Key": "test-secret-key"}
    # Create 6MB payload (over the 5MB limit)
    large_bytes = b"x" * (6 * 1024 * 1024)
    response = client.post(
        "/match/upload",
        headers=headers,
        files={"cv_file": ("large.pdf", large_bytes, "application/pdf")},
        data={"job_description": "We need a Backend Dev"}
    )
    assert response.status_code == 400
    assert "exceeds the maximum allowed size" in response.text

def test_bracket_injection_in_cv():
    from app.services.prompts import PromptBuilder
    cv_with_brackets = "I love {curly_braces} and {current_year}"
    prompt = PromptBuilder.build_cv_base_parsing_prompt(cv_with_brackets)
    assert "{curly_braces}" in prompt
