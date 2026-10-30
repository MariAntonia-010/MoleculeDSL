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
  const NUCLEOS = { He: "1s2", Ne: "[He] 2s2 2p6", Ar: "[Ne] 3s2 3p6", Kr: "[Ar] 3d10 4s2 4p6", Xe: "[Kr] 4d10 5s2 5p6", Rn: "[Xe] 4f14 5d10 6s2 6p6" };

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

  function camadas(simbolo) {
    // Elétrons por camada a partir da configuração eletrônica da fonte
    let config = (DADOS.elementos[simbolo] || {}).config || "";
    for (let i = 0; i < 6 && /\[(\w+)\]/.test(config); i++) config = config.replace(/\[(\w+)\]/, (_, g) => ` ${NUCLEOS[g] || ""} `);
    const porCamada = [];
    for (const [, n, , e] of config.matchAll(/(\d)([spdf])(\d+)/g)) porCamada[n - 1] = (porCamada[n - 1] || 0) + Number(e);
    return Array.from(porCamada, (v) => v || 0);
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
  function codigoDoElemento(simbolo) {
    return `species molecule "Átomo de ${simbolo}" {\n    atom ${simbolo} as a1\n}\n`;
  }
  function mostrarElemento(simbolo) {
    simboloAtual = simbolo;
    const e = DADOS.elementos[simbolo];
    document.querySelectorAll(".elemento").forEach((b) => b.classList.toggle("selecionado", b.dataset.simbolo === simbolo));
    const valencias = DADOS.valencias.valencias[simbolo];
    const comCarga = DADOS.valencias.valencias_com_carga[simbolo];
    const cam = camadas(simbolo);
    document.getElementById("ficha-elemento").innerHTML = `
      <div class="ficha-topo"><span class="simbolo-grande">${simbolo}</span><div><h3>${escapar(e.nome)}</h3><p>Z = ${e.numero} · ${CATEGORIA[e.bloco] || e.bloco}</p></div></div>
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
    document.getElementById("demo-elemento").addEventListener("click", () => abrirDemonstracao(codigoDoElemento(simbolo), `Átomo de ${e.nome}`));
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
      const escuro = raiz.dataset.theme !== "light";
      const cx = w / 2, cy = h / 2, n = bohr.camadas.length;
      const rMax = Math.min(w, h) / 2 - 12, rNucleo = Math.max(12, rMax * 0.14);
      const acento = getComputedStyle(raiz).getPropertyValue("--acento").trim();
      bohr.camadas.forEach((eletrons, k) => {
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
      ctx.fillStyle = corDe(bohr.simbolo);
      ctx.beginPath(); ctx.arc(cx, cy, rNucleo, 0, Math.PI * 2); ctx.fill();
      ctx.fillStyle = bohr.simbolo === "H" ? "#2a2830" : "#fff";
      ctx.font = `700 ${rNucleo * 0.85}px ui-monospace, Menlo, monospace`;
      ctx.textAlign = "center"; ctx.textBaseline = "middle";
      ctx.fillText(bohr.simbolo, cx, cy + 1);
    }
    requestAnimationFrame(desenharBohr);
  }

  /* Bancada: monta o código de uma molécula a partir dos elementos clicados */
  const bancada = [];
  function codigoDaBancada() {
    const contagem = {};
    bancada.forEach((s) => (contagem[s] = (contagem[s] || 0) + 1));
    const linhas = Object.entries(contagem).map(([s, n]) => (n > 1 ? `    ${n}x atom ${s} as ${s.toLowerCase()}` : `    atom ${s} as ${s.toLowerCase()}1`));
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

