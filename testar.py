import glob
import importlib.util
import json
import os
import subprocess
import sys
import tempfile


# Roda o src/main.py em todos os exemplos e confere o resultado:
# - exemplos/: devem passar sem erros nem avisos (código de saída 0)
# - invalidos/, invalidos_sintaticos/, invalidos_semanticos/ e
#   avisos_semanticos/: cada arquivo diz, em linhas
#   "// esperado: <mensagem completa>", os erros e avisos que devem
#   aparecer, na ordem. A saída deve ter exatamente essas mensagens e o
#   código de saída da pasta (0, 1 ou 2).

PASTA_RAIZ = os.path.dirname(os.path.abspath(__file__))
MAIN = os.path.join(PASTA_RAIZ, "src", "main.py")
DESENHAR_ARVORE = os.path.join(PASTA_RAIZ, "src", "desenhar_arvore.py")

PASTAS_VALIDOS = ["exemplos"]
# Pasta e código de saída esperado
PASTAS_COM_MENSAGENS = {
    "invalidos": 1,
    "invalidos_sintaticos": 1,
    "invalidos_semanticos": 2,
    "avisos_semanticos": 0,
}

MARCA_ESPERADO = "// esperado:"


def arquivos(pasta):
    return sorted(glob.glob(os.path.join(PASTA_RAIZ, pasta, "*.mol")))


def rodar(caminho):
    # Força UTF-8 para os acentos das mensagens também no Windows
    ambiente = dict(os.environ, PYTHONIOENCODING="utf-8")
    resultado = subprocess.run(
        [sys.executable, MAIN, caminho],
        capture_output=True,
        env=ambiente,
    )
    saida = (resultado.stdout + resultado.stderr).decode("utf-8")
    mensagens = [
        linha for linha in saida.splitlines()
        if linha.startswith("Erro ") or linha.startswith("Aviso ")
    ]
    return resultado.returncode, saida, mensagens


def rodar_comando(argumentos, ambiente_extra=None, script=MAIN):
    ambiente = dict(os.environ, PYTHONIOENCODING="utf-8")
    ambiente.update(ambiente_extra or {})
    resultado = subprocess.run(
        [sys.executable, script, *argumentos],
        capture_output=True,
        env=ambiente,
    )
    saida = (resultado.stdout + resultado.stderr).decode("utf-8")
    return resultado.returncode, saida


def erros_esperados(caminho):
    # Os casos de BOM e de arquivo fora de UTF-8 também precisam ser lidos
    with open(caminho, encoding="utf-8-sig", errors="replace") as arquivo:
        linhas = arquivo.read().splitlines()
    return [
        linha[len(MARCA_ESPERADO):].strip()
        for linha in linhas
        if linha.startswith(MARCA_ESPERADO)
    ]


def testar_valido(caminho):
    # Devolve a lista de problemas encontrados (vazia se passou)
    codigo, saida, erros = rodar(caminho)
    problemas = []

    if codigo != 0:
        problemas.append(f"código de saída {codigo}, esperado 0")
    if erros:
        problemas.extend(f"mensagem inesperada: {e}" for e in erros)
    if codigo != 0 and not erros:
        problemas.append(f"saída: {saida.strip()}")

    return problemas


def testar_com_mensagens(caminho, codigo_esperado):
    esperados = erros_esperados(caminho)

    if not esperados:
        return [f"o arquivo não tem nenhuma linha '{MARCA_ESPERADO}'"]

    codigo, saida, erros = rodar(caminho)
    problemas = []

    if codigo != codigo_esperado:
        problemas.append(f"código de saída {codigo}, esperado {codigo_esperado}")

    for i in range(max(len(esperados), len(erros))):
        esperado = esperados[i] if i < len(esperados) else None
        obtido = erros[i] if i < len(erros) else None

        if esperado is None:
            problemas.append(f"mensagem a mais: {obtido}")
        elif obtido is None:
            problemas.append(f"faltou a mensagem: {esperado}")
        elif obtido != esperado:
            problemas.append(f"esperado: {esperado}")
            problemas.append(f"obtido:   {obtido}")

    return problemas


def testar_arquivo_inexistente():
    caminho = os.path.join(PASTA_RAIZ, "nao_existe.mol")
    codigo, saida = rodar_comando([caminho])
    esperado = "Erro de entrada [ENT-001]: arquivo não encontrado:"
    problemas = []
    if codigo != 1:
        problemas.append(f"código de saída {codigo}, esperado 1")
    if esperado not in saida:
        problemas.append(f"saída não contém: {esperado}")
        problemas.append(f"saída: {saida.strip()}")
    return problemas


def testar_gerado_ausente():
    with tempfile.TemporaryDirectory() as pasta_vazia:
        codigo, saida = rodar_comando(
            [os.path.join(PASTA_RAIZ, "exemplos", "agua.mol")],
            {"MOLECULEDSL_GERADO": pasta_vazia},
        )
    esperado = "Erro de configuração [CFG-001]: código do ANTLR não encontrado"
    problemas = []
    if codigo != 1:
        problemas.append(f"código de saída {codigo}, esperado 1")
    if esperado not in saida:
        problemas.append(f"saída não contém: {esperado}")
        problemas.append(f"saída: {saida.strip()}")
    return problemas


def testar_limite_de_erros():
    with tempfile.TemporaryDirectory() as pasta:
        caminho = os.path.join(pasta, "muitos_erros.mol")
        with open(caminho, "w", encoding="utf-8") as arquivo:
            arquivo.write('molecule "Muitos erros" {\\n    @@@@@@@@@@@@\\n}\\n')
        codigo, saida = rodar_comando([caminho])

    problemas = []
    quantidade = saida.count("Erro léxico [LEX-001]")
    if codigo != 1:
        problemas.append(f"código de saída {codigo}, esperado 1")
    if quantidade != 10:
        problemas.append(f"{quantidade} erros exibidos, esperado limite de 10")
    if "Aviso de compilação [LIM-001]" not in saida:
        problemas.append("faltou o aviso de erros omitidos")
    return problemas


def testar_ast(caminho):
    codigo, saida = rodar_comando(["--ast", caminho])
    linhas = saida.splitlines()
    if linhas and linhas[-1].startswith("Espécie "):
        linhas.pop()
    obtido = "\n".join(linhas).strip()

    esperado_path = os.path.splitext(caminho)[0] + ".ast.txt"
    with open(esperado_path, encoding="utf-8") as arquivo:
        esperado = arquivo.read().strip()

    problemas = []
    if codigo != 0:
        problemas.append(f"código de saída {codigo}, esperado 0")
    if obtido != esperado:
        problemas.append(f"AST diferente de {os.path.relpath(esperado_path, PASTA_RAIZ)}")
    return problemas


def testar_modelo(caminho):
    codigo, saida = rodar_comando(["--modelo", caminho])
    esperado_path = os.path.splitext(caminho)[0] + ".modelo.txt"
    with open(esperado_path, encoding="utf-8") as arquivo:
        esperado = arquivo.read()

    problemas = []
    if codigo != 0:
        problemas.append(f"código de saída {codigo}, esperado 0")
    if saida != esperado:
        problemas.append(
            f"modelo diferente de "
            f"{os.path.relpath(esperado_path, PASTA_RAIZ)}"
        )
    return problemas


def testar_solver(caminho):
    codigo, saida = rodar_comando(["--resolver", "--modelo", caminho])
    esperados = erros_esperados(caminho)
    problemas = []
    if esperados:
        mensagens = [
            linha
            for linha in saida.splitlines()
            if linha.startswith(("Erro ", "Aviso "))
        ]
        if codigo != 2:
            problemas.append(f"código de saída {codigo}, esperado 2")
        if mensagens != esperados:
            problemas.append(f"mensagens obtidas: {mensagens}")
            problemas.append(f"mensagens esperadas: {esperados}")
        return problemas

    esperado_path = os.path.splitext(caminho)[0] + ".saida.txt"
    with open(esperado_path, encoding="utf-8") as arquivo:
        esperado = arquivo.read()
    if codigo != 0:
        problemas.append(f"código de saída {codigo}, esperado 0")
    if saida != esperado:
        problemas.append(
            f"saída diferente de "
            f"{os.path.relpath(esperado_path, PASTA_RAIZ)}"
        )
    return problemas


def testar_solver_todas(caminho):
    codigo, saida = rodar_comando(["--resolver-todas", caminho])
    esperado_path = os.path.splitext(caminho)[0] + ".todas.txt"
    with open(esperado_path, encoding="utf-8") as arquivo:
        esperado = arquivo.read()
    problemas = []
    if codigo != 0:
        problemas.append(f"código de saída {codigo}, esperado 0")
    if saida != esperado:
        problemas.append(
            f"enumeração diferente de "
            f"{os.path.relpath(esperado_path, PASTA_RAIZ)}"
        )
    return problemas


def chaves_canonicas(resultado_solver):
    # Conjunto das chaves canônicas das soluções, para comparar resultados
    # sem depender da ordem ou dos nomes gerados.
    from ast_nos import LigacaoDecl
    from solver.canonical import canonical_key
    from solver.problem import normalize

    chaves_resultado = set()
    for solucao in resultado_solver.solutions:
        problema, _ = normalize(
            type(solucao)(
                nome=solucao.nome,
                linha=solucao.linha,
                coluna=solucao.coluna,
                comandos=[
                    comando
                    for comando in solucao.comandos
                    if not isinstance(comando, LigacaoDecl)
                ],
                tipo=solucao.tipo,
                carga_total=solucao.carga_total,
                eletrons_desemparelhados=(
                    solucao.eletrons_desemparelhados
                ),
                declaracao_legacy=solucao.declaracao_legacy,
            )
        )
        nomes = {
            atomo.name: atomo.index for atomo in problema.atoms
        }
        arestas = {}
        for comando in solucao.comandos:
            if isinstance(comando, LigacaoDecl):
                par = tuple(
                    sorted(
                        (
                            nomes[comando.origem.texto],
                            nomes[comando.destino.texto],
                        )
                    )
                )
                arestas[par] = {
                    "-": 1,
                    "=": 2,
                    "#": 3,
                }[comando.operador.value]
        chaves_resultado.add(
            canonical_key(arestas, problema.atoms)
        )
    return chaves_resultado


def escrever_mol(pasta, nome, linhas):
    arquivo = os.path.join(pasta, nome)
    with open(arquivo, "w", encoding="utf-8") as saida:
        saida.write("\n".join(linhas) + "\n")
    return arquivo


def testar_fases_solver():
    src = os.path.join(PASTA_RAIZ, "src")
    if src not in sys.path:
        sys.path.insert(0, src)

    from construtor_ast import construir
    from sintatico import analisar
    import semantico
    import solver
    from solver.backtracking import feasible
    from solver.result import SolveStatus, Uniqueness

    regras = semantico.carregar_valencias()
    problemas = []

    def resolver_arquivo(caminho, **opcoes):
        opcoes.setdefault("max_solutions", 10)
        opcoes.setdefault("require_unique", False)
        return solver.solve(
            construir(analisar(caminho)),
            regras,
            solver.SolveRequest(**opcoes),
        )

    # Fase 0: perfil químico com nome e versão explícitos
    agua = os.path.join(PASTA_RAIZ, "resolver", "agua.mol")
    detalhes = resolver_arquivo(agua).summary.details
    if detalhes.get("chemical_profile") != "lewis-introdutorio":
        problemas.append("nome do perfil químico ausente no sumário")
    if detalhes.get("chemical_profile_version") != "1":
        problemas.append("versão do perfil químico ausente no sumário")

    # Fase 1: podas seguras
    casos_poda = [
        ((4, 2), True),
        ((3, 2), False),
        ((4, 0, 2), False),
        ((1, 1, 1, 1), False),
        ((2, 2, 1, 1), True),
        ((1, 1, 1, 1, 2), False),
    ]
    for residual, esperado in casos_poda:
        if feasible(residual) is not esperado:
            problemas.append(f"poda errada para residual {residual}")

    # Fase 2: invariância sob permutação das declarações
    with tempfile.TemporaryDirectory() as pasta:
        ordens = [
            ["    2x atom C", "    atom O", "    6x atom H"],
            ["    6x atom H", "    atom O", "    2x atom C"],
            ["    atom C", "    3x atom H", "    atom O", "    atom C", "    3x atom H"],
        ]
        conjuntos = []
        for indice, corpo in enumerate(ordens):
            arquivo = escrever_mol(
                pasta,
                f"permutacao{indice}.mol",
                ['species molecule "Permutação" {', *corpo, "}"],
            )
            conjuntos.append(chaves_canonicas(resolver_arquivo(arquivo)))
        if any(conjunto != conjuntos[0] for conjunto in conjuntos):
            problemas.append("soluções mudaram com a ordem das declarações")
        if len(conjuntos[0]) != 2:
            problemas.append(
                f"C2H6O deveria ter 2 classes, obtido {len(conjuntos[0])}"
            )

    # Fase 3: entrega em fluxo sem acumular soluções
    ambigua = os.path.join(PASTA_RAIZ, "resolver", "formula_ambigua.mol")
    recebidas = []
    em_fluxo = resolver_arquivo(
        ambigua,
        max_solutions=2,
        on_solution=lambda estrutura, indice: recebidas.append(indice),
    )
    if em_fluxo.solutions:
        problemas.append("modo em fluxo acumulou soluções no resultado")
    if recebidas != [1, 2]:
        problemas.append(f"índices entregues em fluxo: {recebidas}")
    if em_fluxo.summary.status is not SolveStatus.LIMIT_REACHED:
        problemas.append("fluxo limitado não retornou LIMIT_REACHED")
    acumulado = resolver_arquivo(ambigua)
    recebidas_todas = []
    resolver_arquivo(
        ambigua,
        on_solution=lambda estrutura, indice: recebidas_todas.append(
            estrutura
        ),
    )
    if len(recebidas_todas) != len(acumulado.solutions):
        problemas.append("fluxo e lista devolveram quantidades diferentes")

    # Fase 6: filtros objetivos
    filtros = [
        (solver.SolveFilters(rings=1), 1),
        (solver.SolveFilters(rings=0), 2),
        (solver.SolveFilters(multiple_bonds=1), 2),
        (solver.SolveFilters(required=(solver.parse_fragment("C=O"),)), 1),
        (solver.SolveFilters(forbidden=(solver.parse_fragment("O-H"),)), 2),
        (
            solver.SolveFilters(
                rings=0,
                forbidden=(solver.parse_fragment("C=O"),),
            ),
            1,
        ),
        (solver.SolveFilters(required=(solver.parse_fragment("C=C-O"),)), 1),
        (solver.SolveFilters(required=(solver.parse_fragment("H-C=O"),)), 1),
        (solver.SolveFilters(required=(solver.parse_fragment("C-O-C"),)), 1),
        (solver.SolveFilters(forbidden=(solver.parse_fragment("O-C-C"),)), 2),
    ]
    for filtro, esperado in filtros:
        resultado = resolver_arquivo(ambigua, filters=filtro)
        if len(resultado.solutions) != esperado:
            problemas.append(
                f"filtro {filtro.describe()}: "
                f"{len(resultado.solutions)} soluções, esperado {esperado}"
            )
    unica = resolver_arquivo(
        ambigua,
        max_solutions=2,
        require_unique=True,
        filters=solver.SolveFilters(
            rings=0, forbidden=(solver.parse_fragment("C=O"),)
        ),
    )
    if unica.summary.unique is not Uniqueness.TRUE:
        problemas.append("filtro que deixa uma estrutura não deu unicidade")
    vazio = resolver_arquivo(ambigua, filters=solver.SolveFilters(rings=2))
    if vazio.summary.status is not SolveStatus.UNSAT or not str(
        vazio.messages[0]
    ).endswith("e os filtros pedidos"):
        problemas.append("filtro impossível não retornou SOLVER-003")
    if solver.parse_fragment("CO") is not None:
        problemas.append("fragmento sem operador foi aceito")

    codigo, saida = rodar_comando(
        ["--resolver-todas", "--exigir=C=O", "--formato=jsonl", ambigua]
    )
    linhas = [json.loads(linha) for linha in saida.splitlines()]
    if codigo != 0 or len(linhas) != 2:
        problemas.append("CLI com --exigir não devolveu uma solução")
    elif linhas[-1]["details"]["filters"] != ["exigir=C=O"]:
        problemas.append("filtros não aparecem no sumário da CLI")
    codigo, saida = rodar_comando(["--aneis=1", agua])
    if codigo != 1:
        problemas.append("filtro sem opção de resolução foi aceito")

    try:
        import ortools  # noqa: F401
    except ImportError:
        ortools = None
    if ortools is not None:
        for filtro, _ in filtros:
            referencia = resolver_arquivo(ambigua, filters=filtro)
            cpsat = resolver_arquivo(ambigua, filters=filtro, backend="cpsat")
            if chaves_canonicas(referencia) != chaves_canonicas(cpsat):
                problemas.append(
                    f"backends divergem com o filtro {filtro.describe()}"
                )
    return problemas


def testar_fases_quimicas():
    src = os.path.join(PASTA_RAIZ, "src")
    if src not in sys.path:
        sys.path.insert(0, src)

    from construtor_ast import construir
    from sintatico import analisar
    import complexos
    import eletronico
    import estereo
    import semantico
    import solver
    from solver.canonical import is_canonical_heavy
    from solver.problem import SolverAtom

    elementos = semantico.carregar_elementos()
    valencias = semantico.carregar_valencias()
    metalicas = semantico.carregar_ligacoes_metalicas()
    problemas = []

    def modelo_de(*partes):
        modelo, _ = semantico.analisar(
            construir(analisar(os.path.join(PASTA_RAIZ, *partes)))
        )
        return modelo

    # Fase 5: uma rotulação por classe, sem conjunto de chaves
    carbonos = [SolverAtom(i, "C", 0, 1, 0, f"c{i}") for i in range(3)]
    cadeias = [{(0, 1): 1, (1, 2): 1}, {(0, 2): 1, (1, 2): 1}, {(0, 1): 1, (0, 2): 1}]
    # O átomo central de cada cadeia tem 2 H; as pontas, 3
    hidrogenios = [(3, 2, 3), (3, 3, 2), (2, 3, 3)]
    aceitas = [
        is_canonical_heavy(arestas, carbonos, h)
        for arestas, h in zip(cadeias, hidrogenios)
    ]
    if sum(aceitas) != 1:
        problemas.append(f"propano canônico aceito {sum(aceitas)} vez(es)")
    with tempfile.TemporaryDirectory() as pasta:
        for nc, nh, esperado in ((4, 8, 5), (5, 10, 10), (4, 6, 9)):
            arquivo = escrever_mol(
                pasta,
                f"c{nc}h{nh}.mol",
                ['species molecule "X" {', f"    {nc}x atom C", f"    {nh}x atom H", "}"],
            )
            resultado = solver.solve(
                construir(analisar(arquivo)),
                valencias,
                solver.SolveRequest(max_solutions=50, require_unique=False),
            )
            if len(resultado.solutions) != esperado:
                problemas.append(
                    f"C{nc}H{nh}: {len(resultado.solutions)} classes, "
                    f"esperado {esperado}"
                )

    # Fase 7: modelo eletrônico e ressonância
    formas_esperadas = {
        "carbonato": 3,
        "benzeno": 2,
        "acetato": 2,
        "ozonio": 2,
        "agua": 1,
        "cianeto": 1,
    }
    for nome, esperado in formas_esperadas.items():
        formas, _, _ = eletronico.formas_de_ressonancia(
            modelo_de("exemplos", f"{nome}.mol"), elementos, valencias
        )
        if len(formas) != esperado:
            problemas.append(
                f"ressonância de {nome}: {len(formas)}, esperado {esperado}"
            )
    pares = {
        estado.atomo.carga: estado.pares_livres
        for estado in eletronico.estados(
            modelo_de("exemplos", "carbonato.mol"), elementos, valencias
        )
        if estado.atomo.elemento == "O"
    }
    if pares != {0: 2, -1: 3}:
        problemas.append(f"pares livres do carbonato: {pares}")
    formas, observacoes, _ = eletronico.formas_de_ressonancia(
        modelo_de("exemplos", "amonio_por_ligacao_coordenada.mol"),
        elementos,
        valencias,
    )
    if len(formas) != 1 or not any("coordenadas" in o for o in observacoes):
        problemas.append("ressonância não manteve a ligação coordenada fixa")

    # Fase 8: elementos estereogênicos
    casos_estereo = {
        "butan_2_ol": (1, 0),
        "but_2_eno": (0, 1),
        "glicerol": (0, 0),
        "ciclohexeno": (0, 0),
        "isopropanol": (0, 0),
    }
    for nome, (centros_esperados, duplas_esperadas) in casos_estereo.items():
        modelo = modelo_de("exemplos", f"{nome}.mol")
        resultado, _, _ = estereo.analisar(modelo, elementos, valencias)
        tipos = [resultado.elementos[i].tipo for i in resultado.estereogenicos]
        if (tipos.count("centro"), tipos.count("dupla")) != (
            centros_esperados,
            duplas_esperadas,
        ):
            problemas.append(f"estereoquímica de {nome}: {tipos}")
    modelo = modelo_de("exemplos", "butan_2_ol.mol")
    resultado, _, _ = estereo.analisar(modelo, elementos, valencias)
    por_id = {a.id: a for a in modelo.atomos}
    centro = resultado.elementos[resultado.estereogenicos[0]]
    ordem = [por_id[nivel[0]].nome for nivel in centro.prioridades[0]]
    if ordem != ["o", "c3", "c1", "h5"]:
        problemas.append(f"prioridades CIP do butan-2-ol: {ordem}")

    # Fase 9: coordenação e sólidos
    niquel = complexos.analisar(
        modelo_de("avisos_semanticos", "tetracarbonilniquel.mol"),
        elementos,
        valencias,
        metalicas,
    )
    centro = niquel["centros"][0]
    if centro["oxidacao"] != 0 or sum(centro["eletrons"]) != 18:
        problemas.append(f"Ni(CO)4: {centro}")
    if [ligante["carga"] for ligante in niquel["ligantes"]] != [0, 0, 0, 0]:
        problemas.append("ligantes CO de Ni(CO)4 não ficaram neutros")
    sal = complexos.analisar(
        modelo_de("exemplos", "cloreto_de_sodio.mol"), elementos, valencias, metalicas
    )
    if sal["centros"][0]["oxidacao"] != 1 or sal["ligantes"][0]["carga"] != -1:
        problemas.append("NaCl não deu Na(+1) e Cl(-1)")
    sodio = complexos.analisar(
        modelo_de("exemplos", "sodio_metalico.mol"), elementos, valencias, metalicas
    )
    if sodio["centros"] or sodio["motivos"].get("metálica") != 1:
        problemas.append("sódio metálico não ficou como motivo metálico")

    codigo, saida = rodar_comando(
        ["--eletronico", "--ressonancia", "--estereo", "--coordenacao",
         os.path.join(PASTA_RAIZ, "exemplos", "butan_2_ol.mol")]
    )
    for trecho in ("Modelo eletrônico", "Ressonância:", "Centros estereogênicos", "Coordenação:"):
        if trecho not in saida:
            problemas.append(f"CLI não mostrou '{trecho}'")
    if codigo != 0:
        problemas.append(f"CLI dos relatórios saiu com código {codigo}")
    return problemas


def molecula_com_h(pasta, nome, atomos, ligacoes, extras=()):
    # Gera um .mol com os H que completam C(4), N(3), O(2), S(2) e
    # halogênios(1); atomos é "c1:C o1:O ..." e ligacoes "c1-c2 c2=o1 ..."
    valencia = {"C": 4, "N": 3, "O": 2, "S": 2, "Cl": 1, "Br": 1}
    elementos = dict(par.split(":") for par in atomos.split())
    soma = dict.fromkeys(elementos, 0)
    linhas = [f'molecule "{nome}" {{']
    linhas += [f"    atom {e} as {n}" for n, e in elementos.items()]
    corpo = []
    for ligacao in ligacoes.split():
        for simbolo, ordem in (("=", 2), ("#", 3), ("-", 1)):
            if simbolo in ligacao:
                a, b = ligacao.split(simbolo)
                soma[a] += ordem
                soma[b] += ordem
                corpo.append(f"    bond {ligacao}")
                break
    donos = []
    for n, e in elementos.items():
        alvo = soma[n] if e == "S" and soma[n] > 2 else valencia[e]
        donos += [n] * (alvo - soma[n])
    if donos:
        linhas.append(f"    {len(donos)}x atom H as h")
    linhas += corpo
    linhas += [f"    bond {n}-h{i}" for i, n in enumerate(donos, start=1)]
    linhas += [f"    {extra}" for extra in extras]
    linhas.append("}")
    return escrever_mol(pasta, f"{nome}.mol", linhas)


def testar_limites():
    """Plano de limites (docs/plano_limites.md), itens L1 a L9."""
    src = os.path.join(PASTA_RAIZ, "src")
    if src not in sys.path:
        sys.path.insert(0, src)

    from construtor_ast import construir
    from sintatico import analisar
    import aromaticidade
    import eletronico
    import estereo
    import semantico
    import solver
    import tautomeros
    from solver.canonical import column_pairs

    elementos = semantico.carregar_elementos()
    valencias = semantico.carregar_valencias()
    problemas = []

    def modelo_de(caminho):
        modelo, mensagens = semantico.analisar(construir(analisar(caminho)))
        if any(m.severidade == semantico.ERRO for m in mensagens):
            raise AssertionError(f"{caminho}: {mensagens}")
        return modelo

    def exemplo(nome):
        return modelo_de(os.path.join(PASTA_RAIZ, "exemplos", f"{nome}.mol"))

    with tempfile.TemporaryDirectory() as pasta:
        # L1: poda ordenada, com a ordem coluna a coluna
        if column_pairs(4) != [(0, 1), (0, 2), (1, 2), (0, 3), (1, 3), (2, 3)]:
            problemas.append("pares fora da ordem coluna a coluna")
        for formula, carbonos, hidrogenios, esperado in (
            ("C7H16", 7, 16, 9),
            ("C6H12", 6, 12, 25),
            ("C6H6", 6, 6, 217),
        ):
            arquivo = escrever_mol(
                pasta,
                f"{formula}.mol",
                [f'molecule "{formula}" {{', f"    {carbonos}x atom C",
                 f"    {hidrogenios}x atom H", "}"],
            )
            for backend in ("reference", "cpsat"):
                if backend == "cpsat" and importlib.util.find_spec("ortools") is None:
                    continue
                resultado = solver.solve(
                    construir(analisar(arquivo)),
                    valencias,
                    solver.SolveRequest(
                        max_solutions=1000, require_unique=False, backend=backend
                    ),
                )
                if resultado.summary.solutions_emitted != esperado:
                    problemas.append(
                        f"{formula} ({backend}): "
                        f"{resultado.summary.solutions_emitted}, esperado {esperado}"
                    )

        # L3: fragmentos em cadeia
        if str(solver.parse_fragment("O-C=O")) != "O-C=O":
            problemas.append("fragmento O-C=O não foi lido como cadeia")
        if solver.parse_fragment("C=") is not None:
            problemas.append("fragmento incompleto foi aceito")

        # L4: busca isolada num processo separado
        ambigua = os.path.join(PASTA_RAIZ, "resolver", "formula_ambigua.mol")
        isolado = solver.solve(
            construir(analisar(ambigua)),
            valencias,
            solver.SolveRequest(max_solutions=10, require_unique=False, isolate=True),
        )
        if len(isolado.solutions) != 3 or not isolado.summary.details.get("isolated"):
            problemas.append(f"busca isolada: {len(isolado.solutions)} soluções")
        codigo, saida = rodar_comando(["--isolar", ambigua])
        if codigo != 1 or "--isolar exige" not in saida:
            problemas.append("--isolar sem resolução não foi recusado")

        # L5: ressonância com radicais, coordenadas e metálicas
        alila = escrever_mol(
            pasta,
            "alila.mol",
            [
                'species molecule "Allyl radical" unpaired 1 {',
                "    atom C as c1",
                "    atom C as c2",
                "    atom C as c3",
                "    5x atom H as h",
                "    bond c1=c2",
                "    bond c2-c3",
                *(f"    bond {c}-h{i}" for i, c in
                  enumerate(("c1", "c1", "c2", "c3", "c3"), start=1)),
                "}",
            ],
        )
        formas, observacoes, _ = eletronico.formas_de_ressonancia(
            modelo_de(alila), elementos, valencias
        )
        if len(formas) != 2 or not any("radical" in o for o in observacoes):
            problemas.append(f"ressonância da alila: {len(formas)} forma(s)")
        formas, observacoes, _ = eletronico.formas_de_ressonancia(
            exemplo("sodio_metalico"), elementos, valencias
        )
        if any("radical" in o for o in observacoes):
            problemas.append("sódio metálico foi tratado como radical")

        # L6: tautômeros
        for nome, esperado in (
            ("acetona", 2),
            ("ureia", 2),
            ("pirrol", 3),
            ("piridina", 1),
            ("etano", 1),
        ):
            lista, _ = tautomeros.tautomeros(exemplo(nome), elementos, valencias)
            if len(lista) != esperado:
                problemas.append(f"tautômeros de {nome}: {len(lista)}, esperado {esperado}")

        # L7: aromaticidade
        ciclobutadieno = molecula_com_h(
            pasta, "ciclobutadieno", "c1:C c2:C c3:C c4:C",
            "c1=c2 c2-c3 c3=c4 c4-c1", ["ring c1 c2 c3 c4"],
        )
        casos = {
            "benzeno": ["aromático"],
            "naftaleno": ["aromático", "aromático"],
            "pirrol": ["aromático"],
            "ciclopentadieno": ["não aromático"],
            "ciclohexano": ["não aromático"],
        }
        for nome, esperado in casos.items():
            resultado = aromaticidade.analisar(exemplo(nome), elementos, valencias)
            obtido = [
                "não aromático" if e is None else aromaticidade.classificar(e)
                for _, e, _ in resultado
            ]
            if obtido != esperado:
                problemas.append(f"aromaticidade de {nome}: {obtido}")
        resultado = aromaticidade.analisar(
            modelo_de(ciclobutadieno), elementos, valencias
        )
        if [aromaticidade.classificar(e) for _, e, _ in resultado] != ["antiaromático"]:
            problemas.append("ciclobutadieno não ficou antiaromático")

        # L8: contagem exata de estereoisômeros pelo grupo de automorfismos
        tartarico = ("c1:C c2:C c3:C c4:C o1:O o2:O o3:O o4:O o5:O o6:O",
                     "c1-c2 c2-c3 c3-c4 c1=o1 c1-o2 c2-o3 c3-o4 c4=o5 c4-o6")
        anel = "r1:C r2:C r3:C r4:C r5:C r6:C m1:C m2:C"
        ciclo = "r1-r2 r2-r3 r3-r4 r4-r5 r5-r6 r6-r1"
        casos = {
            "tartarico": (*tartarico, 3, 1),
            "dimetil14": (anel, ciclo + " r1-m1 r4-m2", 2, 2),
            "dimetil12": (anel, ciclo + " r1-m1 r2-m2", 3, 1),
            "metilciclohexano": ("r1:C r2:C r3:C r4:C r5:C r6:C m1:C",
                                 ciclo + " r1-m1", 1, 1),
            "aleno": ("c1:C c2:C c3:C c4:C c5:C", "c1-c2 c2=c3 c3=c4 c4-c5", 2, 0),
            "sulfoxido": ("c1:C s1:S o1:O c2:C c3:C", "c1-s1 s1=o1 s1-c2 c2-c3", 2, 0),
            "dibromobutano": ("c1:C c2:C c3:C c4:C b1:Br b2:Br",
                              "c1-c2 c2-c3 c3-c4 c2-b1 c3-b2", 3, 1),
        }
        for nome, (atomos, ligacoes, total, aquirais) in casos.items():
            extras = ["ring r1 r2 r3 r4 r5 r6"] if atomos.startswith("r1") else []
            modelo = modelo_de(molecula_com_h(pasta, nome, atomos, ligacoes, extras))
            resultado, _, _ = estereo.analisar(modelo, elementos, valencias)
            obtido = (
                len(resultado.classes),
                sum(1 for c, e in resultado.classes.items() if c == e),
            )
            if obtido != (total, aquirais):
                problemas.append(f"estereoisômeros de {nome}: {obtido}, esperado {(total, aquirais)}")

        # L9: configuração declarada
        declarados = {
            "acido_tartarico_meso": "aquiral (forma meso)",
            "acido_tri_hidroxiglutarico": "aquiral (forma meso)",
            "trans_1_2_dimetilciclohexano": "par de enantiômeros",
            "penta_2_3_dieno": "Enantiômero: c2 (C#2)=c3 (C#3)=c4 (C#4) Sa",
            "etil_metil_sulfoxido": "Enantiômero: s1 (S#1) R",
        }
        for nome, trecho in declarados.items():
            texto = estereo.formatar(exemplo(nome), elementos, valencias)
            if trecho not in texto:
                problemas.append(f"configuração declarada de {nome}: {texto}")

    for opcao, nome, trecho in (
        ("--tautomeros", "acetona", "Tautômero 2"),
        ("--aromaticidade", "pirrol", "aromático (Hückel)"),
        ("--estereo", "acido_tartarico_meso", "forma meso"),
    ):
        codigo, saida = rodar_comando(
            [opcao, os.path.join(PASTA_RAIZ, "exemplos", f"{nome}.mol")]
        )
        if codigo != 0 or trecho not in saida:
            problemas.append(f"{opcao} em {nome}: {saida}")
    return problemas


def testar_contrato_solver():
    src = os.path.join(PASTA_RAIZ, "src")
    if src not in sys.path:
        sys.path.insert(0, src)

    from construtor_ast import construir
    from sintatico import analisar
    import semantico
    import solver
    from solver.canonical import canonical_key
    from solver.problem import SolverAtom, normalize
    from solver.result import SolveStatus, Uniqueness

    caminho = os.path.join(PASTA_RAIZ, "resolver", "agua.mol")
    molecula = construir(analisar(caminho))
    resultado = solver.solve(molecula, semantico.carregar_valencias())
    problemas = []
    if resultado.summary.status is not SolveStatus.COMPLETE:
        problemas.append("status da água não é COMPLETE")
    if resultado.summary.unique is not Uniqueness.TRUE:
        problemas.append("unicidade da água não é TRUE")
    if not resultado.summary.complete:
        problemas.append("busca da água não foi marcada completa")

    atomos = (
        SolverAtom(0, "C", 0, 1, 0, "c"),
        SolverAtom(1, "O", 0, 1, 0, "o"),
        SolverAtom(2, "H", 0, 1, 0, "h1"),
        SolverAtom(3, "H", 0, 1, 0, "h2"),
    )
    chave_a = canonical_key({(0, 2): 1, (1, 3): 1}, atomos)
    chave_b = canonical_key({(0, 3): 1, (1, 2): 1}, atomos)
    if chave_a != chave_b:
        problemas.append("chave canônica mudou com átomos equivalentes")

    serializado = solver.summary_dict(resultado.summary)
    if serializado["status"] != "complete":
        problemas.append("status serializado incorreto")
    if "chemical_profile_digest" not in serializado["details"]:
        problemas.append("digest do perfil químico ausente")

    grande = construir(
        analisar(os.path.join(PASTA_RAIZ, "resolver", "ciclohexano_ambiguo.mol"))
    )
    limitado = solver.solve(
        grande,
        semantico.carregar_valencias(),
        solver.SolveRequest(max_solutions=2, require_unique=False),
    )
    if limitado.summary.status is not SolveStatus.LIMIT_REACHED:
        problemas.append("enumeração limitada não retornou LIMIT_REACHED")
    cancelado = solver.solve(
        grande,
        semantico.carregar_valencias(),
        solver.SolveRequest(
            max_solutions=2,
            require_unique=False,
            cancel_check=lambda: True,
        ),
    )
    if cancelado.summary.status is not SolveStatus.CANCELLED:
        problemas.append("cancelamento não retornou CANCELLED")
    expirado = solver.solve(
        grande,
        semantico.carregar_valencias(),
        solver.SolveRequest(
            max_solutions=2,
            require_unique=False,
            time_limit_seconds=1e-12,
        ),
    )
    if expirado.summary.status is not SolveStatus.TIMEOUT:
        problemas.append("deadline não retornou TIMEOUT")
    try:
        json.loads(solver.result_json(resultado))
        linhas_jsonl = solver.result_jsonl(resultado).splitlines()
        for linha in linhas_jsonl:
            json.loads(linha)
    except (TypeError, ValueError) as erro:
        problemas.append(f"serialização inválida: {erro}")

    try:
        import ortools  # noqa: F401
    except ImportError:
        ortools = None
    if ortools is not None:
        formulas = [
            "agua.mol",
            "dioxido_carbono.mol",
            "nitrogenio.mol",
            "amonio.mol",
            "formula_ambigua.mol",
        ]
        for nome in formulas:
            entrada = construir(
                analisar(os.path.join(PASTA_RAIZ, "resolver", nome))
            )
            referencia = solver.solve(
                entrada,
                semantico.carregar_valencias(),
                solver.SolveRequest(
                    max_solutions=10,
                    require_unique=False,
                    backend="reference",
                ),
            )
            cpsat = solver.solve(
                entrada,
                semantico.carregar_valencias(),
                solver.SolveRequest(
                    max_solutions=10,
                    require_unique=False,
                    backend="cpsat",
                ),
            )
            if chaves_canonicas(referencia) != chaves_canonicas(cpsat):
                problemas.append(
                    f"backends divergem para {nome}"
                )

    contagens = [
        (1, 4, 1),
        (2, 6, 1),
        (2, 6, 2, "O"),
        (3, 8, 3, "O"),
        (4, 10, 2),
        (5, 12, 3),
        (6, 14, 5),
    ]
    with tempfile.TemporaryDirectory() as pasta:
        for caso in contagens:
            carbonos, hidrogenios, esperado, *hetero = caso
            linhas = ['species molecule "Contagem" {']
            linhas.append(f"    {carbonos}x atom C")
            if hetero:
                linhas.append(f"    atom {hetero[0]}")
            linhas.append(f"    {hidrogenios}x atom H")
            linhas.append("}")
            arquivo = os.path.join(
                pasta, f"c{carbonos}h{hidrogenios}.mol"
            )
            with open(arquivo, "w", encoding="utf-8") as saida:
                saida.write("\n".join(linhas) + "\n")
            estrutura = construir(analisar(arquivo))
            resultado = solver.solve(
                estrutura,
                semantico.carregar_valencias(),
                solver.SolveRequest(
                    max_solutions=esperado + 1,
                    require_unique=False,
                ),
            )
            if len(resultado.solutions) != esperado:
                formula = f"C{carbonos}H{hidrogenios}"
                if hetero:
                    formula += hetero[0]
                problemas.append(
                    f"{formula}: {len(resultado.solutions)} soluções, "
                    f"esperado {esperado}"
                )
            if not resultado.summary.complete:
                problemas.append(f"busca de {arquivo} não ficou completa")
    return problemas


def testar_cli_solver_estruturado():
    problemas = []
    agua = os.path.join(PASTA_RAIZ, "resolver", "agua.mol")
    codigo, saida = rodar_comando(
        ["--resolver", "--formato=json", agua]
    )
    try:
        documento = json.loads(saida)
    except ValueError as erro:
        return [f"JSON da CLI inválido: {erro}"]
    if codigo != 0 or documento["summary"]["status"] != "complete":
        problemas.append("JSON da solução única não ficou COMPLETE")

    ambigua = os.path.join(
        PASTA_RAIZ, "resolver", "formula_ambigua.mol"
    )
    codigo, saida = rodar_comando(
        [
            "--resolver-todas",
            "--max-solucoes=2",
            "--formato=jsonl",
            ambigua,
        ]
    )
    try:
        linhas = [json.loads(linha) for linha in saida.splitlines()]
    except ValueError as erro:
        return [f"JSONL da CLI inválido: {erro}"]
    if codigo != 0:
        problemas.append(f"JSONL limitado saiu com código {codigo}")
    if len(linhas) != 3 or linhas[-1]["status"] != "limit_reached":
        problemas.append("JSONL não contém duas soluções e sumário limitado")
    try:
        import ortools  # noqa: F401
    except ImportError:
        ortools = None
    if ortools is not None:
        codigo, saida = rodar_comando(
            [
                "--resolver",
                "--backend=cpsat",
                "--formato=json",
                agua,
            ]
        )
        documento = json.loads(saida)
        if codigo != 0:
            problemas.append(f"CP-SAT saiu com código {codigo}")
        if documento["summary"]["backend"] != "ortools-cpsat":
            problemas.append("backend CP-SAT não apareceu no sumário")
    return problemas


def testar_svgs_das_arvores():
    problemas = []
    with tempfile.TemporaryDirectory() as pasta:
        for caminho in arquivos("exemplos"):
            nome = os.path.splitext(os.path.basename(caminho))[0]
            for tipo in ("sintatica", "ast"):
                destino = os.path.join(pasta, f"{nome}.{tipo}.svg")
                codigo, saida = rodar_comando(
                    [caminho, "--tipo", tipo, "-o", destino],
                    script=DESENHAR_ARVORE,
                )
                if codigo != 0:
                    problemas.append(
                        f"{nome}/{tipo}: código {codigo}; saída: {saida.strip()}"
                    )
                    continue
                try:
                    with open(destino, encoding="utf-8") as arquivo:
                        svg = arquivo.read()
                except OSError as erro:
                    problemas.append(f"{nome}/{tipo}: {erro}")
                    continue
                if "<svg " not in svg or not svg.rstrip().endswith("</svg>"):
                    problemas.append(f"{nome}/{tipo}: SVG inválido")
    return problemas


def testar_estereo_nas_arvores():
    # O comando stereo aparece como nó próprio na AST em SVG e como regra
    # estereo na parse tree
    caminho = os.path.join(PASTA_RAIZ, "exemplos", "e_1_2_dicloroeteno.mol")
    esperados = {
        "ast": ["EstereoDecl", "descritor: E", "operador: DUPLA"],
        "sintatica": ["estereo", "descritor", "stereo"],
    }
    problemas = []
    with tempfile.TemporaryDirectory() as pasta:
        for tipo, trechos in esperados.items():
            destino = os.path.join(pasta, f"{tipo}.svg")
            codigo, saida = rodar_comando(
                [caminho, "--tipo", tipo, "-o", destino], script=DESENHAR_ARVORE
            )
            if codigo != 0 or not os.path.isfile(destino):
                problemas.append(f"SVG {tipo} não foi gerado: {saida}")
                continue
            with open(destino, encoding="utf-8") as arquivo:
                svg = arquivo.read()
            for trecho in trechos:
                if trecho not in svg:
                    problemas.append(f"SVG {tipo} sem '{trecho}'")
    return problemas


def testar_ast_de_todos_os_exemplos():
    # Cada comando do código vira exatamente um nó do tipo certo, com
    # posição; os quantificadores ficam no nó, sem expansão
    src = os.path.join(PASTA_RAIZ, "src")
    if src not in sys.path:
        sys.path.insert(0, src)
    from ast_nos import AnelDecl, AtomoDecl, EstereoDecl, LigacaoDecl
    from construtor_ast import construir
    from sintatico import analisar_fluxo, tokenizar
    from MoleculeDSLParser import MoleculeDSLParser as P

    tipos = {
        P.ATOM: AtomoDecl,
        P.BOND: LigacaoDecl,
        P.RING: AnelDecl,
        P.STEREO: EstereoDecl,
    }
    problemas = []
    for caminho in arquivos("exemplos"):
        nome = os.path.basename(caminho)
        _, fluxo, erros = tokenizar(caminho)
        arvore, erros_sintaticos = analisar_fluxo(fluxo)
        if erros.erros or erros_sintaticos.erros:
            problemas.append(f"{nome}: não passou da sintaxe")
            continue
        molecula = construir(arvore)
        # Só os tokens depois do '{': o cabeçalho pode usar 'atom' como tipo
        inicio = next(
            i for i, token in enumerate(fluxo.tokens) if token.type == P.ABRE_CHAVE
        )
        esperados = [
            tipos[token.type]
            for token in fluxo.tokens[inicio:]
            if token.type in tipos
        ]
        obtidos = [type(comando) for comando in molecula.comandos]
        if obtidos != esperados:
            problemas.append(f"{nome}: nós {obtidos} para comandos {esperados}")
        for comando in molecula.comandos:
            referencias = []
            if isinstance(comando, LigacaoDecl):
                referencias = [comando.origem, comando.destino]
            elif isinstance(comando, AnelDecl):
                referencias = comando.nomes
            elif isinstance(comando, EstereoDecl):
                referencias = comando.referencias
            for no in (comando, *referencias):
                if no.linha < 1 or no.coluna < 0:
                    problemas.append(f"{nome}: nó sem posição {no}")
        multiplicadores = [
            int(token.text[:-1])
            for token in fluxo.tokens
            if token.type == P.MULTIPLICADOR_ATOMO
        ]
        com_multiplicador = [
            c.multiplicador
            for c in molecula.comandos
            if isinstance(c, AtomoDecl) and c.multiplicador != 1
        ]
        if sorted(com_multiplicador) != sorted(m for m in multiplicadores if m != 1):
            problemas.append(f"{nome}: multiplicadores expandidos na AST")
    return problemas


def main():
    casos = []
    for pasta in PASTAS_VALIDOS:
        for caminho in arquivos(pasta):
            if erros_esperados(caminho):
                casos.append(
                    (
                        caminho,
                        lambda c=caminho: testar_com_mensagens(c, 0),
                    )
                )
            else:
                casos.append((caminho, testar_valido))
    for pasta, codigo in PASTAS_COM_MENSAGENS.items():
        casos += [
            (c, lambda c, codigo=codigo: testar_com_mensagens(c, codigo))
            for c in arquivos(pasta)
        ]

    falhas = 0

    for caminho, testar in casos:
        nome = os.path.relpath(caminho, PASTA_RAIZ)
        problemas = testar(caminho)

        if problemas:
            falhas += 1
            print(f"FALHOU {nome}")
            for problema in problemas:
                print(f"    {problema}")
        else:
            print(f"ok     {nome}")

    casos_especiais = [
        ("entrada/arquivo_inexistente", testar_arquivo_inexistente),
        ("configuracao/gerado_ausente", testar_gerado_ausente),
        ("erros/limite_de_dez", testar_limite_de_erros),
        (
            "ast/agua",
            lambda: testar_ast(os.path.join(PASTA_RAIZ, "exemplos", "agua.mol")),
        ),
        (
            "ast/amonio",
            lambda: testar_ast(os.path.join(PASTA_RAIZ, "exemplos", "amonio.mol")),
        ),
        (
            "ast/ciclopropano",
            lambda: testar_ast(
                os.path.join(PASTA_RAIZ, "exemplos", "ciclopropano.mol")
            ),
        ),
        (
            "ast/aminoborano",
            lambda: testar_ast(
                os.path.join(PASTA_RAIZ, "exemplos", "aminoborano.mol")
            ),
        ),
        (
            "ast/e_1_2_dicloroeteno",
            lambda: testar_ast(
                os.path.join(PASTA_RAIZ, "exemplos", "e_1_2_dicloroeteno.mol")
            ),
        ),
        (
            "modelo/agua",
            lambda: testar_modelo(
                os.path.join(PASTA_RAIZ, "exemplos", "agua.mol")
            ),
        ),
        (
            "modelo/dioxido_carbono",
            lambda: testar_modelo(
                os.path.join(PASTA_RAIZ, "exemplos", "dioxido_carbono.mol")
            ),
        ),
        (
            "modelo/nitrogenio",
            lambda: testar_modelo(
                os.path.join(PASTA_RAIZ, "exemplos", "nitrogenio.mol")
            ),
        ),
        (
            "modelo/hidroxido",
            lambda: testar_modelo(
                os.path.join(PASTA_RAIZ, "exemplos", "hidroxido.mol")
            ),
        ),
        (
            "modelo/sodio_metalico",
            lambda: testar_modelo(
                os.path.join(PASTA_RAIZ, "exemplos", "sodio_metalico.mol")
            ),
        ),
        (
            "modelo/e_1_2_dicloroeteno",
            lambda: testar_modelo(
                os.path.join(PASTA_RAIZ, "exemplos", "e_1_2_dicloroeteno.mol")
            ),
        ),
        ("arvores/svg_todos_exemplos", testar_svgs_das_arvores),
        ("arvores/estereo_nas_arvores", testar_estereo_nas_arvores),
        ("ast/todos_os_exemplos", testar_ast_de_todos_os_exemplos),
        ("solver/contrato_estruturado", testar_contrato_solver),
        ("solver/cli_estruturada", testar_cli_solver_estruturado),
        ("solver/fases_do_plano", testar_fases_solver),
        ("solver/fases_quimicas", testar_fases_quimicas),
        ("solver/limites", testar_limites),
    ]
    casos_especiais += [
        (
            f"solver/{os.path.basename(caminho)}",
            lambda caminho=caminho: testar_solver(caminho),
        )
        for caminho in arquivos("resolver")
    ]
    casos_especiais += [
        (
            f"solver-todas/{os.path.basename(snapshot)}",
            lambda caminho=snapshot[: -len(".todas.txt")] + ".mol": (
                testar_solver_todas(caminho)
            ),
        )
        for snapshot in sorted(
            glob.glob(os.path.join(PASTA_RAIZ, "resolver", "*.todas.txt"))
        )
    ]
    for nome, testar in casos_especiais:
        problemas = testar()
        if problemas:
            falhas += 1
            print(f"FALHOU {nome}")
            for problema in problemas:
                print(f"    {problema}")
        else:
            print(f"ok     {nome}")

    total = len(casos) + len(casos_especiais)
    print(f"\n{total} testes, {falhas} falha(s)")

    if falhas:
        sys.exit(1)


if __name__ == "__main__":
    main()
