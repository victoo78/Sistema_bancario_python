from abc import ABC, abstractmethod
from datetime import datetime

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

class Historico:
    def __init__(self):
        self.transacoes = []

    def adicionar_transacao(self, transacao):
        self.transacoes.append(
            {
                "tipo": transacao.__class__.__name__,
                "valor": transacao.valor,
                "data": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            }
        )

class Conta:
    def __init__(self, cliente, numero):
        self.saldo = 0.0
        self.numero = numero
        self.agencia = "0001"
        self.cliente = cliente
        self.historico = Historico()

    def sacar(self, valor):
        if self.saldo >= valor:
            self.saldo -= valor
            print(f"Saque de R$ {valor:.2f} realizado com sucesso.")
            return True
        else:
            print("Saldo insuficiente.")
            return False

    def depositar(self, valor):
        if valor > 0:
            self.saldo += valor
            print(f"Depósito de R$ {valor:.2f} realizado com sucesso.")
            return True
        else:
            print("Valor inválido para depósito.")
            return False

    def saldo_atual(self):
        return self.saldo

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

# Menu principal com integração
clientes = []
contas = []

menu = """
[d] Depositar
[s] Sacar
[e] Extrato
[nu] Novo Usuário
[nc] Nova Conta
[q] Sair
=> """

while True:
    opcao = input(menu)

    if opcao == "nu":
        cpf = input("CPF (somente números): ")
        if any(c.cpf == cpf for c in clientes):
            print("Usuário já cadastrado.")
            continue
        nome = input("Nome completo: ")
        data_nascimento = input("Data de nascimento (dd/mm/aaaa): ")
        endereco = input("Endereço (logradouro, nro - bairro - cidade/UF): ")
        cliente = PessoaFisica(cpf, nome, data_nascimento, endereco)
        clientes.append(cliente)
        print("Usuário cadastrado com sucesso!")

    elif opcao == "nc":
        cpf = input("Informe o CPF do usuário: ")
        cliente = next((c for c in clientes if c.cpf == cpf), None)
        if not cliente:
            print("Usuário não encontrado.")
            continue
        numero_conta = len(contas) + 1
        conta = ContaCorrente(cliente, numero_conta)
        cliente.adicionar_conta(conta)
        contas.append(conta)
        print("Conta criada com sucesso!")

    elif opcao == "d":
        cpf = input("Informe seu CPF: ")
        cliente = next((c for c in clientes if c.cpf == cpf), None)
        if not cliente or not cliente.contas:
            print("Cliente não encontrado ou sem conta.")
            continue
        valor = float(input("Valor do depósito: "))
        transacao = Deposito(valor)
        cliente.realizar_transacao(cliente.contas[0], transacao)

    elif opcao == "s":
        cpf = input("Informe seu CPF: ")
        cliente = next((c for c in clientes if c.cpf == cpf), None)
        if not cliente or not cliente.contas:
            print("Cliente não encontrado ou sem conta.")
            continue
        valor = float(input("Valor do saque: "))
        transacao = Saque(valor)
        cliente.realizar_transacao(cliente.contas[0], transacao)

    elif opcao == "e":
        cpf = input("Informe seu CPF: ")
        cliente = next((c for c in clientes if c.cpf == cpf), None)
        if not cliente or not cliente.contas:
            print("Cliente não encontrado ou sem conta.")
            continue
        conta = cliente.contas[0]
        print("\nEXTRATO")
        for t in conta.historico.transacoes:
            print(f"{t['data']} - {t['tipo']}: R$ {t['valor']:.2f}")
        print(f"Saldo atual: R$ {conta.saldo_atual():.2f}\n")

    elif opcao == "q":
        break

    else:
        print("Opção inválida!")
