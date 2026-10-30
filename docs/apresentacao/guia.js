  /* ================= guia de uso ================= */
  const LICOES = DADOS.guia;
  let licaoAtual = LICOES[0].id;
  document.getElementById("sumario-guia").innerHTML = LICOES.map((l, i) =>
    `<a href="#/guia/${l.id}" data-licao="${l.id}">${String(i + 1).padStart(2, "0")} · ${escapar(l.titulo)}</a>`).join("");

  function mostrarLicao(id) {
    const licao = LICOES.find((l) => l.id === id) || LICOES[0];
    licaoAtual = licao.id;
    const i = LICOES.indexOf(licao);
    document.querySelectorAll("#sumario-guia a").forEach((a) => a.classList.toggle("ativo", a.dataset.licao === licao.id));
    document.getElementById("licao").innerHTML = `
      <article class="placa licao">
        <span class="rotulo">lição ${String(i + 1).padStart(2, "0")}</span>
        <h3>${escapar(licao.titulo)}</h3>
        ${licao.texto.map((p) => `<p>${escapar(p)}</p>`).join("")}
      </article>
      ${licao.passos ? `<article class="placa passos-guia"><h4>Passo a passo</h4><ol>${licao.passos.map((p) => `
        <li><b>${escapar(p.titulo)}</b><p>${escapar(p.texto)}</p>${p.codigo ? `<pre>${escapar(p.codigo)}</pre>` : ""}</li>`).join("")}</ol></article>` : ""}
      ${licao.anatomia ? `<article class="placa anatomia"><h4>Anatomia do comando</h4>
        <p class="anatomia-codigo">${licao.anatomia.partes.map(([parte], i) => `<span class="parte p${i}">${escapar(parte)}</span>`).join(" ")}</p>
        <dl>${licao.anatomia.partes.map(([parte, sentido], i) => `<dt><span class="parte p${i}">${escapar(parte)}</span></dt><dd>${escapar(sentido)}</dd>`).join("")}</dl></article>` : ""}
      ${licao.exemplos.map((ex, k) => `
        <article class="placa exemplo-guia">
          <div class="exemplo-cabeca"><h4>${escapar(ex.titulo)}</h4><span class="selo-saida ${ex.saida === 0 ? "ok" : "erro"}">saída ${ex.saida}${ex.saida === 0 ? " · compila" : ex.saida === 2 ? " · erro semântico" : " · erro de sintaxe"}</span></div>
          <p>${escapar(ex.explicacao)}</p>
          <div class="exemplo-corpo${ex.bohr ? " com-bohr" : ""}">
            <div><p class="nota">Código</p><pre>${escapar(ex.codigo.trim())}</pre>${ex.bohr ? `<p class="nota" style="margin-top:0.8rem">Modelo de Bohr</p><canvas class="bohr-guia" data-bohr="${ex.bohr}" data-carga="${ex.carga || 0}" aria-label="Modelo de Bohr de ${ex.bohr}"></canvas>` : ""}</div>
            <div><p class="nota">Saída real: <code>${escapar(ex.comando)}</code></p><pre class="${ex.saida === 0 ? "" : "erro"}">${escapar(ex.saida_real)}</pre></div>
          </div>
          ${(() => {
            // AST desenhada para exemplos pequenos que passam da sintaxe
            const r = compilar(ex.codigo);
            return r.especie && r.especie.comandos.length <= 8
              ? `<details class="ast-guia"${licao.id === "construir_atomo" ? " open" : ""}><summary>AST desenhada: como a linguagem entendeu este código</summary>${desenhoArvore(astNo(r.especie, "comp"))}</details>`
              : "";
          })()}
          <div class="acoes" style="justify-content:flex-start;margin-top:0.9rem">
            <button type="button" class="botao pequeno" data-guia-abrir="${k}">Abrir no playground</button>
            <button type="button" class="botao pequeno" data-guia-demo="${k}">Demonstrar tradução</button>
          </div>
        </article>`).join("")}`;
    document.querySelectorAll("[data-guia-abrir]").forEach((b) => b.addEventListener("click", () => {
      const ex = licao.exemplos[Number(b.dataset.guiaAbrir)];
      exemploAtual = null;
      seletor.value = "";
      codigo.value = ex.codigo;
      location.hash = "#/playground";
      executar();
    }));
    document.querySelectorAll("[data-guia-demo]").forEach((b) => b.addEventListener("click", () => {
      const ex = licao.exemplos[Number(b.dataset.guiaDemo)];
      abrirDemonstracao(ex.codigo, ex.titulo);
    }));
    requestAnimationFrame(() => ajustarDesenhos(document.getElementById("licao")));
    document.querySelectorAll(".ast-guia").forEach((d) => d.addEventListener("toggle", () => ajustarDesenhos(d)));
    const pag = document.querySelector("#pg-guia .paginador");
    pag.querySelector(".contador").textContent = `${i + 1} / ${LICOES.length}`;
    pag.querySelector('[data-guia-passo="-1"]').disabled = i === 0;
    pag.querySelector('[data-guia-passo="1"]').disabled = i === LICOES.length - 1;
  }
  document.querySelectorAll("[data-guia-passo]").forEach((b) => b.addEventListener("click", () => {
    const i = LICOES.findIndex((l) => l.id === licaoAtual) + Number(b.dataset.guiaPasso);
    location.hash = `#/guia/${LICOES[i].id}`;
  }));

  // Modelos de Bohr dos exemplos do guia, animados enquanto visíveis
  function animarBohrGuia(tempo) {
    document.querySelectorAll(".bohr-guia").forEach((c) => {
      if (c.offsetParent === null) return;
      const ctx = c.getContext("2d"), dpr = window.devicePixelRatio || 1;
      const w = c.clientWidth, h = c.clientHeight;
      if (c.width !== Math.round(w * dpr)) { c.width = Math.round(w * dpr); c.height = Math.round(h * dpr); }
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.clearRect(0, 0, w, h);
      const carga = Number(c.dataset.carga);
      pintarBohr(ctx, w, h, c.dataset.bohr, camadasComCarga(c.dataset.bohr, carga), tempo, carga);
    });
    requestAnimationFrame(animarBohrGuia);
  }
  requestAnimationFrame(animarBohrGuia);

