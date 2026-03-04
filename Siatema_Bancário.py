from abc import ABC, abstractmethod
from datetime import datetime
import random
import string

# ─────────────────────────────────────────────
#  TRANSAÇÕES
# ─────────────────────────────────────────────

class Transacao(ABC):
    @abstractmethod
    def registrar(self, conta):
        pass

class Deposito(Transacao):
    def __init__(self, valor):
        self.valor = valor

    def registrar(self, conta):
        conta.depositar(self.valor)
        conta.historico.adicionar_transacao(self)

class Saque(Transacao):
    def __init__(self, valor):
        self.valor = valor

    def registrar(self, conta):
        if conta.sacar(self.valor):
            conta.historico.adicionar_transacao(self)

class Pix(Transacao):
    """
    Representa uma transferência via Pix.
    - Se `conta_destino` for None, é um Pix recebido (crédito).
    - Se `conta_destino` estiver preenchida, é um Pix enviado (débito).
    """
    def __init__(self, valor, conta_destino=None, descricao=""):
        self.valor = valor
        self.conta_destino = conta_destino   # conta de destino (objeto Conta)
        self.descricao = descricao
        self.id_transacao = _gerar_id_pix()

    def registrar(self, conta_origem):
        # Débito na conta de origem
        if not conta_origem.sacar(self.valor):
            return

        conta_origem.historico.adicionar_transacao(self)
        print(f"ID da transação Pix: {self.id_transacao}")

        # Crédito na conta de destino
        if self.conta_destino:
            self.conta_destino.depositar(self.valor)
            pix_recebido = _PixRecebido(
                self.valor,
                conta_origem,
                self.id_transacao,
                self.descricao
            )
            self.conta_destino.historico.adicionar_transacao(pix_recebido)

class _PixRecebido(Transacao):
    """Registro interno gerado automaticamente na conta que recebe o Pix."""
    def __init__(self, valor, conta_origem, id_transacao, descricao=""):
        self.valor = valor
        self.conta_origem = conta_origem
        self.id_transacao = id_transacao
        self.descricao = descricao

    def registrar(self, conta):
        # Já creditado pelo Pix.registrar; só salva no histórico
        conta.historico.adicionar_transacao(self)

# ─────────────────────────────────────────────
#  CHAVES PIX
# ─────────────────────────────────────────────

class ChavePix:
    TIPOS_VALIDOS = ("cpf", "email", "celular", "aleatoria")

    def __init__(self, tipo, valor):
        if tipo not in self.TIPOS_VALIDOS:
            raise ValueError(f"Tipo de chave inválido. Use: {self.TIPOS_VALIDOS}")
        self.tipo = tipo
        self.valor = valor

# ─────────────────────────────────────────────
#  HISTÓRICO
# ─────────────────────────────────────────────

class Historico:
    def __init__(self):
        self.transacoes = []

    def adicionar_transacao(self, transacao):
        entrada = {
            "tipo": transacao.__class__.__name__,
            "valor": transacao.valor,
            "data": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        }
        # Detalhes extras para Pix
        if isinstance(transacao, Pix):
            destino = transacao.conta_destino
            entrada["detalhe"] = (
                f"→ Chave/Conta destino: {destino.numero}" if destino else "Pix enviado"
            )
            if transacao.descricao:
                entrada["detalhe"] += f" | Descrição: {transacao.descricao}"
            entrada["id_pix"] = transacao.id_transacao
        elif isinstance(transacao, _PixRecebido):
            entrada["tipo"] = "PixRecebido"
            entrada["detalhe"] = f"← Origem: conta {transacao.conta_origem.numero}"
            if transacao.descricao:
                entrada["detalhe"] += f" | Descrição: {transacao.descricao}"
            entrada["id_pix"] = transacao.id_transacao

        self.transacoes.append(entrada)

# ─────────────────────────────────────────────
#  CONTAS
# ─────────────────────────────────────────────

class Conta:
    def __init__(self, cliente, numero):
        self.saldo = 0.0
        self.numero = numero
        self.agencia = "0001"
        self.cliente = cliente
        self.historico = Historico()
        self.chaves_pix: list[ChavePix] = []

    # ── Operações básicas ──────────────────────
    def sacar(self, valor):
        if self.saldo >= valor:
            self.saldo -= valor
            print(f"Saque de R$ {valor:.2f} realizado com sucesso.")
            return True
        print("Saldo insuficiente.")
        return False

    def depositar(self, valor):
        if valor > 0:
            self.saldo += valor
            print(f"Depósito de R$ {valor:.2f} realizado com sucesso.")
            return True
        print("Valor inválido para depósito.")
        return False

    def saldo_atual(self):
        return self.saldo

    # ── Pix ───────────────────────────────────
    def cadastrar_chave_pix(self, tipo, valor):
        for chave in self.chaves_pix:
            if chave.valor == valor:
                print("Essa chave já está cadastrada nesta conta.")
                return
        self.chaves_pix.append(ChavePix(tipo, valor))
        print(f"Chave Pix '{valor}' ({tipo}) cadastrada com sucesso!")

    def listar_chaves_pix(self):
        if not self.chaves_pix:
            print("Nenhuma chave Pix cadastrada.")
            return
        print("\nChaves Pix cadastradas:")
        for c in self.chaves_pix:
            print(f"  [{c.tipo}] {c.valor}")


class ContaCorrente(Conta):
    def __init__(self, cliente, numero, limite=500.0, limite_saques=3):
        super().__init__(cliente, numero)
        self.limite = limite
        self.limite_saques = limite_saques
        self.saques_realizados = 0

    def sacar(self, valor):
        if valor > self.limite:
            print("O valor do saque excede o limite por operação.")
            return False
        if self.saques_realizados >= self.limite_saques:
            print("Limite de saques diários atingido.")
            return False
        if super().sacar(valor):
            self.saques_realizados += 1
            return True
        return False

# ─────────────────────────────────────────────
#  CLIENTES
# ─────────────────────────────────────────────

class Cliente:
    def __init__(self, endereco):
        self.endereco = endereco
        self.contas = []

    def realizar_transacao(self, conta, transacao):
        transacao.registrar(conta)

    def adicionar_conta(self, conta):
        self.contas.append(conta)

class PessoaFisica(Cliente):
    def __init__(self, cpf, nome, data_nascimento, endereco):
        super().__init__(endereco)
        self.cpf = cpf
        self.nome = nome
        self.data_nascimento = data_nascimento

# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────

def _gerar_id_pix(tamanho=12):
    caracteres = string.ascii_uppercase + string.digits
    return "".join(random.choices(caracteres, k=tamanho))

def _buscar_conta_por_chave(contas, chave_valor):
    """Retorna a primeira conta que possui a chave Pix informada."""
    for conta in contas:
        for chave in conta.chaves_pix:
            if chave.valor == chave_valor:
                return conta
    return None

def _buscar_cliente_por_cpf(clientes, cpf):
    return next((c for c in clientes if c.cpf == cpf), None)

# ─────────────────────────────────────────────
#  MENU PRINCIPAL
# ─────────────────────────────────────────────

clientes = []
contas = []

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

    # ── Novo usuário ──────────────────────────
    if opcao == "nu":
        cpf = input("CPF (somente números): ").strip()
        if any(c.cpf == cpf for c in clientes):
            print("Usuário já cadastrado.")
            continue
        nome = input("Nome completo: ")
        data_nascimento = input("Data de nascimento (dd/mm/aaaa): ")
        endereco = input("Endereço (logradouro, nro - bairro - cidade/UF): ")
        cliente = PessoaFisica(cpf, nome, data_nascimento, endereco)
        clientes.append(cliente)
        print("✔ Usuário cadastrado com sucesso!")

    # ── Nova conta ────────────────────────────
    elif opcao == "nc":
        cpf = input("Informe o CPF do usuário: ").strip()
        cliente = _buscar_cliente_por_cpf(clientes, cpf)
        if not cliente:
            print("Usuário não encontrado.")
            continue
        numero_conta = len(contas) + 1
        conta = ContaCorrente(cliente, numero_conta)
        cliente.adicionar_conta(conta)
        contas.append(conta)
        print(f"✔ Conta corrente nº {numero_conta} criada com sucesso!")

    # ── Depósito ──────────────────────────────
    elif opcao == "d":
        cpf = input("Informe seu CPF: ").strip()
        cliente = _buscar_cliente_por_cpf(clientes, cpf)
        if not cliente or not cliente.contas:
            print("Cliente não encontrado ou sem conta.")
            continue
        valor = float(input("Valor do depósito: R$ "))
        cliente.realizar_transacao(cliente.contas[0], Deposito(valor))

    # ── Saque ─────────────────────────────────
    elif opcao == "s":
        cpf = input("Informe seu CPF: ").strip()
        cliente = _buscar_cliente_por_cpf(clientes, cpf)
        if not cliente or not cliente.contas:
            print("Cliente não encontrado ou sem conta.")
            continue
        valor = float(input("Valor do saque: R$ "))
        cliente.realizar_transacao(cliente.contas[0], Saque(valor))

    # ── Extrato ───────────────────────────────
    elif opcao == "e":
        cpf = input("Informe seu CPF: ").strip()
        cliente = _buscar_cliente_por_cpf(clientes, cpf)
        if not cliente or not cliente.contas:
            print("Cliente não encontrado ou sem conta.")
            continue
        conta = cliente.contas[0]
        print("\n" + "=" * 40)
        print(f"  EXTRATO — Conta nº {conta.numero}")
        print("=" * 40)
        if not conta.historico.transacoes:
            print("  Nenhuma movimentação registrada.")
        for t in conta.historico.transacoes:
            sinal = "-" if t["tipo"] in ("Saque", "Pix") else "+"
            print(f"  {t['data']}  {t['tipo']:<14} {sinal} R$ {t['valor']:.2f}")
            if "detalhe" in t:
                print(f"    {t['detalhe']}")
            if "id_pix" in t:
                print(f"    ID Pix: {t['id_pix']}")
        print("-" * 40)
        print(f"  Saldo atual: R$ {conta.saldo_atual():.2f}")
        print("=" * 40 + "\n")

    # ── Cadastrar chave Pix ───────────────────
    elif opcao == "cp":
        cpf = input("Informe seu CPF: ").strip()
        cliente = _buscar_cliente_por_cpf(clientes, cpf)
        if not cliente or not cliente.contas:
            print("Cliente não encontrado ou sem conta.")
            continue
        print("Tipos de chave: cpf | email | celular | aleatoria")
        tipo = input("Tipo da chave: ").strip().lower()
        if tipo == "aleatoria":
            valor_chave = _gerar_id_pix(16)
            print(f"Chave aleatória gerada: {valor_chave}")
        else:
            valor_chave = input("Valor da chave: ").strip()
        cliente.contas[0].cadastrar_chave_pix(tipo, valor_chave)

    # ── Listar chaves Pix ─────────────────────
    elif opcao == "lp":
        cpf = input("Informe seu CPF: ").strip()
        cliente = _buscar_cliente_por_cpf(clientes, cpf)
        if not cliente or not cliente.contas:
            print("Cliente não encontrado ou sem conta.")
            continue
        cliente.contas[0].listar_chaves_pix()

    # ── Enviar Pix ────────────────────────────
    elif opcao == "px":
        cpf = input("Informe seu CPF: ").strip()
        cliente = _buscar_cliente_por_cpf(clientes, cpf)
        if not cliente or not cliente.contas:
            print("Cliente não encontrado ou sem conta.")
            continue

        conta_origem = cliente.contas[0]
        chave_destino = input("Chave Pix de destino: ").strip()
        conta_destino = _buscar_conta_por_chave(contas, chave_destino)

        if not conta_destino:
            print("Chave Pix não encontrada.")
            continue
        if conta_destino == conta_origem:
            print("Não é possível fazer Pix para a própria conta.")
            continue

        valor = float(input("Valor do Pix: R$ "))
        descricao = input("Descrição (opcional): ").strip()

        print(f"\nConfirmar Pix de R$ {valor:.2f} para conta nº {conta_destino.numero}?")
        confirmacao = input("[s] Confirmar / [n] Cancelar: ").strip().lower()
        if confirmacao != "s":
            print("Pix cancelado.")
            continue

        pix = Pix(valor, conta_destino=conta_destino, descricao=descricao)
        cliente.realizar_transacao(conta_origem, pix)
        print(f"✔ Pix de R$ {valor:.2f} enviado com sucesso!")

    # ── Sair ──────────────────────────────────
    elif opcao == "q":
        print("Encerrando sistema. Até logo!")
        break

    else:
        print("Opção inválida! Tente novamente.")