import shutil
from fastapi import FastAPI, HTTPException, Form, UploadFile, File
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from typing import Dict, Optional
import os
import json
import requests
import tempfile
from datetime import datetime, timedelta
import subprocess
import base64
import itertools
import numpy as np
import sqlite3
from pathlib import Path
import logging
from fastapi.middleware.cors import CORSMiddleware
import main as main

# AI Proxy API settings
AIPROXY_URL = "http://aiproxy.sanand.workers.dev/openai/v1/chat/completions"
AIPROXY_TOKEN = os.getenv("AIPROXY_TOKEN")  # Replace with your actual token
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Use specific domains instead of "*" for security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Define a Pydantic model to handle the request body


function_names = {
    "get_vscode_output": main.get_vscode_output,
    "send_http_request": main.send_http_request,
    "compute_sha256sum": main.compute_sha256sum,
    "google_sheets_formula": main.google_sheets_formula,
    "excel_formula": main.excel_formula,
    "count_wednesdays": main.count_wednesdays,
    "sort_json": main.sort_json,
    "read_csv_answer": main.read_csv_answer,
    "convert_to_json": main.convert_to_json,
    "sum_data_values_from_html": main.sum_data_values_from_html,
    "sum_values_from_files": main.sum_values_from_files,
    "generate_github_raw_url": main.generate_github_raw_url,
    "process_and_hash_files": main.process_and_hash_files,
    "get_filtered_file_size": main.get_filtered_file_size,
    "process_and_rename_files": main.process_and_rename_files,
    "count_different_lines": main.count_different_lines,
    "calculate_gold_ticket_sales": main.calculate_gold_ticket_sales,
    "generate_step_analysis_markdown": main.generate_step_analysis_markdown,
    "compress_image_losslessly": main.compress_image_losslessly,
    "publish_github_page": main.publish_github_page,
    "run_google_colab_code": main.run_google_colab_code,
    "run_image_analysis_colab": main.run_image_analysis_colab,
    "deploy_marks_api": main.deploy_marks_api,
    "push_docker_image": main.push_docker_image,
    "serve_student_data": main.serve_student_data,
    "run_llamafile_with_ngrok": main.run_llamafile_with_ngrok,
    "count_tokens": main.count_tokens,
    "generate_us_addresses": main.generate_us_addresses,
    "extract_text_from_invoice": main.extract_text_from_invoice,
    "generate_text_embedding": main.generate_text_embedding,
    "most_similar": main.most_similar,
    "get_prompt_for_bypass": main.get_prompt_for_bypass,
    "count_ducks_from_cricinfo": main.count_ducks_from_cricinfo,
    "fetch_imdb_movies": main.fetch_imdb_movies,
    "get_wikipedia_outline": main.get_wikipedia_outline,
    "get_osaka_weather_forecast": main.get_osaka_weather_forecast,
    "get_max_latitude_khartoum": main.get_max_latitude_khartoum,
    "get_latest_self_hosting_hn_post": main.get_latest_self_hosting_hn_post,
    "get_newest_boston_user_with_followers": main.get_newest_boston_user_with_followers,
    "schedule_daily_commit": main.schedule_daily_commit,
    "calculate_economics_marks": main.calculate_economics_marks,
    "convert_pdf_to_markdown": main.convert_pdf_to_markdown,
    "calculate_total_margin": main.calculate_total_margin,
    "count_unique_students": main.count_unique_students,
    "count_successful_hindi_requests": main.count_successful_hindi_requests,
    "top_data_consumer_malayalam": main.top_data_consumer_malayalam,
    "total_shirt_sales_sao_paulo": main.total_shirt_sales_sao_paulo,
    "calculate_total_sales": main.calculate_total_sales,
    "count_qhb_key_occurrences": main.count_qhb_key_occurrences,
    "filter_and_sort_posts": main.filter_and_sort_posts,
    "transcribe_youtube_segment": main.transcribe_youtube_segment,
    "reconstruct_image": main.reconstruct_image
}

logger.info(AIPROXY_TOKEN)
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {AIPROXY_TOKEN}"
}
def save_upload_file_temp(file_storage) -> Optional[str]:
    """Save an uploaded file to a temporary file and return the path."""
    try:
        suffix = os.path.splitext(file_storage.filename)[1] if file_storage.filename else ""
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp:
            # file_storage.save(temp.name)
            shutil.copyfileobj(file_storage.file, temp)
            return temp.name
    except Exception as e:
        logger.error(f"Error saving upload file: {str(e)}")
        return None

def remove_temp_file(file_path: str) -> None:
    """Remove a temporary file."""
    try:
        if file_path and os.path.exists(file_path):
            os.unlink(file_path)
    except Exception as e:
        logger.error(f"Error removing temp file: {str(e)}")

def download_file_from_url(url: str) -> Optional[str]:
    """Download a file from a URL and save it to a temporary file."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        with tempfile.NamedTemporaryFile(delete=False) as temp:
            temp.write(response.content)
            return temp.name
    except requests.RequestException as e:
        logger.error(f"Error downloading file: {str(e)}")
        return None

class TaskRequest(BaseModel):
    task: str

@app.get("/status")
async def get_status():
    return "Application running"


@app.post("/run")
async def run_endpoint(task: str, file: UploadFile = File(None)):
    user_prompt = task
    
    print(file)

    uploaded_file_path = None
    if file:
        uploaded_file_path = save_upload_file_temp(file)
        print(uploaded_file_path)
        if not uploaded_file_path:
            raise HTTPException(status_code=500, detail="Failed to save uploaded file")

    if uploaded_file_path:
        user_prompt += " file path " + uploaded_file_path
    user_prompt += ". Give only function calls and parameters"
    payload = {
        "model": "gpt-4o-mini",
        "functions": list(main.functions),
        "function_call": "auto",
        "messages": [{"role": "user", "content": user_prompt}]
    }

    try:
        response = requests.post(AIPROXY_URL, headers=headers, json=payload)
        response.raise_for_status()
        response_json = response.json()
        print(response_json)

    except requests.exceptions.RequestException as e:
        print(str(e))
        raise HTTPException(status_code=500, detail=f"AI Proxy Request Failed: {str(e)}")

    if "choices" in response_json and response_json["choices"]:
        function_call = response_json["choices"][0]["message"].get("function_call")
        print(function_call)
        if function_call:
            function_name = function_call.get("name")
            try:
                function_args = json.loads(function_call.get("arguments"))
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid JSON arguments from AI response")

            print("Function Name:", function_name)
            print("Arguments:", function_args)

            # if uploaded_file_path:
            #     function_args["uploaded_file_path"] = uploaded_file_path

            if function_name not in function_names:
                raise HTTPException(status_code=400, detail=f"Unknown function: {function_name}")

            try:
                result = function_names[function_name](**function_args)
                return {"answer" : str(result)}  
            except HTTPException as e:
                raise e  
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Function execution error: {str(e)}")
        else:
            raise HTTPException(status_code=400, detail="No function call found in AI response")
    else:
        raise HTTPException(status_code=400, detail="Error: No valid choices found in AI response")
