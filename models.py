# models.py
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()


class ClienteModel(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cpf = Column(String(11), unique=True, nullable=False)
    nome = Column(String(100), nullable=False)
    data_nascimento = Column(String(10), nullable=False)
    endereco = Column(String(200), nullable=False)

    contas = relationship("ContaModel", back_populates="cliente", cascade="all, delete-orphan")


class ContaModel(Base):
    __tablename__ = "contas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    numero = Column(Integer, unique=True, nullable=False)
    agencia = Column(String(10), default="0001")
    saldo = Column(Float, default=0.0)
    limite = Column(Float, default=500.0)
    limite_saques = Column(Integer, default=3)
    saques_realizados = Column(Integer, default=0)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False)

    cliente = relationship("ClienteModel", back_populates="contas")
    transacoes = relationship("TransacaoModel", back_populates="conta", cascade="all, delete-orphan")
    chaves_pix = relationship("ChavePixModel", back_populates="conta", cascade="all, delete-orphan")


class TransacaoModel(Base):
    __tablename__ = "transacoes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tipo = Column(String(20), nullable=False)        # Deposito, Saque, Pix, PixRecebido
    valor = Column(Float, nullable=False)
    data = Column(DateTime, default=datetime.now)
    detalhe = Column(String(200), nullable=True)
    id_pix = Column(String(20), nullable=True)
    conta_id = Column(Integer, ForeignKey("contas.id"), nullable=False)

    conta = relationship("ContaModel", back_populates="transacoes")


class ChavePixModel(Base):
    __tablename__ = "chaves_pix"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tipo = Column(String(20), nullable=False)        # cpf, email, celular, aleatoria
    valor = Column(String(100), unique=True, nullable=False)
    conta_id = Column(Integer, ForeignKey("contas.id"), nullable=False)

    conta = relationship("ContaModel", back_populates="chaves_pix")