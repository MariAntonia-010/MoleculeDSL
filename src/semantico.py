import json
import os
from dataclasses import dataclass

from ast_nos import (
    AnelDecl,
    AtomoDecl,
    LigacaoDecl,
    Operador,
    TipoReferencia,
)
from modelo import Atomo, Ligacao, Modelo


PASTA_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARQUIVO_ELEMENTOS = os.path.join(PASTA_RAIZ, "regras", "elementos.json")
ARQUIVO_VALENCIAS = os.path.join(PASTA_RAIZ, "regras", "valencias.json")
ARQUIVO_CLASSIFICACAO = os.path.join(
    PASTA_RAIZ, "regras", "classificacao_ligacoes.json"
)
ARQUIVO_LIGACOES_METALICAS = os.path.join(
    PASTA_RAIZ, "regras", "ligacoes_metalicas.json"
)

ERRO = "erro"
AVISO = "aviso"

# Maior quantidade aceita em "4x atom" e "x4". A linguagem é para moléculas
# simples, e cada átomo vira um objeto no modelo: sem limite, um número
# muito grande faria o programa travar.
LIMITE_QUANTIDADE = 1000


def carregar_elementos():
    with open(ARQUIVO_ELEMENTOS, encoding="utf-8") as arquivo:
        return json.load(arquivo)["elementos"]


def carregar_valencias():
    with open(ARQUIVO_VALENCIAS, encoding="utf-8") as arquivo:
        return json.load(arquivo)


def carregar_classificacao():
    with open(ARQUIVO_CLASSIFICACAO, encoding="utf-8") as arquivo:
        return json.load(arquivo)


def carregar_ligacoes_metalicas():
    with open(ARQUIVO_LIGACOES_METALICAS, encoding="utf-8") as arquivo:
        return json.load(arquivo)


@dataclass
class MensagemSemantica:
    # Erros impedem a compilação; avisos só informam
    severidade: str
    id: str
    linha: int
    coluna: int
    mensagem: str

    def __str__(self):
        tipo = "Erro" if self.severidade == ERRO else "Aviso"
        return (
            f"{tipo} semântico [{self.id}] na linha {self.linha}, "
            f"coluna {self.coluna}: {self.mensagem}"
        )


class AnalisadorSemantico:
    # Monta o modelo (grafo) a partir da AST e confere as regras
    # estruturais e de valência. Os IDs das regras estão em
    # docs/plano_semantico.md.

    def __init__(
        self,
        molecula,
        dados_elementos,
        valencias,
        classificacao,
        ligacoes_metalicas,
    ):
        self.molecula = molecula
        self.dados_elementos = dados_elementos
        self.elementos = set(dados_elementos)
        self.valencias = valencias
        self.classificacao = classificacao
        self.blocos_metalicos = set(
            ligacoes_metalicas["blocos_metalicos"]
        )
        self.mensagens = []
        self.modelo = Modelo(molecula.nome)

        self.por_nome = {}
        self.por_elemento = {}
        self.citados = set()
        self.pares = set()
        self.aneis_vistos = {}

        # Declarações que já deram erro: citá-las não gera outro erro
        self.nomes_invalidos = set()
        self.prefixos_invalidos = set()
        self.elementos_invalidos = set()

    def erro(self, id_regra, no, mensagem):
        self.mensagens.append(MensagemSemantica(ERRO, id_regra, no.linha, no.coluna, mensagem))

    def aviso(self, id_regra, no, mensagem):
        self.mensagens.append(MensagemSemantica(AVISO, id_regra, no.linha, no.coluna, mensagem))

    def tem_erro(self):
        return any(m.severidade == ERRO for m in self.mensagens)

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

        # Com outros erros, átomos sem ligação e problemas de valência
        # seriam só consequência deles
        if not self.tem_erro():
            self.conferir_conexoes()

        if not self.tem_erro():
            self.conferir_ciclos_nao_declarados()
            self.classificar_ligacoes()
            self.conferir_coordenadas()
            self.conferir_ligacoes_metalicas()

        if not self.tem_erro():
            self.conferir_valencias()

        self.mensagens.sort(key=lambda m: (m.linha, m.coluna))
        return self.modelo, self.mensagens

    # ---------- átomos ----------

    def declarar_atomo(self, decl):
        if decl.multiplicador < 1:
            self.erro("STRUCT-007", decl, "a quantidade de átomos precisa ser pelo menos 1")
            self.marcar_invalido(decl)
            return

        if decl.multiplicador > LIMITE_QUANTIDADE:
            self.erro(
                "STRUCT-007",
                decl,
                f"a quantidade de átomos pode ser no máximo {LIMITE_QUANTIDADE}",
            )
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
            # Com quantidade, os nomes seriam prefixo + número (h1, h2...).
            # Guarda só o prefixo, para não percorrer uma quantidade enorme.
            if decl.multiplicador != 1:
                self.prefixos_invalidos.add(decl.nome)

    def nome_invalido(self, texto):
        if texto in self.nomes_invalidos:
            return True
        return any(
            texto.startswith(prefixo) and texto[len(prefixo):].isdigit()
            for prefixo in self.prefixos_invalidos
        )

    # ---------- ligações ----------

    def fixo(self, ref):
        # Uma referência é fixa quando sempre cita o mesmo átomo
        if ref.tipo is TipoReferencia.NOME:
            return ref.texto in self.por_nome
        return len(self.por_elemento.get(ref.texto, [])) == 1

    def resolver(self, ref):
        # Devolve o átomo citado, ou None se houver erro
        if ref.tipo is TipoReferencia.NOME:
            if ref.texto in self.por_nome:
                atomo = self.por_nome[ref.texto]
            else:
                if not self.nome_invalido(ref.texto):
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

        if decl.repeticoes > LIMITE_QUANTIDADE:
            self.erro(
                "STRUCT-007",
                decl,
                f"a repetição da ligação pode ser no máximo {LIMITE_QUANTIDADE}",
            )
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

    def conferir_ciclos_nao_declarados(self):
        """Avisa quando o grafo tem mais ciclos independentes que `ring`s."""
        if not self.modelo.atomos:
            return

        adjacencias = {atomo.id: set() for atomo in self.modelo.atomos}
        for ligacao in self.modelo.ligacoes:
            adjacencias[ligacao.origem].add(ligacao.destino)
            adjacencias[ligacao.destino].add(ligacao.origem)

        componentes = 0
        visitados = set()
        for atomo_id in adjacencias:
            if atomo_id in visitados:
                continue
            componentes += 1
            pilha = [atomo_id]
            while pilha:
                atual = pilha.pop()
                if atual in visitados:
                    continue
                visitados.add(atual)
                pilha.extend(adjacencias[atual] - visitados)

        ciclos_independentes = (
            len(self.modelo.ligacoes) - len(self.modelo.atomos) + componentes
        )
        ciclos_faltantes = max(
            0, ciclos_independentes - len(self.modelo.aneis)
        )
        if ciclos_faltantes == 0:
            return

        if ciclos_faltantes == 1:
            mensagem = (
                "o grafo contém 1 ciclo não declarado; use 'ring' para "
                "identificá-lo"
            )
        else:
            mensagem = (
                f"o grafo contém {ciclos_faltantes} ciclos independentes não "
                "declarados; use 'ring' para identificá-los"
            )
        self.aviso("RING-004", self.molecula, mensagem)


    # ---------- valência e carga ----------

    def classificar_ligacoes(self):
        """Classifica ligações por Δχ; o resultado nunca bloqueia a análise."""
        por_id = {a.id: a for a in self.modelo.atomos}
        limite_apolar = self.classificacao["limite_apolar"]
        limite_ionica = self.classificacao["limite_ionica"]

        for lig in self.modelo.ligacoes:
            if lig.operador is Operador.METALICA:
                lig.classificacao = "metálica"
                continue

            origem = por_id[lig.origem]
            destino = por_id[lig.destino]
            eletronegatividade_origem = self.dados_elementos[
                origem.elemento
            ]["eletronegatividade"]
            eletronegatividade_destino = self.dados_elementos[
                destino.elemento
            ]["eletronegatividade"]

            if (
                eletronegatividade_origem is None
                or eletronegatividade_destino is None
            ):
                continue

            diferenca = abs(
                eletronegatividade_origem - eletronegatividade_destino
            )
            lig.diferenca_eletronegatividade = diferenca
            if diferenca < limite_apolar:
                lig.classificacao = "covalente apolar"
            elif diferenca <= limite_ionica:
                lig.classificacao = "covalente polar"
            else:
                lig.classificacao = "iônica"

    def conferir_coordenadas(self):
        """Confere o par livre do doador e o espaço eletrônico do receptor."""
        por_id = {a.id: a for a in self.modelo.atomos}
        ordem = self.valencias["ordem_ligacao"]
        totais = {a.id: 0 for a in self.modelo.atomos}
        for lig in self.modelo.ligacoes:
            if lig.operador is Operador.METALICA:
                continue
            valor = ordem[lig.operador.name]
            totais[lig.origem] += valor
            totais[lig.destino] += valor

        for lig in self.modelo.ligacoes:
            if lig.operador is not Operador.COORDENADA:
                continue

            doador = por_id[lig.origem]
            eletrons_valencia = self.dados_elementos[doador.elemento][
                "eletrons_valencia"
            ]
            if eletrons_valencia is None:
                self.aviso(
                    "COORD-002",
                    lig,
                    f"não há dados suficientes para conferir o par livre de "
                    f"{doador.rotulo()}",
                )
            else:
                # Antes da doação, a ligação coordenada ainda não contribuía
                # para a ordem e a carga do doador era uma unidade menor.
                ordem_antes = totais[doador.id] - ordem["COORDENADA"]
                carga_antes = doador.carga - 1
                eletrons_nao_ligantes = (
                    eletrons_valencia - carga_antes - ordem_antes
                )
                if eletrons_nao_ligantes < 2:
                    self.aviso(
                        "COORD-001",
                        lig,
                        f"o doador {doador.rotulo()} não possui um par de "
                        "elétrons livre para a ligação coordenada",
                    )

            receptor = por_id[lig.destino]
            dados_receptor = self.dados_elementos[receptor.elemento]
            numero_atomico = dados_receptor["numero_atomico"]
            eletrons_valencia_receptor = dados_receptor["eletrons_valencia"]
            if eletrons_valencia_receptor is None or numero_atomico > 10:
                self.aviso(
                    "COORD-004",
                    lig,
                    f"não há dados suficientes para conferir orbital vazio de "
                    f"{receptor.rotulo()}",
                )
                continue

            # Antes de aceitar o par, a ordem era uma unidade menor e a carga
            # formal do receptor era uma unidade maior. H e He seguem dueto;
            # os demais elementos do segundo período, octeto.
            ordem_antes_receptor = (
                totais[receptor.id] - ordem["COORDENADA"]
            )
            carga_antes_receptor = receptor.carga + 1
            eletrons_nao_ligantes_receptor = (
                eletrons_valencia_receptor
                - carga_antes_receptor
                - ordem_antes_receptor
            )
            eletrons_ao_redor = (
                2 * ordem_antes_receptor
                + eletrons_nao_ligantes_receptor
            )
            capacidade = 2 if numero_atomico <= 2 else 8
            if eletrons_ao_redor >= capacidade:
                self.aviso(
                    "COORD-003",
                    lig,
                    f"o modelo de dueto/octeto não identificou capacidade "
                    f"receptora em {receptor.rotulo()} para receber o par",
                )

    def conferir_ligacoes_metalicas(self):
        """Avisa quando `~` envolve elemento não classificado como metal."""
        por_id = {atomo.id: atomo for atomo in self.modelo.atomos}
        for ligacao in self.modelo.ligacoes:
            if ligacao.operador is not Operador.METALICA:
                continue

            participantes = (
                por_id[ligacao.origem],
                por_id[ligacao.destino],
            )
            nao_metalicos = []
            for atomo in participantes:
                bloco = self.dados_elementos[atomo.elemento]["bloco"]
                if bloco not in self.blocos_metalicos:
                    nao_metalicos.append(f"{atomo.rotulo()} ({bloco})")

            if nao_metalicos:
                self.aviso(
                    "METAL-001",
                    ligacao,
                    "a ligação metálica envolve participante não metálico: "
                    + ", ".join(nao_metalicos),
                )

    def conferir_valencias(self):
        # Só usa os dados de regras/valencias.json: elemento ou carga sem
        # dado não é conferido
        regras = self.valencias
        ordem = regras["ordem_ligacao"]
        por_id = {a.id: a for a in self.modelo.atomos}

        # Limites seguros viram erro; padrões usuais de elementos pesados
        # viram aviso, pois não são tetos físicos universais.
        erros_avisados = set()
        avisos_emitidos = set()
        maximos_estritos = regras["ordem_ligacao_maxima_estrita"]
        ordens_incomuns = regras["ordem_ligacao_incomum"]
        for lig in self.modelo.ligacoes:
            if lig.operador not in (Operador.DUPLA, Operador.TRIPLA):
                continue
            valor_ordem = ordem[lig.operador.name]
            tipo = "dupla" if lig.operador is Operador.DUPLA else "tripla"
            for atomo in (por_id[lig.origem], por_id[lig.destino]):
                posicao = (lig.linha, lig.coluna)
                maximo = maximos_estritos.get(atomo.elemento)
                if maximo is not None and valor_ordem > maximo:
                    if posicao in erros_avisados:
                        continue
                    erros_avisados.add(posicao)
                    self.erro(
                        "BOND-001",
                        lig,
                        f"{atomo.elemento} só faz ligação simples, mas {atomo.rotulo()} "
                        f"está numa ligação {tipo}",
                    )
                    continue

                usual = ordens_incomuns.get(atomo.elemento)
                if usual is not None and valor_ordem > usual:
                    if posicao in avisos_emitidos:
                        continue
                    avisos_emitidos.add(posicao)
                    self.aviso(
                        "BOND-002",
                        lig,
                        f"ligação {tipo} com {atomo.elemento} é incomum no "
                        "perfil Lewis introdutório; trate a ordem como "
                        "representação formal",
                    )
        if self.tem_erro():
            return

        soma = {a.id: 0 for a in self.modelo.atomos}
        vizinhos = {a.id: [] for a in self.modelo.atomos}
        metalicos = set()
        self.avisos_valencia = {}
        for lig in self.modelo.ligacoes:
            if lig.operador is Operador.METALICA:
                metalicos.update((lig.origem, lig.destino))
                continue
            for a, b in ((lig.origem, lig.destino), (lig.destino, lig.origem)):
                soma[a] += ordem[lig.operador.name]
                vizinhos[a].append(por_id[b].elemento)

        for atomo in self.modelo.atomos:
            if atomo.id in metalicos:
                continue
            self.conferir_atomo(atomo, soma[atomo.id], vizinhos[atomo.id])
        self.emitir_avisos_valencia()

    def valencias_neutras(self, atomo, vizinhos):
        regras = self.valencias
        aceitas = regras["valencias"].get(atomo.elemento)
        if aceitas is None:
            return None

        expandidas = regras["valencias_expandidas"].get(atomo.elemento)
        if expandidas and vizinhos and all(v in expandidas["vizinhos"] for v in vizinhos):
            return expandidas["valencias"]

        return aceitas

    def valencias_carregadas(self, elemento):
        # Devolve {carga: [valências]} do elemento, com a carga como inteiro
        tabela = self.valencias["valencias_com_carga"].get(elemento, {})
        return {int(carga): aceitas for carga, aceitas in tabela.items()}

    def conferir_atomo(self, atomo, total, vizinhos):
        el = atomo.elemento
        com_carga = self.valencias_carregadas(el)

        if atomo.carga != 0:
            aceitas = com_carga.get(atomo.carga)
            if aceitas is not None and total not in aceitas:
                self.erro(
                    "CARGA-001",
                    atomo,
                    f"{atomo.rotulo()} com carga {atomo.carga:+d} deveria ter soma das "
                    f"ordens de ligação {self.listar(aceitas)}, mas tem {total}",
                )
            return

        aceitas = self.valencias_neutras(atomo, vizinhos)
        if aceitas is None:
            return

        if total in aceitas:
            return

        # Carga conhecida em que essa soma seria válida, se houver
        carga_possivel = next(
            (carga for carga, valencias in com_carga.items() if total in valencias),
            None,
        )

        if total > max(aceitas):
            # Acima da valência neutra, a carga é a única saída (ex.: N com 4)
            if carga_possivel is not None:
                self.erro(
                    "CARGA-001",
                    atomo,
                    f"a soma das ordens de ligação de {atomo.rotulo()} é {total}, o que "
                    f"só é possível com carga {carga_possivel:+d}: "
                    f"declare atom {el}({carga_possivel:+d})",
                )
            else:
                self.erro(
                    "VAL-001",
                    atomo,
                    f"a soma das ordens de ligação de {atomo.rotulo()} é {total}; "
                    f"o máximo para {el} é {max(aceitas)}",
                )
            return

        # Abaixo da valência pode ser um radical, então é só aviso.
        # Átomos da mesma declaração e com o mesmo resultado são agrupados.
        chave = (
            atomo.linha,
            atomo.coluna,
            atomo.elemento,
            total,
            tuple(aceitas),
            carga_possivel,
        )
        self.avisos_valencia.setdefault(chave, []).append(atomo)

    def emitir_avisos_valencia(self):
        for chave, atomos in self.avisos_valencia.items():
            _, _, elemento, total, aceitas, carga_possivel = chave
            if len(atomos) == 1:
                sujeito = f"de {atomos[0].rotulo()}"
            else:
                rotulos = ", ".join(atomo.rotulo() for atomo in atomos)
                sujeito = f"dos átomos {rotulos}"

            mensagem = (
                f"a soma das ordens de ligação {sujeito} é {total}; "
                f"o esperado para {elemento} é {self.listar(aceitas)}"
            )
            if carga_possivel is not None:
                mensagem += (
                    f" (se for um íon, declare "
                    f"atom {elemento}({carga_possivel:+d}))"
                )
            self.aviso("VAL-002", atomos[0], mensagem)

    @staticmethod
    def listar(valores):
        # [4] vira "4"; [2, 4, 6] vira "2, 4 ou 6"
        textos = [str(v) for v in valores]
        if len(textos) == 1:
            return textos[0]
        return ", ".join(textos[:-1]) + " ou " + textos[-1]


def analisar(molecula):
    # Devolve o modelo e a lista de mensagens semânticas (erros e avisos)
    return AnalisadorSemantico(
        molecula,
        carregar_elementos(),
        carregar_valencias(),
        carregar_classificacao(),
        carregar_ligacoes_metalicas(),
    ).analisar()
