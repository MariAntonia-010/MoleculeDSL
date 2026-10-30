  /* ================= laboratório: misturas e reações ================= */
  // Misturas e reações combinam programas MoleculeDSL já existentes; a
  // linguagem continua descrevendo uma espécie por arquivo.
  const especie = (arquivo) => DADOS.exemplos.find((e) => e.arquivo === `exemplos/${arquivo}.mol`);
  const cacheEspecie = new Map();
  function especieCompilada(arquivo) {
    if (!cacheEspecie.has(arquivo)) {
      const ex = especie(arquivo);
      const r = compilar(ex.codigo);
      cacheEspecie.set(arquivo, { ex, r, pos: layout(r.atomos, r.ligacoes) });
    }
    return cacheEspecie.get(arquivo);
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
      const par = [r.atomos[l.a].el, r.atomos[l.b].el].sort().join(l.op === "->" ? "→" : simbolo[l.ordem] || "~");
      alvo[par] = (alvo[par] || 0) + fator;
    });
    return alvo;
  }
  const textoContagem = (c) => Object.entries(c).filter(([, n]) => n).map(([k, n]) => `${n}× ${k}`).join(", ") || "nenhuma";

  /* ---------- misturas ---------- */
  const OPCOES_MISTURA = ["agua", "etanol", "metanol", "acetona", "metano", "dioxido_carbono", "oxigenio", "nitrogenio", "amonia", "acido_acetico"];
  const quantidades = { agua: 5, etanol: 2 };
  const cenaMistura = new Cena(document.getElementById("cena-mistura"));
  cenaMistura.girar = false;
  cenaMistura.zoom = 1.3;
  let agitacao = 1;

  function montarListaMistura() {
    const lista = document.getElementById("lista-mistura");
    lista.innerHTML = OPCOES_MISTURA.map((arq) => {
      const { ex, r } = especieCompilada(arq);
      return `<div class="item-mistura"><div><b>${escapar(ex.titulo)}</b><small>${formulaHill(r.atomos)}</small></div>
        <div class="contador-mistura"><button type="button" class="botao pequeno" data-menos="${arq}" aria-label="Menos ${escapar(ex.titulo)}">−</button>
        <span>${quantidades[arq] || 0}</span><button type="button" class="botao pequeno" data-mais="${arq}" aria-label="Mais ${escapar(ex.titulo)}">+</button>
        <button type="button" class="botao pequeno" data-demonstrar="${ex.arquivo}">Tradução</button></div></div>`;
    }).join("");
  }
  document.getElementById("lista-mistura").addEventListener("click", (e) => {
    const mais = e.target.closest("[data-mais]"), menos = e.target.closest("[data-menos]");
    if (!mais && !menos) return;
    const arq = (mais || menos).dataset[mais ? "mais" : "menos"];
    quantidades[arq] = Math.max(0, Math.min(10, (quantidades[arq] || 0) + (mais ? 1 : -1)));
    montarListaMistura();
    montarMistura();
  });
  document.getElementById("agitacao").addEventListener("input", (e) => { agitacao = Number(e.target.value); });

  function montarMistura() {
    const instancias = [];
    Object.entries(quantidades).forEach(([arq, n]) => { for (let k = 0; k < n; k++) instancias.push(arq); });
    const rnd = aleatorio(instancias.length * 31 + 7);
    const lado = Math.max(1, Math.ceil(Math.cbrt(instancias.length)));
    const passo = 4.2;
    const atomos = [], ligacoes = [], base = [], moleculas = [];
    instancias.forEach((arq, k) => {
      const { r, pos } = especieCompilada(arq);
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
    // composição
    const total = instancias.length;
    const linhas = Object.entries(quantidades).filter(([, n]) => n).map(([arq, n]) => {
      const { ex, r } = especieCompilada(arq);
      return `<tr><td>${formulaHill(r.atomos)}</td><td>${escapar(ex.titulo)}</td><td>${n}</td><td>${((n / total) * 100).toFixed(0)}%</td></tr>`;
    }).join("");
    const elementos = {};
    Object.entries(quantidades).forEach(([arq, n]) => contarElementos(especieCompilada(arq).r.atomos, n, elementos));
    document.getElementById("info-mistura").innerHTML = total
      ? `<div class="tabela"><table><tr><th>Fórmula</th><th>Espécie</th><th>Moléculas</th><th>Fração</th></tr>${linhas}</table></div>
         <p class="nota">Átomos na cena: ${textoContagem(elementos)}. Numa mistura as moléculas só se movem: nenhuma ligação quebra ou se forma, e cada espécie é um programa MoleculeDSL separado.</p>`
      : `<p class="nota">Adicione moléculas para montar a mistura.</p>`;
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

  function equacao(lado) {
    return lado.map(([n, arq]) => `${n > 1 ? n + " " : ""}${formulaHill(especieCompilada(arq).r.atomos)}`).join(" + ");
  }

  function arranjar(lado, deslocamento) {
    // Uma instância por coeficiente, lado a lado
    const atomos = [], ligacoes = [], pos = [], donos = [];
    const instancias = [];
    lado.forEach(([n, arq]) => { for (let k = 0; k < n; k++) instancias.push(arq); });
    const largura = 3.6;
    instancias.forEach((arq, k) => {
      const { r, pos: p } = especieCompilada(arq);
      const giro = rotacionar(p, 0.4 * k, 0.3);
      const cx = (k - (instancias.length - 1) / 2) * largura + deslocamento;
      const inicio = atomos.length;
      r.atomos.forEach((a, i) => { atomos.push(a); pos.push([giro[i][0] + cx, giro[i][1], giro[i][2]]); donos.push(k); });
      r.ligacoes.forEach((l) => ligacoes.push({ ...l, a: l.a + inicio, b: l.b + inicio }));
    });
    return { atomos, ligacoes, pos };
  }

  function carregarReacao(indice) {
    const reacao = REACOES[indice];
    const R = arranjar(reacao.reagentes, 0), P = arranjar(reacao.produtos, 0);
    const conta = (lado) => lado.reduce((c, [n, arq]) => contarElementos(especieCompilada(arq).r.atomos, n, c), {});
    const cr = conta(reacao.reagentes), cp = conta(reacao.produtos);
    const elementos = [...new Set([...Object.keys(cr), ...Object.keys(cp)])].sort();
    const balanceada = elementos.every((e) => cr[e] === cp[e]);
    // Cada átomo dos produtos herda um átomo dos reagentes do mesmo elemento,
    // escolhendo o mais próximo ainda livre
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
    const ligacoesR = R.ligacoes.map((l) => ({ ...l, lado: "r" }));
    const ligacoesP = balanceada ? P.ligacoes.map((l) => ({ ...l, a: mapa[l.a], b: mapa[l.b], lado: "p", alfa: 0 })) : [];
    reacaoAtual = { reacao, R, destino, ligacoes: [...ligacoesR, ...ligacoesP], balanceada };
    progresso = 0;
    const pos = R.pos.map((p) => [...p]);
    cenaReacao.carregar(R.atomos, reacaoAtual.ligacoes, pos);
    cenaReacao.ajustarEscala(Math.max(...[...R.pos, ...P.pos].map((p) => Math.hypot(...p))) + 0.5);
    cenaReacao.aoQuadro = (tempo) => {
      if (ultimoTempo == null) ultimoTempo = tempo;
      const dt = Math.min(0.3, (tempo - ultimoTempo) / 1000);
      ultimoTempo = tempo;
      if (tocando && reacaoAtual.balanceada) {
        progresso = Math.min(1, progresso + dt / 9);
        document.getElementById("progresso-reacao").value = progresso;
      }
      aplicarProgresso(pos);
    };
    const quebradas = {}, formadas = {};
    reacao.reagentes.forEach(([n, arq]) => tiposDeLigacao(especieCompilada(arq).r, n, quebradas));
    reacao.produtos.forEach(([n, arq]) => tiposDeLigacao(especieCompilada(arq).r, n, formadas));
    document.getElementById("info-reacao").innerHTML = `
      <p class="equacao">${equacao(reacao.reagentes)} <span>→</span> ${equacao(reacao.produtos)}</p>
      <p class="${balanceada ? "estado-ok" : "estado-excede"}">${balanceada ? "Balanceada" : "Não balanceada"}: ${elementos.map((e) => `${e} ${cr[e] || 0} → ${cp[e] || 0}`).join(" · ")}</p>
      <div class="tabela"><table><tr><th>Ligações</th><th>Tipos</th></tr>
        <tr><td>rompidas</td><td>${textoContagem(quebradas)}</td></tr>
        <tr><td>formadas</td><td>${textoContagem(formadas)}</td></tr></table></div>
      <div class="botoes-traducao"><span>Tradução de cada espécie:</span>${[...reacao.reagentes, ...reacao.produtos].map(([, arq]) => especieCompilada(arq).ex)
        .filter((ex, i, todos) => todos.indexOf(ex) === i).map((ex) => `<button type="button" class="botao pequeno" data-demonstrar="${ex.arquivo}">${escapar(ex.titulo)}</button>`).join("")}</div>
      <p class="nota">Animação ilustrativa: mostra a conservação dos átomos e quais ligações se rompem e se formam. Não representa o mecanismo, a velocidade nem a energia da reação.</p>`;
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
    const someR = 1 - Math.min(1, Math.max(0, (t - 0.22) / 0.2));
    const surgeP = Math.min(1, Math.max(0, (t - 0.78) / 0.17));
    ligacoes.forEach((l) => { l.alfa = l.lado === "r" ? someR : surgeP; });
    const fase = [...FASES].reverse().find(([inicio]) => t >= inicio)[1];
    document.getElementById("fase-reacao").textContent = fase;
  }

  const seletorReacao = document.getElementById("reacao");
  seletorReacao.innerHTML = REACOES.map((r, i) => `<option value="${i}">${escapar(r.nome)}</option>`).join("");
  seletorReacao.addEventListener("change", () => { carregarReacao(Number(seletorReacao.value)); tocando = true; atualizarBotaoReacao(); });
  const botaoTocar = document.getElementById("tocar-reacao");
  function atualizarBotaoReacao() { botaoTocar.textContent = tocando ? "❚❚ Pausar" : "▶ Reproduzir"; }
  botaoTocar.addEventListener("click", () => { if (progresso >= 1) progresso = 0; tocando = !tocando; atualizarBotaoReacao(); });
  document.getElementById("reiniciar-reacao").addEventListener("click", () => { progresso = 0; tocando = true; atualizarBotaoReacao(); });
  document.getElementById("progresso-reacao").addEventListener("input", (e) => { progresso = Number(e.target.value); tocando = false; atualizarBotaoReacao(); });

  let laboratorioPronto = false;
  function iniciarLaboratorio() {
    if (laboratorioPronto) return;
    laboratorioPronto = true;
    montarListaMistura();
    montarMistura();
    carregarReacao(0);
    atualizarBotaoReacao();
  }

