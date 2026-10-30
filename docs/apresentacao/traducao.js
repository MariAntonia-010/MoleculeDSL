  /* ================= árvore de tradução ================= */
  // Cada etapa da tradução é explicada por duas lentes: a da computação
  // (compiladores, gramática, estruturas de dados) e a da química.
  const NOME_TOKEN = {
    molecule: "MOLECULE", species: "SPECIES", molecular_ion: "MOLECULAR_ION", ionic_solid: "IONIC_SOLID",
    covalent_network: "COVALENT_NETWORK", metallic_solid: "METALLIC_SOLID", charge: "CHARGE", unpaired: "UNPAIRED",
    atom: "ATOM", bond: "BOND", as: "AS", ring: "RING", stereo: "STEREO", IDENT: "IDENT", NOME: "NOME",
    MULT: "MULTIPLICADOR_ATOMO", REP: "REPETICAO_LIGACAO", INT: "INTEIRO", REAL: "REAL", TEXTO: "TEXTO",
    "{": "ABRE_CHAVE", "}": "FECHA_CHAVE", "(": "ABRE_PAREN", ")": "FECHA_PAREN", "+": "MAIS", EOF: "EOF",
  };
  const NOME_OPERADOR = { "-": "LIGACAO", "=": "DUPLA", "#": "TRIPLA", "->": "COORDENADA", "~": "METALICA" };
  const LIGACAO_QUIMICA = {
    "-": "ligação simples: 1 par de elétrons compartilhado",
    "=": "ligação dupla: 2 pares compartilhados (σ + π)",
    "#": "ligação tripla: 3 pares compartilhados (σ + 2π)",
    "->": "ligação coordenada: o doador cede o par de elétrons",
    "~": "ligação metálica: elétrons deslocalizados (motivo do sólido)",
  };
  const ESPECIE_QUIMICA = {
    molecule: "molécula neutra e discreta", molecular_ion: "íon molecular (tem carga total)",
    ionic_solid: "sólido iônico (rede de íons)", covalent_network: "rede covalente", metallic_solid: "sólido metálico",
  };

  function nomeTokenComp(t) {
    return t.tipo === "OP" ? NOME_OPERADOR[t.valor] : NOME_TOKEN[t.tipo] || t.tipo;
  }

  function nomeElemento(simbolo) {
    const e = DADOS.elementos[simbolo];
    return e ? `${e.nome}, Z = ${e.numero}` : "elemento desconhecido";
  }

  function tokenQuimica(t) {
    switch (t.tipo) {
      case "molecule": case "species": return "abre a descrição de uma espécie química";
      case "molecular_ion": case "ionic_solid": case "covalent_network": case "metallic_solid": return ESPECIE_QUIMICA[t.tipo];
      case "TEXTO": return "nome da espécie";
      case "charge": return "carga total do íon";
      case "unpaired": return "elétrons desemparelhados (radical)";
      case "atom": return "declara átomo(s)";
      case "bond": return "declara uma ligação";
      case "ring": return "marca um anel (ciclo)";
      case "stereo": return "configuração espacial";
      case "as": return "dá nome ao átomo";
      case "IDENT": return DADOS.elementos[t.valor] ? `elemento: ${nomeElemento(t.valor)}` : "símbolo ou descritor";
      case "NOME": return "nome de um átomo específico";
      case "MULT": return `${t.valor.slice(0, -1)} átomos iguais`;
      case "REP": return `repete a ligação ${t.valor.slice(1)} vezes`;
      case "OP": return LIGACAO_QUIMICA[t.valor];
      case "INT": return "valor numérico (carga ou contagem)";
      case "+": return "sinal positivo da carga";
      case "(": case ")": return "delimita a carga formal";
      case "{": return "início dos átomos e ligações";
      case "}": return "fim da espécie";
      case "EOF": return "fim do texto";
      default: return "";
    }
  }

  const REGRAS = {
    programa: ["programa : molecula EOF", "o arquivo inteiro descreve uma única espécie"],
    molecula: ["molecula : cabecalho desemparelhados? '{' comando* '}'", "a espécie: cabeçalho e o conteúdo entre chaves"],
    cabecalho: ["cabecalho : MOLECULE TEXTO | SPECIES tipo TEXTO cargaEspecie?", "o tipo e o nome da espécie"],
    cargaEspecie: ["cargaEspecie : CHARGE sinal INTEIRO", "a carga total do íon"],
    desemparelhados: ["desemparelhados : UNPAIRED INTEIRO", "quantos elétrons ficam sem par"],
    comando: ["comando : atomo | ligacao | anel | estereo", "uma instrução sobre a estrutura"],
    atomo: ["atomo : MULTIPLICADOR_ATOMO? ATOM IDENT carga? (AS NOME)?", "um ou mais átomos de um elemento"],
    carga: ["carga : '(' sinal INTEIRO ')'", "a carga formal do átomo"],
    sinal: ["sinal : MAIS | LIGACAO", "positivo ou negativo"],
    ligacao: ["ligacao : BOND referencia operador referencia REPETICAO_LIGACAO?", "dois átomos que compartilham elétrons"],
    referencia: ["referencia : IDENT | NOME", "qual átomo participa"],
    operador: ["operador : LIGACAO | DUPLA | TRIPLA | COORDENADA | METALICA", "o tipo da ligação"],
    anel: ["anel : RING NOME NOME NOME+", "átomos que formam um ciclo"],
    estereo: ["estereo : STEREO referencia (operador? referencia)? descritor", "arranjo espacial declarado"],
    descritor: ["descritor : IDENT | NOME", "R, S, E, Z, Ra, Sa, cis ou trans"],
  };

  function escapar(texto) {
    return String(texto).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  }

  // Árvore genérica: { rotulo, detalhe, classe, filhos }
  function arvoreHTML(no) {
    const rotulo = `<span class="no-rotulo ${no.classe || ""}">${escapar(no.rotulo)}</span>${no.detalhe ? `<span class="no-detalhe">${escapar(no.detalhe)}</span>` : ""}`;
    if (!no.filhos || !no.filhos.length) return `<li><span class="no">${rotulo}</span></li>`;
    return `<li><details open><summary class="no">${rotulo}</summary><ul>${no.filhos.map(arvoreHTML).join("")}</ul></details></li>`;
  }

  function arvoreSintaticaNo(no, lente) {
    if (no.token) {
      const t = no.token;
      return { rotulo: `${nomeTokenComp(t)} '${t.valor}'`, detalhe: lente === "comp" ? `token, linha ${t.l}, coluna ${t.c}` : tokenQuimica(t), classe: "folha" };
    }
    const [comp, quim] = REGRAS[no.regra] || [no.regra, ""];
    return { rotulo: no.regra, detalhe: lente === "comp" ? comp : quim, filhos: no.filhos.map((f) => arvoreSintaticaNo(f, lente)) };
  }

  function astNo(especie, lente) {
    const q = lente === "quim";
    const filhos = especie.comandos.map((c) => {
      if (c.tipo === "atom") {
        return { rotulo: "AtomoDecl", detalhe: q ? `${c.mult > 1 ? c.mult + " átomos" : "átomo"} de ${nomeElemento(c.el)}${c.carga ? `, carga ${c.carga > 0 ? "+" : ""}${c.carga}` : ""}` : `[${c.l}:${c.c}]`,
          filhos: [["elemento", c.el], ["multiplicador", c.mult], ["carga", c.carga], ["nome", c.nome ?? "None"]].map(([k, v]) => ({ rotulo: `${k}: ${v}`, classe: "folha" })) };
      }
      if (c.tipo === "bond") {
        const op = { "-": "SIMPLES", "=": "DUPLA", "#": "TRIPLA", "->": "COORDENADA", "~": "METALICA" }[c.op];
        return { rotulo: "LigacaoDecl", detalhe: q ? LIGACAO_QUIMICA[c.op] : `[${c.l}:${c.c}]`,
          filhos: [`origem: ${c.origem.texto} (${c.origem.porNome ? "nome" : "elemento"})`, `operador: ${op}`, `destino: ${c.destino.texto} (${c.destino.porNome ? "nome" : "elemento"})`, `repeticoes: ${c.rep}`].map((r) => ({ rotulo: r, classe: "folha" })) };
      }
      if (c.tipo === "ring") return { rotulo: "AnelDecl", detalhe: q ? `ciclo de ${c.nomes.length} átomos` : `[${c.l}:${c.c}]`, filhos: c.nomes.map((n) => ({ rotulo: `nome: ${n.texto}`, classe: "folha" })) };
      return { rotulo: "EstereoDecl", detalhe: q ? "configuração espacial declarada" : `[${c.l}:${c.c}]`, filhos: [...c.refs.map((r) => ({ rotulo: `átomo: ${r.texto}`, classe: "folha" })), { rotulo: `descritor: ${c.descritor}`, classe: "folha" }] };
    });
    return { rotulo: `Molecula '${especie.nome}'`, detalhe: q ? ESPECIE_QUIMICA[especie.tipo] : `tipo=${especie.tipo}`, filhos };
  }

  const ETAPAS = [
    { id: "tokens", titulo: "Tokens", fase: "léxico",
      comp: "O lexer lê caractere por caractere e agrupa em tokens, usando as expressões regulares da gramática (IDENT = [A-Z][a-z]?, NOME = [a-z][a-z0-9_]*). Espaços e comentários são descartados.",
      quim: "O texto é separado em palavras com sentido químico: símbolos de elementos, tipos de ligação, quantidades e nomes de átomos." },
    { id: "sintaxe", titulo: "Árvore sintática", fase: "sintático",
      comp: "O parser (LL, gerado pelo ANTLR no compilador oficial) confere a ordem dos tokens contra as regras da gramática e monta a parse tree: cada nó é uma regra, cada folha um token.",
      quim: "Confere se a frase química está bem formada: todo átomo tem elemento, toda ligação tem dois átomos e um tipo, e a espécie abre e fecha." },
    { id: "ast", titulo: "AST", fase: "visitor",
      comp: "O visitor percorre a parse tree e cria a AST: só os conceitos, sem pontuação, com linha e coluna em cada nó. Quantificadores como 4x ficam no nó.",
      quim: "Sobra o essencial: quais átomos foram declarados, com que carga, e quais ligações existem entre eles." },
    { id: "modelo", titulo: "Modelo (grafo)", fase: "modelo",
      comp: "A AST vira um grafo: átomos são vértices, ligações são arestas com peso (a ordem). Multiplicadores são expandidos e referências por símbolo são resolvidas para átomos concretos.",
      quim: "É a fórmula estrutural: cada átomo individual e cada par de elétrons compartilhado entre dois átomos." },
    { id: "quimica", titulo: "Semântica e química", fase: "semântico",
      comp: "A análise semântica percorre o grafo em etapas (estrutura → valência → carga) e emite diagnósticos com código, linha e coluna. Sem erro, o programa sai com código 0.",
      quim: "Confere a química: a soma das ordens das ligações de cada átomo bate com a valência do elemento? A espécie está inteira, sem partes soltas?" },
  ];

  function conteudoEtapa(etapa, r, lente) {
    const falhou = (fases) => r.falhaEm && fases.includes(r.falhaEm);
    const erroHTML = () => `<div class="etapa-erro"><b>${escapar(r.erros[0].codigo)}</b> linha ${r.erros[0].linha}, coluna ${r.erros[0].coluna}: ${escapar(r.erros[0].mensagem)}<p>A tradução para aqui: as fases seguintes não rodam, para não gerar erros em cascata.</p></div>`;
    if (etapa.id === "tokens") {
      if (!r.tokens) return erroHTML();
      return `<div class="fichas">${r.tokens.filter((t) => t.tipo !== "EOF").map((t) =>
        `<span class="ficha"><code>${escapar(t.valor)}</code><small>${escapar(lente === "comp" ? nomeTokenComp(t) : tokenQuimica(t))}</small></span>`).join("")}</div>`;
    }
    if (etapa.id === "sintaxe") {
      if (!r.tokens) return `<p class="etapa-vazia">Sem tokens, não há o que analisar.</p>`;
      const arvore = r.arvore ? `<ul class="arvore">${arvoreHTML(arvoreSintaticaNo(r.arvore, lente))}</ul>` : "";
      return (falhou(["sintático"]) ? erroHTML() : "") + arvore;
    }
    if (etapa.id === "ast") {
      if (!r.especie) return `<p class="etapa-vazia">A AST só existe quando a sintaxe está correta.</p>`;
      return `<ul class="arvore">${arvoreHTML(astNo(r.especie, lente))}</ul>`;
    }
    if (etapa.id === "modelo") {
      if (!r.especie) return `<p class="etapa-vazia">O modelo depende da AST.</p>`;
      const nomes = r.atomos.map(rotulo);
      const simbolo = { "-": "SIMPLES", "=": "DUPLA", "#": "TRIPLA", "->": "COORDENADA", "~": "METALICA" };
      const vertices = { rotulo: `vértices: ${r.atomos.length} átomo(s)`, detalhe: lente === "comp" ? "lista de Atomo(id, elemento, índice, carga)" : "cada átomo individual",
        filhos: r.atomos.map((a) => ({ rotulo: rotulo(a), detalhe: lente === "comp" ? `id ${a.id}, carga ${a.carga}` : nomeElemento(a.el), classe: "folha" })) };
      const arestas = { rotulo: `arestas: ${r.ligacoes.length} ligação(ões)`, detalhe: lente === "comp" ? "pares (origem, destino) com ordem" : "pares de elétrons compartilhados",
        filhos: r.ligacoes.map((l) => ({ rotulo: `${nomes[l.a]} ${l.op} ${nomes[l.b]}`, detalhe: lente === "comp" ? `${simbolo[l.op]}, ordem ${l.ordem}` : LIGACAO_QUIMICA[l.op], classe: "folha" })) };
      return `<ul class="arvore">${arvoreHTML({ rotulo: "Modelo", detalhe: lente === "comp" ? "grafo não dirigido com pesos" : formulaHill(r.atomos), filhos: [vertices, arestas] })}</ul>`;
    }
    if (!r.especie) return `<p class="etapa-vazia">A semântica depende do modelo.</p>`;
    const soma = r.atomos.map(() => 0);
    r.ligacoes.forEach((l) => { soma[l.a] += l.ordem; soma[l.b] += l.ordem; });
    const linhas = r.atomos.map((a, i) => {
      const permitidas = valenciasDe(a);
      const estado = !permitidas ? "sem regra" : permitidas.includes(soma[i]) ? "ok" : soma[i] > Math.max(...permitidas) ? "excede" : "incompleta";
      return `<tr><td>${escapar(rotulo(a))}</td><td>${soma[i]}</td><td>${permitidas ? permitidas.join(" ou ") : "—"}</td><td class="estado-${estado}">${{ "sem regra": "não conferido", ok: "ok", excede: "excede (VAL-001)", incompleta: "incompleta (VAL-002)" }[estado]}</td></tr>`;
    }).join("");
    const cabecalho = lente === "comp" ? "<tr><th>Vértice</th><th>Σ pesos</th><th>Aceito</th><th>Regra</th></tr>" : "<tr><th>Átomo</th><th>Σ ordens</th><th>Valência</th><th>Situação</th></tr>";
    const diag = [...r.erros, ...r.avisos].map((d) => `<li><b>${escapar(d.codigo)}</b> linha ${d.linha}: ${escapar(d.mensagem)}</li>`).join("");
    return `<p class="etapa-resumo">Fórmula <b>${formulaHill(r.atomos)}</b> · ${r.erros.length ? `<span class="estado-excede">${r.erros.length} erro(s)</span>` : '<span class="estado-ok">sem erros, saída 0</span>'}</p>
      <div class="tabela"><table>${cabecalho}${linhas}</table></div>${diag ? `<ul class="etapa-diag">${diag}</ul>` : ""}`;
  }

  /* Painel reutilizável: abas das etapas, lente e explicação */
  function montarTraducao(alvo, obterCodigo) {
    alvo.innerHTML = `
      <div class="trad-topo">
        <div class="etapas" role="tablist">${ETAPAS.map((e, i) => `<button type="button" class="etapa" role="tab" data-i="${i}"><span>${i + 1}</span>${e.titulo}</button>`).join("")}</div>
        <div class="lentes" role="group" aria-label="Lente">
          <button type="button" data-lente="comp">Computação</button><button type="button" data-lente="quim">Química</button>
        </div>
      </div>
      <p class="trad-explica"></p>
      <div class="trad-conteudo"></div>`;
    const estado = { i: 0, lente: "comp", resultado: null };
    const desenhar = () => {
      estado.resultado = compilar(obterCodigo());
      const etapa = ETAPAS[estado.i];
      alvo.querySelectorAll(".etapa").forEach((b, i) => {
        b.setAttribute("aria-selected", String(i === estado.i));
        // Etapa onde a tradução parou e etapas que não chegaram a rodar
        const parada = { "léxico": 0, "sintático": 1 }[estado.resultado.falhaEm];
        b.classList.toggle("falhou", i === parada);
        b.classList.toggle("bloqueada", parada !== undefined && i > parada);
      });
      alvo.querySelectorAll("[data-lente]").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.lente === estado.lente)));
      alvo.querySelector(".trad-explica").innerHTML = `<b>${escapar(etapa.titulo)}</b> · fase ${escapar(etapa.fase)}. ${escapar(estado.lente === "comp" ? etapa.comp : etapa.quim)}`;
      alvo.querySelector(".trad-conteudo").innerHTML = conteudoEtapa(etapa, estado.resultado, estado.lente);
    };
    alvo.querySelectorAll(".etapa").forEach((b) => b.addEventListener("click", () => { estado.i = Number(b.dataset.i); desenhar(); }));
    alvo.querySelectorAll("[data-lente]").forEach((b) => b.addEventListener("click", () => { estado.lente = b.dataset.lente; desenhar(); }));
    estado.desenhar = desenhar;
    estado.irPara = (i) => { estado.i = i; desenhar(); };
    desenhar();
    return estado;
  }

  /* Demonstração passo a passo num diálogo, sem alterar nada da página */
  const dialogo = document.getElementById("demo");
  let demo = null, demoTimer = null, demoCodigo = "";
  function pararDemo() { clearInterval(demoTimer); demoTimer = null; dialogo.querySelector("[data-demo='tocar']").textContent = "▶ Reproduzir"; }
  function abrirDemonstracao(codigoFonte, titulo) {
    demoCodigo = codigoFonte;
    dialogo.querySelector(".demo-titulo").textContent = titulo || "Tradução";
    dialogo.querySelector(".demo-fonte").textContent = codigoFonte.trim();
    demo = montarTraducao(dialogo.querySelector(".demo-traducao"), () => demoCodigo);
    if (typeof dialogo.showModal === "function") dialogo.showModal(); else dialogo.setAttribute("open", "");
    pararDemo();
    tocarDemo();
  }
  function tocarDemo() {
    if (demoTimer) { pararDemo(); return; }
    dialogo.querySelector("[data-demo='tocar']").textContent = "❚❚ Pausar";
    demoTimer = setInterval(() => {
      if (demo.i >= ETAPAS.length - 1) { pararDemo(); return; }
      demo.irPara(demo.i + 1);
    }, 4200);
  }
  dialogo.querySelector("[data-demo='tocar']").addEventListener("click", tocarDemo);
  dialogo.querySelector("[data-demo='anterior']").addEventListener("click", () => { pararDemo(); demo.irPara(Math.max(0, demo.i - 1)); });
  dialogo.querySelector("[data-demo='proximo']").addEventListener("click", () => { pararDemo(); demo.irPara(Math.min(ETAPAS.length - 1, demo.i + 1)); });
  dialogo.querySelector("[data-demo='fechar']").addEventListener("click", () => { pararDemo(); dialogo.close ? dialogo.close() : dialogo.removeAttribute("open"); });
  dialogo.addEventListener("close", pararDemo);
  document.addEventListener("click", (e) => {
    const botao = e.target.closest("[data-demonstrar]");
    if (!botao) return;
    const arquivo = botao.dataset.demonstrar;
    const ex = DADOS.exemplos.find((x) => x.arquivo === arquivo);
    if (ex) abrirDemonstracao(ex.codigo, `${ex.titulo} — ${ex.arquivo}`);
  });

  tradPlay = montarTraducao(document.getElementById("p-trad"), () => codigo.value);
  document.getElementById("demonstrar-atual").addEventListener("click", () => {
    abrirDemonstracao(codigo.value, exemploAtual ? `${exemploAtual.titulo} — ${exemploAtual.arquivo}` : "Código do playground");
  });

