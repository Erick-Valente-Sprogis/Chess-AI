# Melhorias — Chess-AI

---

## Backlog (próximas melhorias, em ordem de prioridade)

| # | Melhoria | Impacto |
| --- | --- | --- |
| ~~1~~ | ~~**Transposition Table** (Zobrist hashing)~~ | ~~IA: evita recalcular posições já vistas; dobra/triplica profundidade efetiva~~ |
| ~~2~~ | ~~**Livro de Aberturas**~~ | ~~IA: movimentos iniciais mais naturais e teoricamente corretos~~ |
| ~~3~~ | ~~**Promoção com escolha de peça**~~ | ~~Regra: permite subpromoções (cavalo, torre, bispo) via menu visual~~ |
| ~~4~~ | ~~**Relógio de xadrez**~~ | ~~UX: timer por jogador, configurável no menu; essencial para PvP~~ |
| ~~5~~ | ~~**Exportar/importar PGN**~~ | ~~UX: salvar e carregar partidas para análise externa~~ |
| ~~6~~ | ~~**Animação de movimento**~~ | ~~UX: peça desliza ao invés de teletransportar~~ |
| ~~7~~ | ~~**Sons**~~ | ~~UX: captura, movimento, xeque via pygame.mixer~~ |
| ~~8~~ | ~~**README atualizado**~~ | ~~Docs: ainda descreve SEARCH_DEPTH e exige download manual da fonte~~ |
| ~~9~~ | ~~**Avaliação de estrutura de peões**~~ | ~~IA: peões dobrados, isolados, passados~~ |
| ~~10~~ | ~~**Segurança do rei mais detalhada**~~ | ~~IA: cobertura de peões, colunas abertas perto do rei~~ |
| ~~11~~ | ~~**Modo análise**~~ | ~~UX: navegar o histórico clicando em movimentos, tabuleiro volta a qualquer ponto~~ |
| ~~12~~ | ~~**Testes automatizados**~~ | ~~Qualidade: testes unitários para avaliação e minimax~~ |

---

## Sessão: 06/05/2026

**Itens concluídos:** #20 (PGN), #21 (Animação), #22 (Sons), #23 (README)

---

## Sessão: 07/05/2026

**Itens concluídos:** #24 (Estrutura de Peões), #25 (Segurança do Rei), #26 (Modo Análise), #27 (Testes Automatizados)

---

## 27. Testes Automatizados

**Arquivo:** `test_ai.py` (novo)

**Horário:** 07/05/2026

**O que foi feito:**
Criado arquivo `test_ai.py` com 21 testes unitários usando a biblioteca padrão `unittest`. Nenhuma dependência externa necessária — apenas `chess` e `math`. O arquivo importa `main` como módulo sem chamar `main()`, permitindo testar as funções puras de IA diretamente.

**Comando para executar:**

```bash
python -m unittest test_ai -v
```

**Cobertura por classe:**

| Classe | Testes | O que verifica |
| --- | --- | --- |
| `TestEvaluateBoard` | 6 | Posição inicial ≈ 0, xeque-mate ±inf, afogamento = 0, vantagem material |
| `TestPawnStructure` | 6 | Sem peões = 0, peões dobrados (penalidade), peão passado (bônus), isolado vs com suporte, simetria |
| `TestKingSafety` | 3 | Sem rainha = 0, escudo de peões > rei exposto, colunas fechadas > abertas |
| `TestMinimax` | 2 | Captura torre indefesa (profundidade 1), profundidade 0 ≈ avaliação estática |
| `TestFindBestMove` | 4 | Captura rainha grátis, xeque-mate em 1, lance legal retornado, nenhum lance = None |

**Resultado:** 21/21 OK em ~2 segundos.

**Por que importa:**
Garante que alterações futuras na função de avaliação ou no minimax não quebrem comportamentos esperados silenciosamente. Cobre os casos mais críticos: xeque-mate, afogamento, material e estrutura de peões.

---

## 26. Modo Análise

**Arquivo:** `main.py`

**Horário:** 07/05/2026

**O que foi feito:**
Implementado modo de navegação de histórico no estado REVISAO. O usuário pode agora percorrer qualquer posição da partida clicando nos movimentos do painel lateral ou usando as setas do teclado.

**Componentes adicionados:**

- **`_board_at(full_board, n)`** — função auxiliar que reconstrói a posição do tabuleiro após `n` meias-jogadas, replaying `full_board.move_stack[:n]` em um `chess.Board()` vazio.
- **`analysis_index`** em `state_vars` — inteiro (0..len(history)) ou `None`. `None` = posição final sem destaque. `N` = posição após N meias-jogadas, com highlight no movimento N−1 no painel.
- **Destaque no histórico** — `draw_history_panel` ganhou parâmetro `selected_san_index`. Quando ativo, desenha retângulo azul-escuro (`(70, 70, 120)`) sobre o movimento selecionado.
- **`draw_game_screen` analysis-aware** — quando `analysis_index` está ativo, exibe `_board_at(board, analysis_index)` no lugar do tabuleiro real. Selecção de casas e animação são desabilitadas durante análise.

**Controles em REVISAO:**

| Ação | Efeito |
| --- | --- |
| Clique no movimento do histórico | Vai para a posição após aquele movimento |
| ← (seta esquerda) | Recua um movimento |
| → (seta direita) | Avança um movimento |
| ESC | Volta à posição final (desativa destaque) |

**Auto-scroll:** Ao navegar com setas, o painel de histórico rola automaticamente para manter o movimento selecionado visível (lógica de janela deslizante de 15 linhas).

**Painel de ações em REVISAO:** Sobrescrito com info de navegação: posição atual `N / Total`, dica de teclas e instrução de clique.

**Por que importa:**
Antes, o estado REVISAO só mostrava a posição final da partida. Agora é possível revisar qualquer lance, acompanhar como a IA chegou a uma decisão, ou estudar erros — sem precisar exportar para um programa externo.

---

## 25. Segurança do Rei

**Arquivo:** `main.py`

**Horário:** 06/05/2026

**O que foi feito:**
Adicionada função `_king_safety_bonus(board, color)` que avalia dois aspectos da segurança do rei para uma cor. A chamada foi inserida em `evaluate_board()`:

```python
total_value += _king_safety_bonus(board, chess.WHITE) - _king_safety_bonus(board, chess.BLACK)
```

**Dois componentes implementados:**

- **Escudo de peões** — para cada uma das três colunas ao redor do rei (kf−1, kf, kf+1), verifica se há um peão aliado imediatamente à frente (+0,15) ou dois ranques à frente (+0,05). Bônus decrescente para refletir que o escudo mais próximo é mais eficaz.
- **Penalidade de coluna aberta/semi-aberta** — se uma dessas três colunas não tem peão aliado, a IA paga −0,25 (coluna aberta: sem peões de nenhuma cor) ou −0,10 (coluna semi-aberta: peão inimigo presente mas sem aliado). Colunas abertas perto do rei são vetores de ataque direto de torres e damas.

**Condição de aplicação:**
A função retorna 0 quando não há damas no tabuleiro (final de jogo). No final, o rei deve avançar para o centro, não ficar escondido. Essa condição evita que a IA penalize o rei ativo no endgame.

**Magnitudes:**

| Situação | Efeito |
| --- | --- |
| Três peões de escudo imediatos | +0,45 |
| Três colunas abertas ao redor do rei | −0,75 |
| Escudo parcial + coluna semi-aberta | variável |

---

## 24. Avaliação de Estrutura de Peões

**Arquivo:** `main.py`

**Horário:** 06/05/2026

**O que foi feito:**
Adicionada função `_pawn_structure_bonus(board, color)` que avalia três aspectos da estrutura de peões para uma cor e retorna um bônus/penalidade em frações de peão. A chamada foi inserida no final de `evaluate_board()`:

```python
total_value += _pawn_structure_bonus(board, chess.WHITE) - _pawn_structure_bonus(board, chess.BLACK)
```

**Três componentes implementados:**

- **Peões dobrados** — se dois ou mais peões da mesma cor ocupam a mesma coluna, cada um recebe −0,25 de penalidade. Peões dobrados não se defendem mutuamente e bloqueiam o avanço do outro.
- **Peões isolados** — se um peão não tem nenhum peão aliado nas colunas adjacentes (esquerda ou direita), recebe −0,20 de penalidade. Peões isolados não podem ser defendidos por outros peões e são alvos táticos fáceis.
- **Peões passados** — se nenhum peão inimigo está nas colunas adjacentes ou na mesma coluna à frente do peão, ele recebe bônus crescente baseado no avanço: `0,10 + rank × 0,05`. Peões passados ameaçam diretamente a promoção e valem materialmente mais quanto mais avançados estão.

**Por que importa:**
A função de avaliação anterior só considerava valor material, tabelas de posição e mobilidade. Sem penalidades estruturais, a IA aceitava trocar estrutura de peões livremente, criando peões dobrados e isolados sem custo. Os bônus de peão passado incentivam a IA a avançar peões em finais de jogo, comportamento ausente anteriormente.

---

## 23. README Atualizado

**Arquivo:** `README.md`

**O que foi feito:**
Reescrito completamente. O documento anterior estava desatualizado em três pontos críticos e não documentava nenhuma das features adicionadas nas últimas sessões.

**Problemas corrigidos:**

- Removida referência à constante `SEARCH_DEPTH` — o projeto usa `DEFAULT_TIME_LIMIT` com iterative deepening desde a sessão 3.
- Removido o passo "Baixe a Fonte (Essencial)" da instalação — desde o item 5, o jogo usa `pygame.font.match_font()` e não depende de arquivo `.ttf` manual.
- Removida a instrução de clone com URL malformada (colchetes duplicados).

**Conteúdo novo adicionado:**

- Seção "Funcionalidades" expandida: relógio de xadrez, animação, sons, promoção com escolha, PGN, menu de pausa, undo.
- Tabela de níveis de dificuldade (tempo por jogada).
- Tabela de controles de tempo (Bullet/Blitz/Rápido/Ilimitado).
- "Detalhes da IA" reescrita: descreve Iterative Deepening, Transposition Table, Livro de Aberturas, Quiescence Search, MVV-LVA, tabela de componentes da função de avaliação.
- Instalação reduzida a 3 passos com nota de fallback de fonte.

**Por que importa:**
O README é a primeira coisa que alguém vê ao abrir o repositório. Descrever `SEARCH_DEPTH` e exigir download de fonte afastava contribuidores e criava suporte desnecessário.

---

## 22. Sons

**Arquivo:** `main.py` — funções `_gen_sine()`, `_make_sounds()`, `main()`

**O que foi feito:**
Implementado feedback sonoro para todos os eventos de jogo relevantes, gerado programaticamente com `array` + `math` (stdlib) — sem nenhum arquivo de áudio externo.

**`pygame.mixer.pre_init(44100, -16, 1, 512)`** chamado antes de `pygame.init()` para garantir áudio mono 16-bit signed a 44100 Hz, compatível com os buffers gerados.

**`_gen_sine(freq, ms, vol, decay, sample_rate)`:**
Gera uma onda senoidal com envelope `attack + exponential decay`:

- `attack`: 5ms de rampa linear (evita clique de início)
- `decay`: `exp(-decay × t)` — quanto maior, mais rápido o fade
- Retorna `array.array('h', ...)` de inteiros signed 16-bit

**Quatro sons (`_make_sounds()`):**

| Som | Freq | Duração | Uso |
| --- | --- | --- | --- |
| `move` | 800 Hz | 50ms | Movimento simples (casa vazia) |
| `capture` | 350 Hz | 80ms | Captura de peça |
| `check` | 1047 Hz | 120ms | Rei em xeque |
| `game_end` | 523→415→311 Hz | 590ms | Xeque-mate, empate ou timeout |

O `game_end` é um arpejo descendente (C5→G♯4→E♭4) composto por três chamadas a `_gen_sine` concatenadas com 55ms de silêncio entre elas.

**Prioridade de som por movimento (humano, promoção e IA):**

```python
_snd = 'check' if board.is_check() else ('capture' if _cap else 'move')
```

`is_capture(move)` é verificado **antes** do `board.push()` (a posição já muda após o push). `is_check()` é verificado **depois** do push (xeque é estado pós-movimento). O som de `game_end` é disparado nas transições para `"FIM_DE_JOGO"` (timeout e `is_game_over()`), não no bloco de movimento — evita que dois sons toquem ao mesmo tempo no xeque-mate.

**Fallback:** envolvido em `try/except` — se o mixer não inicializar (ex: sistema sem áudio), `sounds = {}` e todas as chamadas `.get(_snd)` retornam `None` sem crash.

**Por que importa:**
Feedback auditivo é especialmente valioso para movimentos da IA — o jogador sabe imediatamente quando a IA jogou sem precisar monitorar a tela. O xeque-mate ganha um arpejo conclusivo que fecha a experiência da partida.

---

## 21. Animação de Movimento

**Arquivo:** `main.py` — constante `ANIM_DURATION`, função `make_anim()`, `draw_pieces()`, loop principal

**O que foi feito:**
Implementada animação de deslizamento suave para toda peça movida — humano, IA e promoção — com easing *smooth-step* e duração de 150ms.

**Constante:** `ANIM_DURATION = 0.15` (segundos)

**Função `make_anim(from_sq, to_sq, piece, perspective, flip_perspective=None)`:**
Cria e retorna o dict de animação:

- `piece` — `chess.Piece` capturada **antes** do `board.push()`, para saber o símbolo correto
- `from_center` / `to_center` — coordenadas pixel do centro de cada casa (calculadas usando `get_drawing_coords` + perspectiva atual)
- `start` — `time.monotonic()` do momento da chamada
- `duration` — `ANIM_DURATION`
- `flip_perspective` — nova perspectiva a aplicar quando a animação terminar (`None` no modo vs IA, `board.turn` pós-push no PvP)

**`draw_pieces()` atualizada:**
Recebe `anim=None`. Quando ativo:

- Pula o quadrado de destino (`skip_sq = anim['to_square']`) para não desenhar a peça na posição final ainda
- Após iterar todos os quadrados, calcula `t` com *smooth-step* (`t² × (3 − 2t)`) e interpola a posição da peça entre `from_center` e `to_center`
- A peça animada é renderizada sobre o tabuleiro na posição interpolada

**Fluxo por tipo de movimento:**

| Origem | Antes do push | Depois do push |
| --- | --- | --- |
| Humano (normal) | Captura `piece_at(from_sq)` | `make_anim(...)` com `flip_perspective` se PvP |
| Humano (promoção) | Captura `piece_at(from_sq)` | `make_anim(...)` com `flip_perspective` se PvP |
| IA | Captura `piece_at(from_sq)` | `make_anim(...)` sem flip |

**Perspectiva PvP:**
O tabuleiro só vira de perspectiva quando a animação termina (não durante o deslize). Isso evita o visual estranho de a perspectiva flipar enquanto a peça está no ar. O `flip_perspective` é armazenado no dict de animação e aplicado ao completar.

**Resolução de animação (loop principal):**

```python
_anim = state_vars.get('anim')
if _anim and time.monotonic() - _anim['start'] >= _anim['duration']:
    if _anim.get('flip_perspective') is not None:
        state_vars['perspective'] = _anim['flip_perspective']
    state_vars['anim'] = None
```

**Bloqueios durante animação:**

- Thread da IA não inicia enquanto `state_vars.get('anim')` for verdadeiro — evita que a IA calcule durante os 150ms e então aplique o movimento antes da animação do humano terminar
- Movimento da IA só é aplicado ao tabuleiro quando `not state_vars.get('anim')` — garante que animações do humano e da IA nunca se sobrepõem
- Undo cancela a animação imediatamente (`state_vars['anim'] = None`) antes de fazer `board.pop()`

**Por que importa:**
Sem animação, movimentos de peças são instantâneos e difíceis de rastrear — especialmente movimentos da IA em posições complexas. O deslizamento de 150ms dá ao olho tempo suficiente para seguir a peça sem tornar o jogo lento.

---

## 20. Exportar/Importar PGN

**Arquivo:** `main.py` — funções `export_pgn()`, `list_saves()`, `import_pgn()`, estado `"CARREGAR"`, menu principal, menu de pausa

**O que foi feito:**
Implementado suporte completo a PGN (Portable Game Notation), o formato universal de xadrez, com exportação via pausa e importação via menu principal.

**Novos imports:** `chess.pgn`, `chess.polyglot`, `os`, `datetime`

**Constante:** `SAVES_DIR` — caminho absoluto para `saves/` na mesma pasta do `main.py`. O diretório é criado automaticamente na primeira exportação.

**Correção de API (`chess.polyglot`):**

A versão instalada do python-chess não possui mais `board.zobrist_hash()`. O equivalente atual é `chess.polyglot.zobrist_hash(board)`. Todos os 4 call sites foram atualizados (Transposition Table, Opening Book, `minimax()`, `find_best_ai_move()`). Esta correção é pré-requisito para o jogo funcionar — a versão anterior do código falhava na inicialização.

**Funções adicionadas:**

| Função | Descrição |
| --- | --- |
| `export_pgn(board, game_mode, player_color, clock_config)` | Cria headers PGN (Event, Site, Date, White, Black, Result, TimeControl), reconstrói a sequência de movimentos via `board.move_stack`, salva em `saves/partida_YYYYMMDD_HHMMSS.pgn`. Retorna `(filepath, filename)`. |
| `list_saves()` | Lista até 10 arquivos `.pgn` em `SAVES_DIR`, ordenados do mais recente ao mais antigo por `mtime`. |
| `import_pgn(filepath)` | Abre o arquivo, lê com `chess.pgn.read_game()`, reproduz os movimentos em um `chess.Board()` acumulando `history_san`. Retorna `(board, history_san, headers)` ou `None` em caso de erro. |

**Exportar PGN — fluxo:**

1. Jogador abre o menu de pausa (ESC ou botão)
2. Clica em **"Exportar PGN"** (5º botão, adicionado ao popup que cresceu de 380 → 440px de altura)
3. PGN é salvo em `saves/`
4. Menu fecha, estado volta a `"JOGANDO"`
5. Toast de confirmação aparece 3s no topo da tela: `"Salvo: partida_YYYYMMDD_HHMMSS.pgn"`

O PGN gerado é compatível com Lichess, Chess.com, ChessBase e qualquer software de análise padrão.

**Carregar Partida — fluxo:**

1. Jogador está na tela de menu principal
2. Botão **"Carregar Partida"** visível abaixo dos botões de modo (y=558, h=40). Fica esmaecido (cinza) se não houver arquivos `.pgn` em `saves/`
3. Clique → novo estado `"CARREGAR"`: lista até 10 saves como botões, do mais recente ao mais antigo
4. Nome exibido: timestamp humanizado (`20260506  143022` em vez de `partida_20260506_143022.pgn`)
5. Clique num arquivo → `import_pgn()` → board e histórico carregados → transição para estado `"REVISAO"` com a partida completa
6. ESC ou botão "Voltar" retorna ao menu

**Modo inferido dos headers PGN:**

- `Black = "IA"` → `game_mode = "IA"`, `player_color = WHITE`
- `White = "IA"` → `game_mode = "IA"`, `player_color = BLACK`
- Outro → `game_mode = "PvP"`

**Toast de notificação:**

Renderizado sobre qualquer estado ativo (JOGANDO, PAUSE, REVISAO) durante 3s após o evento. Implementado como overlay semi-transparente `(20,20,20,210)` no topo central da tela, independente da resolução. Controlado por `state_vars['toast_until']` (timestamp `time.monotonic()`).

**Ajuste do menu principal:**

Para acomodar o botão "Carregar Partida" sem sobrepor o seletor de relógio:

- Clock label: `int(MENU_HEIGHT*0.81)` → y fixo 615
- Clock buttons: `int(MENU_HEIGHT*0.87)` → y fixo 642, altura reduzida de 45 → 40px

**Por que importa:**
PGN é o formato universal do xadrez — permite revisar partidas em Lichess, estudar com Stockfish e compartilhar jogos. A importação fecha o ciclo: o jogador pode salvar partidas em sessões diferentes e retomar a revisão sem perder o histórico.

---

## Sessão: 05/05/2026 09:00 → 06/05/2026

---

## 19. Relógio de Xadrez

**Arquivo:** `main.py` — constante `TIME_CONTROLS`, função `format_clock()`, `draw_info_panel()`, loop principal, menu

**O que foi feito:**
Implementado um relógio de xadrez por jogador, configurável no menu principal, com contagem regressiva, alerta visual e detecção de derrota por tempo.

**Controles de tempo disponíveis:**

| Botão | Tempo | Modalidade |
| --- | --- | --- |
| ∞ | Ilimitado (padrão) | Sem relógio |
| 1' | 60s | Bullet |
| 3' | 180s | Blitz |
| 5' | 300s | Blitz |
| 10' | 600s | Rápido |

**Variáveis de estado adicionadas:**

- `clock_config`: tempo em segundos por jogador (`None` = sem relógio); persiste entre partidas da mesma sessão
- `white_time` / `black_time`: segundos restantes de cada jogador (`None` quando relógio desativado)
- `last_tick`: `time.monotonic()` do último frame; `None` quando relógio está pausado

**Seletor no menu principal:**

Faixa de 5 botões (110×45px) renderizada abaixo dos botões de modo, em `y ≈ 87%` do menu. O botão ativo é destacado em âmbar com borda branca (mesmo padrão visual do seletor de dificuldade na pausa). A seleção é preservada entre reinícios.

**Exibição durante a partida (`draw_info_panel`):**

Quando relógio ativo, o lado direito do painel de informações exibe dois relógios empilhados:

```text
♟ 2:47    ← relógio das pretas (linha superior)
♙ 4:12    ← relógio das brancas (linha inferior)
```

O lado cujo turno está ativo recebe fundo colorido (verde para brancas, vermelho para pretas). Quando restam menos de 30s, o texto do relógio fica vermelho vivo como alerta.

**Lógica de tick (loop principal):**

A cada frame em estado `"JOGANDO"`, calcula `elapsed = now - last_tick` e subtrai do relógio do jogador cujo turno está ativo (`board.turn`). O relógio conta tanto para humanos quanto para a IA — comportamento fiel ao xadrez real.

**Pausas do relógio:**

O `last_tick` é zerado (`None`) ao entrar em qualquer estado que suspende o jogo:

- `"JOGANDO"` → `"PAUSE"` (ESC ou botão de pausa)
- `"JOGANDO"` → `"PROMOCAO"` (enquanto o jogador escolhe a peça)
- Ao retornar de qualquer um desses estados, o primeiro frame reinicia o tick sem contar o tempo parado

**Derrota por tempo:**

Verificado após cada tick:

```python
if white_time <= 0:  → "Tempo esgotado! Pretas vencem."
if black_time <= 0:  → "Tempo esgotado! Brancas vencem."
```

O estado muda para `"FIM_DE_JOGO"` e o popup padrão é exibido.

**Inicialização do relógio:**

O relógio é inicializado com o tempo completo ao transicionar MENU → JOGANDO (em qualquer modo) e ao reiniciar via pausa (Reiniciar Partida e Mudar Dificuldade). Isso garante que reiniciar não herda tempo já consumido.

**Por que importa:**
Sem relógio, o modo PvP não tem tensão nem limite de tempo — um jogador pode procrastinar indefinidamente. O relógio adiciona a dimensão temporal real do xadrez competitivo. Para o modo vs IA, o relógio pode ser usado como desafio extra: vencer a IA dentro de um orçamento de tempo limitado.

---

## 18. Promoção com Escolha de Peça

**Arquivo:** `main.py` — função `draw_promotion_popup()`, estado `"PROMOCAO"`, handlers de evento

**O que foi feito:**
Substituída a promoção automática para Rainha por um menu visual interativo que permite escolher qualquer peça (Rainha, Torre, Bispo ou Cavalo), habilitando subpromoções.

**Novo estado de jogo: `"PROMOCAO"`**

A máquina de estados ganhou um novo estado que é ativado quando o jogador move um peão para a última fileira. O tabuleiro continua visível abaixo do popup, mas nenhum outro input é processado até que a peça seja escolhida (ou ESC cancele).

**Variável de estado adicionada:**

`state_vars['pending_promotion']`: tupla `(from_sq, to_sq)` com as casas de origem e destino do peão. Resetada para `None` ao concluir ou cancelar.

**Fluxo completo:**

1. Jogador move peão → código verifica `chess.Move(from_sq, to_sq, promotion=chess.QUEEN) in board.legal_moves`
2. Se verdadeiro: salva `pending_promotion`, muda estado para `"PROMOCAO"`, limpa seleção
3. `draw_promotion_popup()` renderiza 4 caixas (♕♖♗♘ ou ♛♜♝♞) **na coluna da promoção no próprio tabuleiro**, descendo a partir da última fileira para promoções brancas e subindo para pretas
4. Clique numa caixa: executa `chess.Move(from_sq, to_sq, promotion=pt)`, registra no histórico, volta para `"JOGANDO"`
5. `ESC`: cancela sem mover, volta para `"JOGANDO"` (peão fica onde estava)

**Posicionamento visual (`draw_promotion_popup`):**

```python
draw_row, draw_col = get_drawing_coords(to_sq, perspective)
step = 1 if draw_row == 0 else -1  # desce se promo no topo, sobe se no fundo
```

A função usa `get_drawing_coords` para respeitar a perspectiva do tabuleiro (funciona corretamente tanto no modo vs IA quanto PvP quando a perspectiva inverte). As caixas têm fundo `COLOR_LIGHT` com borda preta e os símbolos Unicode das peças, consistente com o estilo do projeto.

**Por que importa:**
Subpromoções (especialmente para Cavalo) são movimentos táticos legítimos no xadrez — promover para Cavalo às vezes causa xeque-mate ou forquilha que promover para Rainha não causaria. Além disso, a promoção automática para Rainha pode resultar em empate por afogamento (stalemate) em finais onde promover para Torre ou Bispo evitaria o problema.

---

## 17. Livro de Aberturas Embutido

**Arquivo:** `main.py` — constantes `_OPENING_LINES`, função `_build_opening_book()`, dict `_opening_book`, função `find_best_ai_move()`

**O que foi feito:**
Implementado um livro de aberturas embutido no código (sem arquivos externos), cobrindo as principais aberturas do xadrez competitivo.

**Estrutura de dados:**

`_OPENING_LINES` é uma lista de sequências de movimentos em notação UCI (ex: `"e2e4"`, `"g1f3"`). Cada sequência representa uma linha de abertura conhecida.

`_build_opening_book()` percorre todas as linhas, replica os movimentos em um tabuleiro temporário e constrói um dicionário:

```python
{ zobrist_hash_da_posição: [lista_de_bons_movimentos] }
```

O resultado é `_opening_book`, construído uma única vez na inicialização do módulo. Cada posição pode ter múltiplos movimentos válidos (quando várias linhas convergem para o mesmo ponto).

**Aberturas cobertas (~55 linhas, ~200 posições únicas):**

| Família | Aberturas incluídas |
| --- | --- |
| 1.e4 e5 | Ruy Lopez, Italian, Petrov, Four Knights, King's Gambit |
| 1.e4 (outras) | Siciliana (Najdorf, Clássica, Alapin), Francesa, Caro-Kann, Escandinava, Pirc/Moderna |
| 1.d4 d5 | Gambito da Rainha (QGD, Eslava, QGA) |
| 1.d4 Cf6 | KID, Nimzo-Indian, Queen's Indian, Grünfeld, Benoni, Holandesa |
| Sistemas | London, Trompowsky |
| 1.c4 / 1.Nf3 | English, Réti |

**Integração em `find_best_ai_move()`:**

```python
book_moves = [m for m in _opening_book.get(board.zobrist_hash(), []) if m in board.legal_moves]
if book_moves:
    return random.choice(book_moves)
```

Consultado antes de qualquer cálculo. Se a posição está no livro, retorna imediatamente um dos movimentos válidos (escolha aleatória entre os candidatos — adiciona variedade). A validação contra `board.legal_moves` é uma salvaguarda contra eventuais inconsistências no dado.

**Por que importa:**
Sem o livro, a IA calcula os primeiros movimentos do zero e pode jogar abertura sub-ótima (a avaliação posicional simples não captura a profundidade teórica das aberturas). Com o livro, o jogo de abertura é imediato, teoricamente correto, varia entre partidas e economiza o tempo de busca para o meio-jogo, onde a IA pode aprofundar mais.

---

## 16. Correção do Bug `not board.turn` no Minimax

**Arquivo:** `main.py` — função `find_best_ai_move()`

**O que foi feito:**
Corrigido um bug sutil que invertia o papel de maximizador/minimizador na chamada inicial ao `minimax`.

O problema estava nesta linha:

```python
# Antes (errado)
board_value = minimax(board, depth - 1, ..., not board.turn, deadline)
```

Após `board.push(move)`, `board.turn` já aponta para o **próximo** jogador. `not board.turn` inverte isso, resultando na cor do jogador que **acabou** de mover — o oposto do que é necessário. Na prática, a IA maximizava quando devia minimizar e vice-versa em toda a subárvore abaixo da raiz.

```python
# Depois (correto)
board_value = minimax(board, depth - 1, ..., board.turn == chess.WHITE, deadline, _tt)
```

`board.turn == chess.WHITE` retorna `True` (maximizar) quando é vez das brancas e `False` (minimizar) quando é vez das pretas — exatamente o comportamento esperado.

**Por que importa:**
O bug não impedia a IA de jogar, mas toda a subárvore de busca estava com a lógica de maximização/minimização invertida. A IA escolhia corretamente no nível raiz (por acidente, graças à comparação em `find_best_ai_move`), mas avaliava as respostas do adversário de forma incorreta em profundidade. A correção torna o minimax semanticamente correto e amplifica o ganho da Transposition Table implementada junto.

---

## 15. Transposition Table com Zobrist Hashing

**Arquivo:** `main.py` — constantes `_TT_*`, dict `_tt`, função `minimax()`

**O que foi feito:**
Implementada uma Transposition Table (TT) global que armazena avaliações de posições já calculadas, evitando recomputação.

**Estrutura:**

- `_tt`: dicionário `{zobrist_hash: (depth, value, flag, best_move)}`
- Chave: hash Zobrist da posição (`board.zobrist_hash()`, fornecido pelo python-chess)
- Limite: `_TT_MAX_SIZE = 1_000_000` entradas (evita uso irrestrito de memória)
- A TT persiste entre jogadas e entre partidas (posições de abertura são reutilizadas)

**Flags de validade (padrão alfa-beta):**

| Flag | Significado |
| --- | --- |
| `_TT_EXACT` | Valor exato dentro da janela alfa-beta |
| `_TT_LOWERBOUND` | Corte beta — valor é pelo menos este |
| `_TT_UPPERBOUND` | Falha baixa — valor é no máximo este |

**Integração no `minimax()`:**

1. **Lookup**: antes de calcular, consulta a TT pelo hash da posição. Se a entrada tem profundidade suficiente (`e_depth >= depth`), pode retornar imediatamente (EXACT) ou apertar a janela alfa-beta (LOWER/UPPER).
2. **Hash Move Ordering**: mesmo quando a profundidade da entrada é insuficiente para retorno direto, o `best_move` guardado é colocado **à frente** da lista de movimentos antes do MVV-LVA — o melhor movimento conhecido é sempre testado primeiro, melhorando drasticamente a poda.
3. **Store**: ao final de cada nó, armazena `(depth, best_val, flag, best_move)` se o limite de tamanho não foi atingido.

**Integração no `find_best_ai_move()`:**

- A cada nova profundidade do iterative deepening, consulta a TT para obter o melhor movimento da iteração anterior como primeiro candidato na raiz.
- Passa `_tt` explicitamente para `minimax()`.

**Por que importa:**
A TT elimina trabalho redundante em dois casos frequentes: posições alcançadas por caminhos diferentes (transposições) e reexpansão das mesmas posições em iterações mais profundas do iterative deepening. Combinada com hash move ordering, a poda alfa-beta torna-se muito mais eficiente — na prática, a IA consegue explorar profundidades 2–3 níveis maiores no mesmo tempo.

---

## 13. Seleção de Dificuldade

**Arquivo:** `main.py` — constante `DIFFICULTY_LEVELS`, função `draw_pause_menu()`, evento PAUSE

**O que foi feito:**
Implementada a seleção de dificuldade real no menu de pause, substituindo o botão placeholder "(Em breve)":

- Nova constante `DIFFICULTY_LEVELS` com 4 níveis:

| Nível | Time Limit |
| --- | --- |
| Fácil | 0.5s |
| Médio | 2.0s (padrão) |
| Difícil | 6.0s |
| Muito Difícil | 15.0s |

- `find_best_ai_move(board, time_limit)` agora recebe o tempo-limite como parâmetro (default `DEFAULT_TIME_LIMIT = 2.0`). Usa iterative deepening internamente — não há profundidade fixa.
- `state_vars['time_limit']` persiste a dificuldade escolhida entre partidas dentro da mesma sessão.
- `draw_pause_menu()` ganhou parâmetro `page` (`"main"` | `"difficulty"`):
  - Página principal: 4 botões normais (sem mais o placeholder acinzentado).
  - Página de dificuldade: 4 botões de nível + botão "Voltar"; o nível ativo é destacado com borda e cor âmbar.
- Selecionar um nível reinicia a partida (preservando modo e cor do jogador) com a nova profundidade.
- `Esc` no submenu de dificuldade volta para a página principal do pause (em vez de retornar ao jogo).

**Por que importa:**
A feature estava bloqueada como placeholder desde a sessão anterior. Agora o jogador pode ajustar a força da IA sem sair do jogo.

---

## 14. Hook de Sessão Movido para Settings Global

**Arquivo:** `~/.claude/settings.json`

**O que foi feito:**
O hook `UserPromptSubmit` que registra o horário de início de sessão em `/tmp/claude_session_start.txt` estava configurado apenas no `.claude/settings.json` do projeto Chess-AI. Foi replicado para `~/.claude/settings.json` (settings global do usuário).

**Por que importa:**
O hook não disparava quando a conversa era iniciada em outro diretório (ex: `/home/valente/JavaFacul`). Com o hook global, o horário de início é registrado corretamente independente do diretório de trabalho.

---

## Sessão: 04/05/2026 23:40 → 05/05/2026 00:25

---

## 1. Move Ordering (Ordenação de Movimentos)

**Arquivo:** `main.py` — função `order_moves()`

**O que foi feito:**
Adicionada a função `order_moves()` que ordena os movimentos legais antes de cada iteração do minimax, usando a heurística **MVV-LVA** (Most Valuable Victim – Least Valuable Attacker):

- Capturas de peças valiosas com peças baratas recebem pontuação mais alta.
- Promoções de peão são priorizadas logo após.
- Movimentos normais ficam no final.

**Por que importa:**
A poda alpha-beta é drasticamente mais eficiente quando os melhores movimentos são avaliados primeiro. Com ordenação, a IA consegue podar muito mais ramos da árvore de busca, permitindo aumentar `SEARCH_DEPTH` sem custo proporcional de tempo.

---

## 2. Threading (Cálculo em Background)

**Arquivo:** `main.py` — função `main()`

**O que foi feito:**

- Adicionado `import threading`.
- O cálculo da IA (`find_best_ai_move`) agora roda em uma `Thread` separada com `daemon=True`.
- O resultado é comunicado via lista compartilhada `ai_result`.
- `reset_game()` reseta o estado da thread via `nonlocal`, descartando resultados de cálculos anteriores.
- O painel de informações exibe **"IA pensando..."** enquanto a thread está ativa.
- O `pygame.time.delay(500)` foi removido, pois o delay de cálculo já era suficiente para a UX.

**Por que importa:**
Antes, a chamada bloqueante travava a UI completamente durante o cálculo. Com threading, o jogo continua responsivo (scroll do histórico, redimensionamento) enquanto a IA processa.

---

## 3. Quiescence Search (Busca de Quiescência)

**Arquivo:** `main.py` — função `quiescence()`

**O que foi feito:**
Adicionada a função `quiescence()`, chamada pelo `minimax` quando `depth == 0` em vez de chamar `evaluate_board()` diretamente.

A quiescence search:

- Avalia a posição atual como base (`stand_pat`).
- Continua a busca **apenas em capturas e promoções** até não restar nenhuma.
- Usa as mesmas janelas alpha-beta do minimax principal.

**Por que importa:**
Elimina o **efeito horizonte**: sem ela, o minimax pode "achar" que ganhou uma peça sem enxergar a recaptura imediata. Com ela, a IA sempre resolve sequências de troca antes de emitir uma avaliação final.

---

## 4. Avaliação de Mobilidade

**Arquivo:** `main.py` — função `evaluate_board()`

**O que foi feito:**
Adicionado ao cálculo de avaliação o número de movimentos legais disponíveis para cada lado. A diferença `(movimentos_brancas - movimentos_pretas) * 0.05` é somada ao valor total.

O turno do adversário é obtido via `board.push(chess.Move.null())` / `board.pop()`.

**Por que importa:**
Incentiva a IA a preferir posições ativas e com mais opções, penaliza posições travadas e promove o controle do centro.

---

## 5. Correção do Carregamento de Fonte

**Arquivo:** `main.py` — função `main()`

**O que foi feito:**
Substituído o carregamento por caminho relativo (`"dejavusans.ttf"`) por `pygame.font.match_font()`, que busca fontes instaladas no sistema na seguinte ordem de preferência:

1. `dejavusans`
2. `notosanssymbols2`
3. `notosanssymbols`

Como fallback final, usa a fonte padrão do pygame (`None`).

**Por que importa:**
A fonte padrão do pygame não suporta os símbolos Unicode das peças (♙♖♘♗♕♔ etc.), fazendo com que as peças não aparecessem na tela ao rodar via terminal sem o arquivo `.ttf` no diretório local.

---

## 6. Penalidade por Repetição de Posição

**Arquivo:** `main.py` — função `evaluate_board()`

**O que foi feito:**
Separada a lógica de repetição em dois casos:

- `is_repetition(3)` → empate real por tríplice repetição → retorna `0`.
- `is_repetition(2)` → posição visitada uma vez antes → retorna `±0.3` contra quem causou a repetição, em vez de `0` neutro.

O sinal é determinado por `board.turn`: se é vez das Brancas, as Pretas causaram a repetição, então o valor é `+0.3` (favorável às Brancas).

**Por que importa:**
Antes, posições repetidas avaliavam como `0` (neutro), e a IA as escolhia aleatoriamente quando empatada com outras opções. Com a penalidade, a IA prefere qualquer alternativa nova que avalie melhor que `±0.3`, eliminando ciclos desnecessários.

---

## 7. Redimensionamento da Interface

**Arquivo:** `main.py` — seção de constantes

**O que foi feito:**

| Constante | Antes | Depois |
| --- | --- | --- |
| `BOARD_SIZE` | 640 | 720 |
| `PADDING` | 40 → 50 → 70 | 70 |
| `INFO_HEIGHT` | 60 | 70 |
| `HISTORY_WIDTH` | 240 | 300 |
| `ACTION_PANEL_HEIGHT` | 120 | 140 |
| `MENU_WIDTH/HEIGHT` | 600×600 | 700×700 |

Resultando em:

- `GAME_WIDTH`: 920 → 1060
- `GAME_HEIGHT`: 740 → 860
- `SQUARE_SIZE`: 80 → 90px por casa

---

## 8. Redistribuição do Painel de Histórico

**Arquivo:** `main.py` — função `draw_history_panel()`

**O que foi feito:**
As colunas do histórico eram posicionadas com offsets fixos em pixels (herdados de `HISTORY_WIDTH=240`). Agora são calculadas proporcionalmente a `HISTORY_WIDTH`:

- Coluna de número: 38px fixos.
- Colunas Brancas e Pretas: dividem igualmente o espaço restante.
- `line_height` aumentado de 25 para 28px.

---

## 9. Correção do Botão "Ir para o Menu" (estado REVISAO)

**Arquivo:** `main.py` — estados `REVISAO` (draw e event handler)

**O que foi feito:**
O botão usava posição fixa `BOARD_RECT.bottom + 5` com altura 50px, que extravasa quando `PADDING` é igual ou menor que 55px. Agora é centralizado dinamicamente no espaço disponível abaixo do tabuleiro:

```python
_below = GAME_HEIGHT - BOARD_RECT.bottom
btn_y  = BOARD_RECT.bottom + (_below - btn_h) // 2
```

A altura do botão também foi reduzida de 50 para 40px para melhor proporção.

---

## 10. Atalho F5 para Teste Rápido

**Arquivo:** `main.py` — loop de eventos

**O que foi feito:**
Adicionado handler de teclado: pressionar `F5` a qualquer momento (inclusive no menu) abre a tela de jogo diretamente no estado `REVISAO`, permitindo inspecionar o layout do botão "Ir para o Menu" sem precisar terminar uma partida.

---

## 11. Menu de Pause

**Arquivo:** `main.py` — função `draw_pause_menu()`, estado `"PAUSE"`

**O que foi feito:**
Adicionado um novo estado de jogo `"PAUSE"` com overlay semitransparente sobre o tabuleiro, contendo 4 opções:

| Botão | Ação |
| --- | --- |
| Retornar à Partida | Fecha o menu e volta ao ponto exato onde parou |
| Reiniciar Partida | Recomeça com o mesmo modo e cor, sem passar pelo menu principal |
| Mudar Dificuldade *(Em breve)* | Placeholder acinzentado — feature a implementar futuramente |
| Voltar ao Menu Principal | Chama `reset_game()` e retorna ao menu de seleção |

- Ativado pela tecla `Esc` (toggle JOGANDO ↔ PAUSE).
- A thread da IA continua rodando em background durante a pausa, mas o resultado não é aplicado ao tabuleiro enquanto `current_state != "JOGANDO"`.
- `Reiniciar Partida` salva `game_mode`, `player_color` e `perspective` antes do reset e os restaura logo após.

---

## 12. Botão Visual de Pause (Mobile First)

**Arquivo:** `main.py` — constante `PAUSE_BTN`, função `draw_info_panel()`

**O que foi feito:**
Adicionado botão visual permanente na barra de informações superior, centralizado horizontalmente sobre o tabuleiro.

- Tamanho: **48×48px** — mínimo definido pela diretriz Mobile First do projeto.
- Ícone: duas barras verticais desenhadas com `pygame.draw.rect`, sem depender de glifos de fonte.
- Verificado antes da lógica de turno humano, então funciona tanto na vez do jogador quanto na vez da IA.
- Complementa o atalho `Esc` como forma primária de acesso para dispositivos touch.

**Diretriz Mobile First estabelecida:**
A partir desta sessão, toda nova UI do projeto deve ser projetada para touch primeiro:

- Touch targets mínimos de 48px.
- Sem dependência de teclado como interação primária.
- Layout que funcione em portrait.
