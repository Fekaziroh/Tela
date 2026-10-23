"use strict";
// Patch notes, newest first. Source for the window, CHANGELOG.md and the release notes
// (installer/changelog.py). Keep it valid JSON between "= " and the final ";".
// Each language has categories: new, fix, perf (performance), look (appearance and personalization).
// "draft": true = still being worked on (no release). "beta": true = published as a test version (GitHub
// pre-release, only for "Receive test versions"); removing "beta" later promotes it to the stable release.
const CHANGELOG = [
{"v": "1.4.3",
 "pt": {
  "new": [
   "Editor de layout por elemento: com um bloco selecionado, clique em qualquer elemento (valor, gauge, texto, relógio, logos, FPS...) para movê-lo, redimensioná-lo, girá-lo ou apagá-lo. A barra do topo também pode ser editada item por item.",
   "Elementos para arrastar até a tela: dentro de um bloco eles entram no bloco; fora, viram um bloco novo.",
   "Fonte e tamanho do texto por elemento.",
   "Ao apagar ou redimensionar um bloco, os vizinhos se ajustam sozinhos (dá para desligar).",
   "Desligar a tela num horário, como o brilho à noite.",
   "Voltar para uma versão anterior em Avançado › Atualizações, com a opção de não receber de novo a versão que não agradou.",
   "Opção de receber versões de teste antes de saírem para todos.",
   "Seção Sobre em Avançado, com licença, créditos e links do projeto."
  ],
  "fix": [
   "Ao desligar a mídia (ou o FPS) na barra do topo, o lugar ficava vazio; agora os logos aparecem nele.",
   "Os elementos da barra do topo tinham nomes repetidos e pouco claros no editor."
  ],
  "look": [
   "Intervalo de cada item separado por grupos (CPU, GPU, RAM, Discos, Rede), mostrando primeiro só o que é diferente do padrão.",
   "Brilho à noite com o horário em cima da barra, em 24 h.",
   "Uso de CPU e memória da Tela! numa segunda linha ao passar o mouse no ícone da bandeja.",
   "Notas de versão com mais espaço entre as versões.",
   "Em Aparência, as opções da tela vêm primeiro e o tema da janela fica por último."
  ]
 },
 "en": {
  "new": [
   "Element-level layout editor: with a block selected, click any element (value, gauge, text, clock, logos, FPS...) to move, resize, rotate or delete it. The top bar can be edited item by item too.",
   "Elements to drag onto the screen: inside a block they join the block; outside, they become a new block.",
   "Font and text size per element.",
   "When a block is deleted or resized, its neighbours adjust by themselves (can be turned off).",
   "Turn the screen off at set hours, like the night brightness.",
   "Go back to an older version in Advanced › Updates, with an option not to be offered the version you did not like again.",
   "Option to receive test versions before they go out to everyone.",
   "About section in Advanced, with license, credits and project links."
  ],
  "fix": [
   "Turning off the media (or the FPS) in the top bar left an empty space; the logos now show there.",
   "Top bar elements had repeated, unclear names in the editor."
  ],
  "look": [
   "Interval per item split into groups (CPU, GPU, RAM, Disks, Network), showing first only what differs from the default.",
   "Night brightness with the hours above the slider, in 24 h.",
   "Tela!'s CPU and memory use on a second line when hovering the tray icon.",
   "More space between versions in the patch notes.",
   "In Appearance, the screen options come first and the window theme last."
  ]
 }},
{"v": "1.4.2",
 "pt": {
  "new": [
   "Predefinições em Configurações: Performance (menos CPU e memória), Padrão e Personalizado, que fica marcado sozinho quando você muda uma dessas opções.",
   "Perfis: salve as configurações e os layouts com um nome, troque entre eles e exporte ou importe para levar a outro PC.",
   "Aviso de nova versão também no ícone da bandeja, com a opção de atualizar pelo menu dele.",
   "A Tela! avisa quando a tela conectada é de um modelo que ainda não é suportado."
  ],
  "fix": [
   "O tema automático usava o grafite no lugar do preto com o Windows no modo escuro.",
   "O ícone da bandeja (logo, CPU ou GPU) só mudava depois de reiniciar o app."
  ],
  "perf": [
   "Qualidade do desenho (alta ou normal) e prévia ao vivo na janela podem ser desligadas para economizar CPU."
  ],
  "look": [
   "A barra de título da janela segue o tema (com a cor do tema no Windows 11; clara ou escura no Windows 10).",
   "Brilho à noite com a porcentagem ao lado da barra.",
   "O histórico guarda as últimas 15 partidas por padrão e avisa antes de apagar quando você diminui o número.",
   "Notas de versão separadas por categoria."
  ]
 },
 "en": {
  "new": [
   "Presets in Settings: Performance (less CPU and memory), Default and Custom, which is selected by itself when you change one of these options.",
   "Profiles: save the settings and layouts under a name, switch between them and export or import them to take to another PC.",
   "New version notice in the tray icon too, with an option to update from its menu.",
   "Tela! tells you when the connected screen is a model that is not supported yet."
  ],
  "fix": [
   "The automatic theme used graphite instead of black with Windows in dark mode.",
   "The tray icon (logo, CPU or GPU) only changed after restarting the app."
  ],
  "perf": [
   "Drawing quality (high or normal) and the live preview in the window can be turned down to save CPU."
  ],
  "look": [
   "The window title bar follows the theme (theme color on Windows 11; light or dark on Windows 10).",
   "Night brightness with the percentage next to the slider.",
   "The history keeps the last 15 games by default and asks before deleting when you lower the number.",
   "Patch notes split into categories."
  ]
 }},
{"v": "1.4.1",
 "pt": {
  "new": [
   "Histórico de partidas: cada resumo de jogo fica salvo, com busca, gráfico de FPS, opção de mostrar de novo na tela, apagar e exportar em CSV. Você escolhe quantas guardar e a pasta.",
   "Atualizações pelo app: a Tela! avisa quando sai uma versão nova e instala com um clique.",
   "Notas de todas as versões em Avançado e um resumo do que mudou depois de cada atualização.",
   "Tema de cores da tela personalizado, separado dos prontos."
  ],
  "fix": [
   "A imagem de fundo às vezes continuava na tela depois de removida.",
   "A tela podia perder a conexão durante uma transição.",
   "O medidor de FPS volta sozinho quando para de responder e mostra o motivo quando não inicia.",
   "O instalador dava erro 740 ao abrir a Tela! no final."
  ],
  "perf": [
   "A janela usa bem menos memória."
  ],
  "look": [
   "A mídia some 5 s depois de pausar, com transição. Com o jogo aberto, mesmo minimizado, ela continua à direita.",
   "Transição em blocos também ao sair do resumo de jogo.",
   "Tema escuro padrão da janela agora é o Preto. Ajustes de organização em Início e Configurações."
  ]
 },
 "en": {
  "new": [
   "Game history: every game summary is saved, with search, FPS graph, an option to show it on the screen again, delete and export to CSV. You choose how many to keep and the folder.",
   "Updates from the app: Tela! tells you when a new version is out and installs it with one click.",
   "Notes for every version in Advanced and a summary of what changed after each update.",
   "Custom screen color theme, separate from the ready-made ones."
  ],
  "fix": [
   "The background picture sometimes stayed on the screen after removing it.",
   "The screen could lose its connection during a transition.",
   "The FPS meter recovers by itself when it stops responding and shows why when it cannot start.",
   "The setup showed error 740 when opening Tela! at the end."
  ],
  "perf": [
   "The window uses much less memory."
  ],
  "look": [
   "Media hides 5 s after pausing, with a transition. While a game is open, even minimized, it stays on the right.",
   "Block transition also when leaving the game summary.",
   "The default dark window theme is now Black. Tidier Home and Settings."
  ]
 }},
{"v": "1.4.0",
 "pt": {
  "new": [
   "Janela nova, em português, inglês, espanhol e chinês.",
   "Editor de layout: arrastar, redimensionar, ligar e desligar blocos, renomear e escolher sensores numa lista ao vivo.",
   "Tela na vertical, além da horizontal, e as duas invertidas.",
   "Instalador de verdade: não precisa de Python, baixa o PawnIO e o WebView2 só se faltarem e guarda as configurações em %APPDATA%\\Tela.",
   "Assistente na primeira abertura, que traz as configurações das versões antigas."
  ],
  "look": [
   "Temas da janela (automático, prontos ou com as suas cores), temas de cores da tela e imagem de fundo."
  ]
 },
 "en": {
  "new": [
   "New window, in Portuguese, English, Spanish and Chinese.",
   "Layout editor: drag, resize, turn blocks on and off, rename and pick sensors from a live list.",
   "Portrait screen as well as landscape, and both flipped.",
   "A real installer: no Python needed, downloads PawnIO and WebView2 only when missing and keeps the settings in %APPDATA%\\Tela.",
   "First-run assistant that brings the settings from older versions."
  ],
  "look": [
   "Window themes (automatic, ready-made or your own colors), screen color themes and background picture."
  ]
 }},
{"v": "1.3.9",
 "pt": {
  "new": ["Primeiro instalador (Setup.exe) gerado no GitHub."],
  "fix": ["Recuperação automática de erros e registro de atividade que se organiza sozinho."],
  "perf": ["Desenho da tela mais leve."]
 },
 "en": {
  "new": ["First setup (Setup.exe) built on GitHub."],
  "fix": ["Automatic error recovery and an activity log that keeps itself tidy."],
  "perf": ["Lighter screen drawing."]
 }},
{"v": "1.3.8",
 "pt": {
  "new": [
   "Detecção automática do hardware: nomes de CPU, GPU, RAM, VRAM e discos com letras.",
   "Música e vídeo tocando no topo da tela (Spotify, YouTube e outros).",
   "Escolha da porta da tela, brilho e último resumo pelo ícone da bandeja."
  ],
  "fix": ["A tela reconecta sozinha ao voltar da suspensão. O instalador confere o Windows, o .NET e o PawnIO."]
 },
 "en": {
  "new": [
   "Automatic hardware detection: CPU, GPU, RAM, VRAM and disk names with letters.",
   "Music and video playing at the top of the screen (Spotify, YouTube and others).",
   "Screen port choice, brightness and last summary from the tray icon."
  ],
  "fix": ["The screen reconnects by itself after sleep. The installer checks Windows, .NET and PawnIO."]
 }},
{"v": "1.3.7",
 "pt": {
  "new": [
   "Rede com ping, perda de pacotes e aviso de queda, dizendo se o roteador responde.",
   "Brilho à noite. A tela apaga quando o PC é bloqueado ou o monitor desliga."
  ],
  "fix": [
   "O instalador mantém as suas configurações.",
   "Trocar de programa com o jogo aberto não perde mais a sessão; cada jogo tem a sua."
  ],
  "look": ["Transição em cascata entre o painel e o resumo. Cor de fundo da tela."]
 },
 "en": {
  "new": [
   "Network with ping, packet loss and outage warning, saying whether the router answers.",
   "Night brightness. The screen turns off when the PC locks or the monitor sleeps."
  ],
  "fix": [
   "The installer keeps your settings.",
   "Switching apps with a game open no longer loses the session; each game has its own."
  ],
  "look": ["Cascade transition between the panel and the summary. Screen background color."]
 }},
{"v": "1.3.6",
 "pt": {
  "new": [
   "Resumo da partida quando o jogo fecha, com tempo ajustável e botão \"Ver como fica\".",
   "1% low ao lado do frame time e temperatura máxima da partida nos gauges."
  ]
 },
 "en": {
  "new": [
   "Game summary when the game closes, with adjustable time and a \"Preview\" button.",
   "1% low next to the frame time and the game's max temperature in the gauges."
  ]
 }},
{"v": "1.3.5",
 "pt": {
  "new": ["Intervalo e média do FPS ajustáveis, atualizando a cada 0,2 s."],
  "fix": ["Só uma Tela! aberta por vez: ela pergunta antes de fechar a outra cópia."]
 },
 "en": {
  "new": ["Adjustable FPS interval and average, updating every 0.2 s."],
  "fix": ["Only one Tela! open at a time: it asks before closing the other copy."]
 }},
{"v": "1.3.4",
 "pt": {
  "new": [
   "Frame time ao lado do FPS e volume do Windows em um bloco próprio.",
   "Discos mostram a atividade em tempo real, com a barra do espaço ocupado."
  ],
  "look": ["Cores da tela editáveis pela janela."]
 },
 "en": {
  "new": [
   "Frame time next to the FPS and Windows volume in its own block.",
   "Disks show live activity, with the bar showing used space."
  ],
  "look": ["Screen colors editable in the window."]
 }},
{"v": "1.3.3",
 "pt": {
  "new": ["FPS pelo PresentMon, sem precisar do RTSS ou do Afterburner.", "Botão Desinstalar."],
  "perf": ["Programa em pasta, sem sobras na pasta temporária."]
 },
 "en": {
  "new": ["FPS through PresentMon, no RTSS or Afterburner needed.", "Uninstall button."],
  "perf": ["Program in a folder, nothing left in the temp folder."]
 }},
{"v": "1.3.2",
 "pt": {
  "new": ["Intervalo de atualização por item, mostrando a média do período.", "Opção de ligar e desligar as animações."],
  "fix": ["A tela fica preta ao fechar o app e ao desligar ou reiniciar o PC."]
 },
 "en": {
  "new": ["Update interval per item, showing the average of the period.", "Option to turn animations on and off."],
  "fix": ["The screen goes black when the app closes and when the PC shuts down or restarts."]
 }},
{"v": "1.3.1",
 "pt": {
  "fix": ["O download do monitor de hardware voltou a funcionar."],
  "look": ["Versão no título da janela."]
 },
 "en": {
  "fix": ["The hardware monitor download works again."],
  "look": ["Version in the window title."]
 }},
{"v": "1.3.0",
 "pt": {
  "new": ["Monitor de hardware embutido, instalador único e início pelo Agendador de Tarefas."],
  "look": ["Animações suaves: barras e gauges deslizam."]
 },
 "en": {
  "new": ["Embedded hardware monitor, single installer and start through the Task Scheduler."],
  "look": ["Smooth animations: bars and gauges glide."]
 }},
{"v": "1.2.0",
 "pt": {
  "new": [
   "Janela com prévia ao vivo, ícone na bandeja e início com o Windows.",
   "Sensores lidos direto do PC, sem abrir o LibreHardwareMonitor, e executável próprio."
  ]
 },
 "en": {
  "new": [
   "Window with a live preview, tray icon and start with Windows.",
   "Sensors read directly, without opening LibreHardwareMonitor, and its own executable."
  ]
 }},
{"v": "1.1.0",
 "pt": {"new": ["Primeira versão: painel de sensores no estilo do AIDA64, rodando pelo console."]},
 "en": {"new": ["First version: AIDA64-style sensor panel, running from the console."]}}
];

const CL_CATEGORIES = ["new", "fix", "perf", "look"];

function changelogNotes(entry) {
  return entry[S.lang] || (S.lang === "pt" ? entry.pt : entry.en) || entry.en;
}

function changelogHtml(entries) {
  return entries.map(e => {
    const notes = changelogNotes(e);
    const groups = CL_CATEGORIES.filter(c => (notes[c] || []).length).map(c =>
      `<h5>${t("cl.cat_" + c)}</h5><ul>${notes[c].map(n => `<li>${esc(n)}</li>`).join("")}</ul>`).join("");
    return `<section class="cl"><h4>Tela! ${e.v}</h4>${groups}</section>`;
  }).join("");
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
