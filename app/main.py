from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def root():
    return "Comment sentiment v1"

