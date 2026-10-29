from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

RAIZ = Path(__file__).resolve().parent.parent


class GeracaoTest(unittest.TestCase):
    def test_geracao_ausente_ou_incompleta(self):
        # Copia só para diretórios temporários; nunca remove o gerado real.
        for presentes in [[], ["MoleculeDSLLexer.py"],
                          ["MoleculeDSLLexer.py", "MoleculeDSLParser.py"]]:
            with self.subTest(presentes=presentes), tempfile.TemporaryDirectory() as pasta:
                raiz = Path(pasta)
                shutil.copytree(RAIZ / "src", raiz / "src", ignore=shutil.ignore_patterns("__pycache__"))
                (raiz / "gerado").mkdir()
                for nome in presentes:
                    shutil.copy(RAIZ / "gerado" / nome, raiz / "gerado" / nome)
                resultado = subprocess.run(
                    [sys.executable, str(raiz / "src" / "main.py"), str(RAIZ / "exemplos" / "agua.mol")],
                    capture_output=True, text=True, encoding="utf-8", timeout=10,
                )
                self.assertEqual(resultado.returncode, 1)
                self.assertIn("Gere com: sh gerar.sh", resultado.stdout)
                self.assertNotIn("Traceback", resultado.stdout + resultado.stderr)


if __name__ == "__main__":
    unittest.main()
