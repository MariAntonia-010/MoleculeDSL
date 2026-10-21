import glob
import os
import subprocess
import sys


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

    print(f"\n{len(casos)} testes, {falhas} falha(s)")

    if falhas:
        sys.exit(1)


if __name__ == "__main__":
    main()
