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
      ${licao.exemplos.map((ex, k) => `
        <article class="placa exemplo-guia">
          <div class="exemplo-cabeca"><h4>${escapar(ex.titulo)}</h4><span class="selo-saida ${ex.saida === 0 ? "ok" : "erro"}">saída ${ex.saida}${ex.saida === 0 ? " · compila" : ex.saida === 2 ? " · erro semântico" : " · erro de sintaxe"}</span></div>
          <p>${escapar(ex.explicacao)}</p>
          <div class="exemplo-corpo">
            <div><p class="nota">Código</p><pre>${escapar(ex.codigo.trim())}</pre></div>
            <div><p class="nota">Saída real: <code>${escapar(ex.comando)}</code></p><pre class="${ex.saida === 0 ? "" : "erro"}">${escapar(ex.saida_real)}</pre></div>
          </div>
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
    const pag = document.querySelector("#pg-guia .paginador");
    pag.querySelector(".contador").textContent = `${i + 1} / ${LICOES.length}`;
    pag.querySelector('[data-guia-passo="-1"]').disabled = i === 0;
    pag.querySelector('[data-guia-passo="1"]').disabled = i === LICOES.length - 1;
  }
  document.querySelectorAll("[data-guia-passo]").forEach((b) => b.addEventListener("click", () => {
    const i = LICOES.findIndex((l) => l.id === licaoAtual) + Number(b.dataset.guiaPasso);
    location.hash = `#/guia/${LICOES[i].id}`;
  }));

