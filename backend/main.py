# backend/main.py
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from datetime import datetime
import uuid
import os
from typing import List, Optional
from pydantic import BaseModel

app = FastAPI(title="Couple's Sharing App")

# IMPORTANT: Allow your frontend URL
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://couples-frontend.onrender.com", 
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create photos directory
os.makedirs("photos", exist_ok=True)

class Post(BaseModel):
    id: str
    author: str
    content: str
    image_url: Optional[str] = None
    timestamp: str
    hearts: int = 0
    comments: List[dict] = []

# Store posts in memory
posts = []

# Welcome post
posts.append(Post(
    id="1",
    author="System",
    content="💖 Welcome to our special place! Share your thoughts and love here 💖",
    timestamp=datetime.now().isoformat(),
    hearts=0,
    comments=[]
))

@app.get("/")
def root():
    return {"message": "Couple's Sharing App API", "love": "❤️"}

@app.get("/posts")
def get_posts():
    return sorted(posts, key=lambda x: x.timestamp, reverse=True)

@app.post("/post")
def create_post(content: str, author: str):
    new_post = Post(
        id=str(uuid.uuid4()),
        author=author,
        content=content,
        timestamp=datetime.now().isoformat(),
        hearts=0,
        comments=[]
    )
    posts.append(new_post)
    return new_post

@app.post("/upload-media")
async def upload_media(author: str, content: str, media: UploadFile = File(...)):
    file_extension = media.filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{file_extension}"
    filepath = f"photos/{filename}"
    
    with open(filepath, "wb") as f:
        f.write(await media.read())
    
    # Determine media type roughly by extension
    media_type = "image"
    if file_extension.lower() in ['mp4', 'webm', 'ogg']:
        media_type = "video"
    elif file_extension.lower() in ['mp3', 'wav', 'm4a', 'aac', 'weba']:
        media_type = "audio"
        
    new_post = Post(
        id=str(uuid.uuid4()),
        author=author,
        content=content,
        image_url=f"/photos/{filename}",  # Keeping field name for backwards compatibility, but we use it for all media
        timestamp=datetime.now().isoformat(),
        hearts=0,
        comments=[]
    )
    # Monkey-patching the post for the frontend (the frontend will rely on media_type if we pass it, let's add it to Post)
    setattr(new_post, 'media_type', media_type)
    posts.append(new_post)
    
    # Return dict with media_type included
    post_dict = new_post.dict()
    post_dict['media_type'] = media_type
    return post_dict

@app.post("/heart/{post_id}")
def add_heart(post_id: str):
    for post in posts:
        if post.id == post_id:
            post.hearts += 1
            return {"hearts": post.hearts}
    raise HTTPException(status_code=404, detail="Post not found")

@app.post("/comment/{post_id}")
def add_comment(post_id: str, author: str, comment: str):
    for post in posts:
        if post.id == post_id:
            post.comments.append({
                "author": author,
                "comment": comment,
                "timestamp": datetime.now().isoformat()
            })
            return {"comments": post.comments}
    raise HTTPException(status_code=404, detail="Post not found")

@app.get("/photos/{filename}")
def get_media(filename: str):
    filepath = f"photos/{filename}"
    if os.path.exists(filepath):
        return FileResponse(filepath)
    raise HTTPException(status_code=404, detail="Media not found")