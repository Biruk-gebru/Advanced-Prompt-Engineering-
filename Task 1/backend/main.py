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
    return """Here are carefully crafted examples demonstrating how to adapt explanations for different audiences:

Original Technical Concept: "Photosynthesis converts light energy into chemical energy."

Middle School (Ages 11-14):
"Plants have a special superpower called photosynthesis! They take sunlight, water from their roots, and air from their leaves to make their own food (sugar) and release oxygen - that's the air we breathe!"

High School (Ages 14-18):
"Photosynthesis is the biochemical process where plants use chlorophyll in their leaves to capture sunlight energy. This energy converts carbon dioxide and water into glucose (C₆H₁₂O₆) and oxygen through light-dependent and light-independent reactions."

Undergraduate (College Level):
"Photosynthesis consists of two main phases: the light-dependent reactions in thylakoid membranes that produce ATP and NADPH, and the Calvin cycle in the stroma that fixes CO₂ into organic compounds using the Rubisco enzyme."

Graduate/PhD Level:
"The photosynthetic electron transport chain employs photosystems II and I to create proton gradients across thylakoid membranes, driving ATP synthase while simultaneously generating reducing equivalents for carbon fixation via the C3 pathway or, in some species, C4 and CAM adaptations to photorespiration."

Key Adaptation Principles:
1. Complexity: Adjust technical terminology and sentence structure
2. Engagement: Use relatable analogies for younger audiences
3. Precision: Include exact mechanisms for advanced audiences
4. Visual Cues: Suggest mental imagery where helpful

Please apply these adaptation principles to your explanation."""


def get_chain_of_thought_examples() -> str:
    return """Advanced Chain-of-Thought Demonstration:

                Scientific Example:
                Q: Why does ice float on water?
                A: Let's analyze this systematically:
                1. Consider water's density: 1 g/cm³ at 4°C
                2. Observe hydrogen bonding creates hexagonal lattice when freezing
                3. This lattice increases volume by ~9% compared to liquid water
                4. Density = mass/volume → lower density (0.917 g/cm³) for ice
                5. Buoyancy principle: less dense materials float
                Conclusion: Ice floats due to crystalline structure reducing density

                Mathematical Example:
                Q: Solve for x: 3x + 7 = 22
                A: Step-by-step solution:
                1. Original equation: 3x + 7 = 22
                2. Subtract 7 from both sides: 3x = 15
                3. Divide both sides by 3: x = 5
                Verification: 3(5) + 7 = 15 + 7 = 22 ✓

                Economic Example:
                Q: How does inflation affect savings?
                A: Structured reasoning:
                1. Define inflation: general price level increase
                2. Consider $100 at 2% interest vs. 3% inflation
                3. Real value = nominal value / (1 + inflation)
                4. After 1 year: $102/1.03 ≈ $99.03
                5. Conclusion: Savings lose purchasing power

                Chain-of-Thought Best Practices:
                1. Explicitly number each reasoning step
                2. Include relevant formulas/definitions
                3. Show verification when possible
                4. Use domain-specific terminology appropriately
                5. Maintain logical flow between steps

                Apply this rigorous approach to complex problems requiring detailed analysis."""

def create_prompt(topic: str, audience_level: str, paper_content: Optional[str] = None) -> str:
    # Decide which example style to use
    if audience_level in ["Graduate", "PhD"]:
        example_section = get_chain_of_thought_examples()
    else:
        example_section = get_few_shot_examples(audience_level)

    if paper_content:
        base_prompt = f"""You are an expert educator tasked with analyzing and explaining a research paper to a {audience_level} audience.\n\nPaper Content:\n{paper_content}\n\nPlease analyze this paper and create a comprehensive summary that:\n1. Explains the main research findings\n2. Breaks down complex concepts\n3. Describes any visual elements or data\n4. Maintains appropriate complexity for {audience_level} level\n\n{example_section}\n\nFormat your response using proper markdown:\n# Summary\nOne sentence overview\n\n## Introduction\nEngaging introduction appropriate for {audience_level} level\n\n## Key Findings\n* Main point 1\n* Main point 2\n* Main point 3\n\n## Visual Analysis\nAnalysis of graphs, figures, and images (if any)\n\n## Conclusion\nClear wrap-up with key takeaways"""
    else:
        base_prompt = f"""You are an expert educator tasked with explaining {topic} to a {audience_level} audience.\n\nFollow these steps:\n1. First, identify the core concepts of {topic}\n2. Break down important subtopics\n3. Organize the logical flow\n4. Write a comprehensive article that matches the {audience_level} comprehension level\n\n{example_section}\n\nFormat your response using proper markdown:\n# Summary\nOne sentence overview\n\n## Introduction\nEngaging introduction appropriate for {audience_level} level\n\n## Main Concepts\n* Point 1\n* Point 2\n* Point 3\n\n## Detailed Explanation\nKey concepts with examples\n\n## Conclusion\nClear wrap-up with key takeaways"""

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