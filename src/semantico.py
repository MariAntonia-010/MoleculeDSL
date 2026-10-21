import json
import os
from dataclasses import dataclass

from ast_nos import AnelDecl, AtomoDecl, LigacaoDecl
from modelo import Atomo, Ligacao, Modelo


PASTA_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARQUIVO_ELEMENTOS = os.path.join(PASTA_RAIZ, "regras", "elementos.json")


def carregar_elementos():
    with open(ARQUIVO_ELEMENTOS, encoding="utf-8") as arquivo:
        return set(json.load(arquivo)["elementos"])


@dataclass
class ErroSemantico:
    id: str
    linha: int
    coluna: int
    mensagem: str

    def __str__(self):
        return (
            f"Erro semântico [{self.id}] na linha {self.linha}, "
            f"coluna {self.coluna}: {self.mensagem}"
        )


class AnalisadorSemantico:
    # Monta o modelo (grafo) a partir da AST e confere as regras
    # estruturais. Os IDs das regras estão em docs/plano_semantico.md.

    def __init__(self, molecula, elementos):
        self.molecula = molecula
        self.elementos = elementos
        self.erros = []
        self.modelo = Modelo(molecula.nome)

        self.por_nome = {}
        self.por_elemento = {}
        self.citados = set()
        self.pares = set()
        self.aneis_vistos = {}

        # Declarações que já deram erro: citá-las não gera outro erro
        self.nomes_invalidos = set()
        self.elementos_invalidos = set()

    def erro(self, id_regra, no, mensagem):
        self.erros.append(ErroSemantico(id_regra, no.linha, no.coluna, mensagem))

    def analisar(self):
        # Os átomos são coletados antes das ligações, então a ordem dos
        # comandos dentro da molécula não importa
        comandos = self.molecula.comandos

        for c in comandos:
            if isinstance(c, AtomoDecl):
                self.declarar_atomo(c)

        for c in comandos:
            if isinstance(c, LigacaoDecl):
                self.declarar_ligacao(c)

        for c in comandos:
            if isinstance(c, AnelDecl):
                self.declarar_anel(c)

        # Com outros erros, átomos sem ligação seriam só consequência deles
        if not self.erros:
            self.conferir_conexoes()

        self.erros.sort(key=lambda e: (e.linha, e.coluna))
        return self.modelo, self.erros

    # ---------- átomos ----------

    def declarar_atomo(self, decl):
        if decl.multiplicador < 1:
            self.erro("STRUCT-007", decl, "a quantidade de átomos precisa ser pelo menos 1")
            self.marcar_invalido(decl)
            return

        if decl.elemento not in self.elementos:
            self.erro("ELEM-001", decl, f"elemento desconhecido '{decl.elemento}'")
            self.marcar_invalido(decl)
            return

        for i in range(decl.multiplicador):
            # Com quantidade, o nome vira prefixo: 4x atom H as h cria h1 a h4
            nome = decl.nome
            if nome is not None and decl.multiplicador > 1:
                nome = f"{nome}{i + 1}"

            if nome is not None and nome in self.por_nome:
                anterior = self.por_nome[nome]
                self.erro(
                    "STRUCT-002",
                    decl,
                    f"o nome '{nome}' já foi usado na linha {anterior.linha}",
                )
                continue

            do_elemento = self.por_elemento.setdefault(decl.elemento, [])
            atomo = Atomo(
                id=len(self.modelo.atomos) + 1,
                elemento=decl.elemento,
                indice=len(do_elemento) + 1,
                carga=decl.carga,
                nome=nome,
                linha=decl.linha,
                coluna=decl.coluna,
            )
            self.modelo.atomos.append(atomo)
            do_elemento.append(atomo)
            if nome is not None:
                self.por_nome[nome] = atomo

    def marcar_invalido(self, decl):
        self.elementos_invalidos.add(decl.elemento)
        if decl.nome is not None:
            self.nomes_invalidos.add(decl.nome)
            for i in range(max(decl.multiplicador, 0)):
                self.nomes_invalidos.add(f"{decl.nome}{i + 1}")

    # ---------- ligações ----------

    def fixo(self, ref):
        # Uma referência é fixa quando sempre cita o mesmo átomo
        if ref.tipo == "nome":
            return ref.texto in self.por_nome
        return len(self.por_elemento.get(ref.texto, [])) == 1

    def resolver(self, ref):
        # Devolve o átomo citado, ou None se houver erro
        if ref.tipo == "nome":
            if ref.texto in self.por_nome:
                atomo = self.por_nome[ref.texto]
            else:
                if ref.texto not in self.nomes_invalidos:
                    self.erro("STRUCT-001", ref, f"nenhum átomo se chama '{ref.texto}'")
                return None
        else:
            candidatos = self.por_elemento.get(ref.texto, [])

            if not candidatos:
                if ref.texto in self.elementos_invalidos:
                    pass
                elif ref.texto not in self.elementos:
                    self.erro("ELEM-001", ref, f"elemento desconhecido '{ref.texto}'")
                else:
                    self.erro("STRUCT-001", ref, f"nenhum átomo de {ref.texto} foi declarado")
                return None

            if len(candidatos) == 1:
                atomo = candidatos[0]
            else:
                # Com vários átomos do elemento, usa o próximo ainda não citado
                livres = [a for a in candidatos if a.id not in self.citados]
                if not livres:
                    self.erro(
                        "STRUCT-004",
                        ref,
                        f"todos os {len(candidatos)} átomos de {ref.texto} já foram "
                        "citados; declare mais átomos ou use nomes para escolher qual",
                    )
                    return None
                atomo = livres[0]

        self.citados.add(atomo.id)
        return atomo

    def declarar_ligacao(self, decl):
        if decl.repeticoes < 1:
            self.erro("STRUCT-007", decl, "a repetição da ligação precisa ser pelo menos 1")
            return

        if decl.repeticoes > 1 and self.fixo(decl.origem) and self.fixo(decl.destino):
            self.erro(
                "STRUCT-006",
                decl,
                f"a repetição x{decl.repeticoes} ligaria os mesmos dois átomos "
                f"{decl.repeticoes} vezes; use = ou # para ligação dupla ou tripla",
            )
            return

        for _ in range(decl.repeticoes):
            origem = self.resolver(decl.origem)
            destino = self.resolver(decl.destino)

            # Para no primeiro erro, para não repetir o mesmo erro a cada repetição
            if origem is None or destino is None:
                return

            if origem.id == destino.id:
                self.erro(
                    "STRUCT-005",
                    decl,
                    f"o átomo {origem.rotulo()} não pode se ligar a ele mesmo",
                )
                return

            par = frozenset((origem.id, destino.id))
            if par in self.pares:
                self.erro(
                    "STRUCT-006",
                    decl,
                    f"já existe uma ligação entre {origem.rotulo()} e {destino.rotulo()}; "
                    "use = ou # para ligação dupla ou tripla",
                )
                return
            self.pares.add(par)

            self.modelo.ligacoes.append(
                Ligacao(origem.id, destino.id, decl.operador, decl.linha, decl.coluna)
            )

    # ---------- anéis ----------

    def declarar_anel(self, decl):
        # A lista do ring precisa formar um ciclo: sem átomo repetido e
        # com cada átomo ligado ao seguinte, e o último ligado ao primeiro
        atomos = [self.resolver(ref) for ref in decl.nomes]
        if None in atomos:
            return

        vistos = set()
        for atomo, ref in zip(atomos, decl.nomes):
            if atomo.id in vistos:
                self.erro("RING-001", ref, f"o átomo {ref.texto} aparece mais de uma vez no anel")
                return
            vistos.add(atomo.id)

        quantidade = len(atomos)
        for i in range(quantidade):
            atual = atomos[i]
            seguinte = atomos[(i + 1) % quantidade]

            if frozenset((atual.id, seguinte.id)) not in self.pares:
                fecha = i == quantidade - 1
                # O erro aponta para o segundo átomo do par; no fechamento,
                # para o último átomo da lista
                ref = decl.nomes[i] if fecha else decl.nomes[i + 1]
                texto = (
                    f"o anel não fecha: {atual.nome} e {seguinte.nome} não estão ligados"
                    if fecha
                    else f"os átomos {atual.nome} e {seguinte.nome} do anel não estão ligados"
                )
                self.erro("RING-002", ref, texto)
                return

        # O mesmo ciclo pode ser escrito começando de outro átomo ou ao
        # contrário; o conjunto de ligações identifica o anel
        arestas = frozenset(
            frozenset((atomos[i].id, atomos[(i + 1) % quantidade].id))
            for i in range(quantidade)
        )
        if arestas in self.aneis_vistos:
            anterior = self.aneis_vistos[arestas]
            self.erro("RING-003", decl, f"o mesmo anel já foi declarado na linha {anterior.linha}")
            return
        self.aneis_vistos[arestas] = decl

        self.modelo.aneis.append([a.id for a in atomos])

    # ---------- conexões ----------

    def conferir_conexoes(self):
        if not self.molecula.comandos:
            self.erro("STRUCT-003", self.molecula, "a molécula não tem nenhum átomo")
            return

        # Uma molécula de um átomo só (ex.: He) não precisa de ligação
        if len(self.modelo.atomos) < 2:
            return

        ligados = set()
        for lig in self.modelo.ligacoes:
            ligados.update((lig.origem, lig.destino))

        # Agrupa por declaração: "4x atom H" sem ligação dá um erro só
        sem_ligacao = {}
        for atomo in self.modelo.atomos:
            if atomo.id not in ligados:
                sem_ligacao.setdefault((atomo.linha, atomo.coluna), []).append(atomo)

        for atomos in sem_ligacao.values():
            rotulos = ", ".join(a.rotulo() for a in atomos)
            if len(atomos) == 1:
                mensagem = f"o átomo {rotulos} não tem nenhuma ligação"
            else:
                mensagem = f"os átomos {rotulos} não têm nenhuma ligação"
            self.erro("STRUCT-003", atomos[0], mensagem)


def analisar(molecula):
    # Devolve o modelo e a lista de erros semânticos (vazia se não houver)
    return AnalisadorSemantico(molecula, carregar_elementos()).analisar()
