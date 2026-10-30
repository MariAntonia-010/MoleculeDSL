  /* ================= laboratório: misturas e reações ================= */
  // Misturas e reações combinam programas MoleculeDSL: exemplos do projeto
  // ou código escrito na hora. A linguagem continua descrevendo uma espécie
  // por programa; cada espécie passa pelo compilador do navegador antes de
  // entrar na simulação.
  const ESPECIES_LAB = ["hidrogenio", "oxigenio", "agua", "metano", "dioxido_carbono", "monoxido_de_carbono", "nitrogenio",
    "amonia", "cloro", "cloreto_de_hidrogenio", "peroxido_de_hidrogenio", "etanol", "metanol", "acetona", "acido_acetico", "benzeno", "ureia"];
  const especieDoArquivo = (arquivo) => {
    const ex = DADOS.exemplos.find((e) => e.arquivo === `exemplos/${arquivo}.mol`);
    return { titulo: ex.titulo, codigo: ex.codigo, arquivo: ex.arquivo };
  };
  const cacheEspecie = new Map();
  function compilarEspecie(esp) {
    if (!cacheEspecie.has(esp.codigo)) {
      const r = compilar(esp.codigo);
      cacheEspecie.set(esp.codigo, { esp, r, pos: r.erros.length ? [] : layout(r.atomos, r.ligacoes) });
    }
    return cacheEspecie.get(esp.codigo);
  }
  function rotacionar(pos, a, b) {
    const ca = Math.cos(a), sa = Math.sin(a), cb = Math.cos(b), sb = Math.sin(b);
    return pos.map(([x, y, z]) => { const x1 = x * ca + z * sa, z1 = -x * sa + z * ca; return [x1, y * cb - z1 * sb, y * sb + z1 * cb]; });
  }
  function contarElementos(atomos, fator = 1, alvo = {}) {
    atomos.forEach((a) => (alvo[a.el] = (alvo[a.el] || 0) + fator));
    return alvo;
  }
  function tiposDeLigacao(r, fator, alvo) {
    const simbolo = { 1: "-", 2: "=", 3: "#" };
    r.ligacoes.forEach((l) => {
      const par = [r.atomos[l.a].el, r.atomos[l.b].el].sort().join(l.op === "->" ? "→" : simbolo[l.ordem] || "~") + ` (${classificar(l, r.atomos).classe})`;
      alvo[par] = (alvo[par] || 0) + fator;
    });
    return alvo;
  }
  const textoContagem = (c) => Object.entries(c).filter(([, n]) => n).map(([k, n]) => `${n}× ${k}`).join(", ") || "nenhuma";
  const opcoesEspecies = (selecionado) => ESPECIES_LAB.map((arq) => {
    const esp = especieDoArquivo(arq);
    return `<option value="${arq}"${arq === selecionado ? " selected" : ""}>${escapar(esp.titulo)} (${formulaHill(compilarEspecie(esp).r.atomos)})</option>`;
  }).join("") + `<option value="__codigo"${selecionado === "__codigo" ? " selected" : ""}>Código próprio…</option>`;

  // Erro de uma espécie: mesma faixa vermelha do playground
  function alertaEspecie(esp, r) {
    const d = r.erros[0];
    const [titulo, significa, corrigir] = EXPLICA[d.codigo] || ["Erro", "", ""];
    return `<div class="alerta erro" style="cursor:default"><div class="alerta-titulo"><span class="selo">Erro ${escapar(d.fase)} · ${escapar(d.codigo)} · linha ${d.linha}</span><b>${escapar(titulo)}</b></div>
      <p class="alerta-msg">${escapar(esp.titulo)}: ${escapar(d.mensagem)}</p>
      <p class="alerta-ajuda">${escapar(significa)} <strong>Como corrigir:</strong> ${escapar(corrigir)}</p>
      <p class="alerta-saida">A simulação não roda com uma espécie inválida: a semântica vem antes da química.</p></div>`;
  }

  /* ---------- reações ---------- */
  const REACOES = [
    { nome: "Síntese da água", reagentes: [[2, "hidrogenio"], [1, "oxigenio"]], produtos: [[2, "agua"]] },
    { nome: "Combustão do metano", reagentes: [[1, "metano"], [2, "oxigenio"]], produtos: [[1, "dioxido_carbono"], [2, "agua"]] },
    { nome: "Síntese da amônia (Haber-Bosch)", reagentes: [[1, "nitrogenio"], [3, "hidrogenio"]], produtos: [[2, "amonia"]] },
    { nome: "Combustão do etanol", reagentes: [[1, "etanol"], [3, "oxigenio"]], produtos: [[2, "dioxido_carbono"], [3, "agua"]] },
    { nome: "Síntese do cloreto de hidrogênio", reagentes: [[1, "hidrogenio"], [1, "cloro"]], produtos: [[2, "cloreto_de_hidrogenio"]] },
    { nome: "Decomposição da água oxigenada", reagentes: [[2, "peroxido_de_hidrogenio"]], produtos: [[2, "agua"], [1, "oxigenio"]] },
    { nome: "Combustão do monóxido de carbono", reagentes: [[2, "monoxido_de_carbono"], [1, "oxigenio"]], produtos: [[2, "dioxido_carbono"]] },
  ];
  const cenaReacao = new Cena(document.getElementById("cena-reacao"));
  // De frente e sem girar sozinha: reagentes e produtos ficam lado a lado
  cenaReacao.girar = false;
  cenaReacao.rx = -0.25;
  cenaReacao.ry = 0.15;
  cenaReacao.zoom = 1.5;
  let reacaoAtual = null, progresso = 0, tocando = true, ultimoTempo = null;
  const FASES = [[0, "Reagentes"], [0.22, "Ligações se rompem"], [0.42, "Átomos se rearranjam"], [0.78, "Novas ligações se formam"], [0.95, "Produtos"]];

  const equacao = (lado) => lado.map(([n, esp]) => `${n > 1 ? n + " " : ""}${formulaHill(compilarEspecie(esp).r.atomos)}`).join(" + ");
  const contarLado = (lado) => lado.reduce((c, [n, esp]) => contarElementos(compilarEspecie(esp).r.atomos, n, c), {});

  function arranjar(lado) {
    const atomos = [], ligacoes = [], pos = [];
    const instancias = [];
    lado.forEach(([n, esp]) => { for (let k = 0; k < n; k++) instancias.push(esp); });
    const largura = 3.6;
    instancias.forEach((esp, k) => {
      const { r, pos: p } = compilarEspecie(esp);
      const giro = rotacionar(p, 0.4 * k, 0.3);
      const cx = (k - (instancias.length - 1) / 2) * largura;
      const inicio = atomos.length;
      r.atomos.forEach((a, i) => { atomos.push(a); pos.push([giro[i][0] + cx, giro[i][1], giro[i][2]]); });
      r.ligacoes.forEach((l) => ligacoes.push({ ...l, a: l.a + inicio, b: l.b + inicio }));
    });
    return { atomos, ligacoes, pos };
  }

  function simularReacao(reacao) {
    const info = document.getElementById("info-reacao");
    // 1. semântica de cada espécie
    const invalida = [...reacao.reagentes, ...reacao.produtos].map(([, esp]) => esp).find((esp) => compilarEspecie(esp).r.erros.length);
    if (invalida) {
      reacaoAtual = null;
      cenaReacao.carregar([], []);
      document.getElementById("fase-reacao").textContent = "Espécie inválida";
      info.innerHTML = alertaEspecie(invalida, compilarEspecie(invalida).r);
      return;
    }
    // 2. conservação dos átomos
    const cr = contarLado(reacao.reagentes), cp = contarLado(reacao.produtos);
    const elementos = [...new Set([...Object.keys(cr), ...Object.keys(cp)])].sort();
    const balanceada = elementos.every((e) => cr[e] === cp[e]);
    const R = arranjar(reacao.reagentes), P = arranjar(reacao.produtos);
    // Cada átomo dos produtos herda o átomo dos reagentes mais próximo do mesmo elemento
    const mapa = new Array(P.atomos.length).fill(-1), usados = new Set();
    if (balanceada) {
      P.atomos.forEach((a, j) => {
        let melhor = -1, dist = Infinity;
        R.atomos.forEach((b, i) => {
          if (b.el !== a.el || usados.has(i)) return;
          const d = Math.hypot(R.pos[i][0] - P.pos[j][0], R.pos[i][1] - P.pos[j][1]);
          if (d < dist) { dist = d; melhor = i; }
        });
        mapa[j] = melhor; usados.add(melhor);
      });
    }
    const destino = R.pos.map((p) => [...p]);
    mapa.forEach((i, j) => { if (i >= 0) destino[i] = [...P.pos[j]]; });
    const ligacoes = [...R.ligacoes.map((l) => ({ ...l, lado: "r" })), ...(balanceada ? P.ligacoes.map((l) => ({ ...l, a: mapa[l.a], b: mapa[l.b], lado: "p", alfa: 0 })) : [])];
    reacaoAtual = { R, destino, ligacoes, balanceada };
    progresso = 0;
    tocando = balanceada;
    atualizarBotaoReacao();
    const pos = R.pos.map((p) => [...p]);
    cenaReacao.carregar(R.atomos, ligacoes, pos);
    cenaReacao.ajustarEscala(Math.max(...[...R.pos, ...P.pos].map((p) => Math.hypot(...p))) + 0.5);
    cenaReacao.aoQuadro = (tempo) => {
      if (ultimoTempo == null) ultimoTempo = tempo;
      const dt = Math.min(0.3, (tempo - ultimoTempo) / 1000);
      ultimoTempo = tempo;
      if (tocando && reacaoAtual && reacaoAtual.balanceada) {
        progresso = Math.min(1, progresso + dt / 9);
        document.getElementById("progresso-reacao").value = progresso;
      }
      if (reacaoAtual) aplicarProgresso(pos);
    };
    const quebradas = {}, formadas = {};
    reacao.reagentes.forEach(([n, esp]) => tiposDeLigacao(compilarEspecie(esp).r, n, quebradas));
    reacao.produtos.forEach(([n, esp]) => tiposDeLigacao(compilarEspecie(esp).r, n, formadas));
    const especiesUnicas = [...reacao.reagentes, ...reacao.produtos].map(([, esp]) => esp).filter((esp, i, todas) => todas.findIndex((x) => x.codigo === esp.codigo) === i);
    info.innerHTML = `
      <p class="equacao">${equacao(reacao.reagentes)} <span>→</span> ${equacao(reacao.produtos)}</p>
      ${balanceada
        ? `<p class="estado-ok">Balanceada: ${elementos.map((e) => `${e} ${cr[e]} → ${cp[e]}`).join(" · ")}</p>`
        : `<div class="alerta aviso" style="cursor:default"><div class="alerta-titulo"><span class="selo">Conservação da massa</span><b>Reação não balanceada</b></div>
           <p class="alerta-msg">${elementos.filter((e) => cr[e] !== cp[e]).map((e) => `${e}: ${cr[e] || 0} nos reagentes, ${cp[e] || 0} nos produtos`).join(" · ")}</p>
           <p class="alerta-ajuda">Os átomos não se criam nem se destroem. <strong>Como corrigir:</strong> ajuste os coeficientes ou use “Balancear”.</p></div>`}
      <div class="tabela"><table><tr><th>Ligações</th><th>Tipos</th></tr>
        <tr><td>rompidas</td><td>${textoContagem(quebradas)}</td></tr>
        <tr><td>formadas</td><td>${textoContagem(formadas)}</td></tr></table></div>
      <div class="botoes-traducao"><span>Tradução de cada espécie:</span>${especiesUnicas.map((esp, i) => `<button type="button" class="botao pequeno" data-demo-codigo="${i}">${escapar(esp.titulo)}</button>`).join("")}</div>
      <p class="nota">Animação ilustrativa: mostra a conservação dos átomos e quais ligações se rompem e se formam. Não representa o mecanismo, a velocidade nem a energia.</p>`;
    info.querySelectorAll("[data-demo-codigo]").forEach((b) => b.addEventListener("click", () => {
      const esp = especiesUnicas[Number(b.dataset.demoCodigo)];
      abrirDemonstracao(esp.codigo, esp.titulo);
    }));
  }

  const suave = (x) => x * x * (3 - 2 * x);
  function aplicarProgresso(pos) {
    const { R, destino, ligacoes } = reacaoAtual;
    const t = progresso;
    const mover = suave(Math.min(1, Math.max(0, (t - 0.42) / 0.36)));
    const vibra = t < 0.42 ? Math.sin(t * 90) * 0.04 * Math.min(1, t / 0.22) : 0;
    R.pos.forEach((p, i) => {
      for (let c = 0; c < 3; c++) pos[i][c] = p[c] + (destino[i][c] - p[c]) * mover + (c === 1 ? vibra * ((i % 2) * 2 - 1) : 0);
    });
    const someR = reacaoAtual.balanceada ? 1 - Math.min(1, Math.max(0, (t - 0.22) / 0.2)) : 1;
    const surgeP = Math.min(1, Math.max(0, (t - 0.78) / 0.17));
    ligacoes.forEach((l) => { l.alfa = l.lado === "r" ? someR : surgeP; });
    document.getElementById("fase-reacao").textContent = reacaoAtual.balanceada ? [...FASES].reverse().find(([inicio]) => t >= inicio)[1] : "Aguardando balanceamento";
  }

  /* montador de reações */
  const montador = { reagentes: [], produtos: [] };
  function itemMontador(lado, item, i) {
    return `<div class="item-montador">
      <input type="number" min="1" max="9" value="${item.n}" aria-label="Coeficiente" data-lado="${lado}" data-i="${i}" data-campo="n">
      <select data-lado="${lado}" data-i="${i}" data-campo="arq" aria-label="Espécie">${opcoesEspecies(item.arq)}</select>
      <button type="button" class="botao pequeno" data-lado="${lado}" data-i="${i}" data-remover aria-label="Remover">×</button>
      ${item.arq === "__codigo" ? `<textarea data-lado="${lado}" data-i="${i}" data-campo="codigo" spellcheck="false" aria-label="Código MoleculeDSL da espécie">${escapar(item.codigo)}</textarea>` : ""}
    </div>`;
  }
  function desenharMontador() {
    document.getElementById("montador-reagentes").innerHTML = montador.reagentes.map((it, i) => itemMontador("reagentes", it, i)).join("");
    document.getElementById("montador-produtos").innerHTML = montador.produtos.map((it, i) => itemMontador("produtos", it, i)).join("");
  }
  const especieDoItem = (it) => (it.arq === "__codigo" ? { titulo: (it.codigo.match(/"([^"]*)"/) || [, "Código próprio"])[1], codigo: it.codigo } : especieDoArquivo(it.arq));
  const reacaoDoMontador = () => ({
    nome: "Reação montada",
    reagentes: montador.reagentes.map((it) => [it.n, especieDoItem(it)]),
    produtos: montador.produtos.map((it) => [it.n, especieDoItem(it)]),
  });
  function carregarNoMontador(reacao) {
    montador.reagentes = reacao.reagentes.map(([n, arq]) => ({ n, arq, codigo: especieDoArquivo(arq).codigo }));
    montador.produtos = reacao.produtos.map(([n, arq]) => ({ n, arq, codigo: especieDoArquivo(arq).codigo }));
    desenharMontador();
  }
  const caixaMontador = document.getElementById("montador");
  caixaMontador.addEventListener("input", (e) => {
    const { lado, i, campo } = e.target.dataset;
    if (!lado) return;
    const item = montador[lado][Number(i)];
    if (campo === "n") item.n = Math.max(1, Math.min(9, Number(e.target.value) || 1));
    if (campo === "codigo") item.codigo = e.target.value;
    if (campo === "arq") {
      if (e.target.value === "__codigo" && item.arq !== "__codigo") item.codigo = especieDoArquivo(item.arq).codigo;
      item.arq = e.target.value;
      desenharMontador();
    }
  });
  caixaMontador.addEventListener("click", (e) => {
    const remover = e.target.closest("[data-remover]");
    if (remover) { montador[remover.dataset.lado].splice(Number(remover.dataset.i), 1); desenharMontador(); }
  });
  document.getElementById("mais-reagente").addEventListener("click", () => { montador.reagentes.push({ n: 1, arq: "hidrogenio", codigo: "" }); desenharMontador(); });
  document.getElementById("mais-produto").addEventListener("click", () => { montador.produtos.push({ n: 1, arq: "agua", codigo: "" }); desenharMontador(); });
  document.getElementById("simular-reacao").addEventListener("click", () => {
    if (!montador.reagentes.length || !montador.produtos.length) return;
    simularReacao(reacaoDoMontador());
  });
  document.getElementById("balancear-reacao").addEventListener("click", () => {
    // Procura os menores coeficientes inteiros (1 a 8) que conservam os átomos
    const reacao = reacaoDoMontador();
    const todas = [...reacao.reagentes, ...reacao.produtos];
    if (!todas.length || todas.some(([, esp]) => compilarEspecie(esp).r.erros.length)) { simularReacao(reacao); return; }
    const contagens = todas.map(([, esp]) => contarElementos(compilarEspecie(esp).r.atomos));
    const elementos = [...new Set(contagens.flatMap((c) => Object.keys(c)))];
    const nr = reacao.reagentes.length;
    const coef = todas.map(() => 1);
    let achou = null;
    const testar = () => elementos.every((e) => coef.reduce((s, k, i) => s + (i < nr ? 1 : -1) * k * (contagens[i][e] || 0), 0) === 0);
    const busca = (i) => {
      if (achou) return;
      if (i === coef.length) { if (testar()) achou = [...coef]; return; }
      for (let k = 1; k <= 8 && !achou; k++) { coef[i] = k; busca(i + 1); }
    };
    if (coef.length <= 6) busca(0);
    const info = document.getElementById("info-reacao");
    if (!achou) {
      info.innerHTML = `<div class="alerta aviso" style="cursor:default"><div class="alerta-titulo"><span class="selo">Balanceamento</span><b>Sem solução com coeficientes até 8</b></div><p class="alerta-ajuda">Confira se as espécies podem mesmo reagir entre si: os mesmos elementos precisam aparecer dos dois lados.</p></div>`;
      return;
    }
    achou.forEach((k, i) => { (i < nr ? montador.reagentes[i] : montador.produtos[i - nr]).n = k; });
    desenharMontador();
    simularReacao(reacaoDoMontador());
  });

  const seletorReacao = document.getElementById("reacao");
  seletorReacao.innerHTML = REACOES.map((r, i) => `<option value="${i}">${escapar(r.nome)}</option>`).join("");
  seletorReacao.addEventListener("change", () => { carregarNoMontador(REACOES[Number(seletorReacao.value)]); simularReacao(reacaoDoMontador()); });
  const botaoTocar = document.getElementById("tocar-reacao");
  function atualizarBotaoReacao() { botaoTocar.textContent = tocando ? "❚❚ Pausar" : "▶ Reproduzir"; }
  botaoTocar.addEventListener("click", () => { if (progresso >= 1) progresso = 0; tocando = !tocando; atualizarBotaoReacao(); });
  document.getElementById("reiniciar-reacao").addEventListener("click", () => { progresso = 0; tocando = true; atualizarBotaoReacao(); });
  document.getElementById("progresso-reacao").addEventListener("input", (e) => { progresso = Number(e.target.value); tocando = false; atualizarBotaoReacao(); });

  /* ---------- misturas ---------- */
  const componentesMistura = [
    { esp: especieDoArquivo("agua"), n: 6 },
    { esp: especieDoArquivo("etanol"), n: 2 },
  ];
  const cenaMistura = new Cena(document.getElementById("cena-mistura"));
  cenaMistura.girar = false;
  cenaMistura.zoom = 1.3;
  let agitacao = 1;

  function desenharComponentes() {
    document.getElementById("lista-mistura").innerHTML = componentesMistura.map((c, i) => {
      const { r } = compilarEspecie(c.esp);
      return `<div class="item-mistura${r.erros.length ? " invalido" : ""}"><div><b>${escapar(c.esp.titulo)}</b><small>${r.erros.length ? "erro: " + escapar(r.erros[0].codigo) : formulaHill(r.atomos)}</small></div>
        <div class="contador-mistura"><button type="button" class="botao pequeno" data-menos="${i}" aria-label="Menos">−</button><span>${c.n}</span>
        <button type="button" class="botao pequeno" data-mais="${i}" aria-label="Mais">+</button>
        <button type="button" class="botao pequeno" data-tradu="${i}">Tradução</button>
        <button type="button" class="botao pequeno" data-tirar="${i}" aria-label="Remover">×</button></div></div>`;
    }).join("");
  }
  document.getElementById("lista-mistura").addEventListener("click", (e) => {
    const b = e.target.closest("button");
    if (!b) return;
    const { mais, menos, tradu, tirar } = b.dataset;
    if (tradu !== undefined) { const c = componentesMistura[Number(tradu)]; abrirDemonstracao(c.esp.codigo, c.esp.titulo); return; }
    if (tirar !== undefined) componentesMistura.splice(Number(tirar), 1);
    if (mais !== undefined) componentesMistura[Number(mais)].n = Math.min(12, componentesMistura[Number(mais)].n + 1);
    if (menos !== undefined) componentesMistura[Number(menos)].n = Math.max(1, componentesMistura[Number(menos)].n - 1);
    desenharComponentes();
    montarMistura();
  });
  document.getElementById("adicionar-mistura").addEventListener("click", () => {
    const arq = document.getElementById("nova-especie").value;
    const esp = arq === "__codigo" ? { titulo: (document.getElementById("codigo-mistura").value.match(/"([^"]*)"/) || [, "Código próprio"])[1], codigo: document.getElementById("codigo-mistura").value } : especieDoArquivo(arq);
    componentesMistura.push({ esp, n: 2 });
    desenharComponentes();
    montarMistura();
  });
  document.getElementById("nova-especie").addEventListener("change", (e) => {
    const area = document.getElementById("codigo-mistura");
    area.hidden = e.target.value !== "__codigo";
    if (!area.value) area.value = 'species molecule "Minha molécula" {\n    atom O\n    2x atom H as h\n    bond O-h1\n    bond O-h2\n}\n';
  });
  document.getElementById("agitacao").addEventListener("input", (e) => { agitacao = Number(e.target.value); });

  function montarMistura() {
    const info = document.getElementById("info-mistura");
    const invalido = componentesMistura.find((c) => compilarEspecie(c.esp).r.erros.length);
    if (invalido) {
      cenaMistura.carregar([], []);
      info.innerHTML = alertaEspecie(invalido.esp, compilarEspecie(invalido.esp).r);
      return;
    }
    const instancias = componentesMistura.flatMap((c) => Array(c.n).fill(c.esp));
    const rnd = aleatorio(instancias.length * 31 + 7);
    const lado = Math.max(1, Math.ceil(Math.cbrt(instancias.length)));
    const passo = 4.2;
    const atomos = [], ligacoes = [], base = [], moleculas = [];
    instancias.forEach((esp, k) => {
      const { r, pos } = compilarEspecie(esp);
      const centro = [(k % lado) - (lado - 1) / 2, (Math.floor(k / lado) % lado) - (lado - 1) / 2, Math.floor(k / (lado * lado)) - (lado - 1) / 2].map((v) => v * passo + (rnd() - 0.5) * 1.2);
      const giro = rotacionar(pos, rnd() * 6.28, rnd() * 6.28);
      const inicio = atomos.length;
      r.atomos.forEach((a, i) => { atomos.push(a); base.push(giro[i]); });
      r.ligacoes.forEach((l) => ligacoes.push({ ...l, a: l.a + inicio, b: l.b + inicio }));
      moleculas.push({ inicio, fim: atomos.length, centro, vel: [rnd() - 0.5, rnd() - 0.5, rnd() - 0.5].map((v) => v * 0.02), fase: rnd() * 6.28, giro: (rnd() - 0.5) * 0.02 });
    });
    const limite = (lado * passo) / 2 + 1.5;
    const pos = base.map((p) => [...p]);
    cenaMistura.carregar(atomos, ligacoes, pos);
    cenaMistura.ajustarEscala(limite * 1.35);
    cenaMistura.aoQuadro = () => {
      for (const m of moleculas) {
        for (let c = 0; c < 3; c++) {
          m.centro[c] += m.vel[c] * agitacao;
          if (Math.abs(m.centro[c]) > limite) m.vel[c] *= -1;
        }
        m.fase += m.giro * agitacao;
        const ca = Math.cos(m.fase), sa = Math.sin(m.fase);
        for (let i = m.inicio; i < m.fim; i++) {
          const [x, y, z] = base[i];
          pos[i][0] = m.centro[0] + x * ca + z * sa;
          pos[i][1] = m.centro[1] + y;
          pos[i][2] = m.centro[2] - x * sa + z * ca;
        }
      }
    };
    const total = instancias.length;
    const elementos = {};
    componentesMistura.forEach((c) => contarElementos(compilarEspecie(c.esp).r.atomos, c.n, elementos));
    info.innerHTML = total
      ? `<div class="tabela"><table><tr><th>Fórmula</th><th>Espécie</th><th>Moléculas</th><th>Fração</th></tr>${componentesMistura.map((c) =>
          `<tr><td>${formulaHill(compilarEspecie(c.esp).r.atomos)}</td><td>${escapar(c.esp.titulo)}</td><td>${c.n}</td><td>${((c.n / total) * 100).toFixed(0)}%</td></tr>`).join("")}</table></div>
         <p class="nota">Átomos na cena: ${textoContagem(elementos)}. Numa mistura as moléculas só se movem: nenhuma ligação se rompe ou se forma.</p>`
      : `<p class="nota">Adicione componentesMistura para montar a mistura.</p>`;
  }

  let laboratorioPronto = false;
  function iniciarLaboratorio() {
    if (laboratorioPronto) return;
    laboratorioPronto = true;
    document.getElementById("nova-especie").innerHTML = opcoesEspecies("metanol");
    desenharComponentes();
    montarMistura();
    carregarNoMontador(REACOES[0]);
    simularReacao(reacaoDoMontador());
  }

