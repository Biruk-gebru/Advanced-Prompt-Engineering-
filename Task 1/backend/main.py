from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import Literal, Optional, Union, Dict
import os
import json
import requests
import aiohttp
import PyPDF2
import io
from pdf2image import convert_from_bytes
import pytesseract
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize GitHub AI client configuration
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
ENDPOINT = "https://models.github.ai/inference"
MODEL = "openai/gpt-4.1"

if not GITHUB_TOKEN:
    raise ValueError("GITHUB_TOKEN not found in environment variables")

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your Flutter app's domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ArticleRequest(BaseModel):
    topic: Optional[str] = None
    audience_level: Literal["Middle School", "High School", "Undergraduate", "Graduate", "PhD"]
    paper_url: Optional[HttpUrl] = None

class ArticleResponse(BaseModel):
    content: str
    summary: str

async def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract text and analyze images from PDF."""
    try:
        text_content = []
        image_content = []
        
        # Extract text
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
        if len(pdf_reader.pages) == 0:
            raise ValueError("PDF file appears to be empty or corrupted")
            
        for page in pdf_reader.pages:
            text = page.extract_text()
            if text:
                text_content.append(text)
        
        # Convert PDF pages to images and analyze them
        try:
            images = convert_from_bytes(pdf_bytes)
            for i, image in enumerate(images):
                # Extract text from image using OCR
                image_text = pytesseract.image_to_string(image)
                if image_text.strip():
                    image_content.append(f"[Image {i+1} Content: {image_text.strip()}]")
        except Exception as e:
            print(f"Error processing images: {e}")
        
        # Combine text and image content
        if not text_content:
            raise ValueError("Could not extract any text from the PDF")
            
        full_content = "\n\n".join(text_content)
        if image_content:
            full_content += "\n\nImage Analysis:\n" + "\n".join(image_content)
        
        return full_content
    except Exception as e:
        raise ValueError(f"Error processing PDF: {str(e)}")

async def fetch_pdf_from_url(url: str) -> bytes:
    """Fetch PDF content from URL."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Failed to fetch PDF. Status code: {response.status}"
                    )
                
                content_type = response.headers.get('content-type', '')
                if 'application/pdf' not in content_type.lower():
                    raise HTTPException(
                        status_code=400,
                        detail=f"URL does not point to a PDF file. Content-Type: {content_type}"
                    )
                
                pdf_content = await response.read()
                if not pdf_content:
                    raise HTTPException(
                        status_code=400,
                        detail="Downloaded PDF is empty"
                    )
                
                return pdf_content
    except aiohttp.ClientError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error downloading PDF: {str(e)}"
        )

def get_few_shot_examples(audience_level: str) -> str:
    return """Here are examples of how to explain a concept at different levels:

Original: "The mitochondria is the powerhouse of the cell."

Middle School: "Cells have little parts inside them that make energy. One of them is called mitochondria – it gives power to the cell like a battery!"

PhD-level: "Mitochondria are double-membraned organelles that perform oxidative phosphorylation to generate ATP, serving as the metabolic hubs of eukaryotic cells."

Please use these examples to guide the tone and complexity of your response."""

def create_prompt(topic: str, audience_level: str, paper_content: Optional[str] = None) -> str:
    if paper_content:
        base_prompt = f"""You are an expert educator tasked with analyzing and explaining a research paper to a {audience_level} audience.

Paper Content:
{paper_content}

Please analyze this paper and create a comprehensive summary that:
1. Explains the main research findings
2. Breaks down complex concepts
3. Describes any visual elements or data
4. Maintains appropriate complexity for {audience_level} level

{get_few_shot_examples(audience_level)}

Format your response using proper markdown:
# Summary
One sentence overview

## Introduction
Engaging introduction appropriate for {audience_level} level

## Key Findings
* Main point 1
* Main point 2
* Main point 3

## Visual Analysis
Analysis of graphs, figures, and images (if any)

## Conclusion
Clear wrap-up with key takeaways"""
    else:
        base_prompt = f"""You are an expert educator tasked with explaining {topic} to a {audience_level} audience.

Follow these steps:
1. First, identify the core concepts of {topic}
2. Break down important subtopics
3. Organize the logical flow
4. Write a comprehensive article that matches the {audience_level} comprehension level

{get_few_shot_examples(audience_level)}

Format your response using proper markdown:
# Summary
One sentence overview

## Introduction
Engaging introduction appropriate for {audience_level} level

## Main Concepts
* Point 1
* Point 2
* Point 3

## Detailed Explanation
Key concepts with examples

## Conclusion
Clear wrap-up with key takeaways"""

    return base_prompt

async def generate_with_github_ai(prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Content-Type": "application/json"
    }
    
    data = {
        "messages": [
            {"role": "system", "content": "You are an expert educator who explains complex topics clearly using proper markdown formatting."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "top_p": 1,
        "model": MODEL
    }
    
    try:
        response = requests.post(
            f"{ENDPOINT}/chat/completions",
            headers=headers,
            json=data
        )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"GitHub AI API error: {response.text}"
            )
            
        result = response.json()
        return result["choices"][0]["message"]["content"]
        
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error calling GitHub AI API: {str(e)}")

@app.post("/generate_article", response_model=ArticleResponse)
async def generate_article(
    request: str = Form(...),
    file: Optional[UploadFile] = File(None)
):
    try:
        # Parse the request JSON string
        try:
            request_data = json.loads(request)
            article_request = ArticleRequest(**request_data)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON in request field")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid request format: {str(e)}")
        
        paper_content = None
        
        # Handle PDF file upload
        if file:
            try:
                content_type = file.content_type
                if content_type != "application/pdf":
                    raise HTTPException(status_code=400, detail="Only PDF files are supported")
                
                contents = await file.read()
                paper_content = await extract_text_from_pdf(contents)
            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Error processing uploaded PDF: {str(e)}"
                )
        
        # Handle PDF URL
        elif article_request.paper_url:
            try:
                pdf_content = await fetch_pdf_from_url(str(article_request.paper_url))
                paper_content = await extract_text_from_pdf(pdf_content)
            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Error processing PDF from URL: {str(e)}"
                )
        
        # Generate prompt based on input
        prompt = create_prompt(
            topic=article_request.topic if article_request.topic else "the provided paper",
            audience_level=article_request.audience_level,
            paper_content=paper_content
        )
        
        content = await generate_with_github_ai(prompt)
        
        # Extract the summary (first section after # Summary)
        summary = ""
        if "# Summary" in content:
            summary = content.split("# Summary")[1].split("#")[0].strip()

        return ArticleResponse(content=content, summary=summary)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 