import os
from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import openai

app = FastAPI()

# Set up templates and static files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Set up OpenAI API key
openai.api_key = os.environ.get("OPENAI_API_KEY")

class CityInfo(BaseModel):
    landmarks: list[str]
    activities: list[str]

@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/")
async def get_city_info(request: Request, city: str = Form(...)):
    landmarks, activities = await get_city_info_from_ai(city)
    return templates.TemplateResponse("result.html", {
        "request": request,
        "city": city,
        "landmarks": landmarks,
        "activities": activities
    })

async def get_city_info_from_ai(city: str) -> tuple[list[str], list[str]]:
    prompt = f"Provide a list of top 5 landmarks and 5 fun activities in {city}. Format the response as two lists: 'Landmarks:' and 'Activities:'"
    
    client = openai.AsyncOpenAI()
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that provides information about cities."},
            {"role": "user", "content": prompt}
        ]
    )
    
    content = response.choices[0].message.content
    landmarks, activities = parse_response(content)
    return landmarks, activities

def parse_response(content: str) -> tuple[list[str], list[str]]:
    lines = content.split('\n')
    landmarks = []
    activities = []
    current_list = None
    
    for line in lines:
        if line.startswith("Landmarks:"):
            current_list = landmarks
        elif line.startswith("Activities:"):
            current_list = activities
        elif line.strip().startswith("-") and current_list is not None:
            current_list.append(line.strip()[2:])
    
    return landmarks, activities

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)