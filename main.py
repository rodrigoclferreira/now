
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
import fitz  # PyMuPDF
import openai
import os
from tempfile import NamedTemporaryFile

app = FastAPI()
openai.api_key = os.getenv("OPENAI_API_KEY")

def extract_text_from_pdf(file_bytes: bytes) -> str:
    with NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    doc = fitz.open(tmp_path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text

@app.post("/hubspot-chatgpt")
async def process_file(prompt: str = Form(...), file: UploadFile = File(...)):
    file_bytes = await file.read()

    if file.filename.lower().endswith(".pdf"):
        file_text = extract_text_from_pdf(file_bytes)
    else:
        file_text = file_bytes.decode(errors="ignore")

    full_prompt = f"{prompt}\n\nConteúdo do arquivo:\n{file_text}"

    try:
        completion = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": full_prompt}],
            temperature=0.5
        )
        resposta = completion.choices[0].message["content"]
        return JSONResponse(content={"resposta": resposta})
    except Exception as e:
        return JSONResponse(status_code=500, content={"erro": str(e)})
