from fastapi import FastAPI

from app.routes.agendamentos import router as agendamentos_router
from app.routes.barbeiros import router as barbeiros_router
from app.routes.servicos import router as servicos_router

app = FastAPI(title="Gerenciador de Barbearia")

app.include_router(agendamentos_router)
app.include_router(barbeiros_router)
app.include_router(servicos_router)

@app.get("/")

def inicio():

        return {'mensagem': 'API da barbearia funcionando'}

@app.get('/status')

def status():
        
                return {'status': 'online'}
