from fastapi import FastAPI, File, UploadFile
import pandas as pd
from io import BytesIO

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Bienvenue sur Vynal Docs Automator API"}

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    content = await file.read()
    if file.filename.endswith(".csv"):
        df = pd.read_csv(BytesIO(content))
        return {"filename": file.filename, "columns": df.columns.tolist(), "rows": len(df)}
    return {"message": "Format de fichier non pris en charge"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
