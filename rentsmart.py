"""RentSmart - Sistema de orcamentos de locacao da R.M Imoveis.

Projeto de Algorithmic Thinking & Introduction to Object-Oriented Programming.
Executar com: python rentsmart.py
"""

import csv
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path


TAXA_CONTRATUAL = Decimal('2000.00')
CENTAVO = Decimal('0.01')


def dinheiro(valor):
    """Devolve uma quantia formatada como moeda brasileira."""
    valor = valor.quantize(CENTAVO, rounding=ROUND_HALF_UP)
    parte_inteira, centavos = f'{valor:.2f}'.split('.')
    grupos = []
    while parte_inteira:
        grupos.insert(0, parte_inteira[-3:])
        parte_inteira = parte_inteira[:-3]
    return f"R$ {'.'.join(grupos)},{centavos}"


def valor_csv(valor):
    """Numero com virgula decimal, sem simbolo de moeda, para o Excel brasileiro."""
    return f'{valor:.2f}'.replace('.', ',')


class Imovel:
    """Classe base: guarda o aluguel inicial e o nome do tipo de imovel."""

    def __init__(self, nome, aluguel_base):
        self.nome = nome
        self.aluguel_base = aluguel_base

    def adicionais(self):
        """Cada tipo de imovel implementa seus proprios adicionais."""
        return []

    def percentual_desconto(self):
        return Decimal('0.00')

    def detalhes(self):
        return []

    def calcular_orcamento(self):
        acrescimos = self.adicionais()
        subtotal = self.aluguel_base + sum((v for _, v in acrescimos), Decimal('0.00'))
        desconto = (subtotal * self.percentual_desconto()).quantize(
            CENTAVO, rounding=ROUND_HALF_UP
        )
        total = subtotal - desconto
        return {
            'base': self.aluguel_base,
            'adicionais': acrescimos,
            'subtotal': subtotal,
            'desconto': desconto,
            'aluguel_mensal': total,
        }


class Apartamento(Imovel):
    def __init__(self, quartos, garagem, possui_criancas):
        if quartos not in (1, 2):
            raise ValueError('Apartamento deve ter 1 ou 2 quartos.')
        if not isinstance(garagem, bool) or not isinstance(possui_criancas, bool):
            raise ValueError('Garagem e presenca de criancas devem ser sim ou nao.')
        super().__init__('Apartamento', Decimal('700.00'))
        self.quartos = quartos
        self.garagem = garagem
        self.possui_criancas = possui_criancas

    def adicionais(self):
        itens = []
        if self.quartos == 2:
            itens.append(('Segundo quarto', Decimal('200.00')))
        if self.garagem:
            itens.append(('Vaga de garagem', Decimal('300.00')))
        return itens

    def percentual_desconto(self):
        if not self.possui_criancas:
            return Decimal('0.05')
        return Decimal('0.00')

    def detalhes(self):
        return [
            f'Quartos: {self.quartos}',
            f'Garagem: {"Sim" if self.garagem else "Nao"}',
            f'Possui criancas: {"Sim" if self.possui_criancas else "Nao"}',
        ]


class Casa(Imovel):
    def __init__(self, quartos, garagem):
        if quartos not in (1, 2):
            raise ValueError('Casa deve ter 1 ou 2 quartos.')
        if not isinstance(garagem, bool):
            raise ValueError('Garagem deve ser sim ou nao.')
        super().__init__('Casa', Decimal('900.00'))
        self.quartos = quartos
        self.garagem = garagem

    def adicionais(self):
        itens = []
        if self.quartos == 2:
            itens.append(('Segundo quarto', Decimal('250.00')))
        if self.garagem:
            itens.append(('Vaga de garagem', Decimal('300.00')))
        return itens

    def detalhes(self):
        return [
            f'Quartos: {self.quartos}',
            f'Garagem: {"Sim" if self.garagem else "Nao"}',
        ]


class Estudio(Imovel):
    def __init__(self, vagas):
        if isinstance(vagas, bool) or not isinstance(vagas, int) or (vagas != 0 and vagas < 2):
            raise ValueError('O estudio permite 0 vagas ou um pacote de 2 ou mais vagas.')
        super().__init__('Estudio', Decimal('1200.00'))
        self.vagas = vagas

    def adicionais(self):
        if self.vagas == 0:
            return []
        itens = [('Pacote de 2 vagas', Decimal('250.00'))]
        if self.vagas > 2:
            itens.append((f'Vagas extras ({self.vagas - 2})', Decimal('60.00') * (self.vagas - 2)))
        return itens

    def detalhes(self):
        return [f'Vagas de estacionamento: {self.vagas}']


class ContratoLocacao:
    """Responsavel pelo parcelamento da taxa e pela projecao de pagamentos."""

    def __init__(self, imovel, parcelas):
        if not isinstance(imovel, Imovel):
            raise ValueError('Informe um imovel valido.')
        if isinstance(parcelas, bool) or not isinstance(parcelas, int) or not 1 <= parcelas <= 5:
            raise ValueError('A taxa pode ser dividida de 1 a 5 parcelas.')
        self.imovel = imovel
        self.parcelas = parcelas
        self.taxa_contratual = TAXA_CONTRATUAL

    def valores_parcelas(self):
        """Divide a taxa em centavos sem perder ou criar dinheiro."""
        total_centavos = int(self.taxa_contratual * 100)
        por_parcela, sobra = divmod(total_centavos, self.parcelas)
        return [
            Decimal(por_parcela + (1 if i < sobra else 0)) / 100
            for i in range(self.parcelas)
        ]

    def projecao(self):
        aluguel = self.imovel.calcular_orcamento()['aluguel_mensal']
        valores_taxa = self.valores_parcelas()
        linhas = []
        acumulado = Decimal('0.00')
        for mes in range(1, 13):
            parcela = valores_taxa[mes - 1] if mes <= self.parcelas else Decimal('0.00')
            total_mes = aluguel + parcela
            acumulado += total_mes
            linhas.append({
                'mes': mes,
                'aluguel': aluguel,
                'parcela_taxa': parcela,
                'total_mes': total_mes,
                'acumulado': acumulado,
            })
        return linhas

    def exportar_csv(self, caminho='projecao_locacao.csv'):
        caminho = Path(caminho)
        with caminho.open('w', newline='', encoding='utf-8-sig') as arquivo:
            escritor = csv.writer(arquivo, delimiter=';')
            escritor.writerow([
                'Mes', 'Aluguel mensal (R$)', 'Parcela da taxa contratual (R$)',
                'Total do mes (R$)', 'Total acumulado (R$)'
            ])
            for linha in self.projecao():
                escritor.writerow([
                    linha['mes'], valor_csv(linha['aluguel']),
                    valor_csv(linha['parcela_taxa']), valor_csv(linha['total_mes']),
                    valor_csv(linha['acumulado'])
                ])
        return caminho

    def exibir_orcamento(self):
        orcamento = self.imovel.calcular_orcamento()
        print('\n' + '=' * 55)
        print('              RENTSMART - ORCAMENTO')
        print('=' * 55)
        print(f'Tipo de imovel: {self.imovel.nome}')
        for detalhe in self.imovel.detalhes():
            print(detalhe)
        print('-' * 55)
        print(f'Aluguel base:                 {dinheiro(orcamento["base"])}')
        for descricao, valor in orcamento['adicionais']:
            print(f'{descricao}: {dinheiro(valor)}')
        print(f'Subtotal antes do desconto:  {dinheiro(orcamento["subtotal"])}')
        if orcamento['desconto'] > 0:
            print(f'Desconto de 5%:             -{dinheiro(orcamento["desconto"])}')
        print(f'ALUGUEL MENSAL:              {dinheiro(orcamento["aluguel_mensal"])}')
        print('-' * 55)
        print(f'Taxa contratual (separada):  {dinheiro(self.taxa_contratual)}')
        print(f'Parcelamento escolhido: {self.parcelas} vez(es)')
        for numero, parcela in enumerate(self.valores_parcelas(), start=1):
            print(f'  Parcela {numero}: {dinheiro(parcela)}')
        print('-' * 55)
        print('PROJECAO DOS 12 MESES')
        for linha in self.projecao():
            print(
                f'Mes {linha["mes"]:>2}: aluguel {dinheiro(linha["aluguel"])} + '
                f'taxa {dinheiro(linha["parcela_taxa"])} = {dinheiro(linha["total_mes"])}'
            )
        print(f'TOTAL PREVISTO NO ANO:       {dinheiro(self.projecao()[-1]["acumulado"])}')
        print('=' * 55)


def pedir_inteiro(pergunta, permitidos=None, minimo=None):
    while True:
        try:
            numero = int(input(pergunta).strip())
        except ValueError:
            print('Entrada invalida. Digite um numero inteiro.')
            continue
        if permitidos is not None and numero not in permitidos:
            print('Opcao invalida. Escolha uma das opcoes informadas.')
        elif minimo is not None and numero < minimo:
            print(f'Informe um numero maior ou igual a {minimo}.')
        else:
            return numero


def pedir_sim_nao(pergunta):
    while True:
        resposta = input(pergunta).strip().lower()
        if resposta in ('s', 'sim'):
            return True
        if resposta in ('n', 'nao', 'não'):
            return False
        print('Resposta invalida. Digite S para sim ou N para nao.')


def escolher_imovel():
    print('\nEscolha o tipo de imovel:')
    print('1 - Apartamento')
    print('2 - Casa')
    print('3 - Estudio')
    escolha = pedir_inteiro('Opcao: ', permitidos=(1, 2, 3))

    if escolha in (1, 2):
        quartos = pedir_inteiro('Numero de quartos (1 ou 2): ', permitidos=(1, 2))
        garagem = pedir_sim_nao('Deseja 1 vaga de garagem? (S/N): ')
        if escolha == 1:
            criancas = pedir_sim_nao('Possui criancas? (S/N): ')
            return Apartamento(quartos, garagem, criancas)
        return Casa(quartos, garagem)

    print('No estudio, o estacionamento pode ser sem vaga ou pacote de 2 vagas.')
    print('A partir da terceira vaga, cada vaga extra custa R$ 60,00.')
    while True:
        vagas = pedir_inteiro('Quantidade de vagas (0 ou 2 ou mais): ', minimo=0)
        if vagas != 1:
            return Estudio(vagas)
        print('Uma vaga isolada nao e oferecida para estudios.')


def main():
    print('Bem-vindo ao RentSmart - R.M Imoveis')
    try:
        imovel = escolher_imovel()
        parcelas = pedir_inteiro('Parcelar a taxa de R$ 2.000,00 em quantas vezes (1 a 5)? ', permitidos=range(1, 6))
        contrato = ContratoLocacao(imovel, parcelas)
        contrato.exibir_orcamento()
        caminho = contrato.exportar_csv()
        print(f'\nArquivo CSV gerado: {caminho.resolve()}')
        print('O aluguel e a taxa contratual foram calculados separadamente.')
    except (KeyboardInterrupt, EOFError):
        print('\nOperacao encerrada sem gerar novo orcamento.')


if __name__ == '__main__':
    main()
