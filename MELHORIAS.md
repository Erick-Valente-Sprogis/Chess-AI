# Melhorias — Chess-AI

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
|---|---|---|
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
