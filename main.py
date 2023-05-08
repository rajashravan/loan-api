from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/poo")
async def root():
    return {"message": "Hello sadfsadf"}