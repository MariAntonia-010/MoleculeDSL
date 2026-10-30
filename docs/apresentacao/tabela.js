  /* ================= tabela periódica ================= */
  const CATEGORIA = {
    "Alkali metal": "metal alcalino", "Alkaline earth metal": "metal alcalinoterroso", "Transition metal": "metal de transição",
    "Post-transition metal": "metal pós-transição", Metalloid: "semimetal", Nonmetal: "não metal", Halogen: "halogênio",
    "Noble gas": "gás nobre", Lanthanide: "lantanídeo", Actinide: "actinídeo",
  };
  const CLASSE_CATEGORIA = {
    "Alkali metal": "c1", "Alkaline earth metal": "c2", "Transition metal": "c3", "Post-transition metal": "c4", Metalloid: "c5",
    Nonmetal: "c6", Halogen: "c7", "Noble gas": "c8", Lanthanide: "c9", Actinide: "c10",
  };

  function posicaoNaTabela(z) {
    // [linha, coluna]; lantanídeos e actinídeos ficam nas linhas 9 e 10
    if (z === 1) return [1, 1];
    if (z === 2) return [1, 18];
    const periodos = [[3, 10, 2], [11, 18, 3], [19, 36, 4], [37, 54, 5], [55, 86, 6], [87, 118, 7]];
    for (const [ini, fim, per] of periodos) {
      if (z < ini || z > fim) continue;
      const k = z - ini;
      if (per <= 3) return [per, k < 2 ? k + 1 : k + 11];
      if (per <= 5) return [per, k + 1];
      if (k < 2) return [per, k + 1];
      if (k < 17) return [per === 6 ? 9 : 10, k + 1];
      return [per, k - 14 + 1];
    }
    return [1, 1];
  }


  function montarTabela() {
    const grade = document.getElementById("tabela-periodica");
    const celulas = Object.entries(DADOS.elementos).sort((a, b) => a[1].numero - b[1].numero).map(([simbolo, e]) => {
      const [linha, coluna] = posicaoNaTabela(e.numero);
      const regra = DADOS.valencias.valencias[simbolo] ? " com-regra" : "";
      return `<button type="button" class="elemento ${CLASSE_CATEGORIA[e.bloco] || ""}${regra}" style="grid-row:${linha};grid-column:${coluna}" data-simbolo="${simbolo}" title="${escapar(e.nome)}">
        <small>${e.numero}</small><b>${simbolo}</b></button>`;
    });
    grade.innerHTML = celulas.join("") +
      `<span class="marcador-f" style="grid-row:6;grid-column:3">57–71</span><span class="marcador-f" style="grid-row:7;grid-column:3">89–103</span>`;
    document.getElementById("legenda-tabela").innerHTML = Object.entries(CATEGORIA).map(([k, v]) =>
      `<span><i class="${CLASSE_CATEGORIA[k]}"></i>${v}</span>`).join("") + `<span><i class="com-regra-amostra"></i>valência conferida pelo compilador</span>`;
    grade.addEventListener("click", (e) => {
      const b = e.target.closest("[data-simbolo]");
      if (b) mostrarElemento(b.dataset.simbolo);
    });
  }

  let simboloAtual = "C";
  // Um átomo sozinho não é molécula (IUPAC): o exemplo usa species atom
  function codigoDoElemento(simbolo) {
    return `species atom "${DADOS.elementos[simbolo].nome}" {\n    atom ${simbolo}\n}\n`;
  }
  function mostrarElemento(simbolo) {
    simboloAtual = simbolo;
    const e = DADOS.elementos[simbolo];
    document.querySelectorAll(".elemento").forEach((b) => b.classList.toggle("selecionado", b.dataset.simbolo === simbolo));
    const valencias = DADOS.valencias.valencias[simbolo];
    const comCarga = DADOS.valencias.valencias_com_carga[simbolo];
    const cam = camadas(simbolo);
    document.getElementById("ficha-elemento").innerHTML = `
      <div class="ficha-topo"><span class="simbolo-grande">${simbolo}</span><div><h3>${escapar(e.nome)}</h3><p>Z = ${e.numero} · ${CATEGORIA[e.bloco] || e.bloco} · nome na fonte (PubChem): ${escapar(e.nome_fonte)}</p></div></div>
      <div class="duas-lentes">
        <div><h4>Para a química</h4><dl>
          <dt>Configuração</dt><dd>${escapar(e.config || "—")}</dd>
          <dt>Camadas</dt><dd>${cam.join(", ") || "—"}</dd>
          <dt>Elétrons de valência</dt><dd>${e.valencia ?? "sem dado na fonte"}</dd>
          <dt>Eletronegatividade</dt><dd>${e.eletronegatividade ?? "sem dado"}</dd>
          <dt>Estados de oxidação</dt><dd>${(e.estados || []).join(", ") || "—"}</dd></dl></div>
        <div><h4>Para o compilador</h4><dl>
          <dt>Token</dt><dd><code>IDENT '${simbolo}'</code>, casa [A-Z][a-z]?</dd>
          <dt>Nó da AST</dt><dd><code>AtomoDecl(elemento='${simbolo}')</code></dd>
          <dt>Valência</dt><dd>${valencias ? `aceita soma de ordens ${valencias.join(" ou ")}${comCarga ? `; com carga: ${Object.entries(comCarga).map(([c, v]) => `${c} → ${v.join("/")}`).join(", ")}` : ""}` : "sem regra com fonte: a valência não é conferida (nunca é inventada)"}</dd>
          <dt>Classificação</dt><dd>${e.eletronegatividade != null ? "entra no cálculo de Δχ das ligações" : "sem eletronegatividade: ligação “não classificada”"}</dd></dl></div>
      </div>
      <pre>${escapar(codigoDoElemento(simbolo).trim())}</pre>
      <div class="acoes-ficha">
        <button type="button" class="botao pequeno" id="demo-elemento">Demonstrar tradução</button>
        <button type="button" class="botao pequeno" id="usar-elemento">Abrir no playground</button>
        <button type="button" class="botao pequeno primario" id="bancada-mais">+ adicionar à bancada</button>
      </div>`;
    document.getElementById("demo-elemento").addEventListener("click", () => abrirDemonstracao(codigoDoElemento(simbolo), `Átomo isolado de ${e.nome.toLowerCase()}`));
    document.getElementById("usar-elemento").addEventListener("click", () => {
      exemploAtual = null;
      codigo.value = codigoDoElemento(simbolo);
      location.hash = "#/playground";
      executar();
    });
    document.getElementById("bancada-mais").addEventListener("click", () => { bancada.push(simbolo); desenharBancada(); });
    bohr.camadas = cam;
    bohr.simbolo = simbolo;
  }

  /* Modelo de Bohr: núcleo e camadas com elétrons girando */
  const bohr = { camadas: [], simbolo: "", canvas: document.getElementById("bohr") };
  function desenharBohr(tempo) {
    const c = bohr.canvas;
    if (c.offsetParent !== null) {
      const ctx = c.getContext("2d"), dpr = window.devicePixelRatio || 1;
      const w = c.clientWidth, h = c.clientHeight;
      if (c.width !== Math.round(w * dpr)) { c.width = Math.round(w * dpr); c.height = Math.round(h * dpr); }
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.clearRect(0, 0, w, h);
      pintarBohr(ctx, w, h, bohr.simbolo, bohr.camadas, tempo);
    }
    requestAnimationFrame(desenharBohr);
  }

  /* Bancada: monta o código de uma molécula a partir dos elementos clicados */
  const bancada = [];
  function codigoDaBancada() {
    const contagem = {};
    bancada.forEach((s) => (contagem[s] = (contagem[s] || 0) + 1));
    const linhas = Object.entries(contagem).map(([s, n]) => (n > 1 ? `    ${n}x atom ${s} as ${s.toLowerCase()}` : `    atom ${s} as ${s.toLowerCase()}1`));
    if (bancada.length === 1) return codigoDoElemento(bancada[0]);
    return `species molecule "Minha molécula" {\n${linhas.join("\n")}\n\n    // ligue os átomos com bond, por exemplo: bond ${bancada[0] ? bancada[0].toLowerCase() + "1" : "a1"}-...\n}\n`;
  }
  function desenharBancada() {
    const caixa = document.getElementById("bancada");
    if (!bancada.length) {
      caixa.innerHTML = `<p class="nota" style="margin:0">Clique num elemento e em “+ adicionar à bancada” para montar uma molécula. O código MoleculeDSL aparece aqui.</p>`;
      return;
    }
    const valencias = bancada.map((s) => (DADOS.valencias.valencias[s] || [null])[0]);
    const conhecidas = valencias.every((v) => v != null);
    const soma = valencias.reduce((t, v) => t + (v || 0), 0);
    const nota = !conhecidas
      ? "Há elemento sem regra de valência: o compilador não confere a valência dele."
      : soma % 2
        ? `Soma das valências = ${soma}, ímpar: não fecha sem carga ou radical.`
        : `Soma das valências = ${soma}: cabem ${soma / 2} ordens de ligação no total. Com --resolver o compilador tenta ligar os átomos sozinho.`;
    caixa.innerHTML = `<div class="fichas">${bancada.map((s, i) => `<button type="button" class="ficha" data-tirar-bancada="${i}" title="Remover"><code>${s}</code><small>remover</small></button>`).join("")}</div>
      <p class="nota">${escapar(nota)}</p>
      <pre>${escapar(codigoDaBancada().trim())}</pre>
      <div class="acoes-ficha"><button type="button" class="botao pequeno primario" id="bancada-abrir">Abrir no playground</button><button type="button" class="botao pequeno" id="bancada-limpar">Limpar</button></div>`;
    caixa.querySelectorAll("[data-tirar-bancada]").forEach((b) => b.addEventListener("click", () => { bancada.splice(Number(b.dataset.tirarBancada), 1); desenharBancada(); }));
    document.getElementById("bancada-limpar").addEventListener("click", () => { bancada.length = 0; desenharBancada(); });
    document.getElementById("bancada-abrir").addEventListener("click", () => {
      exemploAtual = null;
      seletor.value = "";
      codigo.value = codigoDaBancada();
      location.hash = "#/playground";
      executar();
    });
  }

  let tabelaPronta = false;
  function iniciarTabela() {
    if (tabelaPronta) return;
    tabelaPronta = true;
    montarTabela();
    mostrarElemento(simboloAtual);
    desenharBancada();
    requestAnimationFrame(desenharBohr);
  }

