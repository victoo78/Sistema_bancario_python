# main.py
from abc import ABC, abstractmethod
from datetime import datetime
import random
import string

from database import get_session
from models import ClienteModel, ContaModel, TransacaoModel, ChavePixModel

# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────

def _gerar_id_pix(tamanho=12):
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=tamanho))


def _buscar_cliente(session, cpf):
    return session.query(ClienteModel).filter_by(cpf=cpf).first()


def _buscar_conta_por_chave(session, chave_valor):
    chave = session.query(ChavePixModel).filter_by(valor=chave_valor).first()
    return chave.conta if chave else None


def _proximo_numero_conta(session):
    total = session.query(ContaModel).count()
    return total + 1


def _registrar_transacao(session, conta, tipo, valor, detalhe=None, id_pix=None):
    transacao = TransacaoModel(
        tipo=tipo,
        valor=valor,
        data=datetime.now(),
        detalhe=detalhe,
        id_pix=id_pix,
        conta_id=conta.id,
    )
    session.add(transacao)
    session.commit()

# ─────────────────────────────────────────────
#  OPERAÇÕES BANCÁRIAS
# ─────────────────────────────────────────────

def depositar(session, conta, valor):
    if valor <= 0:
        print("Valor inválido para depósito.")
        return False
    conta.saldo += valor
    session.commit()
    _registrar_transacao(session, conta, "Deposito", valor)
    print(f"✔ Depósito de R$ {valor:.2f} realizado com sucesso.")
    return True


def sacar(session, conta, valor):
    if valor > conta.limite:
        print("O valor excede o limite por operação.")
        return False
    if conta.saques_realizados >= conta.limite_saques:
        print("Limite de saques diários atingido.")
        return False
    if conta.saldo < valor:
        print("Saldo insuficiente.")
        return False

    conta.saldo -= valor
    conta.saques_realizados += 1
    session.commit()
    _registrar_transacao(session, conta, "Saque", valor)
    print(f"✔ Saque de R$ {valor:.2f} realizado com sucesso.")
    return True


def enviar_pix(session, conta_origem, conta_destino, valor, descricao=""):
    if conta_origem.saldo < valor:
        print("Saldo insuficiente para o Pix.")
        return False

    id_pix = _gerar_id_pix()

    # Débito
    conta_origem.saldo -= valor
    detalhe_origem = f"→ Conta destino: {conta_destino.numero}"
    if descricao:
        detalhe_origem += f" | {descricao}"
    _registrar_transacao(session, conta_origem, "Pix", valor, detalhe_origem, id_pix)

    # Crédito
    conta_destino.saldo += valor
    detalhe_destino = f"← Conta origem: {conta_origem.numero}"
    if descricao:
        detalhe_destino += f" | {descricao}"
    _registrar_transacao(session, conta_destino, "PixRecebido", valor, detalhe_destino, id_pix)

    session.commit()
    print(f"✔ Pix de R$ {valor:.2f} enviado com sucesso!")
    print(f"   ID da transação: {id_pix}")
    return True

# ─────────────────────────────────────────────
#  MENU PRINCIPAL
# ─────────────────────────────────────────────

menu = """
╔══════════════════════════════╗
║      BANCO DIGITAL           ║
╠══════════════════════════════╣
║  [d]  Depositar              ║
║  [s]  Sacar                  ║
║  [e]  Extrato                ║
║  [nu] Novo Usuário           ║
║  [nc] Nova Conta             ║
╠══════════════════════════════╣
║  [cp] Cadastrar Chave Pix    ║
║  [lp] Listar Chaves Pix      ║
║  [px] Enviar Pix             ║
╠══════════════════════════════╣
║  [q]  Sair                   ║
╚══════════════════════════════╝
=> """

while True:
    opcao = input(menu).strip().lower()
    session = get_session()

    try:
        # ── Novo usuário ──────────────────────────
        if opcao == "nu":
            cpf = input("CPF (somente números): ").strip()
            if _buscar_cliente(session, cpf):
                print("Usuário já cadastrado.")
                continue
            nome = input("Nome completo: ")
            data_nascimento = input("Data de nascimento (dd/mm/aaaa): ")
            endereco = input("Endereço (logradouro, nro - bairro - cidade/UF): ")
            cliente = ClienteModel(cpf=cpf, nome=nome, data_nascimento=data_nascimento, endereco=endereco)
            session.add(cliente)
            session.commit()
            print("✔ Usuário cadastrado com sucesso!")

        # ── Nova conta ────────────────────────────
        elif opcao == "nc":
            cpf = input("Informe o CPF do usuário: ").strip()
            cliente = _buscar_cliente(session, cpf)
            if not cliente:
                print("Usuário não encontrado.")
                continue
            numero = _proximo_numero_conta(session)
            conta = ContaModel(numero=numero, cliente_id=cliente.id)
            session.add(conta)
            session.commit()
            print(f"✔ Conta corrente nº {numero} criada com sucesso!")

        # ── Depósito ──────────────────────────────
        elif opcao == "d":
            cpf = input("Informe seu CPF: ").strip()
            cliente = _buscar_cliente(session, cpf)
            if not cliente or not cliente.contas:
                print("Cliente não encontrado ou sem conta.")
                continue
            valor = float(input("Valor do depósito: R$ "))
            depositar(session, cliente.contas[0], valor)

        # ── Saque ─────────────────────────────────
        elif opcao == "s":
            cpf = input("Informe seu CPF: ").strip()
            cliente = _buscar_cliente(session, cpf)
            if not cliente or not cliente.contas:
                print("Cliente não encontrado ou sem conta.")
                continue
            valor = float(input("Valor do saque: R$ "))
            sacar(session, cliente.contas[0], valor)

        # ── Extrato ───────────────────────────────
        elif opcao == "e":
            cpf = input("Informe seu CPF: ").strip()
            cliente = _buscar_cliente(session, cpf)
            if not cliente or not cliente.contas:
                print("Cliente não encontrado ou sem conta.")
                continue
            conta = cliente.contas[0]
            transacoes = (
                session.query(TransacaoModel)
                .filter_by(conta_id=conta.id)
                .order_by(TransacaoModel.data)
                .all()
            )
            print("\n" + "=" * 45)
            print(f"  EXTRATO — Conta nº {conta.numero} | Ag. {conta.agencia}")
            print("=" * 45)
            if not transacoes:
                print("  Nenhuma movimentação registrada.")
            for t in transacoes:
                sinal = "-" if t.tipo in ("Saque", "Pix") else "+"
                data_fmt = t.data.strftime("%d/%m/%Y %H:%M:%S")
                print(f"  {data_fmt}  {t.tipo:<14} {sinal} R$ {t.valor:.2f}")
                if t.detalhe:
                    print(f"    {t.detalhe}")
                if t.id_pix:
                    print(f"    ID Pix: {t.id_pix}")
            print("-" * 45)
            print(f"  Saldo atual: R$ {conta.saldo:.2f}")
            print("=" * 45 + "\n")

        # ── Cadastrar chave Pix ───────────────────
        elif opcao == "cp":
            cpf = input("Informe seu CPF: ").strip()
            cliente = _buscar_cliente(session, cpf)
            if not cliente or not cliente.contas:
                print("Cliente não encontrado ou sem conta.")
                continue
            conta = cliente.contas[0]
            print("Tipos de chave: cpf | email | celular | aleatoria")
            tipo = input("Tipo da chave: ").strip().lower()
            if tipo not in ("cpf", "email", "celular", "aleatoria"):
                print("Tipo inválido.")
                continue
            if tipo == "aleatoria":
                valor_chave = _gerar_id_pix(16)
                print(f"Chave aleatória gerada: {valor_chave}")
            else:
                valor_chave = input("Valor da chave: ").strip()

            # Verifica duplicidade no banco
            existente = session.query(ChavePixModel).filter_by(valor=valor_chave).first()
            if existente:
                print("Essa chave já está cadastrada.")
                continue

            chave = ChavePixModel(tipo=tipo, valor=valor_chave, conta_id=conta.id)
            session.add(chave)
            session.commit()
            print(f"✔ Chave Pix '{valor_chave}' cadastrada com sucesso!")

        # ── Listar chaves Pix ─────────────────────
        elif opcao == "lp":
            cpf = input("Informe seu CPF: ").strip()
            cliente = _buscar_cliente(session, cpf)
            if not cliente or not cliente.contas:
                print("Cliente não encontrado ou sem conta.")
                continue
            chaves = cliente.contas[0].chaves_pix
            if not chaves:
                print("Nenhuma chave Pix cadastrada.")
            else:
                print("\nChaves Pix cadastradas:")
                for c in chaves:
                    print(f"  [{c.tipo}] {c.valor}")

        # ── Enviar Pix ────────────────────────────
        elif opcao == "px":
            cpf = input("Informe seu CPF: ").strip()
            cliente = _buscar_cliente(session, cpf)
            if not cliente or not cliente.contas:
                print("Cliente não encontrado ou sem conta.")
                continue
            conta_origem = cliente.contas[0]
            chave_destino = input("Chave Pix de destino: ").strip()
            conta_destino = _buscar_conta_por_chave(session, chave_destino)
            if not conta_destino:
                print("Chave Pix não encontrada.")
                continue
            if conta_destino.id == conta_origem.id:
                print("Não é possível fazer Pix para a própria conta.")
                continue
            valor = float(input("Valor do Pix: R$ "))
            descricao = input("Descrição (opcional): ").strip()
            print(f"\nConfirmar Pix de R$ {valor:.2f} para conta nº {conta_destino.numero}?")
            if input("[s] Confirmar / [n] Cancelar: ").strip().lower() != "s":
                print("Pix cancelado.")
                continue
            enviar_pix(session, conta_origem, conta_destino, valor, descricao)

        # ── Sair ──────────────────────────────────
        elif opcao == "q":
            print("Encerrando sistema. Até logo!")
            break

        else:
            print("Opção inválida!")

    except Exception as e:
        session.rollback()
        print(f"Erro inesperado: {e}")
    finally:
        session.close()