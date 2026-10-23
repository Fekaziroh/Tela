"use strict";
// Patch notes, newest first. Source for the window, CHANGELOG.md and the release notes
// (installer/changelog.py). Keep it valid JSON between "= " and the final ";".
// Each language has categories: new, fix, perf (performance), look (appearance and personalization).
// "draft": true = still being worked on (no release). "beta": true = published as a test version (GitHub
// pre-release, only for "Receive test versions"); removing "beta" later promotes it to the stable release.
const CHANGELOG = [
{
 "v": "1.4.6",
 "beta": true,
 "pt": {
  "new": [
   "Temas da tela (Aparência): Clean, Completo, Cockpit, Linhas e Retrô, com formatos diferentes e não só cores, cada um na horizontal e na vertical. Passe o mouse num tema para ver a prévia e clique para usar.",
   "Salve a tela do seu jeito como um tema novo, exporte e importe arquivos .tela-theme para compartilhar. As mudanças do Layout e as cores ficam guardadas em cada tema, e “Restaurar original” desfaz.",
   "Clima ao lado da data: temperatura e céu da sua cidade (Configurações › Clima, pelo Open-Meteo; só o nome da cidade sai do PC).",
   "Textos da tela editáveis (ex.: CONSUMO por POTÊNCIA) e título do bloco dos discos automático (SSD, HD ou Discos) ou do seu jeito.",
   "Resumo da partida personalizável: escolha FPS, temperaturas, gráfico (em cima ou embaixo) e duração; o que fica aparece maior.",
   "Editor: copiar, colar e duplicar (Ctrl+C / Ctrl+V / Ctrl+D), guias de alinhamento ao arrastar (com Shift move livre, sem grade), zoom (Ctrl+roda do mouse) com grade, e ajuste automático dos elementos dentro do bloco ao apagar ou redimensionar um deles.",
   "Reconectar a tela e Reiniciar a Tela! no menu da bandeja e em Avançado, para quando algo travar. Liberar a tela para outro programa e Liberar memória da janela também no menu da bandeja.",
   "Voltar para outra versão mostra o tamanho de cada uma."
  ],
  "fix": [
   "Sem jogo aberto, a música às vezes ia para a direita e o logo ficava no lugar dela: um programa que tinha mostrado FPS continuava contando como jogo. Agora só conta um jogo que ainda tem janela (minimizado também) e teve FPS na última meia hora.",
   "Pausar agora só congela a tela; ao continuar, ela segue de onde parou sem redesenhar tudo. Liberar a tela para outro programa virou uma opção separada.",
   "As notificações do Windows mostram só “Tela!” como nome do app."
  ],
  "look": [
   "Novo tema padrão, Clean, inspirado na primeira versão: logos nas pontas, relógio grande no meio, painéis de CPU e GPU mais limpos e um bloco só para rede e volume. Quem já usava continua com o layout de antes (agora o tema Completo) e recebe um aviso.",
   "Aparência reorganizada: Temas da tela, Cores e fundo juntos, Logos e Tema da janela. Textos da janela mais diretos (ex.: “Fundo”)."
  ]
 },
 "en": {
  "new": [
   "Screen themes (Appearance): Clean, Full, Cockpit, Lines and Retro, with different shapes and not just colors, each in landscape and portrait. Hover a theme to preview it and click to use it.",
   "Save the screen your way as a new theme, export and import .tela-theme files to share. Layout changes and colors are kept per theme, and “Restore original” undoes them.",
   "Weather next to the date: temperature and sky for your city (Settings › Weather, from Open-Meteo; only the city name leaves the PC).",
   "Editable screen texts (e.g. POWER to WATTS) and a disks block title that is automatic (SSD, HD or Disks) or your own.",
   "Customizable game summary: choose FPS, temperatures, graph (top or bottom) and duration; what stays shows bigger.",
   "Editor: copy, paste and duplicate (Ctrl+C / Ctrl+V / Ctrl+D), alignment guides while dragging (Shift moves freely, without the grid), zoom (Ctrl+mouse wheel) with a grid, and automatic adjustment of the elements inside a block when one is deleted or resized.",
   "Reconnect the screen and Restart Tela! in the tray menu and in Advanced, for when something gets stuck. Release the screen for another program and Free the window's memory also in the tray menu.",
   "Going back to another version shows the size of each one."
  ],
  "fix": [
   "With no game open, the music sometimes moved to the right and the logo took its place: a program that had shown FPS kept counting as a game. Now only a game that still has a window (minimized too) and had FPS in the last half hour counts.",
   "Pause now only freezes the screen; when resumed it carries on without redrawing everything. Releasing the screen for another program is a separate option.",
   "Windows notifications show just “Tela!” as the app name."
  ],
  "look": [
   "New default theme, Clean, inspired by the first version: logos at the ends, a big clock in the middle, cleaner CPU and GPU panels and one block for network and volume. If you already used Tela!, you keep your layout (now the Full theme) and get a notice.",
   "Appearance reorganized: Screen themes, Colors and background together, Logos and Window theme."
  ]
 },
 "es": {
  "new": [
   "Temas de la pantalla (Apariencia): Clean, Completo, Cockpit, Líneas y Retro, con formas diferentes y no solo colores, cada uno en horizontal y vertical. Pasa el ratón sobre un tema para ver la vista previa y haz clic para usarlo.",
   "Guarda la pantalla a tu manera como un tema nuevo, exporta e importa archivos .tela-theme para compartir. Los cambios del Diseño y los colores se guardan en cada tema, y “Restaurar original” los deshace.",
   "Clima junto a la fecha: temperatura y cielo de tu ciudad (Ajustes › Clima, de Open-Meteo; solo el nombre de la ciudad sale del PC).",
   "Textos de la pantalla editables (ej.: CONSUMO por POTENCIA) y título del bloque de discos automático (SSD, HD o Discos) o a tu manera.",
   "Resumen de la partida personalizable: elige FPS, temperaturas, gráfico (arriba o abajo) y duración; lo que queda se ve más grande.",
   "Editor: copiar, pegar y duplicar (Ctrl+C / Ctrl+V / Ctrl+D), guías de alineación al arrastrar (con Shift se mueve libre, sin cuadrícula), zoom (Ctrl+rueda) con cuadrícula y ajuste automático de los elementos dentro del bloque al borrar o redimensionar uno.",
   "Reconectar la pantalla y Reiniciar Tela! en el menú de la bandeja y en Avanzado, para cuando algo se trabe. Liberar la pantalla para otro programa y Liberar la memoria de la ventana también en el menú de la bandeja.",
   "Volver a otra versión muestra el tamaño de cada una."
  ],
  "fix": [
   "Sin juego abierto, la música a veces iba a la derecha y el logo se quedaba en su lugar: un programa que había mostrado FPS seguía contando como juego. Ahora solo cuenta un juego que aún tiene ventana (minimizado también) y tuvo FPS en la última media hora.",
   "Pausar ahora solo congela la pantalla; al continuar sigue desde donde estaba sin redibujar todo. Liberar la pantalla para otro programa es una opción aparte.",
   "Las notificaciones de Windows muestran solo “Tela!” como nombre de la app."
  ],
  "look": [
   "Nuevo tema predeterminado, Clean, inspirado en la primera versión: logos en los extremos, reloj grande en el centro, paneles de CPU y GPU más limpios y un solo bloque para red y volumen. Quien ya lo usaba conserva su diseño (ahora el tema Completo) y recibe un aviso.",
   "Apariencia reorganizada: Temas de la pantalla, Colores y fondo juntos, Logos y Tema de la ventana."
  ]
 },
 "zh": {
  "new": [
   "屏幕主题（外观）：Clean、完整、仪表、曲线和复古，不只是颜色，布局也各不相同，每个都支持横屏和竖屏。鼠标悬停可预览，点击即可使用。",
   "可将自己调整的屏幕另存为新主题，并导出、导入 .tela-theme 文件进行分享。布局修改和颜色按主题分别保存，“恢复原样”可撤销。",
   "日期旁显示天气：你所在城市的温度和天气（设置 › 天气，数据来自 Open-Meteo；只有城市名称会发送到网络）。",
   "屏幕文字可编辑（例如把“功耗”改成“功率”），磁盘区块标题可自动（SSD、HD 或 磁盘）或自定义。",
   "游戏总结可自定义：选择 FPS、温度、曲线（上方或下方）和时长；保留的内容显示得更大。",
   "编辑器：复制、粘贴和复制一份（Ctrl+C / Ctrl+V / Ctrl+D），拖动时显示对齐参考线（按住 Shift 自由移动，不受网格限制），缩放（Ctrl+鼠标滚轮）并可显示网格；删除或调整元素大小时，区块内的其他元素自动调整。",
   "托盘菜单和高级页面新增“重新连接屏幕”和“重启 Tela!”，在卡住时使用。托盘菜单也新增“释放屏幕给其他程序”和“释放窗口内存”。",
   "回退到其他版本时会显示每个版本的大小。"
  ],
  "fix": [
   "没有打开游戏时，音乐有时会移到右侧，左侧仍显示徽标：曾显示过 FPS 的程序一直被当作游戏。现在只有仍有窗口（包括最小化）且在最近半小时内有 FPS 的游戏才算。",
   "暂停现在只会冻结屏幕；继续后从原处接着显示，不再全部重绘。“释放屏幕给其他程序”成为单独的选项。",
   "Windows 通知中的应用名称只显示“Tela!”。"
  ],
  "look": [
   "新的默认主题 Clean，灵感来自第一个版本：两端是徽标，中间是大时钟，CPU 和 GPU 面板更简洁，网络和音量合为一个区块。老用户保留原来的布局（现在是“完整”主题），并会收到提示。",
   "外观页面重新整理：屏幕主题、颜色与背景、徽标和窗口主题。"
  ]
 }
},
{
 "v": "1.4.5",
 "beta": true,
 "pt": {
  "new": [
   "Primeira abertura: se outro programa da tela estiver aberto (como o app original), o assistente avisa e oferece fechá-lo."
  ],
  "fix": [
   "Títulos de música em japonês, chinês ou coreano apareciam como quadradinhos na tela.",
   "No editor, o nome e a posição do elemento aparecem embaixo da tela também ao clicar nele, não só ao mover."
  ],
  "look": [
   "Na vertical, o frame time fica embaixo da música e o FPS ganha mais espaço. Layouts antigos sem mudança nesses itens são atualizados sozinhos."
  ]
 },
 "en": {
  "new": [
   "First run: if another screen program is open (such as the original app), the assistant tells you and offers to close it."
  ],
  "fix": [
   "Music titles in Japanese, Chinese or Korean showed as boxes on the screen.",
   "In the editor, the element's name and position show under the screen when you click it too, not only while moving it."
  ],
  "look": [
   "In portrait, the frame time sits under the music and the FPS gets more room. Older layouts that kept these items unchanged are updated by themselves."
  ]
 },
 "es": {
  "new": [
   "Primer inicio: si otro programa de la pantalla está abierto (como la app original), el asistente avisa y ofrece cerrarlo."
  ],
  "fix": [
   "Los títulos de música en japonés, chino o coreano aparecían como cuadritos en la pantalla.",
   "En el editor, el nombre y la posición del elemento aparecen bajo la pantalla también al hacer clic, no solo al moverlo."
  ],
  "look": [
   "En vertical, el frame time queda bajo la música y los FPS tienen más espacio. Los diseños antiguos sin cambios en esos elementos se actualizan solos."
  ]
 },
 "zh": {
  "new": [
   "首次运行：如果屏幕的其他程序（例如原厂应用）正在运行，向导会提示并提供关闭选项。"
  ],
  "fix": [
   "日文、中文或韩文的音乐标题在屏幕上显示为方框。",
   "在编辑器中，点击元素时屏幕下方也会显示其名称和位置，而不仅是在移动时。"
  ],
  "look": [
   "竖屏时，帧时间显示在音乐下方，FPS 有更多空间。未改动这些项目的旧布局会自动更新。"
  ]
 }
},
{"v": "1.4.4",
 "pt": {
  "new": [
   "Alertas de temperatura: um aviso discreto do Windows quando o CPU ou a GPU passa do limite que você escolher por um tempo, sem repetir toda hora.",
   "Quando outro programa (como o app original da tela) está usando a tela, a Tela! avisa qual é e oferece fechá-lo para assumir.",
   "Busca em Configurações.",
   "Orientação da tela na aba Layout e um atalho Horizontal/Vertical no Início.",
   "No editor: Shift seleciona vários blocos para mover ou apagar juntos; Esc tira a seleção; Delete e Backspace apagam.",
   "Opção de liberar a memória da janela enquanto ela fica na bandeja (ligada na predefinição Performance).",
   "Tempo entre as buscas de atualização ajustável (2 a 24 horas)."
  ],
  "fix": [
   "As notas de versão em espanhol e chinês apareciam em inglês.",
   "Atualizar ou voltar de versão agora apaga também as pastas antigas do monitor de hardware e do PresentMon, e os instaladores baixados não ficam acumulados na pasta temporária."
  ],
  "look": [
   "Na vertical, a mídia ocupa o lugar da data durante o jogo e o frame time fica embaixo do FPS.",
   "Frame time maior na horizontal, com tamanho dos números, segundos e posição (em cima ou ao lado) ajustáveis no editor.",
   "No editor, o bloco selecionado sobe para o topo da coluna e o conteúdo dele fica legível."
  ]
 },
 "en": {
  "new": [
   "Temperature alerts: a discreet Windows notice when the CPU or GPU stays above the limit you choose for a while, without repeating all the time.",
   "When another program (such as the screen's original app) is using the screen, Tela! tells you which one and offers to close it and take over.",
   "Search in Settings.",
   "Screen orientation in the Layout tab and a Landscape/Portrait shortcut on Home.",
   "In the editor: Shift selects several blocks to move or delete together; Esc clears the selection; Delete and Backspace delete.",
   "Option to free the window's memory while it is in the tray (on in the Performance preset).",
   "Adjustable time between update checks (2 to 24 hours)."
  ],
  "fix": [
   "The patch notes in Spanish and Chinese showed in English.",
   "Updating or going back to another version now also removes the old hardware monitor and PresentMon folders, and downloaded setups no longer pile up in the temp folder."
  ],
  "look": [
   "In portrait, the media takes the date's place during a game and the frame time sits below the FPS.",
   "Bigger frame time in landscape, with number size, seconds and position (above or beside) adjustable in the editor.",
   "In the editor, the selected block moves to the top of the side column and its content stays readable."
  ]
 },
 "es": {
  "new": [
   "Alertas de temperatura: un aviso discreto de Windows cuando la CPU o la GPU se mantiene por encima del límite que elijas durante un tiempo, sin repetirse a cada rato.",
   "Cuando otro programa (como la app original de la pantalla) está usando la pantalla, Tela! te dice cuál es y ofrece cerrarlo para usarla.",
   "Búsqueda en Ajustes.",
   "Orientación de la pantalla en la pestaña Diseño y un atajo Horizontal/Vertical en Inicio.",
   "En el editor: Mayús selecciona varios bloques para moverlos o borrarlos juntos; Esc quita la selección; Supr y Retroceso borran.",
   "Opción de liberar la memoria de la ventana mientras está en la bandeja (activada en la predefinición Rendimiento).",
   "Tiempo entre búsquedas de actualizaciones ajustable (de 2 a 24 horas)."
  ],
  "fix": [
   "Las notas de versión en español y chino aparecían en inglés.",
   "Actualizar o volver a otra versión ahora también borra las carpetas antiguas del monitor de hardware y de PresentMon, y los instaladores descargados ya no se acumulan en la carpeta temporal."
  ],
  "look": [
   "En vertical, la multimedia ocupa el lugar de la fecha durante el juego y el frame time queda debajo de los FPS.",
   "Frame time más grande en horizontal, con tamaño de los números, segundos y posición (encima o al lado) ajustables en el editor.",
   "En el editor, el bloque seleccionado sube al principio de la columna y su contenido se lee bien."
  ]
 },
 "zh": {
  "new": [
   "温度警报：CPU 或 GPU 持续超过你设定的上限一段时间后，显示一次低调的 Windows 通知，不会反复提醒。",
   "当其他程序（如屏幕自带的应用）占用屏幕时，Tela! 会告诉你是哪个程序，并可关闭它来接管屏幕。",
   "设置中的搜索。",
   "屏幕方向移到“布局”选项卡，主页新增横屏/竖屏快捷切换。",
   "编辑器中：按住 Shift 可选择多个方块一起移动或删除；Esc 取消选择；Delete 和 Backspace 可删除。",
   "可选择在窗口位于托盘时释放其内存（“性能”预设中默认开启）。",
   "检查更新的间隔可调（2 到 24 小时）。"
  ],
  "fix": [
   "西班牙语和中文的版本说明显示为英文。",
   "更新或回到其他版本时，现在也会删除旧的硬件监控和 PresentMon 文件夹，下载的安装程序不再堆积在临时文件夹中。"
  ],
  "look": [
   "竖屏时，游戏中媒体显示在日期位置，帧时间位于 FPS 下方。",
   "横屏的帧时间图更大，可在编辑器中调整数字大小、秒数和位置（上方或旁边）。",
   "编辑器中，所选方块会移到侧栏顶部，其内容清晰可读。"
  ]
 }},
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
 },
 "es": {
  "new": [
   "Editor de diseño por elemento: con un bloque seleccionado, haz clic en cualquier elemento (valor, indicador, texto, reloj, logos, FPS...) para moverlo, redimensionarlo, girarlo o borrarlo. La barra superior también se edita elemento por elemento.",
   "Elementos para arrastrar a la pantalla: dentro de un bloque entran en el bloque; fuera, se convierten en un bloque nuevo.",
   "Fuente y tamaño del texto por elemento.",
   "Al borrar o redimensionar un bloque, los vecinos se ajustan solos (se puede desactivar).",
   "Apagar la pantalla en un horario, como el brillo nocturno.",
   "Volver a una versión anterior en Avanzado › Actualizaciones, con la opción de no volver a recibir la versión que no te gustó.",
   "Opción de recibir versiones de prueba antes de que salgan para todos.",
   "Sección Acerca de en Avanzado, con licencia, créditos y enlaces del proyecto."
  ],
  "fix": [
   "Al desactivar la multimedia (o los FPS) en la barra superior quedaba un hueco; ahora aparecen los logos.",
   "Los elementos de la barra superior tenían nombres repetidos y poco claros en el editor."
  ],
  "look": [
   "Intervalo de cada elemento separado por grupos (CPU, GPU, RAM, Discos, Red), mostrando primero solo lo que difiere del predeterminado.",
   "Brillo nocturno con el horario encima de la barra, en formato 24 h.",
   "Uso de CPU y memoria de Tela! en una segunda línea al pasar el ratón por el icono de la bandeja.",
   "Más espacio entre versiones en las notas de versión.",
   "En Apariencia, las opciones de la pantalla van primero y el tema de la ventana al final."
  ]
 },
 "zh": {
  "new": [
   "按元素编辑布局：选中一个方块后，点击任意元素（数值、仪表、文字、时钟、徽标、FPS……）即可移动、调整大小、旋转或删除。顶部栏也可以逐项编辑。",
   "可拖到屏幕上的元素：放进方块内即加入该方块；放在外面则成为新方块。",
   "每个元素可单独设置字体和字号。",
   "删除或调整方块大小时，相邻方块会自动调整（可关闭）。",
   "可在指定时间关闭屏幕，类似夜间亮度。",
   "可在 高级 › 更新 中回到旧版本，并可选择不再提供你不喜欢的版本。",
   "可选择在正式发布前接收测试版。",
   "高级 中新增“关于”部分，包含许可证、致谢和项目链接。"
  ],
  "fix": [
   "在顶部栏关闭媒体（或 FPS）后会留下空白；现在会在该位置显示徽标。",
   "编辑器中顶部栏元素的名称重复且不清楚。"
  ],
  "look": [
   "各项更新间隔按组（CPU、GPU、内存、磁盘、网络）分开，先只显示与默认不同的项。",
   "夜间亮度的时间显示在滑块上方，采用 24 小时制。",
   "鼠标悬停在托盘图标上时，第二行显示 Tela! 的 CPU 和内存占用。",
   "版本说明中各版本之间留出更多空间。",
   "在“外观”中，屏幕选项排在前面，窗口主题放在最后。"
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
 },
 "es": {
  "new": [
   "Predefiniciones en Ajustes: Rendimiento (menos CPU y memoria), Predeterminado y Personalizado, que se selecciona solo cuando cambias una de estas opciones.",
   "Perfiles: guarda los ajustes y diseños con un nombre, cambia entre ellos y expórtalos o impórtalos para llevarlos a otro PC.",
   "Aviso de nueva versión también en el icono de la bandeja, con la opción de actualizar desde su menú.",
   "Tela! avisa cuando la pantalla conectada es un modelo aún no compatible."
  ],
  "fix": [
   "El tema automático usaba grafito en lugar de negro con Windows en modo oscuro.",
   "El icono de la bandeja (logo, CPU o GPU) solo cambiaba después de reiniciar la app."
  ],
  "perf": [
   "La calidad del dibujo (alta o normal) y la vista previa en vivo de la ventana se pueden reducir para ahorrar CPU."
  ],
  "look": [
   "La barra de título de la ventana sigue el tema (color del tema en Windows 11; clara u oscura en Windows 10).",
   "Brillo nocturno con el porcentaje junto a la barra.",
   "El historial guarda las últimas 15 partidas por defecto y pregunta antes de borrar cuando reduces el número.",
   "Notas de versión separadas por categorías."
  ]
 },
 "zh": {
  "new": [
   "设置中的预设：性能（更少 CPU 和内存）、默认和自定义；更改其中任一选项时会自动选中“自定义”。",
   "配置文件：以名称保存设置和布局，可在它们之间切换，也可导出或导入到另一台电脑。",
   "托盘图标也会提示新版本，并可从其菜单直接更新。",
   "连接的屏幕型号尚不受支持时，Tela! 会提示。"
  ],
  "fix": [
   "Windows 深色模式下，自动主题使用了石墨色而不是黑色。",
   "托盘图标（徽标、CPU 或 GPU）只有在重启应用后才会改变。"
  ],
  "perf": [
   "可降低绘制质量（高或普通）并关闭窗口中的实时预览，以节省 CPU。"
  ],
  "look": [
   "窗口标题栏跟随主题（Windows 11 使用主题颜色；Windows 10 为浅色或深色）。",
   "夜间亮度的百分比显示在滑块旁边。",
   "历史记录默认保留最近 15 局，减少数量前会先确认。",
   "版本说明按类别分开。"
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
 },
 "es": {
  "new": [
   "Historial de partidas: cada resumen de juego se guarda, con búsqueda, gráfico de FPS, opción de volver a mostrarlo en la pantalla, borrar y exportar a CSV. Tú eliges cuántas guardar y la carpeta.",
   "Actualizaciones desde la app: Tela! avisa cuando sale una versión nueva y la instala con un clic.",
   "Notas de todas las versiones en Avanzado y un resumen de lo que cambió después de cada actualización.",
   "Tema de colores de pantalla personalizado, separado de los predefinidos."
  ],
  "fix": [
   "La imagen de fondo a veces seguía en la pantalla después de quitarla.",
   "La pantalla podía perder la conexión durante una transición.",
   "El medidor de FPS se recupera solo cuando deja de responder y muestra el motivo cuando no puede iniciarse.",
   "El instalador mostraba el error 740 al abrir Tela! al final."
  ],
  "perf": [
   "La ventana usa mucha menos memoria."
  ],
  "look": [
   "La multimedia se oculta 5 s después de pausar, con transición. Con un juego abierto, aunque esté minimizado, se queda a la derecha.",
   "Transición en bloques también al salir del resumen de partida.",
   "El tema oscuro predeterminado de la ventana ahora es Negro. Inicio y Ajustes más ordenados."
  ]
 },
 "zh": {
  "new": [
   "游戏记录：每局总结都会保存，支持搜索、FPS 图表、重新显示到屏幕、删除和导出 CSV。可选择保留数量和文件夹。",
   "应用内更新：有新版本时 Tela! 会提示，一键即可安装。",
   "高级 中可查看所有版本的说明，每次更新后会显示更新内容摘要。",
   "自定义屏幕配色主题，与预设主题分开。"
  ],
  "fix": [
   "背景图片删除后有时仍留在屏幕上。",
   "屏幕可能在过渡动画期间断开连接。",
   "FPS 计数器停止响应时会自动恢复，无法启动时会显示原因。",
   "安装程序在最后打开 Tela! 时出现错误 740。"
  ],
  "perf": [
   "窗口占用的内存大幅减少。"
  ],
  "look": [
   "媒体暂停 5 秒后以过渡动画隐藏。游戏打开时（即使最小化）媒体保持在右侧。",
   "离开游戏总结时也有方块过渡动画。",
   "窗口的默认深色主题现在是黑色。主页和设置更加整洁。"
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
 },
 "es": {
  "new": [
   "Ventana nueva, en portugués, inglés, español y chino.",
   "Editor de diseño: arrastrar, redimensionar, activar y desactivar bloques, renombrar y elegir sensores de una lista en vivo.",
   "Pantalla en vertical además de horizontal, y ambas invertidas.",
   "Un instalador de verdad: no necesita Python, descarga PawnIO y WebView2 solo si faltan y guarda los ajustes en %APPDATA%\\Tela.",
   "Asistente en el primer inicio, que trae los ajustes de versiones anteriores."
  ],
  "look": [
   "Temas de la ventana (automático, predefinidos o con tus colores), temas de colores de la pantalla e imagen de fondo."
  ]
 },
 "zh": {
  "new": [
   "全新窗口，支持葡萄牙语、英语、西班牙语和中文。",
   "布局编辑器：拖动、调整大小、开关方块、重命名，并可从实时列表中选择传感器。",
   "除横屏外还支持竖屏，并都可翻转。",
   "真正的安装程序：无需 Python，仅在缺少时下载 PawnIO 和 WebView2，设置保存在 %APPDATA%\\Tela。",
   "首次运行向导，可导入旧版本的设置。"
  ],
  "look": [
   "窗口主题（自动、预设或自定义颜色）、屏幕配色主题和背景图片。"
  ]
 }},
{"v": "1.3.9",
 "pt": {
  "new": [
   "Primeiro instalador (Setup.exe) gerado no GitHub."
  ],
  "fix": [
   "Recuperação automática de erros e registro de atividade que se organiza sozinho."
  ],
  "perf": [
   "Desenho da tela mais leve."
  ]
 },
 "en": {
  "new": [
   "First setup (Setup.exe) built on GitHub."
  ],
  "fix": [
   "Automatic error recovery and an activity log that keeps itself tidy."
  ],
  "perf": [
   "Lighter screen drawing."
  ]
 },
 "es": {
  "new": [
   "Primer instalador (Setup.exe) generado en GitHub."
  ],
  "fix": [
   "Recuperación automática de errores y un registro de actividad que se mantiene ordenado solo."
  ],
  "perf": [
   "Dibujo de la pantalla más ligero."
  ]
 },
 "zh": {
  "new": [
   "首个在 GitHub 上生成的安装程序（Setup.exe）。"
  ],
  "fix": [
   "自动错误恢复，活动日志会自动整理。"
  ],
  "perf": [
   "屏幕绘制更轻量。"
  ]
 }},
{"v": "1.3.8",
 "pt": {
  "new": [
   "Detecção automática do hardware: nomes de CPU, GPU, RAM, VRAM e discos com letras.",
   "Música e vídeo tocando no topo da tela (Spotify, YouTube e outros).",
   "Escolha da porta da tela, brilho e último resumo pelo ícone da bandeja."
  ],
  "fix": [
   "A tela reconecta sozinha ao voltar da suspensão. O instalador confere o Windows, o .NET e o PawnIO."
  ]
 },
 "en": {
  "new": [
   "Automatic hardware detection: CPU, GPU, RAM, VRAM and disk names with letters.",
   "Music and video playing at the top of the screen (Spotify, YouTube and others).",
   "Screen port choice, brightness and last summary from the tray icon."
  ],
  "fix": [
   "The screen reconnects by itself after sleep. The installer checks Windows, .NET and PawnIO."
  ]
 },
 "es": {
  "new": [
   "Detección automática del hardware: nombres de CPU, GPU, RAM, VRAM y discos con letras.",
   "Música y vídeo en reproducción en la parte superior de la pantalla (Spotify, YouTube y otros).",
   "Elección del puerto de la pantalla, brillo y último resumen desde el icono de la bandeja."
  ],
  "fix": [
   "La pantalla se reconecta sola al volver de la suspensión. El instalador comprueba Windows, .NET y PawnIO."
  ]
 },
 "zh": {
  "new": [
   "自动检测硬件：CPU、GPU、内存、显存名称以及带盘符的磁盘。",
   "屏幕顶部显示正在播放的音乐和视频（Spotify、YouTube 等）。",
   "可从托盘图标选择屏幕端口、调整亮度和查看上一局总结。"
  ],
  "fix": [
   "从睡眠恢复后屏幕会自动重新连接。安装程序会检查 Windows、.NET 和 PawnIO。"
  ]
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
  "look": [
   "Transição em cascata entre o painel e o resumo. Cor de fundo da tela."
  ]
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
  "look": [
   "Cascade transition between the panel and the summary. Screen background color."
  ]
 },
 "es": {
  "new": [
   "Red con ping, pérdida de paquetes y aviso de caída, indicando si el router responde.",
   "Brillo nocturno. La pantalla se apaga cuando el PC se bloquea o el monitor se suspende."
  ],
  "fix": [
   "El instalador conserva tus ajustes.",
   "Cambiar de programa con un juego abierto ya no pierde la sesión; cada juego tiene la suya."
  ],
  "look": [
   "Transición en cascada entre el panel y el resumen. Color de fondo de la pantalla."
  ]
 },
 "zh": {
  "new": [
   "网络显示延迟、丢包和断网提示，并说明路由器是否有响应。",
   "夜间亮度。电脑锁定或显示器休眠时关闭屏幕。"
  ],
  "fix": [
   "安装程序会保留你的设置。",
   "游戏打开时切换程序不会再丢失会话；每个游戏都有自己的会话。"
  ],
  "look": [
   "面板与总结之间的瀑布式过渡。屏幕背景颜色。"
  ]
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
 },
 "es": {
  "new": [
   "Resumen de partida cuando el juego se cierra, con tiempo ajustable y botón \"Ver cómo queda\".",
   "1% low junto al frame time y la temperatura máxima de la partida en los indicadores."
  ]
 },
 "zh": {
  "new": [
   "游戏关闭时显示本局总结，可调整显示时间，并有“预览效果”按钮。",
   "帧时间旁显示 1% low，仪表中显示本局最高温度。"
  ]
 }},
{"v": "1.3.5",
 "pt": {
  "new": [
   "Intervalo e média do FPS ajustáveis, atualizando a cada 0,2 s."
  ],
  "fix": [
   "Só uma Tela! aberta por vez: ela pergunta antes de fechar a outra cópia."
  ]
 },
 "en": {
  "new": [
   "Adjustable FPS interval and average, updating every 0.2 s."
  ],
  "fix": [
   "Only one Tela! open at a time: it asks before closing the other copy."
  ]
 },
 "es": {
  "new": [
   "Intervalo y promedio de FPS ajustables, actualizando cada 0,2 s."
  ],
  "fix": [
   "Solo una Tela! abierta a la vez: pregunta antes de cerrar la otra copia."
  ]
 },
 "zh": {
  "new": [
   "可调整 FPS 刷新间隔和平均值，每 0.2 秒更新一次。"
  ],
  "fix": [
   "同一时间只能打开一个 Tela!：关闭另一个副本前会先询问。"
  ]
 }},
{"v": "1.3.4",
 "pt": {
  "new": [
   "Frame time ao lado do FPS e volume do Windows em um bloco próprio.",
   "Discos mostram a atividade em tempo real, com a barra do espaço ocupado."
  ],
  "look": [
   "Cores da tela editáveis pela janela."
  ]
 },
 "en": {
  "new": [
   "Frame time next to the FPS and Windows volume in its own block.",
   "Disks show live activity, with the bar showing used space."
  ],
  "look": [
   "Screen colors editable in the window."
  ]
 },
 "es": {
  "new": [
   "Frame time junto a los FPS y volumen de Windows en su propio bloque.",
   "Los discos muestran la actividad en tiempo real, con la barra del espacio usado."
  ],
  "look": [
   "Colores de la pantalla editables desde la ventana."
  ]
 },
 "zh": {
  "new": [
   "FPS 旁显示帧时间，Windows 音量有独立方块。",
   "磁盘实时显示活动，进度条显示已用空间。"
  ],
  "look": [
   "可在窗口中编辑屏幕颜色。"
  ]
 }},
{"v": "1.3.3",
 "pt": {
  "new": [
   "FPS pelo PresentMon, sem precisar do RTSS ou do Afterburner.",
   "Botão Desinstalar."
  ],
  "perf": [
   "Programa em pasta, sem sobras na pasta temporária."
  ]
 },
 "en": {
  "new": [
   "FPS through PresentMon, no RTSS or Afterburner needed.",
   "Uninstall button."
  ],
  "perf": [
   "Program in a folder, nothing left in the temp folder."
  ]
 },
 "es": {
  "new": [
   "FPS mediante PresentMon, sin necesidad de RTSS ni Afterburner.",
   "Botón Desinstalar."
  ],
  "perf": [
   "Programa en una carpeta, sin restos en la carpeta temporal."
  ]
 },
 "zh": {
  "new": [
   "通过 PresentMon 获取 FPS，无需 RTSS 或 Afterburner。",
   "卸载按钮。"
  ],
  "perf": [
   "程序位于独立文件夹，不在临时文件夹留下文件。"
  ]
 }},
{"v": "1.3.2",
 "pt": {
  "new": [
   "Intervalo de atualização por item, mostrando a média do período.",
   "Opção de ligar e desligar as animações."
  ],
  "fix": [
   "A tela fica preta ao fechar o app e ao desligar ou reiniciar o PC."
  ]
 },
 "en": {
  "new": [
   "Update interval per item, showing the average of the period.",
   "Option to turn animations on and off."
  ],
  "fix": [
   "The screen goes black when the app closes and when the PC shuts down or restarts."
  ]
 },
 "es": {
  "new": [
   "Intervalo de actualización por elemento, mostrando el promedio del período.",
   "Opción para activar y desactivar las animaciones."
  ],
  "fix": [
   "La pantalla se pone negra al cerrar la app y al apagar o reiniciar el PC."
  ]
 },
 "zh": {
  "new": [
   "每个项目可设置更新间隔，显示该时段的平均值。",
   "可开启或关闭动画。"
  ],
  "fix": [
   "关闭应用以及电脑关机或重启时屏幕变黑。"
  ]
 }},
{"v": "1.3.1",
 "pt": {
  "fix": [
   "O download do monitor de hardware voltou a funcionar."
  ],
  "look": [
   "Versão no título da janela."
  ]
 },
 "en": {
  "fix": [
   "The hardware monitor download works again."
  ],
  "look": [
   "Version in the window title."
  ]
 },
 "es": {
  "fix": [
   "La descarga del monitor de hardware vuelve a funcionar."
  ],
  "look": [
   "Versión en el título de la ventana."
  ]
 },
 "zh": {
  "fix": [
   "硬件监控组件的下载恢复正常。"
  ],
  "look": [
   "窗口标题中显示版本号。"
  ]
 }},
{"v": "1.3.0",
 "pt": {
  "new": [
   "Monitor de hardware embutido, instalador único e início pelo Agendador de Tarefas."
  ],
  "look": [
   "Animações suaves: barras e gauges deslizam."
  ]
 },
 "en": {
  "new": [
   "Embedded hardware monitor, single installer and start through the Task Scheduler."
  ],
  "look": [
   "Smooth animations: bars and gauges glide."
  ]
 },
 "es": {
  "new": [
   "Monitor de hardware integrado, instalador único e inicio mediante el Programador de tareas."
  ],
  "look": [
   "Animaciones suaves: las barras y los indicadores se deslizan."
  ]
 },
 "zh": {
  "new": [
   "内置硬件监控、单一安装程序，并通过任务计划程序启动。"
  ],
  "look": [
   "流畅动画：进度条和仪表平滑移动。"
  ]
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
 },
 "es": {
  "new": [
   "Ventana con vista previa en vivo, icono en la bandeja e inicio con Windows.",
   "Sensores leídos directamente, sin abrir LibreHardwareMonitor, y ejecutable propio."
  ]
 },
 "zh": {
  "new": [
   "带实时预览的窗口、托盘图标和开机启动。",
   "直接读取传感器，无需打开 LibreHardwareMonitor，并有独立的可执行文件。"
  ]
 }},
{"v": "1.1.0",
 "pt": {
  "new": [
   "Primeira versão: painel de sensores no estilo do AIDA64, rodando pelo console."
  ]
 },
 "en": {
  "new": [
   "First version: AIDA64-style sensor panel, running from the console."
  ]
 },
 "es": {
  "new": [
   "Primera versión: panel de sensores al estilo de AIDA64, funcionando desde la consola."
  ]
 },
 "zh": {
  "new": [
   "第一个版本：AIDA64 风格的传感器面板，从控制台运行。"
  ]
 }}
];

const CL_CATEGORIES = ["new", "fix", "perf", "look"];

function changelogNotes(entry) {
  return entry[S.lang] || entry.en;
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
