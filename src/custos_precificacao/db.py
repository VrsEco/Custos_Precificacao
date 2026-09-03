from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from custos_precificacao.config import DATABASE_URL

engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, future=True)
