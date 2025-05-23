
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import fitz  # PyMuPDF
import openai
import os
from tempfile import NamedTemporaryFile
import traceback

app = FastAPI()
openai.api_key = os.getenv("OPENAI_API_KEY")

DEFAULT_PROMPT = (
    "Você receberá abaixo o conteúdo de um Termo de Securitização de uma CRA. Extraia os seguintes campos e apresente a resposta como um JSON com essas chaves (mesmo que algumas fiquem em branco):\n"
    "- numero_emissao\n"
    "- emissor\n"
    "- cedente\n"
    "- valor_total_emissao\n"
    "- data_emissao\n"
    "- data_vencimento\n"
    "- tipo_lastro\n"
    "- remuneracao\n"
    "- serie\n"
    "- garantias\n"
    "- forma_colocacao\n"
    "- coordenador_lider\n"
    "- agente_fiduciario\n"
    "- classificacao_risco\n"
    "- lastro_detalhado\n"
    "- taxa_aquisicao_recebiveis\n"
    "- fundo_garantidor\n"
    "- regime_colocacao\n"
    "- destinatario_recursos\n"
    "- data_liquidacao\n"
    "- tipo_emissao\n"
    "\nAnalise o conteúdo do documento e retorne os campos acima de forma precisa e estruturada.\n"
)

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
async def process_file(file: UploadFile = File(...)):
    try:
        file_bytes = await file.read()

        if file.filename.lower().endswith(".pdf"):
            file_text = extract_text_from_pdf(file_bytes)
        else:
            file_text = file_bytes.decode(errors="ignore")

        # Limita o tamanho do conteúdo para evitar erros de token
        MAX_CHARS = 12000
        file_text = file_text[:MAX_CHARS]

        full_prompt = f"{DEFAULT_PROMPT}\n\n{file_text}"

        completion = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": full_prompt}],
            temperature=0.3
        )

        resposta = completion.choices[0].message["content"]
        return JSONResponse(content={"resposta": resposta})

    except Exception as e:
        tb = traceback.format_exc()
        print("Erro completo:\n", tb)
        return JSONResponse(status_code=500, content={"erro": str(e), "trace": tb})
