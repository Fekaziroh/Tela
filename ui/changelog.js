"use strict";
// Patch notes, newest first. Source for the window, CHANGELOG.md and the release notes
// (installer/changelog.py). Keep it valid JSON between "= " and the final ";".
// "draft": true = still being worked on; the workflow only publishes the release once it is removed.
const CHANGELOG = [
{"v": "1.4.1", "pt": [
  "Histórico de partidas: cada resumo de jogo fica salvo. Dá para buscar, ver o gráfico de FPS, mostrar de novo na tela, apagar e exportar em CSV. Você escolhe quantas guardar e a pasta.",
  "Atualizações pelo app: a Tela! avisa quando sai uma versão nova e instala com um clique.",
  "Notas de versão de todas as versões em Avançado, e um resumo do que mudou depois de cada atualização.",
  "Mídia: some 5 s depois de pausar, com fade. Com o jogo aberto (mesmo minimizado) ela continua à direita.",
  "Transição suave também ao sair do resumo de jogo.",
  "Tema de cores da tela personalizado, separado dos prontos.",
  "Correção: a imagem de fundo às vezes não saía ao remover.",
  "Correção: a tela podia perder a conexão durante uma transição.",
  "O medidor de FPS se recupera sozinho quando para de responder, e mostra o motivo se não iniciar.",
  "A janela usa bem menos memória.",
  "Instalador: corrigido o erro 740 ao abrir a Tela! no final."
], "en": [
  "Game history: every game summary is saved. Search it, see the FPS graph, show a game on the screen again, delete or export to CSV. You choose how many to keep and the folder.",
  "Updates from the app: Tela! tells you when a new version is out and installs it with one click.",
  "Patch notes for every version in Advanced, and a summary of what changed after each update.",
  "Media: hides 5 s after pausing, with a fade. While a game is open (even minimized) it stays on the right.",
  "Smooth transition when leaving the game summary too.",
  "Custom screen color theme, separate from the ready-made ones.",
  "Fix: the background picture sometimes stayed after removing it.",
  "Fix: the screen could lose its connection during a transition.",
  "The FPS meter recovers by itself when it stops responding, and shows why when it cannot start.",
  "The window uses much less memory.",
  "Setup: fixed error 740 when opening Tela! at the end."
]},
{"v": "1.4.0", "pt": [
  "Janela nova: temas (automático, prontos ou com as suas cores) e idiomas português, inglês, espanhol e chinês.",
  "Editor de layout: arrastar, redimensionar, ligar e desligar blocos, renomear e escolher sensores numa lista ao vivo.",
  "Tela na vertical, além da horizontal (e as duas invertidas).",
  "Temas de cores da tela e imagem de fundo.",
  "Instalador de verdade: não precisa de Python, baixa o PawnIO e o WebView2 só se faltarem e guarda as configurações em %APPDATA%\\Tela.",
  "Assistente na primeira abertura, que traz as configurações das versões antigas."
], "en": [
  "New window: themes (automatic, ready-made or your own colors) and Portuguese, English, Spanish and Chinese.",
  "Layout editor: drag, resize, turn blocks on and off, rename and pick sensors from a live list.",
  "Portrait screen as well as landscape (and both flipped).",
  "Screen color themes and background picture.",
  "A real installer: no Python needed, downloads PawnIO and WebView2 only when missing and keeps the settings in %APPDATA%\\Tela.",
  "First-run assistant that brings the settings from older versions."
]},
{"v": "1.3.9", "pt": [
  "Revisão geral: desenho mais leve, recuperação automática de erros e log que gira sozinho.",
  "Primeiro Setup.exe gerado no GitHub."
], "en": [
  "General review: lighter drawing, automatic error recovery and a log that rotates by itself.",
  "First Setup.exe built on GitHub."
]},
{"v": "1.3.8", "pt": [
  "Detecção automática do hardware: nomes de CPU, GPU, RAM, VRAM e discos com letras.",
  "Música e vídeo tocando no topo (Spotify, YouTube…).",
  "Escolha da porta da tela e reconexão ao voltar da suspensão.",
  "Brilho e último resumo no ícone da bandeja. O instalador confere Windows, .NET e PawnIO."
], "en": [
  "Automatic hardware detection: CPU, GPU, RAM, VRAM and disk names with letters.",
  "Music and video playing at the top (Spotify, YouTube…).",
  "Choice of the screen port and reconnection after sleep.",
  "Brightness and last summary in the tray icon. The installer checks Windows, .NET and PawnIO."
]},
{"v": "1.3.7", "pt": [
  "Transição em cascata entre o painel e o resumo.",
  "Rede com ping, perda de pacotes e aviso de queda (dizendo se o roteador responde).",
  "Brilho à noite. A tela apaga ao bloquear o PC ou o monitor desligar. Cor de fundo da tela.",
  "O instalador mantém as suas configurações.",
  "Depois: trocar de programa com o jogo aberto não perde mais a sessão; cada jogo tem a sua."
], "en": [
  "Cascade transition between the panel and the summary.",
  "Network with ping, packet loss and outage warning (saying whether the router answers).",
  "Night brightness. The screen turns off when the PC locks or the monitor sleeps. Screen background color.",
  "The installer keeps your settings.",
  "Later: switching apps with a game open no longer loses the session; each game has its own."
]},
{"v": "1.3.6", "pt": [
  "1% low ao lado do frametime e temperatura máxima da partida nos gauges.",
  "Resumo da partida quando o jogo fecha, com tempo ajustável e botão \"Ver como fica\"."
], "en": [
  "1% low next to the frame time and the game's max temperature in the gauges.",
  "Game summary when the game closes, with adjustable time and a \"Preview\" button."
]},
{"v": "1.3.5", "pt": [
  "Só uma Tela! aberta por vez: pergunta se fecha a outra cópia.",
  "FPS a cada 0,2 s, com tempo e média ajustáveis por item."
], "en": [
  "Only one Tela! open at a time: asks before closing the other copy.",
  "FPS every 0.2 s, with time and average adjustable per item."
]},
{"v": "1.3.4", "pt": [
  "Frametime ao lado do FPS e volume do Windows em bloco próprio.",
  "Discos mostram a atividade em tempo real, com a barra do espaço ocupado. Cores editáveis pela janela."
], "en": [
  "Frame time next to the FPS and Windows volume in its own block.",
  "Disks show live activity, with the bar showing used space. Colors editable in the window."
]},
{"v": "1.3.3", "pt": [
  "FPS pelo PresentMon, sem precisar de RTSS ou Afterburner.",
  "Programa em pasta, sem sobras na pasta temporária. Botão Desinstalar."
], "en": [
  "FPS through PresentMon, no RTSS or Afterburner needed.",
  "Program in a folder, nothing left in the temp folder. Uninstall button."
]},
{"v": "1.3.2", "pt": [
  "A tela fica preta ao sair do app e ao desligar ou reiniciar o PC.",
  "Intervalo de atualização por item, com média do período. Liga/desliga das animações."
], "en": [
  "The screen goes black when the app closes and when the PC shuts down or restarts.",
  "Update interval per item, averaging the period. Animations on/off."
]},
{"v": "1.3.1", "pt": [
  "Corrigido o download do monitor de hardware. Versão no título da janela."
], "en": [
  "Fixed the hardware monitor download. Version in the window title."
]},
{"v": "1.3.0", "pt": [
  "Animações suaves: barras e gauges deslizam.",
  "Monitor de hardware embutido, instalador único, início pelo Agendador de Tarefas."
], "en": [
  "Smooth animations: bars and gauges glide.",
  "Embedded hardware monitor, single installer, start through the Task Scheduler."
]},
{"v": "1.2.0", "pt": [
  "Janela com prévia ao vivo, ícone na bandeja e início com o Windows.",
  "Sensores lidos direto do PC, sem abrir o LibreHardwareMonitor. Executável próprio."
], "en": [
  "Window with a live preview, tray icon and start with Windows.",
  "Sensors read directly, without opening LibreHardwareMonitor. Its own executable."
]},
{"v": "1.1.0", "pt": [
  "Primeira versão: painel de sensores no estilo do AIDA64, rodando pelo console."
], "en": [
  "First version: AIDA64-style sensor panel, running from the console."
]}
];

function changelogNotes(entry) {
  return entry[S.lang] || (S.lang === "pt" ? entry.pt : entry.en) || entry.en;
}

function changelogHtml(entries) {
  return entries.map(e => `<section class="cl"><h4>Tela! ${e.v}</h4><ul>${changelogNotes(e).map(n => `<li>${esc(n)}</li>`).join("")}</ul></section>`).join("");
}

function showChangelog() {
  const body = document.createElement("div");
  body.className = "cl-wrap";
  body.innerHTML = changelogHtml(CHANGELOG);
  openModal({ title: t("cl.title"), body, buttons: [{ label: t("modal.close"), primary: true }] });
}

// after an update: the notes of every version newer than the one that was installed
function showWhatsNew(from) {
  const vt = v => (v || "0").split(".").map(Number);
  const gt = (a, b) => { const x = vt(a), y = vt(b); for (let i = 0; i < 3; i++) { if ((x[i] || 0) !== (y[i] || 0)) return (x[i] || 0) > (y[i] || 0); } return false; };
  const list = CHANGELOG.filter(e => gt(e.v, from) && !gt(e.v, S.init.version));
  if (!list.length) return;
  const body = document.createElement("div");
  body.className = "cl-wrap";
  body.innerHTML = changelogHtml(list);
  openModal({ title: t("cl.updated", { v: S.init.version }), body, buttons: [
    { label: t("cl.all"), onClick: () => { showChangelog(); return false; } },
    { label: t("modal.close"), primary: true }] });
}
