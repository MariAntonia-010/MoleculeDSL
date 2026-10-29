import glob
import os
import subprocess
import sys
import tempfile


# Roda o src/main.py em todos os exemplos e confere o resultado:
# - exemplos/: devem passar sem erros nem avisos (código de saída 0)
# - invalidos/, invalidos_sintaticos/, invalidos_semanticos/ e
#   avisos_semanticos/: cada arquivo diz, em linhas
#   "// esperado: <início da mensagem>", os erros e avisos que devem
#   aparecer, na ordem. A saída deve ter exatamente essas mensagens e o
#   código de saída da pasta (0, 1 ou 2).

PASTA_RAIZ = os.path.dirname(os.path.abspath(__file__))
MAIN = os.path.join(PASTA_RAIZ, "src", "main.py")

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


def rodar_comando(argumentos, ambiente_extra=None):
    ambiente = dict(os.environ, PYTHONIOENCODING="utf-8")
    ambiente.update(ambiente_extra or {})
    resultado = subprocess.run(
        [sys.executable, MAIN, *argumentos],
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
        elif not obtido.startswith(esperado):
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


def main():
    casos = [(c, testar_valido) for p in PASTAS_VALIDOS for c in arquivos(p)]
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
