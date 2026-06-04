#  Python Library API

API REST para gerenciamento de catálogo de livros, desenvolvida com FastAPI e containerizada com Docker.

---

##  Fluxo Completo — Docker + Aplicação

### Fase 1 — Build da Imagem

```
main.py (FastAPI)
      ↓ inclui
  Dockerfile
      ↓ usa
docker-compose.yml (build: . / ports: 8000:8000)
      ↓ cria
Imagem Docker (python + app + dependências)
```

O `docker-compose` lê o `docker-compose.yml`, que chama o `Dockerfile`, que constrói a imagem Docker com todas as dependências do projeto (`main.py` + Python + bibliotecas).

---

### Fase 2 — Execução do Container

A partir da imagem criada, o Docker sobe o container e executa a aplicação na **porta 8000:8000**.

```
Cliente
  │  POST /adiciona(/livros)
  │  GET /livros(/livros)
  │  PUT /atualiza/{id}(/livros)
  │  DELETE /delete/{id}(/livros)
  │  (HTTP Basic Auth + body JSON)
  │
  ▼
Container Docker (porta 8000:8000)
  │
  ▼
┌─────────────────────────────┐
│  Validação Pydantic         │──── ✗ ──▶ Retorna erro ao cliente
└─────────────────────────────┘
  │ ✓
  ▼
┌─────────────────────────────┐
│  Autenticação HTTP Basic    │──── ✗ ──▶ Retorna erro ao cliente
└─────────────────────────────┘
  │ ✓
  ▼
┌─────────────────────────────┐
│  SQLAlchemy ORM             │
└─────────────────────────────┘
  │
  ▼
┌─────────────────────────────┐
│  Banco de dados livros.db   │
│  (SQLite)                   │
└─────────────────────────────┘
  │
  ▼
Retorna resposta JSON ao cliente
```

---

##  Tecnologias

- **Python 3.12+**
- **FastAPI >= 0.134.0** — framework web
- **SQLAlchemy >= 2.0.0** — ORM para banco de dados
- **Uvicorn >= 0.41.0** — servidor ASGI
- **SQLite** — banco de dados
- **Pydantic** — validação de dados (incluso no FastAPI)
- **Poetry >= 2.0.0** — gerenciador de dependências
- **Docker + Docker Compose** — containerização

---

##  Requisitos para rodar o projeto

### Com Docker (recomendado)
- [Docker Desktop](https://www.docker.com/get-started) (já inclui o Docker Compose)
- Git

### Sem Docker (rodar local)
- Python 3.12 ou superior
- Poetry 1.8.3 ou superior

Verifique suas versões:
```bash
python --version   # precisa ser 3.12+
poetry --version   # precisa ser 1.8.3+
docker --version   # precisa estar instalado
```

---

##  Como rodar em outra máquina

### Com Docker (recomendado)

**1. Clone o repositório:**
```bash
git clone https://github.com/LuannaDEV/PYTHON-LIBRARY.git
cd PYTHON-LIBRARY
```

**2. Crie o arquivo `.env`** na raiz do projeto:
```
DATABASE_URL=sqlite:///./livros.db
MEU_USUARIO=admin
MINHA_SENHA=admin
PYTHONUNBUFFERED=1
```

**3. Suba o container:**
```bash
docker compose up -d --build
```

**4. Verifique se está rodando:**
```bash
docker ps
```

---

### Sem Docker (rodar local)

**1. Clone o repositório:**
```bash
git clone https://github.com/LuannaDEV/PYTHON-LIBRARY.git
cd PYTHON-LIBRARY
```

**2. Instale as dependências:**
```bash
pip install poetry==1.8.3
poetry install --no-root
```

**3. Crie o arquivo `.env`** na raiz do projeto:
```
DATABASE_URL=sqlite:///./livros.db
MEU_USUARIO=admin
MINHA_SENHA=admin
PYTHONUNBUFFERED=1
```

**4. Rode a aplicação:**
```bash
poetry run uvicorn main:app --host 0.0.0.0 --port 8000
```

---

##  Acessar a API

| O que | Endereço |
|---|---|
| Documentação interativa | http://localhost:8000/docs |
| API direto | http://localhost:8000/livros |

---

##  Autenticação

Todos os endpoints exigem **HTTP Basic Auth**:

| Campo | Valor padrão |
|---|---|
| Usuário | `admin` |
| Senha | `admin` |

---

##  Endpoints disponíveis

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/livros` | Lista todos os livros |
| `POST` | `/adiciona` | Adiciona um novo livro |
| `PUT` | `/atualiza/{id}` | Atualiza um livro |
| `DELETE` | `/delete/{id}` | Remove um livro |

---

##  Como parar

```bash
docker compose down

PARA TESTAR A API: 
Invoke-WebRequest -Uri http://localhost:8000/chamadas-externas | Select-Object -ExpandProperty Content
```
