from fastapi import FastAPI

app = FastAPI()

@app.get("/")

def inicio():

        return {'mensagem': 'API da barbearia funcionando'}

@app.get('/status')

def status():
        
                return {'status': 'online'}