from fastapi import FastAPI
from app.routes.agendamentos import router
from app.database.connection import Base, engine
from app.models import agendamento


Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(router)

@app.get("/")

def inicio():

        return {'mensagem': 'API da barbearia funcionando'}

@app.get('/status')

def status():
        
                return {'status': 'online'}