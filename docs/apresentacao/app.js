  "use strict";
  const DADOS = JSON.parse(document.getElementById("dados").textContent);
  const raiz = document.documentElement;

  /* ---------------- tema ---------------- */
  try {
    const salvo = localStorage.getItem("moleculedsl-tema");
    if (salvo) raiz.dataset.theme = salvo;
    else if (matchMedia("(prefers-color-scheme: light)").matches) raiz.dataset.theme = "light";
  } catch (e) {}
  document.querySelector(".tema").addEventListener("click", () => {
    raiz.dataset.theme = raiz.dataset.theme === "light" ? "dark" : "light";
    try { localStorage.setItem("moleculedsl-tema", raiz.dataset.theme); } catch (e) {}
  });

  /* ---------------- abas ---------------- */
  document.querySelectorAll(".abas").forEach((grupo) => {
    grupo.querySelectorAll(".aba").forEach((aba) => {
      aba.addEventListener("click", () => {
        grupo.querySelectorAll(".aba").forEach((outra) => {
          outra.setAttribute("aria-selected", String(outra === aba));
          document.getElementById(outra.dataset.painel).hidden = outra !== aba;
        });
      });
    });
  });

  /* ================= compilador do navegador ================= */
  // Palavras reservadas e tipos de espécie vêm da gramática, via gerador
  const PALAVRAS = new Set(DADOS.palavras);
  const TIPOS_ESPECIE = new Map(DADOS.tipos_especie.map((t) => [t.tipo, t.exige_carga]));
  const OPERADORES = { "-": 1, "=": 2, "#": 3, "->": 1, "~": 0 };

  class ErroDSL extends Error {
    constructor(fase, codigo, linha, coluna, mensagem) { super(mensagem); this.fase = fase; this.codigo = codigo; this.linha = linha; this.coluna = coluna; }
    diagnostico() { return { tipo: "erro", fase: this.fase, codigo: this.codigo, linha: this.linha, coluna: this.coluna, mensagem: this.message }; }
  }

  function tokenizar(texto) {
    const tokens = [];
    let i = 0, linha = 1, coluna = 0;
    const avancar = (n) => {
      for (let k = 0; k < n; k++) {
        if (texto[i] === "\n") { linha++; coluna = 0; } else { coluna++; }
        i++;
      }
    };
    while (i < texto.length) {
      const resto = texto.slice(i);
      let m;
      if ((m = /^[ \t\r\n﻿]+/.exec(resto))) { avancar(m[0].length); continue; }
      if (resto.startsWith("//")) { const fim = resto.indexOf("\n"); avancar(fim < 0 ? resto.length : fim); continue; }
      const pos = { l: linha, c: coluna };
      const empurrar = (tipo, valor) => { tokens.push({ tipo, valor, ...pos }); avancar(valor.length); };
      if (resto[0] === '"') {
        m = /^"[^"\r\n]*"/.exec(resto);
        if (!m) throw new ErroDSL("léxico", "LEX-002", linha, coluna, "texto sem aspas de fechamento na mesma linha");
        empurrar("TEXTO", m[0]); continue;
      }
      if ((m = /^[1-7][spdf][0-9]+/.exec(resto))) { empurrar("SUBCAMADA", m[0]); continue; }
      if ((m = /^[0-9]+x/.exec(resto)) && !/^[0-9]+x[a-z0-9_]/.test(resto)) { empurrar("MULT", m[0]); continue; }
      if ((m = /^[0-9]+\.[0-9]+/.exec(resto))) { empurrar("REAL", m[0]); continue; }
      if ((m = /^[0-9]+/.exec(resto))) { empurrar("INT", m[0]); continue; }
      if ((m = /^[a-z][a-z0-9_]*/.exec(resto))) {
        const v = m[0];
        empurrar(PALAVRAS.has(v) ? v : /^x[0-9]+$/.test(v) ? "REP" : "NOME", v); continue;
      }
      if ((m = /^[A-Z][a-z]?/.exec(resto))) { empurrar("IDENT", m[0]); continue; }
      if (resto.startsWith("->")) { empurrar("OP", "->"); continue; }
      if ("-=#~".includes(resto[0])) { empurrar("OP", resto[0]); continue; }
      if ("+(){}[]".includes(resto[0])) { empurrar(resto[0], resto[0]); continue; }
      throw new ErroDSL("léxico", "LEX-001", linha, coluna, "<>".includes(resto[0])
        ? `caractere inválido '${resto[0]}': a única seta da linguagem é '->', a ligação coordenada do doador para o receptor`
        : `caractere inválido '${resto[0]}'`);
    }
    tokens.push({ tipo: "EOF", valor: "fim do arquivo", l: linha, c: coluna });
    return tokens;
  }

  function analisarSintaxe(tokens) {
    // Além da espécie (AST), monta a árvore sintática: cada regra da
    // gramática vira um nó, e cada token consumido, uma folha
    let p = 0;
    const raizArvore = { regra: "programa", filhos: [] };
    const pilha = [raizArvore];
    const abrir = (regra) => { const no = { regra, filhos: [] }; pilha[pilha.length - 1].filhos.push(no); pilha.push(no); };
    const fechar = () => pilha.pop();
    const atual = () => tokens[p];
    const consumir = () => { const t = tokens[p++]; pilha[pilha.length - 1].filhos.push({ token: t }); return t; };
    const descrever = (t) => (t.tipo === "EOF" ? "fim do arquivo" : `'${t.valor}'`);
    const falhar = (esperado, codigo = "SIN-001") => {
      const t = atual();
      const erro = new ErroDSL("sintático", t.tipo === "EOF" ? "SIN-004" : codigo, t.l, t.c, `esperado ${esperado}, encontrado ${descrever(t)}`);
      erro.arvore = raizArvore;
      throw erro;
    };
    const pegar = (tipo, esperado) => { if (atual().tipo !== tipo) falhar(esperado); return consumir(); };
    const talvez = (tipo) => (atual().tipo === tipo ? consumir() : null);
    const sinal = (esperado) => {
      abrir("sinal");
      const v = atual().valor === "+" ? 1 : atual().tipo === "OP" && atual().valor === "-" ? -1 : falhar(esperado);
      consumir();
      fechar();
      return v;
    };

    const especie = { tipo: "molecule", nome: "", carga: null, desemparelhados: null, comandos: [], arvore: raizArvore, legado: false };
    abrir("molecula");
    abrir("cabecalho");
    if (talvez("molecule")) {
      especie.legado = true;
      especie.nome = pegar("TEXTO", "nome da espécie entre aspas").valor.slice(1, -1);
    } else if (talvez("species")) {
      const tipo = atual().tipo;
      if (!TIPOS_ESPECIE.has(tipo)) falhar("tipo de espécie depois de 'species'");
      consumir();
      especie.tipo = tipo;
      especie.nome = pegar("TEXTO", "nome da espécie entre aspas").valor.slice(1, -1);
      if (TIPOS_ESPECIE.get(tipo)) {
        abrir("cargaEspecie");
        pegar("charge", "'charge' com a carga do íon");
        const s = sinal("sinal da carga (+ ou -)");
        especie.carga = s * Number(pegar("INT", "número inteiro na carga").valor);
        fechar();
      }
    } else {
      falhar("'molecule' ou 'species' no início do programa");
    }
    fechar();
    if (atual().tipo === "unpaired") {
      abrir("desemparelhados");
      consumir();
      especie.desemparelhados = Number(pegar("INT", "número depois de 'unpaired'").valor);
      fechar();
    }
    if (atual().tipo === "charge") falhar("'{': 'charge' só vale em molecular_ion e monatomic_ion; molécula, átomo e sólido são neutros, então use 'species molecular_ion'");
    pegar("{", "'{' depois do nome da espécie");

    const referencia = (onde) => {
      abrir("referencia");
      const t = atual();
      if (t.tipo !== "IDENT" && t.tipo !== "NOME") falhar(`elemento ou nome de átomo ${onde}`);
      consumir();
      fechar();
      return { texto: t.valor, porNome: t.tipo === "NOME", l: t.l, c: t.c };
    };
    const operador = (esperado) => {
      abrir("operador");
      const op = pegar("OP", esperado).valor;
      fechar();
      return op;
    };

    while (atual().tipo !== "}") {
      const t = atual();
      if (t.tipo === "EOF") falhar("'}' para fechar a molécula");
      abrir("comando");
      if (t.tipo === "MULT" || t.tipo === "atom") {
        abrir("atomo");
        const mult = t.tipo === "MULT" ? Number(consumir().valor.slice(0, -1)) : 1;
        pegar("atom", "'atom' depois do multiplicador");
        const massaToken = talvez("INT");
        const el = pegar("IDENT", "símbolo de elemento depois de 'atom'");
        let carga = 0;
        if (atual().tipo === "(") {
          abrir("carga");
          consumir();
          const s = sinal("sinal na carga, como (+1) ou (-1)");
          carga = s * Number(pegar("INT", "número inteiro na carga").valor);
          pegar(")", "')' para fechar a carga");
          fechar();
        }
        let nome = null;
        if (talvez("as")) {
          if (atual().tipo === "IDENT") {
            // 'Agua' vira 'Ag' + 'ua': junta o resto colado
            const t = atual(), s = tokens[p + 1];
            const texto = t.valor + (s && s.tipo === "NOME" && s.l === t.l && s.c === t.c + t.valor.length ? s.valor : "");
            falhar(`nome de átomo com letra minúscula ('${texto}' começa como elemento; escreva '${texto.toLowerCase()}')`);
          }
          nome = pegar("NOME", "nome de átomo depois de 'as'").valor;
        }
        fechar();
        especie.comandos.push({ tipo: "atom", mult, el: el.valor, carga, nome, massa: massaToken ? Number(massaToken.valor) : null, l: t.l, c: t.c });
      } else if (t.tipo === "bond") {
        abrir("ligacao");
        consumir();
        const origem = referencia("na ligação");
        const op = operador("operador de ligação (-, =, #, -> ou ~)");
        const destino = referencia("na ligação");
        const rep = talvez("REP");
        fechar();
        especie.comandos.push({ tipo: "bond", origem, op, destino, rep: rep ? Number(rep.valor.slice(1)) : 1, l: t.l, c: t.c });
      } else if (t.tipo === "ring") {
        abrir("anel");
        consumir();
        const nomes = [];
        while (atual().tipo === "NOME") { const n = consumir(); nomes.push({ texto: n.valor, porNome: true, l: n.l, c: n.c }); }
        if (nomes.length < 3) falhar("pelo menos três nomes de átomos no anel");
        fechar();
        especie.comandos.push({ tipo: "ring", nomes, l: t.l, c: t.c });
      } else if (t.tipo === "configuration") {
        abrir("configuracao");
        consumir();
        const ref = referencia("em 'configuration'");
        let nucleo = null;
        if (atual().tipo === "[") {
          abrir("nucleo");
          consumir();
          nucleo = pegar("IDENT", "gás nobre entre colchetes, como [Ne]").valor;
          pegar("]", "']' para fechar o núcleo de gás nobre");
          fechar();
        }
        const subcamadas = [];
        while (atual().tipo === "SUBCAMADA") subcamadas.push(consumir().valor);
        if (!subcamadas.length) {
          if (atual().tipo === "INT" && tokens[p + 1] && ["s", "p", "d", "f"].includes(tokens[p + 1].valor)) falhar(`a quantidade de elétrons da subcamada, como ${atual().valor}${tokens[p + 1].valor}2`);
          falhar("subcamada como 2p4 (camada 1 a 7, tipo s, p, d ou f e número de elétrons)");
        }
        fechar();
        especie.comandos.push({ tipo: "configuration", ref, nucleo, subcamadas, l: t.l, c: t.c });
      } else if (t.tipo === "stereo") {
        abrir("estereo");
        consumir();
        const refs = [referencia("em 'stereo'")];
        let op = null;
        if (atual().tipo === "OP") { op = operador("operador"); refs.push(referencia("em 'stereo'")); }
        else if ((atual().tipo === "NOME" || atual().tipo === "IDENT") && ["NOME", "IDENT"].includes(tokens[p + 1].tipo)) refs.push(referencia("em 'stereo'"));
        abrir("descritor");
        const d = atual();
        if (d.tipo !== "IDENT" && d.tipo !== "NOME") falhar("descritor (R, S, r, s, E, Z, Ra, Sa, cis ou trans)");
        consumir();
        fechar();
        fechar();
        especie.comandos.push({ tipo: "stereo", refs, op, descritor: d.valor, l: t.l, c: t.c });
      } else {
        if (atual().tipo === "INT" && tokens[p + 1] && ["s", "p", "d", "f"].includes(tokens[p + 1].valor)) {
          falhar(`a quantidade de elétrons da subcamada, como ${atual().valor}${tokens[p + 1].valor}2`, "SIN-002");
        }
        if (atual().tipo === "INT" && p > 1 && tokens[p - 1].tipo === "IDENT" && tokens[p - 2].tipo === "atom" && tokens[p - 1].l === atual().l && tokens[p - 1].c + tokens[p - 1].valor.length === atual().c) {
          falhar(`'${atual().valor}x atom ${tokens[p - 1].valor}' para ${atual().valor} átomos, ou 'atom ${atual().valor}${tokens[p - 1].valor}' para o isótopo de número de massa ${atual().valor}`, "SIN-002");
        }
        if (atual().tipo === "[" && p > 0 && tokens[p - 1].tipo === "SUBCAMADA") {
          falhar("o núcleo de gás nobre logo depois do átomo, antes das subcamadas, como 'configuration c [He] 2s2 2p2'", "SIN-002");
        }
        falhar("'atom', 'bond', 'ring', 'stereo', 'configuration' ou '}'", "SIN-002");
      }
      fechar();
    }
    consumir();
    fechar();
    if (atual().tipo !== "EOF") falhar("fim do arquivo depois de '}'", "SIN-002");
    consumir();
    return especie;
  }

  function analisarSemantica(especie) {
    const erros = [], avisos = [];
    // atomos: ids dos átomos envolvidos, para destacá-los no desenho 3D
    const erro = (no, codigo, msg, atomos = []) => erros.push({ tipo: "erro", fase: "semântico", codigo, linha: no.l, coluna: no.c, mensagem: msg, atomos });
    const aviso = (no, codigo, msg, atomos = []) => avisos.push({ tipo: "aviso", fase: "semântico", codigo, linha: no.l, coluna: no.c, mensagem: msg, atomos });
    const atomos = [], porNome = new Map(), porElemento = new Map(), contagem = new Map();
    for (const cmd of especie.comandos.filter((c) => c.tipo === "atom")) {
      if (!DADOS.elementos[cmd.el]) { erro(cmd, "ELEM-001", `elemento desconhecido '${cmd.el}'`); continue; }
      if (cmd.massa != null) {
        const z = DADOS.elementos[cmd.el].numero;
        if (cmd.massa < z) { erro(cmd, "ATOM-001", `o número de massa ${cmd.massa} é menor que o número atômico de ${cmd.el} (${z}): daria ${cmd.massa - z} nêutrons`); continue; }
        const naturais = DADOS.isotopos[cmd.el];
        if (naturais && !naturais.includes(cmd.massa)) aviso(cmd, "ATOM-005", naturais.length
          ? `${cmd.massa}${cmd.el} não é isótopo de composição natural (CIAAW: ${naturais.map((a) => a + cmd.el).join(", ")}); pode ser radioativo ou artificial`
          : `${cmd.massa}${cmd.el}: ${cmd.el} não tem isótopo de composição natural (CIAAW); todo isótopo dele é radioativo`);
      }
      for (let k = 1; k <= cmd.mult; k++) {
        const nome = cmd.nome == null ? null : cmd.mult > 1 ? cmd.nome + k : cmd.nome;
        if (nome && porNome.has(nome)) { erro(cmd, "STRUCT-002", `o nome '${nome}' já foi usado`); continue; }
        contagem.set(cmd.el, (contagem.get(cmd.el) || 0) + 1);
        const atomo = { id: atomos.length, el: cmd.el, carga: cmd.carga, nome, indice: contagem.get(cmd.el), massa: cmd.massa, configuracao: null };
        atomos.push(atomo);
        if (nome) porNome.set(nome, atomo);
        if (!porElemento.has(cmd.el)) porElemento.set(cmd.el, []);
        porElemento.get(cmd.el).push(atomo);
      }
    }
    const citados = new Set();
    const resolver = (ref, fixo) => {
      if (ref.porNome) {
        const a = porNome.get(ref.texto);
        if (!a) { erro(ref, "STRUCT-001", `nenhum átomo se chama '${ref.texto}'`); return null; }
        citados.add(a.id); return a;
      }
      const lista = porElemento.get(ref.texto) || [];
      if (!lista.length) { erro(ref, DADOS.elementos[ref.texto] ? "STRUCT-001" : "ELEM-001", DADOS.elementos[ref.texto] ? `nenhum átomo de ${ref.texto} foi declarado` : `elemento desconhecido '${ref.texto}'`); return null; }
      if (lista.length === 1) { citados.add(lista[0].id); return lista[0]; }
      if (fixo) { erro(ref, "STEREO-001", `'${ref.texto}' não identifica um único átomo; use o nome do átomo`); return null; }
      const livre = lista.find((a) => !citados.has(a.id));
      if (!livre) { erro(ref, "STRUCT-004", `todos os ${lista.length} átomos de ${ref.texto} já foram citados; use nomes`); return null; }
      citados.add(livre.id); return livre;
    };
    const ligacoes = [], pares = new Set();
    for (const cmd of especie.comandos.filter((c) => c.tipo === "bond")) {
      for (let k = 0; k < cmd.rep; k++) {
        const a = resolver(cmd.origem), b = resolver(cmd.destino);
        if (!a || !b) break;
        if (a.id === b.id) { erro(cmd, "STRUCT-005", `o átomo ${rotulo(a)} não pode se ligar a ele mesmo`, [a.id]); break; }
        const chave = Math.min(a.id, b.id) + "-" + Math.max(a.id, b.id);
        if (pares.has(chave)) { erro(cmd, "STRUCT-006", `já existe uma ligação entre ${rotulo(a)} e ${rotulo(b)}; use = ou # para ligação múltipla`, [a.id, b.id]); break; }
        pares.add(chave);
        ligacoes.push({ a: a.id, b: b.id, op: cmd.op, ordem: OPERADORES[cmd.op] });
      }
    }
    const temPar = (x, y) => pares.has(Math.min(x, y) + "-" + Math.max(x, y));
    for (const cmd of especie.comandos.filter((c) => c.tipo === "ring")) {
      const lista = cmd.nomes.map((r) => resolver(r));
      if (lista.includes(null)) continue;
      for (let k = 0; k < lista.length; k++) {
        const x = lista[k], y = lista[(k + 1) % lista.length];
        if (!temPar(x.id, y.id)) { erro(cmd.nomes[(k + 1) % lista.length], "RING-002", `os átomos ${x.nome} e ${y.nome} do anel não estão ligados`); break; }
      }
    }
    const configuracoes = [];
    for (const cmd of especie.comandos.filter((c) => c.tipo === "stereo")) {
      const lista = cmd.refs.map((r) => resolver(r, true));
      if (!lista.includes(null)) configuracoes.push({ atomos: lista, op: cmd.op, descritor: cmd.descritor });
    }
    // Configuração eletrônica (ATOM-002, 003, 004, 006)
    for (const cmd of especie.comandos.filter((c) => c.tipo === "configuration")) {
      if (especie.tipo !== "atom" && especie.tipo !== "monatomic_ion") {
        erro(cmd, "ATOM-006", "configuration descreve um átomo isolado ou um íon monoatômico; numa molécula os elétrons ocupam orbitais moleculares");
        continue;
      }
      const a = resolver(cmd.ref, true);
      if (!a) continue;
      if (a.configuracao) { erro(cmd, "ATOM-006", `${rotulo(a)} já tem configuração declarada`, [a.id]); continue; }
      if (cmd.nucleo && !NUCLEOS_GAS[cmd.nucleo]) { erro(cmd, "ATOM-002", `[${cmd.nucleo}] não é núcleo de gás nobre; use ${Object.keys(NUCLEOS_GAS).map((g) => `[${g}]`).join(", ")}`, [a.id]); continue; }
      if (cmd.nucleo) {
        // Núcleo grande demais, ou subcamada que já está dentro dele
        const nucleo = lerSubcamadas(`[${cmd.nucleo}]`), eletrons = DADOS.elementos[a.el].numero - a.carga;
        const contar = (g) => lerSubcamadas(`[${g}]`).reduce((t, x) => t + x[2], 0);
        if (contar(cmd.nucleo) >= eletrons) {
          const menores = Object.keys(NUCLEOS_GAS).filter((g) => contar(g) < eletrons);
          erro(cmd, "ATOM-003", `o núcleo [${cmd.nucleo}] sozinho tem ${contar(cmd.nucleo)} elétrons, e ${rotulo(a)} tem ${eletrons}${menores.length ? `; use [${menores[menores.length - 1]}]` : "; escreva as subcamadas sem núcleo"}`, [a.id]);
          continue;
        }
        const dentro = new Set(nucleo.map(([n, l]) => `${n},${l}`));
        const repetidas = cmd.subcamadas.filter((s) => dentro.has(`${s[0]},${"spdf".indexOf(s[1])}`));
        if (repetidas.length) { erro(cmd, "ATOM-002", `${repetidas.map((r) => r.slice(0, 2)).join(", ")} já está no núcleo [${cmd.nucleo}]; depois do núcleo vêm só as subcamadas de fora dele`, [a.id]); continue; }
      }
      const lista = lerSubcamadas((cmd.nucleo ? `[${cmd.nucleo}] ` : "") + cmd.subcamadas.join(" "));
      const pauli = problemasPauli(lista);
      if (pauli.length) { erro(cmd, "ATOM-002", pauli.join("; "), [a.id]); continue; }
      const z = DADOS.elementos[a.el].numero, total = lista.reduce((t, x) => t + x[2], 0);
      if (total !== z - a.carga) { erro(cmd, "ATOM-003", `a configuração tem ${total} elétrons, mas ${rotulo(a)} (Z=${z}, carga ${a.carga >= 0 ? "+" : ""}${a.carga}) tem ${z - a.carga}`, [a.id]); continue; }
      a.configuracao = paraMapa(lista);
      const ref = fundamental(a.el, a.carga);
      if (ref && !mapasIguais(ref, a.configuracao)) aviso(cmd, "ATOM-004", `a configuração não é o estado fundamental de ${rotulo(a)} (referência: ${textoConfig(ref)}); descreve um estado excitado`, [a.id]);
    }
    // Hund (ATOM-007): unpaired de um átomo isolado
    if (!erros.length && (especie.tipo === "atom" || especie.tipo === "monatomic_ion") && especie.desemparelhados != null && atomos.length === 1) {
      const m = atomos[0].configuracao || fundamental(atomos[0].el, atomos[0].carga);
      if (m && hundDe(m) !== especie.desemparelhados) aviso({ l: 1, c: 0 }, "ATOM-007", `unpaired=${especie.desemparelhados}, mas a configuração ${textoConfig(m)} tem ${hundDe(m)} elétron(s) desemparelhado(s) pela regra de Hund`, [0]);
    }

    // Tipo da espécie (IUPAC: molécula tem mais de um átomo)
    const atomica = especie.tipo === "atom" || especie.tipo === "monatomic_ion";
    const somaCargas = atomos.reduce((t, a) => t + a.carga, 0);
    const cabecalho = { l: 1, c: 0 };
    if (!erros.length) {
      if (!especie.legado && especie.carga != null && somaCargas !== especie.carga) {
        erro(cabecalho, "CARGA-002", `a soma das cargas formais é ${somaCargas >= 0 ? "+" : ""}${somaCargas}, mas a espécie declara carga total ${especie.carga >= 0 ? "+" : ""}${especie.carga}`);
      }
      if (!especie.legado && especie.carga == null && somaCargas !== 0 && !["ionic_solid", "covalent_network", "metallic_solid"].includes(especie.tipo)) {
        erro(cabecalho, "CARGA-002", `a soma das cargas formais é ${somaCargas >= 0 ? "+" : ""}${somaCargas}, mas a espécie declara carga total +0`);
      }
      if (atomica && (atomos.length !== 1 || ligacoes.length)) {
        erro(cabecalho, "SPEC-001", `${especie.tipo} descreve um único átomo, sem ligações; foram declarados ${atomos.length} átomo(s) e ${ligacoes.length} ligação(ões)`);
      } else if (especie.tipo === "atom" && somaCargas) {
        erro(cabecalho, "SPEC-001", "atom descreve um átomo neutro; para um átomo com carga use species monatomic_ion com charge");
      } else if (!atomica && atomos.length === 1 && (especie.tipo === "molecule" || especie.tipo === "molecular_ion")) {
        aviso(cabecalho, "SPEC-003", `uma molécula tem mais de um átomo (IUPAC); para uma espécie de um átomo só use species ${somaCargas ? "monatomic_ion" : "atom"}`, [0]);
      }
    }
    if (!erros.length && (especie.tipo === "ionic_solid" || especie.tipo === "covalent_network")) {
      aviso(cabecalho, "SPEC-002", `${especie.tipo} é uma estrutura estendida; o grafo representa apenas um motivo finito`);
    }
    if (!erros.length) {
      especie.comandos.filter((c) => c.tipo === "bond" && c.op === "~").forEach((c) => {
        aviso(c, "METAL-002", "ligação metálica é coletiva; uma aresta do grafo molecular não valida um sólido metálico");
      });
    }
    if (!erros.length && !atomica) {
      const soma = atomos.map(() => 0);
      for (const lig of ligacoes) { soma[lig.a] += lig.ordem; soma[lig.b] += lig.ordem; }
      const linhaAtomo = new Map();
      especie.comandos.filter((c) => c.tipo === "atom").forEach((c) => (porElemento.get(c.el) || []).forEach((a) => { if (!linhaAtomo.has(a.id)) linhaAtomo.set(a.id, c); }));
      const abaixo = [];
      for (const a of atomos) {
        const permitidas = valenciasDe(a);
        if (!permitidas) continue;
        const maximo = Math.max(...permitidas);
        const no = linhaAtomo.get(a.id) || { l: 1, c: 0 };
        if (soma[a.id] > maximo) erro(no, "VAL-001", `a soma das ordens de ligação de ${rotulo(a)} é ${soma[a.id]}; o máximo para ${a.el}${a.carga ? `(${a.carga > 0 ? "+" : ""}${a.carga})` : ""} é ${maximo}`, [a.id]);
        else if (!permitidas.includes(soma[a.id])) abaixo.push([no, a, permitidas]);
      }
      // Radical declarado: cada ligação que falta é um elétron do unpaired
      const faltam = abaixo.reduce((t, [, a, p]) => t + Math.min(...p.filter((v) => v > soma[a.id])) - soma[a.id], 0);
      if (!(especie.desemparelhados && faltam === especie.desemparelhados)) {
        abaixo.forEach(([no, a, permitidas]) => aviso(no, "VAL-002", `a soma das ordens de ligação de ${rotulo(a)} é ${soma[a.id]}; o esperado para ${a.el} é ${permitidas.join(" ou ")}`, [a.id]));
      }
      if (atomos.length > 1 && !especie.legado && especie.tipo !== "ionic_solid" && especie.tipo !== "metallic_solid" && componentes(atomos, ligacoes) > 1) {
        erro({ l: 1, c: 0 }, "STRUCT-008", "a entidade tem partes desconectadas");
      }
    }
    return { atomos, ligacoes, configuracoes, erros, avisos };
  }

  /* Estrutura do átomo: mesma lógica de src/atomo.py */
  const LETRA_L = "spdf";
  const NUCLEOS_GAS = { He: "1s2", Ne: "[He] 2s2 2p6", Ar: "[Ne] 3s2 3p6", Kr: "[Ar] 3d10 4s2 4p6", Xe: "[Kr] 4d10 5s2 5p6", Rn: "[Xe] 4f14 5d10 6s2 6p6" };
  const capacidadeL = (l) => 2 * (2 * l + 1);
  function lerSubcamadas(texto) {
    for (let i = 0; i < 6 && /\[(\w+)\]/.test(texto); i++) texto = texto.replace(/\[(\w+)\]/, (_, g) => ` ${NUCLEOS_GAS[g] || ""} `);
    return [...texto.matchAll(/(\d)([spdf])(\d+)/g)].map(([, n, letra, e]) => [Number(n), LETRA_L.indexOf(letra), Number(e)]);
  }
  function problemasPauli(lista) {
    const problemas = [], vistas = new Set();
    for (const [n, l, e] of lista) {
      if (l >= n) problemas.push(`a subcamada ${n}${LETRA_L[l]} não existe: na camada ${n}, l vai de 0 a ${n - 1}`);
      else if (e > capacidadeL(l) || e === 0) problemas.push(`${n}${LETRA_L[l]}${e}: a subcamada ${LETRA_L[l]} comporta de 1 a ${capacidadeL(l)} elétrons (princípio de Pauli)`);
      if (vistas.has(`${n},${l}`)) problemas.push(`a subcamada ${n}${LETRA_L[l]} aparece mais de uma vez`);
      vistas.add(`${n},${l}`);
    }
    return problemas;
  }
  const paraMapa = (lista) => { const m = new Map(); lista.forEach(([n, l, e]) => { if (e) m.set(`${n},${l}`, e); }); return m; };
  const ordemMadelung = () => { const p = []; for (let n = 1; n < 8; n++) for (let l = 0; l < Math.min(n, 4); l++) p.push([n, l]); return p.sort((a, b) => a[0] + a[1] - b[0] - b[1] || a[0] - b[0]); };
  function fundamental(simbolo, carga) {
    const texto = (DADOS.elementos[simbolo] || {}).config;
    if (!texto) return null;
    const m = paraMapa(lerSubcamadas(texto));
    for (let k = 0; k < carga; k++) {
      const chave = [...m.keys()].sort((a, b) => { const [na, la] = a.split(",").map(Number), [nb, lb] = b.split(",").map(Number); return nb - na || lb - la; })[0];
      if (!chave) break;
      m.set(chave, m.get(chave) - 1);
      if (!m.get(chave)) m.delete(chave);
    }
    for (let k = 0; k < -carga; k++) {
      for (const [n, l] of ordemMadelung()) { const c = `${n},${l}`; if ((m.get(c) || 0) < capacidadeL(l)) { m.set(c, (m.get(c) || 0) + 1); break; } }
    }
    return m;
  }
  const textoConfig = (m) => [...m.entries()].map(([c, e]) => [...c.split(",").map(Number), e]).sort((a, b) => a[0] - b[0] || a[1] - b[1]).map(([n, l, e]) => `${n}${LETRA_L[l]}${e}`).join(" ");
  const hundDe = (m) => [...m.entries()].reduce((t, [c, e]) => { const o = 2 * Number(c.split(",")[1]) + 1; return t + (e <= o ? e : 2 * o - e); }, 0);
  // Termo espectroscópico pelas regras de Hund (mesma conta de src/atomo.py)
  function termoDe(m) {
    let dobroS = 0, totalL = 0, decideJ = null;
    [...m.entries()].map(([c, e]) => [...c.split(",").map(Number), e]).sort((a, b) => a[1] - b[1] || a[0] - b[0]).forEach(([, l, e]) => {
      const o = 2 * l + 1;
      if (e >= capacidadeL(l)) return;
      const acima = Math.min(e, o), abaixo = e - acima;
      dobroS += acima - abaixo;
      for (let k = 0; k < acima; k++) totalL += l - k;
      for (let k = 0; k < abaixo; k++) totalL += l - k;
      if (e !== o) decideJ = e < o;
    });
    const dobroJ = decideJ === null || decideJ ? Math.abs(2 * totalL - dobroS) : 2 * totalL + dobroS;
    return `${dobroS + 1}${"SPDFGHIKLMNOQRTUV"[totalL] || "L=" + totalL}${dobroJ % 2 ? dobroJ + "/2" : dobroJ / 2}`;
  }
  const camadasDeMapa = (m) => { const v = []; m.forEach((e, c) => { const n = Number(c.split(",")[0]); v[n - 1] = (v[n - 1] || 0) + e; }); return Array.from(v, (x) => x || 0); };
  const mapasIguais = (a, b) => a.size === b.size && [...a].every(([c, e]) => b.get(c) === e);

  function valenciasDe(a) {
    const v = DADOS.valencias;
    if (a.carga) {
      const tabela = (v.valencias_com_carga[a.el] || {})[(a.carga > 0 ? "+" : "") + a.carga];
      return tabela || null;
    }
    const base = v.valencias[a.el];
    if (!base) return null;
    const expandidas = (v.valencias_expandidas[a.el] || {}).valencias || [];
    return [...new Set([...base, ...expandidas])];
  }

  function componentes(atomos, ligacoes) {
    const pai = atomos.map((_, i) => i);
    const achar = (x) => (pai[x] === x ? x : (pai[x] = achar(pai[x])));
    ligacoes.forEach((l) => { pai[achar(l.a)] = achar(l.b); });
    return new Set(atomos.map((_, i) => achar(i))).size;
  }

  // Mesma regra do compilador: Δχ < 0,4 apolar, até 1,7 polar, acima iônica
  // (convenção didática de Pauling, não uma fronteira rígida); ~ é metálica
  function classificar(l, atomos) {
    if (l.op === "~") return { classe: "metálica", dx: null };
    const xa = (DADOS.elementos[atomos[l.a].el] || {}).eletronegatividade;
    const xb = (DADOS.elementos[atomos[l.b].el] || {}).eletronegatividade;
    if (xa == null || xb == null) return { classe: "não classificada", dx: null };
    const dx = Math.abs(xa - xb);
    const { limite_apolar, limite_ionica } = DADOS.classificacao;
    return { classe: dx < limite_apolar ? "covalente apolar" : dx <= limite_ionica ? "covalente polar" : "iônica", dx };
  }

  function rotulo(a) { return a.nome ? `${a.nome} (${a.el}#${a.indice})` : `${a.el}#${a.indice}`; }

  // Ordem de Hill; isótopo declarado leva o número de massa sobrescrito
  // antes do símbolo (²H₂O), logo depois do mesmo elemento natural
  const SOBRESCRITO = "⁰¹²³⁴⁵⁶⁷⁸⁹";
  function formulaHill(atomos) {
    const n = new Map();
    atomos.forEach((a) => { const k = `${a.el}|${a.massa || 0}`; n.set(k, (n.get(k) || 0) + 1); });
    const temC = atomos.some((a) => a.el === "C");
    const ordem = [...n.keys()].sort((x, y) => {
      const [ex, mx] = x.split("|"), [ey, my] = y.split("|");
      const p = (e) => (temC ? (e === "C" ? 0 : e === "H" ? 1 : 2) : 2);
      return p(ex) - p(ey) || ex.localeCompare(ey) || Number(mx) - Number(my);
    });
    return ordem.map((k) => {
      const [e, m] = k.split("|");
      const massa = Number(m) ? String(m).replace(/\d/g, (d) => SOBRESCRITO[d]) : "";
      return massa + e + (n.get(k) > 1 ? n.get(k) : "");
    }).join("");
  }

  function compilar(texto) {
    // Guarda o resultado de cada fase, para a demonstração da tradução
    let tokens = null;
    try {
      tokens = tokenizar(texto);
      const especie = analisarSintaxe(tokens);
      return { tokens, arvore: especie.arvore, especie, ...analisarSemantica(especie) };
    } catch (e) {
      if (e instanceof ErroDSL) {
        return { tokens, arvore: e.arvore || null, falhaEm: e.fase, erros: [e.diagnostico()], avisos: [], atomos: [], ligacoes: [], configuracoes: [] };
      }
      throw e;
    }
  }

  /* Explicação de cada diagnóstico: o que significa e como corrigir */
  const EXPLICA = {
    "LEX-001": ["Caractere inválido", "O lexer encontrou um símbolo que não pertence à linguagem.", "Apague o caractere ou troque por um operador válido: - = # -> ~."],
    "LEX-002": ["Texto sem fechar", "O nome da espécie abriu aspas e não fechou na mesma linha.", "Feche as aspas: \"Nome\"."],
    "SIN-001": ["Comando incompleto", "A estrutura do comando não segue a gramática: falta algo ou algo veio fora de ordem.", "Compare com a forma do comando em Doc → Comandos; a mensagem diz o que era esperado."],
    "SIN-002": ["Comando inválido", "Apareceu algo que não começa nenhum comando.", "Comece cada linha com atom, bond, ring ou stereo, e feche a espécie com }."],
    "SIN-004": ["Fim inesperado", "O código terminou antes de a construção ficar completa.", "Feche a espécie com } ou complete o último comando."],
    "ELEM-001": ["Elemento desconhecido", "O símbolo não está na tabela periódica usada pelo compilador.", "Use o símbolo com a primeira letra maiúscula e a segunda minúscula: Cl, não CL."],
    "STRUCT-001": ["Átomo não encontrado", "A referência cita um nome ou um elemento que não foi declarado com atom.", "Declare o átomo (atom C as c9) ou corrija o nome na ligação."],
    "STRUCT-002": ["Nome repetido", "Dois átomos receberam o mesmo nome.", "Use nomes únicos. Com 4x atom H as h, os nomes já são h1, h2, h3 e h4."],
    "STRUCT-004": ["Átomos esgotados", "Citando pelo símbolo, cada ligação usa o próximo átomo ainda não citado, e não sobrou nenhum.", "Dê nomes aos átomos e use os nomes nas ligações."],
    "STRUCT-005": ["Ligação consigo mesmo", "Os dois lados da ligação são o mesmo átomo.", "Ligue a outro átomo; confira os nomes."],
    "STRUCT-006": ["Ligação repetida", "Esses dois átomos já estão ligados.", "Para dupla ou tripla, escreva uma única linha com = ou #, em vez de repetir bond."],
    "STRUCT-008": ["Partes desconectadas", "Algum átomo não tem caminho de ligações até os demais.", "Ligue todos os átomos, ou use species ionic_solid para um sólido iônico."],
    "RING-002": ["Anel não fecha", "Dois átomos vizinhos na lista do ring não estão ligados.", "Liste os átomos na ordem do ciclo e declare a ligação que falta."],
    "STEREO-001": ["Referência ambígua", "Em stereo cada referência precisa apontar para um único átomo.", "Use o nome do átomo em vez do símbolo do elemento."],
    "ATOM-001": ["Número de massa impossível", "O número de massa A conta prótons e nêutrons (A = Z + N); menor que Z daria nêutrons negativos.", "Use um número de massa maior ou igual ao número atômico, como atom 12C ou atom 13C."],
    "ATOM-002": ["Subcamada inválida", "Pelo princípio de Pauli, a subcamada l comporta 2(2l+1) elétrons (s2, p6, d10, f14), e na camada n só existem l de 0 a n−1.", "Confira a subcamada: 2p tem no máximo 6 elétrons e não existe 2d; o núcleo entre colchetes deve ser um gás nobre."],
    "ATOM-003": ["Número de elétrons errado", "A configuração precisa ter Z − carga elétrons: o átomo neutro tem tantos elétrons quanto prótons.", "Some as subcamadas e ajuste; para um íon, lembre que a carga +1 tira um elétron."],
    "ATOM-004": ["Estado excitado", "A configuração é possível, mas não é a de menor energia (estado fundamental medido).", "Se quis o estado fundamental, use a referência indicada; se quis um estado excitado, o aviso só registra isso."],
    "ATOM-005": ["Isótopo não natural", "O número de massa não está entre os isótopos de composição natural da CIAAW: pode ser radioativo ou artificial.", "Confira o número de massa; para a composição natural, omita-o (atom C)."],
    "ATOM-006": ["Configuração fora de lugar", "A configuração eletrônica descreve um átomo isolado ou um íon monoatômico; em moléculas os elétrons ocupam orbitais moleculares.", "Use configuration só com species atom ou species monatomic_ion, uma vez por átomo."],
    "ATOM-007": ["Contra a regra de Hund", "Pela regra de Hund os elétrons ocupam orbitais de mesma energia um a um; isso fixa quantos ficam desemparelhados.", "Ajuste o unpaired para o valor indicado pela configuração."],
    "SPEC-001": ["Tipo de espécie incompatível", "O tipo do cabeçalho não combina com o conteúdo: atom e monatomic_ion descrevem um único átomo, sem ligações.", "Use species molecule para mais de um átomo, ou species monatomic_ion com charge para um átomo com carga."],
    "SPEC-002": ["Motivo de uma estrutura estendida", "Sólidos iônicos e redes covalentes são infinitos; o grafo descreve só uma unidade que se repete.", "Nada a corrigir: o aviso registra o limite do modelo."],
    "METAL-002": ["Ligação metálica coletiva", "Num metal os elétrons ficam deslocalizados por todo o sólido; uma aresta ~ só indica o motivo.", "Nada a corrigir: o aviso registra o limite do modelo."],
    "SPEC-003": ["Molécula de um átomo só", "Pela IUPAC, molécula é uma entidade neutra com mais de um átomo. Um átomo sozinho é um átomo; com carga, é um íon monoatômico.", "Troque o cabeçalho por species atom \"Nome\" ou species monatomic_ion \"Nome\" charge ±N."],
    "CARGA-002": ["Carga total diferente", "A soma das cargas formais dos átomos não bate com a carga declarada no cabeçalho.", "Ajuste a carga de algum átomo, como atom N(+1), ou o charge do cabeçalho."],
    "VAL-001": ["Valência excedida", "A soma das ordens das ligações passa do máximo permitido para o elemento.", "Remova uma ligação, troque = por -, ou declare a carga do átomo, como atom N(+1)."],
    "VAL-002": ["Valência incompleta", "O átomo tem menos ligações que o esperado. Pode faltar hidrogênio, ou a espécie é um íon ou radical.", "Adicione os H que faltam, declare a carga (atom C(-1)) ou use unpaired para radical."],
  };

  const EXEMPLOS_DE_ERRO = {
    valencia: 'species molecule "Pentavalente" {\n    atom C as c\n    5x atom H as h\n    bond c-h1\n    bond c-h2\n    bond c-h3\n    bond c-h4\n    bond c-h5\n}\n',
    nome: 'species molecule "Agua" {\n    atom O as o\n    2x atom H as h\n    bond o-h1\n    bond o-h3\n}\n',
    caractere: 'species molecule "Metano" {\n    atom C @\n    4x atom H\n}\n',
    chave: 'species molecule "Amonia" {\n    atom N\n    3x atom H\n    bond N-H x3\n',
    repetida: 'species molecule "Oxigenio" {\n    atom O as o1\n    atom O as o2\n    bond o1-o2\n    bond o1-o2\n}\n',
    incompleta: 'species molecule "Etano" {\n    atom C as c1\n    atom C as c2\n    4x atom H as h\n    bond c1-c2\n    bond c1-h1\n    bond c1-h2\n    bond c2-h3\n    bond c2-h4\n}\n',
  };

  /* ================= desenho 3D ================= */
  const CORES = { H: "#e4e3ea", C: "#5d5b66", N: "#8c95d8", O: "#d68c9a", S: "#d7c47a", P: "#d9a36f",
    F: "#8fc7a4", Cl: "#86bf9a", Br: "#b08470", I: "#9a80bd", B: "#d3b39a", Na: "#b1a2e6", K: "#b1a2e6" };
  const corDe = (el) => CORES[el] || "#b9a3f7";
  const raioDe = (el) => (el === "H" ? 0.36 : 0.56);

  function aleatorio(semente) {
    let s = semente >>> 0 || 1;
    return () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296);
  }

  function layout(atomosReais, ligacoesReais) {
    // Pares livres entram como pontos invisíveis que se repelem (VSEPR):
    // assim a água sai angular e a amônia piramidal
    const atomos = [...atomosReais];
    const ligacoes = [...ligacoesReais];
    const soma = atomosReais.map(() => 0);
    ligacoesReais.forEach((l) => { soma[l.a] += l.ordem; soma[l.b] += l.ordem; });
    atomosReais.forEach((a, i) => {
      const eletrons = (DADOS.elementos[a.el] || {}).valencia;
      if (eletrons == null || a.el === "H" || !soma[i]) return;
      const pares = Math.floor((eletrons - a.carga - soma[i]) / 2);
      for (let k = 0; k < Math.min(pares, 3); k++) {
        atomos.push({ el: "par", fantasma: true });
        ligacoes.push({ a: i, b: atomos.length - 1, ordem: 1, fantasma: true });
      }
    });
    const n = atomos.length;
    const rnd = aleatorio(n * 7919 + ligacoes.length * 104729);
    const pos = atomos.map(() => [rnd() - 0.5, rnd() - 0.5, rnd() - 0.5].map((v) => v * Math.cbrt(n) * 1.6));
    const vizinhos = atomos.map(() => new Set());
    ligacoes.forEach((l) => { vizinhos[l.a].add(l.b); vizinhos[l.b].add(l.a); });
    const repouso = (l) => {
      if (l.fantasma) return 0.75;
      const h = atomos[l.a].el === "H" || atomos[l.b].el === "H";
      if (l.ordem === 0) return 2.2;
      return (h ? 1.05 : 1.5) * ({ 1: 1, 2: 0.88, 3: 0.79 }[l.ordem] || 1);
    };
    let passo = 0.12;
    const iteracoes = n > 60 ? 500 : 900;
    for (let it = 0; it < iteracoes; it++) {
      const forca = pos.map(() => [0, 0, 0]);
      for (let i = 0; i < n; i++) {
        for (let j = i + 1; j < n; j++) {
          const d = [0, 1, 2].map((k) => pos[i][k] - pos[j][k]);
          const r2 = d[0] * d[0] + d[1] * d[1] + d[2] * d[2] + 0.01;
          const r = Math.sqrt(r2);
          let k = 0.9 / r2;
          if (vizinhos[i].has(j)) k *= 0.2;
          else for (const v of vizinhos[i]) if (vizinhos[v].has(j)) { k *= 2.4; break; }
          if (r > 6) continue;
          for (let c = 0; c < 3; c++) { forca[i][c] += (d[c] / r) * k; forca[j][c] -= (d[c] / r) * k; }
        }
      }
      for (const l of ligacoes) {
        const d = [0, 1, 2].map((k) => pos[l.b][k] - pos[l.a][k]);
        const r = Math.hypot(...d) + 1e-6;
        const k = 2.2 * (r - repouso(l));
        for (let c = 0; c < 3; c++) { forca[l.a][c] += (d[c] / r) * k; forca[l.b][c] -= (d[c] / r) * k; }
      }
      for (let i = 0; i < n; i++) {
        for (let c = 0; c < 3; c++) pos[i][c] += Math.max(-0.4, Math.min(0.4, forca[i][c] * passo));
      }
      passo *= 0.997;
    }
    const reais = pos.slice(0, atomosReais.length);
    const centro = [0, 1, 2].map((k) => reais.reduce((s, p) => s + p[k], 0) / Math.max(reais.length, 1));
    reais.forEach((p) => { for (let k = 0; k < 3; k++) p[k] -= centro[k]; });
    return reais;
  }

  const NUCLEOS = { He: "1s2", Ne: "[He] 2s2 2p6", Ar: "[Ne] 3s2 3p6", Kr: "[Ar] 3d10 4s2 4p6", Xe: "[Kr] 4d10 5s2 5p6", Rn: "[Xe] 4f14 5d10 6s2 6p6" };
  function camadas(simbolo) {
    // Elétrons por camada a partir da configuração eletrônica da fonte
    let config = (DADOS.elementos[simbolo] || {}).config || "";
    for (let i = 0; i < 6 && /\[(\w+)\]/.test(config); i++) config = config.replace(/\[(\w+)\]/, (_, g) => ` ${NUCLEOS[g] || ""} `);
    const porCamada = [];
    for (const [, n, , e] of config.matchAll(/(\d)([spdf])(\d+)/g)) porCamada[n - 1] = (porCamada[n - 1] || 0) + Number(e);
    return Array.from(porCamada, (v) => v || 0);
  }

  // Elétrons por camada de um íon: tira da camada mais externa (cátion) ou
  // completa a mais externa (ânion)
  function camadasComCarga(simbolo, carga) {
    const lista = camadas(simbolo);
    let resto = carga;
    while (resto > 0 && lista.length) {
      lista[lista.length - 1]--;
      if (!lista[lista.length - 1]) lista.pop();
      resto--;
    }
    if (resto < 0) lista[Math.max(0, lista.length - 1)] = (lista[lista.length - 1] || 0) - resto;
    return lista;
  }

  // Modelo de Bohr: núcleo com o símbolo e camadas com elétrons girando
  function pintarBohr(ctx, w, h, simbolo, lista, tempo, carga = 0, massa = null) {
    const escuro = raiz.dataset.theme !== "light";
    const cx = w / 2, cy = h / 2, n = Math.max(lista.length, 1);
    const rMax = Math.min(w, h) / 2 - 14, rNucleo = Math.max(12, rMax * 0.14);
    const acento = getComputedStyle(raiz).getPropertyValue("--acento").trim();
    lista.forEach((eletrons, k) => {
      const r = rNucleo + ((k + 1) / n) * (rMax - rNucleo);
      ctx.strokeStyle = escuro ? "rgba(255,255,255,0.12)" : "rgba(30,20,60,0.14)";
      ctx.lineWidth = 1;
      ctx.beginPath(); ctx.arc(cx, cy, r, 0, Math.PI * 2); ctx.stroke();
      const giro = (tempo / 1000) * (0.5 / (k + 1));
      for (let i = 0; i < eletrons; i++) {
        const ang = giro + (i / eletrons) * Math.PI * 2;
        ctx.fillStyle = acento;
        ctx.beginPath(); ctx.arc(cx + r * Math.cos(ang), cy + r * Math.sin(ang), Math.max(2.2, rMax * 0.022), 0, Math.PI * 2); ctx.fill();
      }
    });
    ctx.fillStyle = corDe(simbolo);
    ctx.beginPath(); ctx.arc(cx, cy, rNucleo, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = simbolo === "H" ? "#2a2830" : "#fff";
    ctx.font = `700 ${rNucleo * 0.8}px ui-monospace, Menlo, monospace`;
    ctx.textAlign = "center"; ctx.textBaseline = "middle";
    ctx.fillText(simbolo, cx, cy + 1);
    const z = (DADOS.elementos[simbolo] || {}).numero;
    ctx.fillStyle = escuro ? "rgba(236,235,242,0.75)" : "rgba(28,26,35,0.75)";
    ctx.font = `600 ${Math.max(10, rNucleo * 0.42)}px ui-monospace, Menlo, monospace`;
    ctx.fillText(massa ? `${massa}${simbolo}: ${z} p, ${massa - z} n` : `${z} prótons`, cx, cy + rNucleo + Math.max(12, rNucleo * 0.5));
    if (carga) {
      ctx.fillStyle = acento;
      ctx.font = `700 ${rNucleo * 0.7}px ui-monospace, Menlo, monospace`;
      ctx.fillText(`${Math.abs(carga) > 1 ? Math.abs(carga) : ""}${carga > 0 ? "+" : "−"}`, cx + rNucleo * 1.1, cy - rNucleo * 0.9);
    }
  }

  const COR_CLASSE = {
    "covalente apolar": ["rgba(200, 196, 214, 0.6)", "rgba(70, 64, 88, 0.55)"],
    "covalente polar": ["#b9a3f7", "#7a5ae0"],
    "iônica": ["#e0bd72", "#a3700a"],
    "metálica": ["rgba(200, 196, 214, 0.6)", "rgba(70, 64, 88, 0.55)"],
    "não classificada": ["rgba(200, 196, 214, 0.3)", "rgba(70, 64, 88, 0.3)"],
  };

  class Cena {
    constructor(canvas) {
      this.canvas = canvas;
      this.ctx = canvas.getContext("2d");
      this.atomos = []; this.ligacoes = []; this.pos = [];
      this.rx = -0.35; this.ry = 0.5; this.zoom = 1;
      this.girar = true; this.rotulos = false; this.semH = false;
      this.arrastando = false;
      // velocidade da rotação automática; aoQuadro(t) anima posições (misturas e reações)
      this.velocidade = 0.006;
      this.destaques = new Map(); // id do átomo -> "erro" ou "aviso"
      this.aoQuadro = null;
      const inicio = (x, y) => { this.arrastando = true; this.ultimo = [x, y]; canvas.style.cursor = "grabbing"; };
      const mover = (x, y) => {
        if (!this.arrastando) return;
        this.ry += (x - this.ultimo[0]) * 0.01; this.rx += (y - this.ultimo[1]) * 0.01;
        this.ultimo = [x, y]; this.desenhar();
      };
      const fim = () => { this.arrastando = false; canvas.style.cursor = "grab"; };
      canvas.addEventListener("pointerdown", (e) => { canvas.setPointerCapture(e.pointerId); inicio(e.clientX, e.clientY); });
      canvas.addEventListener("pointermove", (e) => mover(e.clientX, e.clientY));
      canvas.addEventListener("pointerup", fim);
      canvas.addEventListener("pointercancel", fim);
      canvas.addEventListener("wheel", (e) => { e.preventDefault(); this.zoom = Math.min(3, Math.max(0.4, this.zoom * (e.deltaY > 0 ? 0.92 : 1.08))); this.desenhar(); }, { passive: false });
      new ResizeObserver(() => this.desenhar()).observe(canvas);
      const quadro = (tempo) => {
        if (this.atomos.length && this.visivel()) {
          let mudou = false;
          if (this.aoQuadro) { this.aoQuadro(tempo); mudou = true; }
          if (this.atomos.length === 1) mudou = true;
          if (this.girar && !this.arrastando) { this.ry += this.velocidade; mudou = true; }
          if (mudou) this.desenhar();
        }
        requestAnimationFrame(quadro);
      };
      requestAnimationFrame(quadro);
    }
    visivel() { return this.canvas.offsetParent !== null; }
    carregar(atomos, ligacoes, posicoes = null) {
      this.aoQuadro = null;
      this.atomos = atomos; this.ligacoes = ligacoes; this.pos = posicoes || layout(atomos, ligacoes);
      this.classes = ligacoes.map((l) => classificar(l, atomos).classe);
      this.ajustarEscala();
      this.desenhar();
    }
    ajustarEscala(raioMinimo = 1.5) {
      const raio = Math.max(raioMinimo, ...this.pos.map((p) => Math.hypot(...p)));
      this.escalaBase = 1 / (raio + 0.8);
    }
    desenhar() {
      const c = this.canvas, ctx = this.ctx;
      const dpr = window.devicePixelRatio || 1;
      const w = c.clientWidth, h = c.clientHeight;
      if (!w || !h) return;
      if (c.width !== Math.round(w * dpr) || c.height !== Math.round(h * dpr)) { c.width = Math.round(w * dpr); c.height = Math.round(h * dpr); }
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.clearRect(0, 0, w, h);
      if (!this.atomos.length) return;
      const escuro = raiz.dataset.theme !== "light";
      if (this.atomos.length === 1) {
        // Espécie de um átomo só: modelo de Bohr com a carga do íon
        const a = this.atomos[0];
        const lista = a.configuracao ? camadasDeMapa(a.configuracao) : camadasComCarga(a.el, a.carga);
        pintarBohr(ctx, w, h, a.el, lista, performance.now(), a.carga, a.massa);
        return;
      }
      const cy = Math.cos(this.ry), sy = Math.sin(this.ry), cx = Math.cos(this.rx), sx = Math.sin(this.rx);
      const escala = Math.min(w, h) * 0.46 * this.escalaBase * this.zoom;
      const proj = this.pos.map(([x, y, z]) => {
        const x1 = x * cy + z * sy, z1 = -x * sy + z * cy;
        const y1 = y * cx - z1 * sx, z2 = y * sx + z1 * cx;
        const f = 6 / (6 - z2 * this.escalaBase * 2.2);
        return { x: w / 2 + x1 * escala * f, y: h / 2 + y1 * escala * f, z: z2, f };
      });
      const oculto = (i) => this.semH && this.atomos[i].el === "H";
      const itens = [];
      this.ligacoes.forEach((l, k) => { if (!oculto(l.a) && !oculto(l.b)) itens.push({ t: "l", l, k, z: (proj[l.a].z + proj[l.b].z) / 2 - 0.01 }); });
      this.atomos.forEach((a, i) => { if (!oculto(i)) itens.push({ t: "a", i, z: proj[i].z }); });
      itens.sort((p, q) => p.z - q.z);
      const corLigacao = escuro ? "rgba(200, 196, 214, 0.55)" : "rgba(70, 64, 88, 0.5)";
      for (const item of itens) {
        if (item.t === "l") {
          const { l } = item, A = proj[l.a], B = proj[l.b];
          const dx = B.x - A.x, dy = B.y - A.y, len = Math.hypot(dx, dy) || 1;
          const nx = -dy / len, ny = dx / len;
          if (l.alfa === 0) continue;
          ctx.globalAlpha = l.alfa == null ? 1 : l.alfa;
          const largura = Math.max(1.2, 0.09 * escala * (A.f + B.f) / 2);
          const classe = (this.classes || [])[item.k] || "não classificada";
          ctx.strokeStyle = (COR_CLASSE[classe] || [corLigacao, corLigacao])[escuro ? 0 : 1];
          ctx.lineWidth = l.ordem > 1 ? largura * 0.7 : largura;
          ctx.lineCap = "round";
          // coordenada: traço longo; iônica: tracejado; metálica: pontilhado
          ctx.setLineDash(l.op === "->" ? [largura * 2.2, largura * 1.1] : l.op === "~" ? [1, largura * 1.8] : classe === "iônica" ? [largura * 0.9, largura * 0.9] : []);
          const linhas = l.ordem <= 1 ? [0] : l.ordem === 2 ? [-0.5, 0.5] : [-1, 0, 1];
          const sep = largura * 1.35;
          for (const o of linhas) {
            ctx.beginPath();
            ctx.moveTo(A.x + nx * o * sep, A.y + ny * o * sep);
            ctx.lineTo(B.x + nx * o * sep, B.y + ny * o * sep);
            ctx.stroke();
          }
          ctx.setLineDash([]);
          ctx.globalAlpha = 1;
        } else {
          const a = this.atomos[item.i], P = proj[item.i];
          const r = raioDe(a.el) * escala * P.f * 0.62;
          const g = ctx.createRadialGradient(P.x - r * 0.35, P.y - r * 0.4, r * 0.1, P.x, P.y, r);
          const base = corDe(a.el);
          g.addColorStop(0, "#ffffff");
          g.addColorStop(0.25, base);
          g.addColorStop(1, escuro ? "#141417" : "#8d89a0");
          ctx.fillStyle = g;
          ctx.beginPath(); ctx.arc(P.x, P.y, r, 0, Math.PI * 2); ctx.fill();
          const destaque = this.destaques.get(item.i);
          if (destaque) {
            const cor = destaque === "erro" ? "#e5485f" : "#d9a531";
            const pulso = 1.35 + Math.sin(performance.now() / 260) * 0.12;
            ctx.strokeStyle = cor; ctx.lineWidth = 2.5;
            ctx.beginPath(); ctx.arc(P.x, P.y, r * pulso, 0, Math.PI * 2); ctx.stroke();
            ctx.globalAlpha = 0.18; ctx.fillStyle = cor;
            ctx.beginPath(); ctx.arc(P.x, P.y, r * pulso * 1.3, 0, Math.PI * 2); ctx.fill();
            ctx.globalAlpha = 1;
          }
          if (this.rotulos && r > 7) {
            ctx.fillStyle = a.el === "H" ? "#2a2830" : "#ffffff";
            ctx.font = `600 ${Math.max(9, r * 0.75)}px ui-monospace, Menlo, monospace`;
            ctx.textAlign = "center"; ctx.textBaseline = "middle";
            ctx.fillText(a.el, P.x, P.y + 0.5);
          }
        }
      }
    }
  }

  /* ================= playground ================= */
  const codigo = document.getElementById("codigo");
  const numeros = document.getElementById("numeros");
  const seletor = document.getElementById("exemplo");
  const cena = new Cena(document.getElementById("cena-3d"));
  const vazio = document.getElementById("cena-vazia");
  let exemploAtual = null;
  let tradPlay = null; // painel de tradução ao vivo, criado depois dos módulos
  let arvoresProntas = false; // aba Árvores, idem

  seletor.innerHTML = '<option value="" disabled>Código próprio (escolha um exemplo para carregar)</option>';
  // Um <optgroup> por grupo: átomos, íons, moléculas, isótopos, sólidos...
  const gruposSeletor = new Map();
  DADOS.exemplos.forEach((ex, i) => {
    if (!gruposSeletor.has(ex.grupo)) {
      const grupo = document.createElement("optgroup");
      grupo.label = ex.grupo;
      seletor.appendChild(grupo);
      gruposSeletor.set(ex.grupo, grupo);
    }
    const op = document.createElement("option");
    op.value = i; op.textContent = `${ex.titulo} — ${ex.arquivo}`;
    gruposSeletor.get(ex.grupo).appendChild(op);
  });

  codigo.addEventListener("scroll", () => {
    numeros.style.transform = `translateY(${-codigo.scrollTop}px)`;
    const realce = document.getElementById("realce");
    realce.style.transform = `translate(${-codigo.scrollLeft}px, ${-codigo.scrollTop}px)`;
  });

  function executar() {
    const r = compilar(codigo.value);
    renderizarDiagnosticos(r);
    if (tradPlay) tradPlay.desenhar();
    if (arvoresProntas) atualizarArvores();
    const modelo = document.querySelector("#p-modelo pre");
    document.getElementById("legenda-ligacoes").innerHTML = legendaLigacoes(r);
    if (r.atomos.length && !r.erros.length) {
      const nomes = r.atomos.map(rotulo);
      const simbolo = { "-": "SIMPLES", "=": "DUPLA", "#": "TRIPLA", "->": "COORDENADA", "~": "METALICA" };
      modelo.textContent = [`Modelo '${r.especie.nome}' tipo=${r.especie.tipo}`, `Átomos (${r.atomos.length})`, ...r.atomos.map((a) => `  ${rotulo(a)} carga=${a.carga >= 0 ? "+" : ""}${a.carga}`),
        `Ligações (${r.ligacoes.length})`, ...r.ligacoes.map((l) => {
          const { classe, dx } = classificar(l, r.atomos);
          return `  ${nomes[l.a]} ${simbolo[l.op]} ${nomes[l.b]} classificação=${classe}${dx != null ? ` Δχ=${dx.toFixed(2)}` : ""}`;
        }),
        ...(r.configuracoes.length ? [`Configurações (${r.configuracoes.length})`, ...r.configuracoes.map((c) => `  ${c.atomos.map(rotulo).join(c.op || " ")} ${c.descritor}`)] : [])].join("\n");
    } else {
      modelo.textContent = "Corrija os erros para ver o modelo.";
    }
    const real = document.querySelector("#p-real pre");
    const intacto = exemploAtual && codigo.value === exemploAtual.codigo;
    real.textContent = intacto ? exemploAtual.saida : "O código foi editado ou não veio de um exemplo. Para a análise oficial, salve num arquivo .mol e rode python3 src/main.py --modelo arquivo.mol.";
    const resumo = document.getElementById("resumo");
    if (r.atomos.length) {
      const multiplas = r.ligacoes.filter((l) => l.ordem >= 2).length;
      const aneis = r.ligacoes.filter((l) => l.ordem > 0).length - r.atomos.length + componentes(r.atomos, r.ligacoes.filter((l) => l.ordem > 0));
      const carga = r.atomos.reduce((t, a) => t + a.carga, 0);
      const sobrescrito = (n) => String(n).replace(/./g, (c) => "⁰¹²³⁴⁵⁶⁷⁸⁹"[c] || c);
      const sufixo = carga ? `${Math.abs(carga) > 1 ? sobrescrito(Math.abs(carga)) : ""}${carga > 0 ? "⁺" : "⁻"}` : "";
      const plural = (n, um, varios) => `<b>${n}</b> ${n === 1 ? um : varios}`;
      resumo.innerHTML = `<span>fórmula (Hill) <b>${formulaHill(r.atomos)}${sufixo}</b></span><span>${plural(r.atomos.length, "átomo", "átomos")}</span><span>${plural(r.ligacoes.length, "ligação", "ligações")}</span><span><b>${multiplas}</b> múltiplas</span><span><b>${Math.max(0, aneis)}</b> anéis</span>`;
    } else {
      resumo.innerHTML = "";
    }
    if (r.atomos.length) { vazio.hidden = true; cena.carregar(r.atomos, r.ligacoes); }
    else { vazio.hidden = false; vazio.textContent = r.erros.length ? "Corrija o erro para desenhar a molécula" : "Declare átomos para desenhar"; cena.carregar([], []); }
  }

  function legendaLigacoes(r) {
    if (!r.ligacoes.length) {
      if (r.atomos.length !== 1) return "";
      const a = r.atomos[0], m = a.configuracao || fundamental(a.el, a.carga);
      const eletrosfera = m ? ` · ${textoConfig(m)} · termo ${termoDe(m)}` : "";
      return `<span class="item-legenda">${r.especie && r.especie.tipo === "monatomic_ion" ? "íon monoatômico" : "átomo isolado"}: modelo de Bohr, sem ligações${eletrosfera}</span>`;
    }
    const contagem = {};
    r.ligacoes.forEach((l) => {
      const { classe } = classificar(l, r.atomos);
      const nome = l.op === "->" ? `coordenada (${classe})` : classe;
      contagem[nome] = (contagem[nome] || 0) + 1;
    });
    return Object.entries(contagem).map(([nome, n]) => {
      const base = nome.startsWith("coordenada") ? "coordenada" : nome;
      return `<span class="item-legenda"><i class="traco ${base.replace(/\s/g, "-")}"></i>${n}× ${nome}</span>`;
    }).join("") + `<span class="item-legenda fraco">Δχ: &lt; 0,4 apolar · até 1,7 polar · &gt; 1,7 iônica (convenção didática)</span>`;
  }

  function renderizarAlerta(r) {
    // Faixa no topo do playground: erro em vermelho, aviso em âmbar
    const alerta = document.getElementById("alerta");
    const principal = r.erros[0] || r.avisos[0];
    document.querySelector(".cena").classList.toggle("com-erro", r.erros.length > 0);
    document.querySelector(".cena").classList.toggle("com-aviso", !r.erros.length && r.avisos.length > 0);
    if (!principal) {
      alerta.className = "alerta ok";
      alerta.innerHTML = `<b>Compila sem erros</b><span>A análise semântica aceitou a espécie: o compilador sairia com código 0.</span>`;
      return;
    }
    const [titulo, significa, corrigir] = EXPLICA[principal.codigo] || ["Diagnóstico", "", ""];
    const erro = principal.tipo === "erro";
    const saida = !erro ? "o compilador sairia com código 0, mas mostraria este aviso" : principal.fase === "semântico" ? "a compilação para na análise semântica (código de saída 2)" : "a compilação para antes da semântica (código de saída 1)";
    const extras = r.erros.length + r.avisos.length - 1;
    alerta.className = "alerta " + (erro ? "erro" : "aviso");
    alerta.innerHTML = `<div class="alerta-titulo"><span class="selo"></span><b></b></div><p class="alerta-msg"></p>
      <p class="alerta-ajuda"><span></span> <strong>Como corrigir:</strong> <span></span></p><p class="alerta-saida"></p>`;
    alerta.querySelector(".selo").textContent = `${erro ? "Erro" : "Aviso"} ${principal.fase} · ${principal.codigo} · linha ${principal.linha}`;
    alerta.querySelector(".alerta-titulo b").textContent = titulo;
    alerta.querySelector(".alerta-msg").textContent = principal.mensagem;
    const [sig, cor] = alerta.querySelectorAll(".alerta-ajuda span");
    sig.textContent = significa; cor.textContent = corrigir;
    alerta.querySelector(".alerta-saida").textContent = `Resultado: ${saida}.${extras > 0 ? ` Há mais ${extras} diagnóstico(s) na aba Diagnóstico.` : ""}`;
    alerta.onclick = () => irParaLinha(principal.linha);
  }

  function realcarLinhas(r) {
    const tipoPorLinha = new Map();
    [...r.avisos, ...r.erros].forEach((d) => tipoPorLinha.set(d.linha, d.tipo));
    document.getElementById("realce").innerHTML = codigo.value.split("\n").map((linha, i) => {
      const tipo = tipoPorLinha.get(i + 1);
      const texto = escaparHTML(linha) || " ";
      return tipo ? `<mark class="${tipo}">${texto}</mark>` : texto;
    }).join("\n") + "\n";
  }
  const escaparHTML = (t) => t.replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));

  function renderizarDiagnosticos(r) {
    renderizarAlerta(r);
    realcarLinhas(r);
    cena.destaques = new Map();
    r.avisos.forEach((d) => (d.atomos || []).forEach((id) => cena.destaques.set(id, "aviso")));
    r.erros.forEach((d) => (d.atomos || []).forEach((id) => cena.destaques.set(id, "erro")));
    const painel = document.getElementById("p-diag");
    painel.innerHTML = "";
    const lista = [...r.erros, ...r.avisos];
    const linhasMarcadas = new Set(lista.map((d) => d.linha));
    numeros.innerHTML = codigo.value.split("\n").map((_, i) => linhasMarcadas.has(i + 1) ? `<span class="marcada">${i + 1}</span>` : String(i + 1)).join("\n");
    if (!r.erros.length) {
      const ok = document.createElement("div");
      ok.className = "diag ok";
      ok.innerHTML = `<div class="topo-diag"><span class="selo">OK</span><span class="titulo">Sem erros</span></div><p class="msg"></p>`;
      ok.querySelector(".msg").textContent = `Espécie '${r.especie.nome}': ${r.atomos.length} átomos e ${r.ligacoes.length} ligações, análise do navegador concluída.`;
      painel.appendChild(ok);
    }
    for (const d of lista) {
      const [titulo, significa, corrigir] = EXPLICA[d.codigo] || ["Diagnóstico", "", ""];
      const item = document.createElement("button");
      item.type = "button";
      item.className = "diag" + (d.tipo === "aviso" ? " aviso" : "");
      item.innerHTML = `<div class="topo-diag"><span class="selo"></span><span class="titulo"></span><span class="onde"></span></div><p class="msg"></p><dl><dt>O que é</dt><dd class="significa"></dd><dt>Como corrigir</dt><dd class="corrigir"></dd></dl>`;
      item.querySelector(".selo").textContent = `${d.tipo === "aviso" ? "Aviso" : "Erro"} ${d.fase} · ${d.codigo}`;
      item.querySelector(".titulo").textContent = titulo;
      item.querySelector(".onde").textContent = `linha ${d.linha}, coluna ${d.coluna}`;
      item.querySelector(".msg").textContent = d.mensagem;
      item.querySelector(".significa").textContent = significa;
      item.querySelector(".corrigir").textContent = corrigir;
      item.addEventListener("click", () => irParaLinha(d.linha));
      painel.appendChild(item);
    }
  }

  function irParaLinha(n) {
    const linhas = codigo.value.split("\n");
    const inicio = linhas.slice(0, n - 1).reduce((t, l) => t + l.length + 1, 0);
    codigo.focus();
    codigo.setSelectionRange(inicio, inicio + (linhas[n - 1] || "").length);
    codigo.scrollTop = Math.max(0, (n - 4) * parseFloat(getComputedStyle(codigo).lineHeight));
  }

  document.querySelectorAll("[data-erro]").forEach((botao) => botao.addEventListener("click", () => {
    exemploAtual = null;
    codigo.value = EXEMPLOS_DE_ERRO[botao.dataset.erro];
    seletor.value = "";
    executar();
    document.getElementById("alerta").scrollIntoView({ behavior: "smooth", block: "center" });
    document.querySelector('[data-painel="p-diag"]').click();
  }));

  let espera;
  codigo.addEventListener("input", () => {
    if (exemploAtual && codigo.value !== exemploAtual.codigo) seletor.value = "";
    clearTimeout(espera); espera = setTimeout(executar, 250);
  });
  codigo.addEventListener("keydown", (e) => {
    if (e.key === "Tab") {
      e.preventDefault();
      const i = codigo.selectionStart;
      codigo.setRangeText("    ", i, codigo.selectionEnd, "end");
      codigo.dispatchEvent(new Event("input"));
    }
  });
  seletor.addEventListener("change", () => carregarExemplo(Number(seletor.value)));
  document.getElementById("limpar").addEventListener("click", () => {
    exemploAtual = null;
    seletor.value = "";
    codigo.value = 'species molecule "Nova" {\n    \n}\n';
    executar(); codigo.focus();
  });
  document.getElementById("girar").addEventListener("change", (e) => { cena.girar = e.target.checked; });
  document.getElementById("rotulos").addEventListener("change", (e) => { cena.rotulos = e.target.checked; cena.desenhar(); });
  document.getElementById("esconder-h").addEventListener("change", (e) => { cena.semH = e.target.checked; cena.desenhar(); });
  document.getElementById("recentrar").addEventListener("click", () => { cena.rx = -0.35; cena.ry = 0.5; cena.zoom = 1; cena.desenhar(); });

  function carregarExemplo(i) {
    exemploAtual = DADOS.exemplos[i];
    seletor.value = i;
    codigo.value = exemploAtual.codigo;
    executar();
  }

  /* vitrine do início */
  const vitrine = new Cena(document.getElementById("vitrine-3d"));
  vitrine.velocidade = 0.0016;
  const benzeno = DADOS.exemplos.find((e) => e.arquivo.endsWith("benzeno.mol")) || DADOS.exemplos[0];
  const rb = compilar(benzeno.codigo);
  vitrine.rx = -0.9;
  vitrine.carregar(rb.atomos, rb.ligacoes);

  /* ================= malha do fundo ================= */
  (() => {
    const tela = document.getElementById("malha");
    const ctx = tela.getContext("2d");
    const parado = matchMedia("(prefers-reduced-motion: reduce)").matches;
    let nos = [], largura = 0, altura = 0;
    const DISTANCIA = 150;
    function montar() {
      const dpr = window.devicePixelRatio || 1;
      largura = innerWidth; altura = innerHeight;
      tela.width = largura * dpr; tela.height = altura * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      const quantidade = Math.round(Math.min(90, (largura * altura) / 16000));
      const rnd = aleatorio(42);
      nos = Array.from({ length: quantidade }, () => ({
        x: rnd() * largura, y: rnd() * altura,
        vx: (rnd() - 0.5) * 0.25, vy: (rnd() - 0.5) * 0.25,
        r: 1.6 + rnd() * 2.2,
      }));
    }
    function quadro() {
      const claro = raiz.dataset.theme === "light";
      const cor = claro ? "122, 90, 224" : "185, 163, 247";
      ctx.clearRect(0, 0, largura, altura);
      for (const no of nos) {
        if (!parado) {
          no.x += no.vx; no.y += no.vy;
          if (no.x < 0 || no.x > largura) no.vx *= -1;
          if (no.y < 0 || no.y > altura) no.vy *= -1;
        }
      }
      for (let i = 0; i < nos.length; i++) {
        for (let j = i + 1; j < nos.length; j++) {
          const d = Math.hypot(nos[i].x - nos[j].x, nos[i].y - nos[j].y);
          if (d < DISTANCIA) {
            ctx.strokeStyle = `rgba(${cor}, ${(1 - d / DISTANCIA) * (claro ? 0.22 : 0.18)})`;
            ctx.lineWidth = 1;
            ctx.beginPath(); ctx.moveTo(nos[i].x, nos[i].y); ctx.lineTo(nos[j].x, nos[j].y); ctx.stroke();
          }
        }
      }
      ctx.fillStyle = `rgba(${cor}, ${claro ? 0.32 : 0.3})`;
      for (const no of nos) { ctx.beginPath(); ctx.arc(no.x, no.y, no.r, 0, Math.PI * 2); ctx.fill(); }
      if (!parado && !document.hidden) requestAnimationFrame(quadro);
    }
    addEventListener("resize", () => { montar(); if (parado) quadro(); });
    document.addEventListener("visibilitychange", () => { if (!document.hidden && !parado) requestAnimationFrame(quadro); });
    new MutationObserver(() => { if (parado) quadro(); }).observe(raiz, { attributes: true, attributeFilter: ["data-theme"] });
    montar();
    quadro();
  })();

  /* @modulos */

  /* ================= rotas e paginação ================= */
  const slides = [...document.querySelectorAll(".slide")];
  const pontinhos = document.querySelector("#pg-conteudo .pontinhos");
  slides.forEach((s, i) => {
    const b = document.createElement("button");
    b.type = "button"; b.setAttribute("aria-label", `${i + 1}: ${s.dataset.titulo}`);
    b.addEventListener("click", () => (location.hash = `#/conteudo/${i + 1}`));
    pontinhos.appendChild(b);
  });
  const topicos = [...document.querySelectorAll(".topico")].map((t) => t.dataset.topico);
  let slideAtual = 1, topicoAtual = topicos[0];

  function mostrarSlide(n) {
    slideAtual = Math.min(slides.length, Math.max(1, n || 1));
    slides.forEach((s, i) => s.classList.toggle("ativo", i === slideAtual - 1));
    pontinhos.querySelectorAll("button").forEach((b, i) => b.classList.toggle("ativo", i === slideAtual - 1));
    const pag = document.querySelector("#pg-conteudo .paginador");
    pag.querySelector(".contador").textContent = `${slideAtual} / ${slides.length} · ${slides[slideAtual - 1].dataset.titulo}`;
    pag.querySelector('[data-passo="-1"]').disabled = slideAtual === 1;
    pag.querySelector('[data-passo="1"]').disabled = slideAtual === slides.length;
  }
  function mostrarTopico(nome) {
    topicoAtual = topicos.includes(nome) ? nome : topicos[0];
    document.querySelectorAll(".topico").forEach((t) => t.classList.toggle("ativo", t.dataset.topico === topicoAtual));
    document.querySelectorAll(".sumario a").forEach((a) => a.classList.toggle("ativo", a.dataset.topico === topicoAtual));
    const i = topicos.indexOf(topicoAtual);
    const pag = document.querySelector("#pg-doc .paginador");
    pag.querySelector(".contador").textContent = `${i + 1} / ${topicos.length}`;
    pag.querySelector('[data-doc-passo="-1"]').disabled = i === 0;
    pag.querySelector('[data-doc-passo="1"]').disabled = i === topicos.length - 1;
  }
  document.querySelectorAll("[data-passo]").forEach((b) => b.addEventListener("click", () => {
    location.hash = `#/conteudo/${slideAtual + Number(b.dataset.passo)}`;
  }));
  document.querySelectorAll("[data-doc-passo]").forEach((b) => b.addEventListener("click", () => {
    location.hash = `#/doc/${topicos[topicos.indexOf(topicoAtual) + Number(b.dataset.docPasso)]}`;
  }));

  document.querySelectorAll("[data-ancora]").forEach((link) => link.addEventListener("click", (e) => {
    e.preventDefault();
    document.querySelector(link.getAttribute("href")).scrollIntoView({ behavior: "smooth" });
  }));
  const secoesInicio = ["s-inicio", "s-modulos", "s-linguagem", "s-comecar"].map((id) => document.getElementById(id));
  addEventListener("scroll", () => {
    if (!document.body.classList.contains("no-inicio")) return;
    let atual = secoesInicio[0].id;
    for (const secao of secoesInicio) if (secao.getBoundingClientRect().top <= innerHeight * 0.45) atual = secao.id;
    document.querySelectorAll(".pontos a").forEach((a) => a.classList.toggle("ativo", a.getAttribute("href") === "#" + atual));
  }, { passive: true });

  let primeiraVez = true;
  function rotear() {
    const partes = location.hash.replace(/^#\/?/, "").split("/");
    const rota = ["guia", "conteudo", "uso", "doc", "playground", "laboratorio", "tabela"].includes(partes[0]) ? partes[0] : "inicio";
    document.querySelectorAll(".pagina").forEach((p) => p.classList.toggle("ativa", p.id === "pg-" + rota));
    document.querySelectorAll(".rotas a").forEach((a) => a.classList.toggle("ativo", a.dataset.rota === rota));
    document.body.classList.toggle("no-inicio", rota === "inicio");
    document.querySelectorAll(".pontos a").forEach((a, i) => a.classList.toggle("ativo", i === 0));
    if (rota === "conteudo") mostrarSlide(Number(partes[1]));
    if (rota === "doc") mostrarTopico(partes[1]);
    if (rota === "guia") mostrarLicao(partes[1]);
    if (rota === "playground") {
      if (!codigo.value) carregarExemplo(0);
      requestAnimationFrame(() => cena.desenhar());
    }
    if (rota === "inicio") requestAnimationFrame(() => vitrine.desenhar());
    if (rota === "laboratorio") iniciarLaboratorio();
    if (rota === "tabela") iniciarTabela();
    if (!primeiraVez) window.scrollTo({ top: 0 });
    primeiraVez = false;
  }
  addEventListener("hashchange", rotear);
  addEventListener("keydown", (e) => {
    if (e.target.closest("textarea, select, input")) return;
    if (!document.getElementById("pg-conteudo").classList.contains("ativa")) return;
    if (e.key === "ArrowRight" && slideAtual < slides.length) location.hash = `#/conteudo/${slideAtual + 1}`;
    if (e.key === "ArrowLeft" && slideAtual > 1) location.hash = `#/conteudo/${slideAtual - 1}`;
  });
  new MutationObserver(() => { cena.desenhar(); vitrine.desenhar(); }).observe(raiz, { attributes: true, attributeFilter: ["data-theme"] });
  rotear();
