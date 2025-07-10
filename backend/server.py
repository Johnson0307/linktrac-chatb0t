from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
from datetime import datetime
import httpx
import uuid
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME', 'linktrac_chatbot')

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# Asas API Configuration
ASAAS_API_KEY = "761a62e9-36e2-470c-9416-fdb3eaf3ea08"
ASAAS_BASE_URL = "https://sandbox.asaas.com/api/v3"

# Contact Information
CONTACTS = {
    "suporte": {
        "dia": "61 3465-7605",
        "noite": {
            "name": "Johnson",
            "phone": "61996638648"
        }
    },
    "vendedores": [
        {"name": "Michael", "phone": "61998764076"},
        {"name": "Marcos", "phone": "61998490015"},
        {"name": "Yan", "phone": "61998477963"},
        {"name": "Adriel", "phone": "61996970993"}
    ]
}

# Pydantic Models
class ChatMessage(BaseModel):
    session_id: str
    message: str
    sender: str  # 'user' or 'bot'
    timestamp: datetime
    department: Optional[str] = None

class ChatRequest(BaseModel):
    session_id: str
    message: str
    department: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    department: str
    options: Optional[List[str]] = None
    contact_info: Optional[dict] = None

class DebtConsultationRequest(BaseModel):
    customer_id: str
    session_id: str

class BoletoRequest(BaseModel):
    customer_id: str
    value: float
    due_date: str
    description: str
    session_id: str

# Asas Service
class AsaasService:
    def __init__(self):
        self.api_key = ASAAS_API_KEY
        self.base_url = ASAAS_BASE_URL
        self.headers = {"access_token": self.api_key}
    
    async def consult_debt(self, customer_id: str):
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/payments",
                    params={"customer": customer_id},
                    headers=self.headers
                )
                if response.status_code == 200:
                    return response.json()
                else:
                    return {"error": "Cliente não encontrado ou sem débitos"}
            except Exception as e:
                return {"error": f"Erro na consulta: {str(e)}"}
    
    async def generate_boleto(self, payment_data: dict):
        async with httpx.AsyncClient() as client:
            try:
                boleto_data = {
                    "customer": payment_data["customer_id"],
                    "billingType": "BOLETO",
                    "value": payment_data["value"],
                    "dueDate": payment_data["due_date"],
                    "description": payment_data["description"]
                }
                
                response = await client.post(
                    f"{self.base_url}/payments",
                    json=boleto_data,
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return {"error": "Erro ao gerar boleto"}
            except Exception as e:
                return {"error": f"Erro na geração do boleto: {str(e)}"}

asaas_service = AsaasService()

# Chat Bot Logic
class ChatBot:
    def __init__(self):
        self.departments = ["financeiro", "suporte", "vendas"]
    
    async def process_message(self, message: str, session_id: str, department: str = None):
        message_lower = message.lower()
        
        # Initial greeting or department selection
        if not department or message_lower in ["oi", "olá", "hello", "hi", "início", "menu"]:
            return ChatResponse(
                response="👋 Olá! Sou o **Linktrac Chatbot Suporte**!\n\nComo posso ajudá-lo hoje?",
                department="geral",
                options=["💰 Financeiro", "🎯 Vendas", "🛠️ Suporte", "📞 Contatos"]
            )
        
        # Department routing
        if "financeiro" in message_lower or "débito" in message_lower or "boleto" in message_lower:
            return ChatResponse(
                response="💰 **Departamento Financeiro**\n\nEscolha uma opção:",
                department="financeiro",
                options=["📊 Consultar Débitos", "📋 Gerar Boleto", "🔙 Voltar ao Menu"]
            )
        
        if "vendas" in message_lower or "produto" in message_lower or "serviço" in message_lower:
            return ChatResponse(
                response="🎯 **Departamento de Vendas**\n\nNossos vendedores estão prontos para ajudar!",
                department="vendas",
                contact_info=CONTACTS["vendedores"],
                options=["📞 Ver Contatos", "🔙 Voltar ao Menu"]
            )
        
        if "suporte" in message_lower or "ajuda" in message_lower or "problema" in message_lower:
            return ChatResponse(
                response="🛠️ **Suporte Técnico**\n\nEstamos aqui para resolver seu problema!",
                department="suporte",
                contact_info=CONTACTS["suporte"],
                options=["📞 Ver Contatos", "🔙 Voltar ao Menu"]
            )
        
        if "contatos" in message_lower or "telefone" in message_lower:
            return ChatResponse(
                response="📞 **Nossos Contatos**\n\n**Suporte:**\n• Dia: 61 3465-7605\n• Noite: Johnson - 61996638648\n\n**Vendas:**\n• Michael: 61998764076\n• Marcos: 61998490015\n• Yan: 61998477963\n• Adriel: 61996970993",
                department="contatos",
                options=["🔙 Voltar ao Menu"]
            )
        
        # Financial operations
        if "consultar débitos" in message_lower or "consulta" in message_lower:
            return ChatResponse(
                response="📊 **Consulta de Débitos**\n\nPor favor, informe seu ID de cliente para consultar os débitos.",
                department="financeiro_consulta",
                options=["🔙 Voltar ao Financeiro"]
            )
        
        if "gerar boleto" in message_lower or "boleto" in message_lower:
            return ChatResponse(
                response="📋 **Geração de Boleto**\n\nPara gerar um boleto, preciso das seguintes informações:\n• ID do Cliente\n• Valor\n• Data de Vencimento\n• Descrição",
                department="financeiro_boleto",
                options=["🔙 Voltar ao Financeiro"]
            )
        
        # Default response
        return ChatResponse(
            response="🤖 Desculpe, não entendi sua mensagem.\n\nPor favor, escolha uma das opções disponíveis ou digite 'menu' para ver as opções principais.",
            department="geral",
            options=["🏠 Menu Principal", "📞 Contatos"]
        )

chat_bot = ChatBot()

# API Routes
@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        # Save user message
        user_message = ChatMessage(
            session_id=request.session_id,
            message=request.message,
            sender="user",
            timestamp=datetime.utcnow(),
            department=request.department
        )
        await db.chat_messages.insert_one(user_message.dict())
        
        # Process message
        response = await chat_bot.process_message(
            request.message, 
            request.session_id, 
            request.department
        )
        
        # Save bot response
        bot_message = ChatMessage(
            session_id=request.session_id,
            message=response.response,
            sender="bot",
            timestamp=datetime.utcnow(),
            department=response.department
        )
        await db.chat_messages.insert_one(bot_message.dict())
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/consult-debt")
async def consult_debt(request: DebtConsultationRequest):
    try:
        # Consult debt via Asas API
        debt_data = await asaas_service.consult_debt(request.customer_id)
        
        # Save consultation
        consultation = {
            "session_id": request.session_id,
            "customer_id": request.customer_id,
            "debt_data": debt_data,
            "timestamp": datetime.utcnow()
        }
        await db.debt_consultations.insert_one(consultation)
        
        return {"success": True, "data": debt_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate-boleto")
async def generate_boleto(request: BoletoRequest):
    try:
        # Generate boleto via Asas API
        boleto_data = await asaas_service.generate_boleto({
            "customer_id": request.customer_id,
            "value": request.value,
            "due_date": request.due_date,
            "description": request.description
        })
        
        # Save boleto generation
        boleto_record = {
            "session_id": request.session_id,
            "customer_id": request.customer_id,
            "value": request.value,
            "due_date": request.due_date,
            "description": request.description,
            "boleto_data": boleto_data,
            "timestamp": datetime.utcnow()
        }
        await db.boleto_generations.insert_one(boleto_record)
        
        return {"success": True, "data": boleto_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/chat-history/{session_id}")
async def get_chat_history(session_id: str):
    try:
        messages = await db.chat_messages.find(
            {"session_id": session_id}
        ).sort("timestamp", 1).to_list(100)
        
        return {"messages": messages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/contacts")
async def get_contacts():
    return {"contacts": CONTACTS}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "Linktrac Chatbot Suporte"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)