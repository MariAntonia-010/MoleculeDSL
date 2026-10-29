import glob
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
        ("arvores/svg_todos_exemplos", testar_svgs_das_arvores),
        ("solver/contrato_estruturado", testar_contrato_solver),
        ("solver/cli_estruturada", testar_cli_solver_estruturado),
        ("solver/fases_do_plano", testar_fases_solver),
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
