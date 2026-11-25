  /* ================= buraco negro: species black_hole ================= */
  // Um programa que compila para species black_hole { collapse N mol of
  // "Bloco" } devora a tela. A semântica (HOLE-001 a HOLE-006, em app.js e
  // src/semantico.py) decide pela química e pela física se a matéria vira
  // buraco negro; aqui fica só a imagem, calculada por traçado de raios na
  // métrica de Schwarzschild. Pesquisa e limites: docs/plano_buraco_negro.md

  /* ---------- renderizador: traçado de raios de Schwarzschild ---------- */
  // Unidades G = c = M = 1. O observador fica parado a uma distância uD do
  // buraco, 8° acima do plano do disco, olhando para ele. A página é uma
  // folha perpendicular à linha de visada, à mesma distância atrás do buraco.
  const VERTEX_BN = "attribute vec2 p; void main() { gl_Position = vec4(p, 0.0, 1.0); }";
  const FRAGMENT_BN = `
precision highp float;
uniform vec2 uRes;
uniform vec2 uCentro;
uniform float uD;
uniform float uTanFov;
uniform float uElev;
uniform sampler2D uPagina;
uniform float uTemPagina;
uniform vec3 uFundo;
uniform float uDisco;
uniform float uEspiral;
uniform float uTempo;

const float RIN = 6.0;
const float ROUT = 20.0;

float hash(vec3 p) { p = fract(p * 0.3183099 + 0.1); p *= 17.0; return fract(p.x * p.y * p.z * (p.x + p.y + p.z)); }

// Céu: estrelas por célula de direção
vec3 ceu(vec3 d) {
  vec3 col = vec3(0.0);
  for (int k = 0; k < 2; k++) {
    float escala = k == 0 ? 90.0 : 220.0;
    vec3 q = d * escala;
    vec3 cel = floor(q);
    float h = hash(cel);
    if (h > (k == 0 ? 0.985 : 0.992)) {
      vec3 centro = cel + 0.5 + 0.35 * (vec3(hash(cel + 1.3), hash(cel + 2.7), hash(cel + 4.1)) - 0.5);
      float dist = length(q - centro);
      float brilho = smoothstep(0.45, 0.0, dist) * (h - 0.98) * 110.0;
      vec3 tom = mix(vec3(1.0, 0.8, 0.6), vec3(0.7, 0.8, 1.0), hash(cel + 7.7));
      col += tom * brilho;
    }
  }
  return col + uFundo * 0.25;
}

// Cor aproximada de corpo negro (ajuste de Tanner Helland), T em kelvin
vec3 corpoNegro(float T) {
  float t = clamp(T, 1000.0, 40000.0) / 100.0;
  float r = t <= 66.0 ? 1.0 : clamp(1.292936 * pow(t - 60.0, -0.1332047), 0.0, 1.0);
  float g = t <= 66.0 ? clamp(0.3900816 * log(t) - 0.6318414, 0.0, 1.0) : clamp(1.1298909 * pow(t - 60.0, -0.0755148), 0.0, 1.0);
  float b = t >= 66.0 ? 1.0 : (t <= 19.0 ? 0.0 : clamp(0.5432068 * log(t - 10.0) - 1.1962541, 0.0, 1.0));
  return vec3(r, g, b);
}

// Disco fino: perfil de temperatura do disco fino, redshift gravitacional
// e Doppler da órbita circular no fator g; brilho com g^4
vec3 disco(vec3 hit, float r, float Lz) {
  float omega = pow(r, -1.5);
  float g = sqrt(1.0 - 3.0 / r) / (1.0 - omega * Lz);
  g /= sqrt(1.0 - 2.0 / uD);
  float perfil = pow(r, -0.75) * pow(max(1.0 - sqrt(RIN / r), 0.0), 0.25);
  float pico = pow(RIN * 49.0 / 36.0, -0.75) * pow(1.0 - sqrt(36.0 / 49.0), 0.25);
  float T = perfil / pico;
  // Faixas de gás em órbita, giradas com a velocidade kepleriana
  float ang = atan(hit.z, hit.x) + omega * uTempo * 6.0;
  float faixas = 0.85 + 0.15 * sin(r * 5.3 + 1.5 * sin(ang * 2.0 + r * 0.7)) * (0.6 + 0.4 * sin(ang * 5.0 - r * 2.3));
  float borda = smoothstep(ROUT, ROUT - 6.0, r);
  vec3 cor = corpoNegro(4300.0 * T * g);
  return cor * pow(g, 4.0) * pow(T, 4.0) * faixas * borda * 4.0;
}

vec3 pagina(vec2 pix) {
  if (uTemPagina < 0.5) return uFundo;
  // Fora da folha, só o céu; a espiral não abre buraco na borda
  vec2 uv0 = pix / uRes;
  if (uv0.x < 0.0 || uv0.x > 1.0 || uv0.y < 0.0 || uv0.y > 1.0) return vec3(-1.0);
  // Espiral didática: a página que cai gira mais perto do buraco
  vec2 rel = pix - uCentro;
  float rho = length(rel);
  float escalaE = sqrt(2.0 / uD) / uTanFov * uRes.y * 0.5;
  float puxao = uEspiral * pow(escalaE / max(rho, 1.0), 1.2);
  float ang = min(puxao, 9.0);
  float c = cos(ang), s = sin(ang);
  rel = mat2(c, s, -s, c) * rel * (1.0 + min(0.35 * puxao, 2.0));
  vec2 uv = clamp((uCentro + rel) / uRes, 0.0, 1.0);
  vec3 col = texture2D(uPagina, uv).rgb;
  // O que cai fica mais vermelho e mais escuro para quem olha de longe
  float queda = clamp(puxao * 0.35, 0.0, 1.0);
  col = mix(col, vec3(dot(col, vec3(0.9, 0.3, 0.05)), dot(col, vec3(0.25, 0.25, 0.05)), 0.0), queda * 0.8);
  return col * (1.0 - 0.6 * queda);
}

void main() {
  vec2 q = (gl_FragCoord.xy - uCentro) / (uRes.y * 0.5) * uTanFov;
  vec3 cam = uD * vec3(0.0, sin(uElev), cos(uElev));
  vec3 f = -normalize(cam);
  vec3 dir0 = vec3(1.0, 0.0, 0.0);
  vec3 cima = cross(dir0, f);
  vec3 raio = normalize(f + q.x * dir0 + q.y * cima);

  vec3 e1 = normalize(cam);
  float ce = dot(raio, e1);
  vec3 tang = raio - ce * e1;
  float st = length(tang);
  if (st < 1e-7) { gl_FragColor = vec4(0.0, 0.0, 0.0, 1.0); return; }
  vec3 e2 = tang / st;
  vec3 n = cross(e1, e2);

  float u = 1.0 / uD;
  float h = 1.0 - 2.0 * u;
  float b = uD * st / sqrt(h);
  float du = sqrt(max(1.0 / (b * b) - u * u * h, 0.0)) * (ce < 0.0 ? 1.0 : -1.0);
  // Momento angular do fóton em torno do eixo do disco (sentido real, não o traçado)
  float Lz = -b * n.y;

  vec3 plano = f * uD;
  vec3 ant = cam;
  float phi = 0.0;
  vec3 cor = vec3(0.0);
  bool fim = false;

  for (int i = 0; i < 420; i++) {
    float dphi = min(0.035, max(0.3 * u / max(abs(du), 1e-6), 1e-5));
    // RK4 de u'' = -u + 3u²
    float k1u = du, k1v = -u + 3.0 * u * u;
    float u2 = u + 0.5 * dphi * k1u, v2 = du + 0.5 * dphi * k1v;
    float k2u = v2, k2v = -u2 + 3.0 * u2 * u2;
    float u3 = u + 0.5 * dphi * k2u, v3 = du + 0.5 * dphi * k2v;
    float k3u = v3, k3v = -u3 + 3.0 * u3 * u3;
    float u4 = u + dphi * k3u, v4 = du + dphi * k3v;
    float k4u = v4, k4v = -u4 + 3.0 * u4 * u4;
    float un = u + dphi * (k1u + 2.0 * k2u + 2.0 * k3u + k4u) / 6.0;
    float dun = du + dphi * (k1v + 2.0 * k2v + 2.0 * k3v + k4v) / 6.0;

    if (un >= 0.5) { cor = vec3(0.0); fim = true; break; }

    if (un <= 0.0) {
      // Escapou: segue em linha reta a partir do último ponto
      vec3 d = normalize((-sin(phi) * e1 + cos(phi) * e2) / u - (cos(phi) * e1 + sin(phi) * e2) * du / (u * u));
      float df = dot(d, f);
      float s = df > 1e-5 ? dot(plano - ant, f) / df : -1.0;
      if (s > 0.0) {
        vec3 hit = ant + s * d - plano;
        vec2 pix = uCentro + vec2(dot(hit, dir0), dot(hit, cima)) / (2.0 * uD) / uTanFov * (uRes.y * 0.5);
        vec3 pg = pagina(pix);
        cor = pg.x < 0.0 ? ceu(d) : pg;
      } else cor = ceu(d);
      fim = true;
      break;
    }

    phi += dphi;
    u = un; du = dun;
    vec3 pos = (cos(phi) * e1 + sin(phi) * e2) / u;

    if (uDisco > 0.0 && ant.y * pos.y < 0.0) {
      float a = ant.y / (ant.y - pos.y);
      vec3 hit = mix(ant, pos, a);
      float r = length(hit);
      if (r > RIN && r < ROUT) { cor = (1.0 - exp(-disco(hit, r, Lz))) * uDisco; fim = true; break; }
    }

    float sa = dot(ant - plano, f), sp = dot(pos - plano, f);
    if (sa < 0.0 && sp >= 0.0) {
      vec3 hit = mix(ant, pos, sa / (sa - sp)) - plano;
      vec2 pix = uCentro + vec2(dot(hit, dir0), dot(hit, cima)) / (2.0 * uD) / uTanFov * (uRes.y * 0.5);
      vec3 pg = pagina(pix);
      cor = pg.x < 0.0 ? ceu(normalize(pos - ant)) : pg;
      fim = true;
      break;
    }

    if (u < 0.25 / uD && du < 0.0) {
      vec3 d = normalize(pos - ant);
      cor = ceu(d);
      fim = true;
      break;
    }
    ant = pos;
  }
  if (!fim) cor = vec3(0.0);
  gl_FragColor = vec4(cor, 1.0);
}`;

  class LenteSchwarzschild {
    constructor(canvas, preservar = false) {
      const gl = canvas.getContext("webgl", { antialias: false, alpha: false, preserveDrawingBuffer: preservar });
      if (!gl) throw new Error("sem WebGL");
      this.gl = gl;
      this.canvas = canvas;
      const sombreador = (tipo, fonte) => {
        const s = gl.createShader(tipo);
        gl.shaderSource(s, fonte);
        gl.compileShader(s);
        if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s));
        return s;
      };
      const prog = gl.createProgram();
      gl.attachShader(prog, sombreador(gl.VERTEX_SHADER, VERTEX_BN));
      gl.attachShader(prog, sombreador(gl.FRAGMENT_SHADER, FRAGMENT_BN));
      gl.linkProgram(prog);
      if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(prog));
      gl.useProgram(prog);
      const buf = gl.createBuffer();
      gl.bindBuffer(gl.ARRAY_BUFFER, buf);
      gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
      const loc = gl.getAttribLocation(prog, "p");
      gl.enableVertexAttribArray(loc);
      gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
      this.u = {};
      ["uRes", "uCentro", "uD", "uTanFov", "uElev", "uPagina", "uTemPagina", "uFundo", "uDisco", "uEspiral", "uTempo"].forEach((n) => { this.u[n] = gl.getUniformLocation(prog, n); });
      this.textura = gl.createTexture();
      gl.bindTexture(gl.TEXTURE_2D, this.textura);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
      this.temPagina = false;
    }
    usarPagina(imagem) {
      const gl = this.gl;
      this.temPagina = false;
      if (!imagem) return;
      gl.bindTexture(gl.TEXTURE_2D, this.textura);
      gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, true);
      try {
        gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGB, gl.RGB, gl.UNSIGNED_BYTE, imagem);
        this.temPagina = true;
      } catch (e) {
        // Imagem contaminada (origem cruzada): segue sem a página
      }
    }
    // escala: fração da resolução do canvas em CSS; centro em px CSS a partir do topo
    desenhar({ D, centro, escala = 1, disco = 1, espiral = 0, tempo = 0, fundo = [0.05, 0.05, 0.07] }) {
      const gl = this.gl, c = this.canvas;
      const w = Math.max(2, Math.round(c.clientWidth * escala)), h = Math.max(2, Math.round(c.clientHeight * escala));
      if (c.width !== w || c.height !== h) { c.width = w; c.height = h; }
      gl.viewport(0, 0, w, h);
      const k = w / c.clientWidth;
      const cx = (centro ? centro[0] : c.clientWidth / 2) * k, cy = h - (centro ? centro[1] : c.clientHeight / 2) * k;
      gl.uniform2f(this.u.uRes, w, h);
      gl.uniform2f(this.u.uCentro, cx, cy);
      gl.uniform1f(this.u.uD, D);
      gl.uniform1f(this.u.uTanFov, Math.tan((25 * Math.PI) / 180));
      gl.uniform1f(this.u.uElev, (8 * Math.PI) / 180);
      gl.uniform1i(this.u.uPagina, 0);
      gl.uniform1f(this.u.uTemPagina, this.temPagina ? 1 : 0);
      gl.uniform3f(this.u.uFundo, ...fundo);
      gl.uniform1f(this.u.uDisco, disco);
      gl.uniform1f(this.u.uEspiral, espiral);
      gl.uniform1f(this.u.uTempo, tempo);
      gl.activeTexture(gl.TEXTURE0);
      gl.bindTexture(gl.TEXTURE_2D, this.textura);
      gl.drawArrays(gl.TRIANGLES, 0, 3);
    }
  }

  /* ---------- foto da página ---------- */
  // A área visível vira uma imagem SVG com foreignObject: o CSS da página
  // vai junto, com html, body e :root trocados por classes, e cada canvas
  // vira a imagem do que ele mostra agora
  function corDeFundo() {
    const m = getComputedStyle(document.body).backgroundColor.match(/[\d.]+/g) || [14, 13, 18];
    return m.slice(0, 3).map((v) => Number(v) / 255);
  }
  async function fotografarPagina() {
    const W = innerWidth, H = innerHeight, Y = scrollY;
    const css = [...document.querySelectorAll("style")].map((s) => s.textContent).join("\n")
      .replace(/:root/g, ".cap-raiz")
      .replace(/(^|[\s,{}])html(?=[\s{,.\[:])/g, "$1.cap-raiz")
      .replace(/(^|[\s,{}])body(?=[\s{,.\[:])/g, "$1.cap-corpo")
      // Numa imagem SVG a animação fica parada no primeiro quadro (opacidade 0)
      + "\n.cap-raiz *, .cap-raiz *::before, .cap-raiz *::after { animation: none !important; transition: none !important; }";
    const originais = [...document.body.querySelectorAll("canvas")];
    const corpo = document.body.cloneNode(true);
    [...corpo.querySelectorAll("canvas")].forEach((copia, i) => {
      const orig = originais[i], img = document.createElement("img");
      try { img.src = orig.toDataURL(); } catch (e) { img.src = "data:,"; }
      if (orig.id) img.id = orig.id;
      if (orig.className) img.className = orig.className;
      const caixa = orig.getBoundingClientRect();
      img.setAttribute("style", `display:block;width:${caixa.width}px;height:${caixa.height}px;${orig.id === "malha" ? "position:fixed;inset:0;z-index:-1" : ""}`);
      copia.replaceWith(img);
    });
    const campos = [...document.body.querySelectorAll("textarea, input, select")];
    [...corpo.querySelectorAll("textarea, input, select")].forEach((copia, i) => {
      const orig = campos[i];
      if (orig.tagName === "TEXTAREA") copia.textContent = orig.value;
      else if (orig.tagName === "SELECT") [...copia.options].forEach((o, j) => { if (j === orig.selectedIndex) o.setAttribute("selected", ""); else o.removeAttribute("selected"); });
      else if (orig.type === "checkbox" || orig.type === "radio") { if (orig.checked) copia.setAttribute("checked", ""); }
      else copia.setAttribute("value", orig.value);
    });
    corpo.querySelectorAll("script, dialog:not([open]), .pagina:not(.ativa), .bn-tela").forEach((n) => n.remove());
    const raizCap = document.createElement("div");
    raizCap.className = "cap-raiz";
    if (raiz.dataset.theme) raizCap.dataset.theme = raiz.dataset.theme;
    raizCap.setAttribute("style", `width:${W}px;height:${H}px;overflow:hidden;position:relative;background:var(--bg)`);
    const estilo = document.createElement("style");
    estilo.textContent = css;
    const corpoCap = document.createElement("div");
    corpoCap.className = `cap-corpo ${document.body.className}`;
    corpoCap.setAttribute("style", `position:relative;top:${-Y}px;min-height:${H + Y}px`);
    corpoCap.append(...corpo.childNodes);
    raizCap.append(estilo, corpoCap);
    // A barra do topo é sticky: rolada a página, ela fica presa em cima
    const topo = corpoCap.querySelector(".topo");
    if (topo && Y > 0) {
      const fixo = topo.cloneNode(true);
      fixo.style.cssText = "position:absolute;top:0;left:0;right:0";
      raizCap.append(fixo);
    }
    const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}"><foreignObject x="0" y="0" width="100%" height="100%">${new XMLSerializer().serializeToString(raizCap)}</foreignObject></svg>`;
    const img = new Image();
    img.src = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(svg);
    await img.decode();
    const tela = document.createElement("canvas");
    const k = Math.min(devicePixelRatio || 1, 2);
    tela.width = Math.round(W * k);
    tela.height = Math.round(H * k);
    const ctx = tela.getContext("2d");
    ctx.fillStyle = getComputedStyle(document.body).backgroundColor;
    ctx.fillRect(0, 0, tela.width, tela.height);
    ctx.drawImage(img, 0, 0, tela.width, tela.height);
    ctx.getImageData(0, 0, 1, 1); // lança se a imagem contaminou o canvas
    return tela;
  }

  /* ---------- a tela sendo devorada ---------- */
  const FASES_BN = [
    [0, "Colapso: a massa cai abaixo do raio de Schwarzschild"],
    [0.14, "Lente gravitacional: a página se curva num anel de Einstein"],
    [0.36, "Disco de acreção: o lado que vem na nossa direção brilha mais (Doppler)"],
    [0.62, "Sombra: nenhum raio que passa a menos de 2,6 r_s volta"],
    [0.86, "Dentro da esfera de fótons: a sombra ocupa a tela inteira"],
  ];
  const D_INICIO = 2600, D_FIM = 2.45, DURACAO_BN = 12000;
  const degrau = (a, b, x) => { const t = Math.min(1, Math.max(0, (x - a) / (b - a))); return t * t * (3 - 2 * t); };
  function estadoBN(tau, origem) {
    const s = Math.pow(tau, 1.25);
    const meio = [innerWidth / 2, innerHeight / 2], m = degrau(0.12, 0.7, tau);
    const D = Math.exp(Math.log(D_INICIO) + (Math.log(D_FIM) - Math.log(D_INICIO)) * s);
    return {
      D,
      centro: [origem[0] + (meio[0] - origem[0]) * m, origem[1] + (meio[1] - origem[1]) * m],
      // O disco some antes de o observador chegar à borda dele (r = 20M)
      disco: degrau(0.18, 0.42, tau) * degrau(16, 34, D),
      espiral: 2.4 * degrau(0.08, 0.95, tau),
    };
  }

  let devorando = null;
  async function devorarTela(origem, botao, legenda = "") {
    if (devorando) return;
    devorando = { cancelar: () => {} };
    const parado = matchMedia("(prefers-reduced-motion: reduce)").matches;
    let foto = null;
    try { foto = await fotografarPagina(); } catch (e) { foto = null; }

    const tela = document.createElement("div");
    tela.className = "bn-tela";
    tela.setAttribute("role", "dialog");
    tela.setAttribute("aria-modal", "true");
    tela.setAttribute("aria-label", "Buraco negro devorando a tela");
    tela.innerHTML = `<canvas aria-hidden="true"></canvas>
      <p class="bn-fase" aria-live="polite"></p>
      <p class="bn-medida" aria-hidden="true"></p>
      <button type="button" class="botao pequeno bn-sair">Esc · voltar</button>
      <div class="bn-fim" hidden><div class="bn-cartao">
        <p class="rotulo"></p>
        <h2></h2>
        <p class="bn-texto"></p>
        <div class="acoes"><button type="button" class="botao primario bn-voltar">Evaporar e voltar</button>${parado ? '<button type="button" class="botao bn-animar">Ver a animação mesmo assim</button>' : ""}</div>
      </div></div>`;
    document.body.append(tela);
    const canvas = tela.querySelector("canvas");
    let lente;
    try { lente = new LenteSchwarzschild(canvas); } catch (e) { tela.remove(); devorando = null; return; }
    lente.usarPagina(foto);
    const fundo = corDeFundo();
    const rolagem = raiz.style.overflow;
    raiz.style.overflow = "hidden";
    const fase = tela.querySelector(".bn-fase"), medida = tela.querySelector(".bn-medida"), fim = tela.querySelector(".bn-fim");
    const teto = Math.min(devicePixelRatio || 1, 1.5);
    let quadro = 0, escala = teto, lentos = 0, inicio = null, tempoAnt = null, media = 16, faseAtual = -1, encerrado = false;

    function mostrar(tau, tempo) {
      const e = estadoBN(tau, origem);
      lente.desenhar({ ...e, escala, fundo, tempo });
      const f = FASES_BN.reduce((acc, [t], i) => (tau >= t ? i : acc), 0);
      if (f !== faseAtual) { faseAtual = f; fase.textContent = FASES_BN[f][1]; }
      medida.textContent = `${legenda ? legenda + " · " : ""}observador a r = ${cientificoPt(e.D, 3)} M`;
    }
    function cartao(rotulo, titulo, texto) {
      fim.querySelector(".rotulo").textContent = rotulo;
      fim.querySelector("h2").textContent = titulo;
      fim.querySelector(".bn-texto").textContent = texto;
      fim.hidden = false;
    }
    function terminar() {
      fase.textContent = "";
      cartao("horizonte", "A tela foi devorada", "Para um observador parado dentro da esfera de fótons, a sombra cobre mais da metade do céu. A página continua lá fora: daqui, nenhum raio dela chega.");
      (fim.querySelector(".bn-animar") || fim.querySelector(".bn-voltar")).focus();
    }
    function passo(agora) {
      if (encerrado) return;
      if (inicio == null) inicio = agora;
      // Qualidade adaptativa: baixa a resolução só com lentidão seguida;
      // saltos longos (aba em segundo plano) não contam
      const dt = tempoAnt == null ? 16 : agora - tempoAnt;
      if (dt < 250) {
        media = media * 0.8 + dt * 0.2;
        lentos = media > 40 ? lentos + 1 : 0;
        if (lentos > 8 && escala > 0.45) { escala *= 0.85; lentos = 0; media = 25; }
        else if (media < 18 && escala < teto) escala = Math.min(escala * 1.03, teto);
      }
      tempoAnt = agora;
      const tau = Math.min(1, (agora - inicio) / DURACAO_BN);
      mostrar(tau, (agora - inicio) / 1000);
      if (tau < 1) quadro = requestAnimationFrame(passo);
      else terminar();
    }
    function animar() {
      fim.hidden = true;
      fim.querySelector(".bn-voltar").textContent = "Evaporar e voltar";
      inicio = null; tempoAnt = null;
      tela.querySelector(".bn-sair").focus();
      quadro = requestAnimationFrame(passo);
    }
    // Evaporação: a mesma linha do tempo de trás para a frente, rápida
    function voltar() {
      if (encerrado) return;
      cancelAnimationFrame(quadro);
      fim.hidden = true;
      const sair = () => {
        encerrado = true;
        cancelAnimationFrame(quadro);
        tela.remove();
        raiz.style.overflow = rolagem;
        removeEventListener("keydown", teclado, true);
        devorando = null;
        if (botao) botao.focus();
      };
      if (parado) { sair(); return; }
      fase.textContent = "Evaporação: a página volta";
      const t0 = performance.now(), deQuanto = Math.min(1, inicio == null ? 1 : (performance.now() - inicio) / DURACAO_BN);
      const reverso = (agora) => {
        const tau = deQuanto * (1 - Math.min(1, (agora - t0) / 1600));
        mostrar(tau, (agora - t0) / 1000);
        if (tau > 0) quadro = requestAnimationFrame(reverso);
        else sair();
      };
      quadro = requestAnimationFrame(reverso);
    }
    function teclado(e) {
      if (e.key === "Escape") { e.preventDefault(); voltar(); }
      if (e.key === "Tab") {
        const focaveis = [...tela.querySelectorAll("button")].filter((b) => b.offsetParent);
        if (!focaveis.length) return;
        const i = focaveis.indexOf(document.activeElement);
        e.preventDefault();
        focaveis[(i + (e.shiftKey ? -1 : 1) + focaveis.length) % focaveis.length].focus();
      }
    }
    addEventListener("keydown", teclado, true);
    tela.querySelector(".bn-sair").addEventListener("click", voltar);
    tela.querySelector(".bn-voltar").addEventListener("click", voltar);
    const animarMesmo = tela.querySelector(".bn-animar");
    if (animarMesmo) animarMesmo.addEventListener("click", animar);
    devorando.cancelar = voltar;

    if (parado) {
      // Sem animação: um quadro do meio do caminho e o texto do fim
      mostrar(0.6, 0);
      fase.textContent = FASES_BN[3][1];
      cartao("movimento reduzido", "Um quadro parado", "O sistema pede menos movimento, então a animação não começou sozinha. Este é o meio do caminho: a página atrás do buraco, curvada pela lente. A animação dura 12 segundos e termina com a tela inteira preta.");
      fim.querySelector(".bn-voltar").textContent = "Voltar";
      fim.querySelector(".bn-voltar").focus();
    } else {
      tela.querySelector(".bn-sair").focus();
      quadro = requestAnimationFrame(passo);
    }
  }

  /* ---------- playground: o programa compilado devora a tela ---------- */
  // A cena 3D mostra o buraco negro calculado; com o programa válido por
  // um instante sem edição, a tela começa a ser devorada sozinha. O mesmo
  // código não devora de novo até ser editado.
  let cenaBN = null, lenteCenaBN = null, ultimoDevorado = null, esperaBN = 0;
  function desenharCenaBN() {
    if (lenteCenaBN && cenaBN && !cenaBN.hidden && cenaBN.clientWidth) {
      lenteCenaBN.desenhar({ D: 40, escala: Math.min(devicePixelRatio || 1, 2), fundo: corDeFundo(), disco: 1 });
    }
  }
  function mostrarBuracoNoPlayground(r, texto) {
    const caixa = document.getElementById("cena-3d").parentElement;
    if (!cenaBN) {
      cenaBN = document.createElement("canvas");
      cenaBN.className = "cena-bn";
      cenaBN.setAttribute("aria-label", "Buraco negro de Schwarzschild com disco de acreção, visto 8° acima do disco");
      caixa.append(cenaBN);
      try { lenteCenaBN = new LenteSchwarzschild(cenaBN, true); } catch (e) { lenteCenaBN = null; }
      new ResizeObserver(desenharCenaBN).observe(cenaBN);
      new MutationObserver(desenharCenaBN).observe(raiz, { attributes: true, attributeFilter: ["data-theme"] });
    }
    clearTimeout(esperaBN);
    const valido = Boolean(r && r.buraco);
    cenaBN.hidden = !valido;
    if (!valido) return;
    if (!lenteCenaBN) {
      const vazio = document.getElementById("cena-vazia");
      vazio.hidden = false;
      vazio.textContent = "O buraco negro compilou, mas a imagem dele é calculada na placa de vídeo e precisa de WebGL, que este navegador não ofereceu.";
      cenaBN.hidden = true;
      return;
    }
    requestAnimationFrame(desenharCenaBN);
    if (texto === ultimoDevorado) return;
    esperaBN = setTimeout(() => {
      // Fora do playground, com um diálogo aberto (a demonstração da tradução)
      // ou com outra animação em curso, o buraco fica só na cena
      if (!document.getElementById("pg-playground").classList.contains("ativa") || devorando || document.querySelector("dialog[open]")) return;
      ultimoDevorado = texto;
      const rect = caixa.getBoundingClientRect();
      const bn = r.buraco;
      // Centro da cena, trazido para dentro da tela quando ela está fora de vista
      const dentro = (v, max) => Math.min(max * 0.85, Math.max(max * 0.15, v));
      devorarTela([dentro(rect.left + rect.width / 2, innerWidth), dentro(rect.top + rect.height / 2, innerHeight)], document.getElementById("codigo"),
        `${r.especie.nome}: ${cientificoPt(bn.massaSolar)} M☉, horizonte de ${comprimentoPt(bn.rs)}`);
    }, 1200);
  }
