from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form, Request
from pydantic import ValidationError
from app.schemas.match import JobMatchResponse, CandidateProfile, JobMatchResult, JobProfile
from app.services.prompts import PromptBuilder
from app.core.llm import generate_json
from app.services.pdf_parser import extract_cv_text_robust
from app.services.ocr_service import extract_text_from_image
from app.core.config import MAX_CV_SIZE_BYTES, MAX_JD_CHARS, MAX_IMAGE_SIZE_BYTES, GROQ_EXTRACTION_MODEL
import logging
import asyncio

from app.core.limiter import limiter

router = APIRouter()

async def perform_match(cv_text: str, job_description: str) -> JobMatchResponse:
    """
    Evaluates a candidate's CV against a target job description in three steps:
    1. Extract CV text into a structured profile.
    2. Extract Job Description text into a structured profile.
    3. Evaluate the profiles against each other using a rubric.
    """
    cv_base_prompt = PromptBuilder.build_cv_base_parsing_prompt(cv_text)
    cv_skills_prompt = PromptBuilder.build_cv_skills_parsing_prompt(cv_text)
    job_prompt = PromptBuilder.build_job_parsing_prompt(job_description)

    try:
        # Steps 1 & 2: Parse CV (base and skills separately) and Job Description concurrently
        cv_base_json, cv_skills_json, job_json = await asyncio.gather(
            generate_json(cv_base_prompt, model_name=GROQ_EXTRACTION_MODEL),
            generate_json(cv_skills_prompt, model_name=GROQ_EXTRACTION_MODEL, max_tokens=8192),
            generate_json(job_prompt, model_name=GROQ_EXTRACTION_MODEL)
        )
        
        # Merge the two CV parsing results
        cv_json = {**cv_base_json, **cv_skills_json}
    except Exception:
        logging.exception("Error communicating with LLM during parsing")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred communicating with the AI service during parsing."
        )

    try:
        parsed_candidate = CandidateProfile(**cv_json)
    except ValidationError as ve:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, 
            detail=f"Failed to parse CV into expected structure: {str(ve)}"
        )

    try:
        parsed_job = JobProfile(**job_json)
    except ValidationError as ve:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, 
            detail=f"Failed to parse Job Description into expected structure: {str(ve)}"
        )

    try:
        # Step 3: Evaluate Match
        match_prompt = PromptBuilder.build_job_matching_prompt(
            candidate_profile=parsed_candidate.model_dump_json(),
            job_profile=parsed_job.model_dump_json()
        )
        match_json = await generate_json(match_prompt)
        match_result = JobMatchResult.model_validate(match_json)
    except ValidationError as ve:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, 
            detail=f"Failed to parse evaluation result into expected structure: {str(ve)}"
        )
    except Exception:
        logging.exception("Error communicating with LLM during job evaluation")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred communicating with the AI service during job evaluation."
        )

    # Return the combined response
    return JobMatchResponse(
        parsed_candidate=parsed_candidate,
        parsed_job=parsed_job,
        match_result=match_result
    )


@router.post("/match/upload", response_model=JobMatchResponse, status_code=status.HTTP_200_OK)
@limiter.limit("10/minute")
async def match_candidate_to_job_upload(
    request: Request,
    cv_file: UploadFile = File(..., description="Candidate CV as a PDF file"),
    job_description: str = Form(None, json_schema_extra={"format": "textarea"}, description="Job description as plain text (paste directly)"),
    job_description_image: UploadFile = File(None, description="Job description as a screenshot/image (PNG, JPEG, WEBP). Used when text is not available.")
):
    """
    Match a candidate's CV PDF against a job description.
    The job description can be provided in one of two ways:
    - **job_description**: Paste the full text directly.
    - **job_description_image**: Upload a screenshot of the job posting (PNG/JPEG/WEBP).
      The image will be processed via OCR to extract the text automatically.
    
    Exactly one of `job_description` or `job_description_image` must be provided.
    """
    # --- Validate CV file ---
    if not cv_file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported for the CV.")

    file_bytes = await cv_file.read()
    
    if len(file_bytes) > MAX_CV_SIZE_BYTES:
        raise HTTPException(status_code=400, detail="CV file exceeds the maximum allowed size (5MB).")

    try:
        cv_text = await extract_cv_text_robust(file_bytes)
    except Exception as e:
        logging.exception("Failed to read PDF file")
        raise HTTPException(status_code=400, detail="Failed to read PDF file. Please ensure it is a valid PDF.")

    # --- Resolve job description text ---
    jd_text: str | None = None

    # Priority 1: pasted text
    if job_description and job_description.strip():
        jd_text = job_description.strip()

    # Priority 2: image OCR
    elif job_description_image is not None:
        allowed_image_types = {"image/png", "image/jpeg", "image/jpg", "image/webp", "image/gif"}
        content_type = job_description_image.content_type or "image/png"

        if content_type not in allowed_image_types:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported image format '{content_type}'. Accepted formats: PNG, JPEG, WEBP."
            )

        image_bytes = await job_description_image.read()
        if not image_bytes:
            raise HTTPException(status_code=400, detail="The uploaded job description image is empty.")
            
        if len(image_bytes) > MAX_IMAGE_SIZE_BYTES:
            raise HTTPException(status_code=400, detail="Job description image exceeds the maximum allowed size (10MB).")

        try:
            jd_text = await extract_text_from_image(image_bytes, content_type)
        except Exception:
            logging.exception("OCR failed to extract text from the job description image")
            raise HTTPException(
                status_code=500,
                detail="OCR failed to extract text from the job description image."
            )

        if not jd_text or not jd_text.strip():
            raise HTTPException(
                status_code=422,
                detail="OCR could not extract any readable text from the provided image. Please ensure the image is clear and contains legible text, or paste the job description as text instead."
            )

    else:
        raise HTTPException(
            status_code=400,
            detail="You must provide either 'job_description' (text) or 'job_description_image' (screenshot). Neither was supplied."
        )

    if jd_text and len(jd_text) > MAX_JD_CHARS:
        raise HTTPException(status_code=400, detail="Job description exceeds the maximum allowed character count.")

    return await perform_match(cv_text, jd_text)
