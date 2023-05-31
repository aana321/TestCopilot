import uvicorn
from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from starlette.middleware.cors import CORSMiddleware
from assistant import RetrievalAssistant, Message
from config import system_prompt, origins
from storageClient import get_redis_connection

# Initialise Redis connection
redis_client = get_redis_connection()

app = FastAPI()
templates = Jinja2Templates(directory="templates")
redis_client = get_redis_connection()
chat = RetrievalAssistant()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/get_answer")
@app.options("/get_answer")
async def get_answer(request: dict):
    prompt = request.get('prompt')
    messages = []
    system_message = Message('system', system_prompt)
    messages.append(system_message.message())

    user_message = Message('user', prompt)
    messages.append(user_message.message())

    response = chat.ask_assistant(messages)

    generated = response['content']
    past = prompt

    return {"generated": generated, "past": past}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
