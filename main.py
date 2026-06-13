from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy import create_engine, Column, Integer, String, asc, desc
import os
import asyncio
import redis
import json

redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_response=True)


DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

app = FastAPI(
    title="API de livros.",
    description="API para gerenciar catalogo de livros.",
    version="1.0",
    contact={
        "name": "Luanna",
        "email": "dev.luanna.espindola@gmail.com"
    }
)

MEU_USUARIO = os.getenv("MEU_USUARIO")
MINHA_SENHA = os.getenv("MINHA_SENHA")
security = HTTPBasic()


async def chamadas_externas1():
    await asyncio.sleep(2)
    return "Resultado chamada 1"

async def chamadas_externas2():
    await asyncio.sleep(2)
    return "Resultado chamada 2"

async def chamadas_externas3():
    await asyncio.sleep(2)
    return "Resultado chamada 3"

@app.get("/chamadas-externas")
async def chamadas():
    tarefa1 = asyncio.create_task(chamadas_externas1())
    tarefa2 = asyncio.create_task(chamadas_externas2())
    tarefa3 = asyncio.create_task(chamadas_externas3())
    
    resultado1 = await tarefa1
    resultado2 = await tarefa2
    resultado3 = await tarefa3
    
    return {
        "mensagem": "Todas as chamadas nas APIS foram concluidas com sucesso", 
        "resultado": [resultado1, resultado2, resultado3]
        
    }
    
def autenticar_meu_usuario(credentials: HTTPBasicCredentials = Depends(security)):
    is_username_correct = secrets.compare_digest(credentials.username, MEU_USUARIO)
    is_password_correct = secrets.compare_digest(credentials.password, MINHA_SENHA)

    if not (is_username_correct and is_password_correct):
        raise HTTPException(status_code=401, detail="Usuario ou senha incorretos")

    return credentials.username


class LivroDB(Base):
    __tablename__ = "Livros"
    id = Column(Integer, primary_key=True, index=True)
    nome_livro = Column(String, index=True)
    autor_livro = Column(String, index=True)
    ano_livro = Column(Integer, index=True)


Base.metadata.create_all(bind=engine)


def salvar_livro_redis(livro_id: int, livro: Livro):
    redis_client.set(f"livro:{livro_id}", json.dumps(livro.dict()))
    
def deletar_livro_redis(livro_id: int):
    redis_client.delete(f"livro:{livro_id}")
    


def sessao_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class Livro(BaseModel):
    nome_livro: str
    autor_livro: str
    ano_livro: int

@app.get("/debug/redis")
def livros_redis():
    chaves = redis_client.keys("livros:*") #pega o nome das chaves, ex: livro2, livro2, livro3
    livros = []
    for chave in chaves:
        valor = redis_client.get(chave) #pega o valor da chave, nao o nome da chave, e coloca em valor
        ttl = redis.client.ttl(chave)
        
        
        livros.append({"chave":chave, "valor": json.loads(valor), "ttl": ttl}) 
    return livros

@app.post("/livros")
async def post_livros(livro: Livro, db: Session = Depends(sessao_db), usuario: str = Depends(autenticar_meu_usuario)):
    db_livro = db.query(LivroDB).filter(
        LivroDB.nome_livro == livro.nome_livro,
        LivroDB.autor_livro == livro.autor_livro
    ).first()
    if db_livro:
        raise HTTPException(status_code=400, detail="Este livro ja existe!")

    novo_livro = LivroDB(**livro.dict())
    db.add(novo_livro)
    db.commit()
    db.refresh(novo_livro)
    salvar_livro_redis(novo_livro.id, livro)

    return {"mensagem": f"O livro foi criado com sucesso pelo usuario '{usuario}'!"}


@app.put("/livros/{id_livro}")
async def put_livros(id_livro: int, livro: Livro, db: Session = Depends(sessao_db), usuario: str = Depends(autenticar_meu_usuario)):
    
    db_livro = db.query(LivroDB).filter(LivroDB.id == id_livro).first()
    if not db_livro:
        raise HTTPException(status_code=404, detail="Livro nao encontrado")

    for key, value in livro.dict().items():
        setattr(db_livro, key, value)
    db.commit()
    db.refresh(db_livro)

    return {"mensagem": f"O livro foi atualizado com sucesso pelo usuario '{usuario}'!"}


@app.delete("/livros/{id_livro}")
async def delete_livros(id_livro: int, db: Session = Depends(sessao_db), usuario: str = Depends(autenticar_meu_usuario)):
    db_livro = db.query(LivroDB).filter(LivroDB.id == id_livro).first()
    if not db_livro:
        raise HTTPException(status_code=404, detail="Livro nao encontrado")
    db.delete(db_livro)
    db.commit()
    deletar_livro_redis(id_livro)
    return {"mensagem": f"Livro deletado com sucesso pelo usuario '{usuario}'"}


@app.get("/livros")
async def get_livros(  livro: Livro,
    order_by: str = "id",       
    order_dir: str = "asc",
    page: int = 1,
    limit: int = 10,
    db: Session = Depends(sessao_db),
    usuario: str = Depends(autenticar_meu_usuario)
    
):
   
   
    
    if page < 1 or limit < 1:
            raise HTTPException(status_code=400, detail="Page ou limit invalidos!")

    cache_key = f"livros:page={page}&limit={limit}"
    cached = redis_client.get(cache_key) 
        
    if cached:
        return json.loads(cached)
    
    livros = db.query(LivroDB).offset((page - 1) * limit).limit(limit).all()

    if not livros: 
            return {"mensagem": "Nao existe nenhum livro!"}
        
    total_livros = db.query(LivroDB).count()
        
    resposta ={
        
        "page": page,
        "limit":limit,
        "total_livros": total_livros,
        "livros": [
            {
            "id": livro.id,
                "nome_livro": livro.nome_livro,
                "autor_livro": livro.autor_livro,
                "ano_livro": livro.ano_livro
            
            
        } for livro in livros
                    ]
    } 
        
    redis_client.setex(cache_key, 30, json.dumps(resposta)) 
        

    