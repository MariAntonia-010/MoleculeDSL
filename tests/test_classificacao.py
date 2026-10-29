import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from ast_nos import Operador
from classificacao import ErroConfiguracao, carregar_configuracao, classificar, limites
from construtor_ast import construir
from modelo import Atomo, Ligacao, Modelo, formatar
from semantico import analisar
from sintatico import analisar as analisar_sintaxe
from main import compilar


class ClassificacaoTest(unittest.TestCase):
    def modelo(self, origem=1.0, destino=1.0, operador=Operador.SIMPLES):
        modelo = Modelo("Fronteiras", [
            Atomo(1, "H", 1, 0, None, 1, 0),
            Atomo(2, "O", 1, 0, None, 2, 0),
        ], [Ligacao(1, 2, operador, 3, 0)])
        dados = {"H": {"eletronegatividade": origem}, "O": {"eletronegatividade": destino}}
        return modelo, dados

    def test_fronteiras_e_direcao(self):
        for delta, esperado in [(0, "covalente apolar"), (0.39, "covalente apolar"),
                                (0.4, "covalente polar"), (1.7, "covalente polar"),
                                (1.71, "iônica")]:
            for origem, destino in [(1, 1 + delta), (1 + delta, 1)]:
                with self.subTest(delta=delta, origem=origem):
                    modelo, dados = self.modelo(origem, destino)
                    classificar(modelo, dados, carregar_configuracao())
                    self.assertEqual(modelo.ligacoes[0].classificacao, esperado)

    def test_limites_personalizados(self):
        modelo, dados = self.modelo(1, 1.4)
        classificar(modelo, dados, {"limite_apolar": 0.5, "limite_polar": 2})
        self.assertEqual(modelo.ligacoes[0].classificacao, "covalente apolar")

    def test_dado_ausente_em_qualquer_extremidade(self):
        for origem, destino in [(None, 1), (1, None), (None, None)]:
            modelo, dados = self.modelo(origem, destino)
            classificar(modelo, dados, carregar_configuracao())
            self.assertIsNone(modelo.ligacoes[0].classificacao)
            self.assertIsNone(modelo.ligacoes[0].diferenca_eletronegatividade)
            self.assertIn("eletronegatividade indisponível", formatar(modelo))

    def test_metalica_nao_usa_delta(self):
        modelo, dados = self.modelo(1, 4, Operador.METALICA)
        classificar(modelo, dados, carregar_configuracao())
        self.assertEqual(modelo.ligacoes[0].classificacao, "metálica")
        self.assertIsNone(modelo.ligacoes[0].diferenca_eletronegatividade)

    def test_ordem_e_coordenada_preservadas(self):
        for operador in [Operador.SIMPLES, Operador.DUPLA, Operador.TRIPLA, Operador.COORDENADA]:
            modelo, dados = self.modelo(1, 2, operador)
            classificar(modelo, dados, carregar_configuracao())
            ligacao = modelo.ligacoes[0]
            self.assertEqual(ligacao.classificacao, "covalente polar")
            self.assertEqual((ligacao.origem, ligacao.destino, ligacao.operador), (1, 2, operador))

    def test_configuracoes_invalidas(self):
        for config in [None, [], {}, {"limite_apolar": "a", "limite_polar": 1.7}]:
            with self.subTest(config=config), self.assertRaises(ErroConfiguracao):
                limites(config)
        for apolar, polar in [(-1, 1.7), (1.7, 1.7), (2, 1), (float("nan"), 2),
                              (0.4, float("inf")), (True, 2)]:
            with self.subTest(apolar=apolar, polar=polar), self.assertRaises(ErroConfiguracao):
                limites({"limite_apolar": apolar, "limite_polar": polar})

    def test_arquivo_configuracao_invalido(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "ligacoes.json"
            with self.assertRaises(ErroConfiguracao):
                carregar_configuracao(caminho)
            for conteudo in ["{", json.dumps({"limite_apolar": 3, "limite_polar": 1})]:
                caminho.write_text(conteudo)
                with self.assertRaises(ErroConfiguracao):
                    carregar_configuracao(caminho)

    def test_integracao_com_dados_e_exemplos(self):
        for arquivo, esperado in [("agua.mol", "covalente polar"),
                                  ("hidrogenio.mol", "covalente apolar"),
                                  ("cloreto_de_sodio.mol", "iônica")]:
            with self.subTest(arquivo=arquivo), contextlib.redirect_stdout(io.StringIO()):
                arvore = analisar_sintaxe(str(RAIZ / "exemplos" / arquivo))
                modelo, mensagens = analisar(construir(arvore))
                self.assertEqual(mensagens, [])
                self.assertTrue(modelo.ligacoes)
                self.assertTrue(all(l.classificacao == esperado for l in modelo.ligacoes))
                self.assertIn("Δχ=", formatar(modelo))

    def test_classificacao_nao_rejeita_molecula(self):
        arvore = analisar_sintaxe(str(RAIZ / "exemplos" / "agua.mol"))
        modelo, mensagens = analisar(
            construir(arvore), {"limite_apolar": 0, "limite_polar": 0.1}
        )
        self.assertEqual(mensagens, [])
        self.assertTrue(all(l.classificacao == "iônica" for l in modelo.ligacoes))

    def test_cli_configuracao_invalida_sem_traceback(self):
        saida = io.StringIO()
        with patch("semantico.carregar_configuracao", side_effect=ErroConfiguracao("limites inválidos")):
            with contextlib.redirect_stdout(saida):
                codigo = compilar(str(RAIZ / "exemplos" / "agua.mol"), set())
        self.assertEqual(codigo, 1)
        self.assertEqual(saida.getvalue(), "Erro de configuração: limites inválidos\n")


if __name__ == "__main__":
    unittest.main()
