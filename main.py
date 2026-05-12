from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy import create_engine, Column, Integer, String, asc, desc
import os


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


@app.post("/adiciona")
def post_livros(livro: Livro, db: Session = Depends(sessao_db), usuario: str = Depends(autenticar_meu_usuario)):
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

    return {"mensagem": f"O livro foi criado com sucesso pelo usuario '{usuario}'!"}


@app.put("/atualiza/{id_livro}")
def put_livros(id_livro: int, livro: Livro, db: Session = Depends(sessao_db), usuario: str = Depends(autenticar_meu_usuario)):
    
    db_livro = db.query(LivroDB).filter(LivroDB.id == id_livro).first()
    if not db_livro:
        raise HTTPException(status_code=404, detail="Livro nao encontrado")

    for key, value in livro.dict().items():
        setattr(db_livro, key, value)
    db.commit()
    db.refresh(db_livro)

    return {"mensagem": f"O livro foi atualizado com sucesso pelo usuario '{usuario}'!"}


@app.delete("/delete/{id_livro}")
def delete_livros(id_livro: int, db: Session = Depends(sessao_db), usuario: str = Depends(autenticar_meu_usuario)):
    db_livro = db.query(LivroDB).filter(LivroDB.id == id_livro).first()
    if not db_livro:
        raise HTTPException(status_code=404, detail="Livro nao encontrado")
    db.delete(db_livro)
    db.commit()
    return {"mensagem": f"Livro deletado com sucesso pelo usuario '{usuario}'"}


@app.get("/livros")
def get_livros(
    order_by: str = "id",       
    order_dir: str = "asc",
    page: int = 1,
    limit: int = 10,
    db: Session = Depends(sessao_db),
    usuario: str = Depends(autenticar_meu_usuario)
):
    if page < 1 or limit < 1:
        raise HTTPException(status_code=400, detail="Page ou limit invalidos!")

    campos_validos = {"id", "nome_livro", "autor_livro", "ano_livro"}
    if order_by not in campos_validos:
        raise HTTPException(status_code=400, detail="Campo de ordenacao invalido!")

    if order_dir not in ("asc", "desc"):
        raise HTTPException(status_code=400, detail="order_dir invalido! Use 'asc' ou 'desc'.")

    coluna = getattr(LivroDB, order_by)
    direcao = asc if order_dir == "asc" else desc

    livros = db.query(LivroDB).order_by(direcao(coluna)).offset((page - 1) * limit).limit(limit).all()

    if not livros:
        return {"mensagem": "Nao existe nenhum livro!"}

    total_livros = db.query(LivroDB).count()

    return {
        "usuario": usuario,
        "page": page,
        "limit": limit,
        "total": total_livros,
        "livros": [
            {
                "id": livro.id,
                "nome_livro": livro.nome_livro,
                "autor_livro": livro.autor_livro,
                "ano_livro": livro.ano_livro
            }
            for livro in livros
        ]
    }