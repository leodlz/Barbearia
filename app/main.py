from fastapi import FastAPI
from app.routes.agendamentos import router

app = FastAPI()

app.include_router(router)

@app.get("/")

def inicio():

        return {'mensagem': 'API da barbearia funcionando'}

@app.get('/status')

def status():
        
                return {'status': 'online'}