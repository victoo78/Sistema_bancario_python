# database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from models import Base

# Carrega as variáveis do arquivo .env
load_dotenv()

DB_USER     = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST     = os.getenv("DB_HOST")
DB_PORT     = os.getenv("DB_PORT")
DB_NAME     = os.getenv("DB_NAME")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL, echo=False)  # echo=True para ver o SQL gerado no terminal

# Cria todas as tabelas no banco caso ainda não existam
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)


def get_session():
    """Retorna uma sessão ativa do banco de dados."""
    return Session()


