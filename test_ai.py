"""Testes unitários para as funções de avaliação e busca da IA."""
import math
import os
import sys
import time
import unittest

import chess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ai  # módulo de IA; main() NÃO é chamada


# ---------------------------------------------------------------------------
# evaluate_board
# ---------------------------------------------------------------------------
class TestEvaluateBoard(unittest.TestCase):

    def test_initial_position_near_zero(self):
        """Posição inicial deve ser aproximadamente simétrica (≈ 0)."""
        val = ai.evaluate_board(chess.Board())
        self.assertAlmostEqual(val, 0.0, delta=1.5)

    def test_checkmate_returns_positive_inf(self):
        """Scholar's mate: pretas estão em xeque-mate → +inf (brancas vencem)."""
        # 1.e4 e5 2.Bc4 Nc6 3.Qh5 Nf6?? 4.Qxf7#
        board = chess.Board("r1bqkb1r/pppp1Qpp/2n2n2/4p3/2B1P3/8/PPPP1PPP/RNB1K1NR b KQkq - 0 4")
        self.assertTrue(board.is_checkmate())
        self.assertEqual(ai.evaluate_board(board), math.inf)

    def test_checkmate_returns_negative_inf(self):
        """Pretas vencem por xeque-mate → -inf."""
        # Fool's mate: 1.f3 e5 2.g4 Qh4#
        board = chess.Board("rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3")
        self.assertTrue(board.is_checkmate())
        self.assertEqual(ai.evaluate_board(board), -math.inf)

    def test_stalemate_returns_zero(self):
        """Afogamento deve retornar 0."""
        board = chess.Board("k7/2Q5/1K6/8/8/8/8/8 b - - 0 1")
        self.assertTrue(board.is_stalemate())
        self.assertEqual(ai.evaluate_board(board), 0)

    def test_white_material_advantage(self):
        """Brancas com rainha extra → avaliação fortemente positiva."""
        board = chess.Board("4k3/8/8/8/8/8/8/Q3K3 w - - 0 1")
        self.assertGreater(ai.evaluate_board(board), 5.0)

    def test_black_material_advantage(self):
        """Pretas com rainha extra → avaliação fortemente negativa (perspectiva brancas)."""
        board = chess.Board("q3k3/8/8/8/8/8/8/4K3 b - - 0 1")
        self.assertLess(ai.evaluate_board(board), -5.0)


# ---------------------------------------------------------------------------
# _pawn_structure_bonus
# ---------------------------------------------------------------------------
class TestPawnStructure(unittest.TestCase):

    def test_no_pawns_returns_zero(self):
        """Sem peões → bônus exatamente 0 para ambas as cores."""
        board = chess.Board("4k3/8/8/8/8/8/8/4K3 w - - 0 1")
        self.assertEqual(ai._pawn_structure_bonus(board, chess.WHITE), 0.0)
        self.assertEqual(ai._pawn_structure_bonus(board, chess.BLACK), 0.0)

    def test_doubled_pawns_penalty(self):
        """Dois peões brancos na mesma coluna → bônus negativo."""
        # Peões em e3 e e4 (coluna e)
        board = chess.Board("4k3/8/8/8/4P3/4P3/8/4K3 w - - 0 1")
        score = ai._pawn_structure_bonus(board, chess.WHITE)
        self.assertLess(score, 0.0, "Peões dobrados devem gerar penalidade.")

    def test_passed_pawn_advanced_bonus(self):
        """Dois peões passados avançados (rank 6) sem penalidade de isolamento → bônus > 0.5."""
        # d7 e e7: adjacentes entre si (não isolados), nenhum peão preto à frente
        board = chess.Board("4k3/3PP3/8/8/8/8/8/4K3 w - - 0 1")
        score = ai._pawn_structure_bonus(board, chess.WHITE)
        self.assertGreater(score, 0.5, "Peões passados avançados sem isolamento devem dar bônus significativo.")

    def test_passed_pawn_outscores_blocked(self):
        """Peão passado deve pontuar mais que peão bloqueado por adversário."""
        board_passed = chess.Board("4k3/8/8/4P3/8/8/8/4K3 w - - 0 1")  # e5, nenhum preto à frente
        board_blocked = chess.Board("4k3/8/4p3/4P3/8/8/8/4K3 w - - 0 1")  # e5 bloqueado por e6
        self.assertGreater(
            ai._pawn_structure_bonus(board_passed, chess.WHITE),
            ai._pawn_structure_bonus(board_blocked, chess.WHITE),
            "Peão passado deve valer mais que peão bloqueado."
        )

    def test_isolated_pawn_reduces_score(self):
        """Peão isolado deve pontuar menos que peão com suporte lateral."""
        board_iso  = chess.Board("4k3/8/8/8/P7/8/8/4K3 w - - 0 1")   # a4 sem vizinhos
        board_supp = chess.Board("4k3/8/8/8/PP6/8/8/4K3 w - - 0 1")  # a4 + b4 (suporte)
        self.assertLess(
            ai._pawn_structure_bonus(board_iso, chess.WHITE),
            ai._pawn_structure_bonus(board_supp, chess.WHITE),
            "Peão isolado deve pontuar menos que peão com suporte."
        )

    def test_symmetry_equal_pawns(self):
        """Posição simétrica → bônus brancas ≈ bônus pretas (mesma magnitude)."""
        board = chess.Board()  # posição inicial: peões espelhados
        white = ai._pawn_structure_bonus(board, chess.WHITE)
        black = ai._pawn_structure_bonus(board, chess.BLACK)
        self.assertAlmostEqual(white, black, delta=0.5)


# ---------------------------------------------------------------------------
# _king_safety_bonus
# ---------------------------------------------------------------------------
class TestKingSafety(unittest.TestCase):

    def test_no_queens_returns_zero(self):
        """Sem rainhas no tabuleiro → bônus de segurança deve ser 0 (final de jogo)."""
        board = chess.Board("4k3/pppppppp/8/8/8/8/PPPPPPPP/4K3 w - - 0 1")
        self.assertEqual(ai._king_safety_bonus(board, chess.WHITE), 0.0)
        self.assertEqual(ai._king_safety_bonus(board, chess.BLACK), 0.0)

    def test_pawn_shield_beats_exposed_king(self):
        """Rei com escudo de peões intacto (f2,g2,h2) deve superar rei exposto."""
        # Rainha presente → avaliação de segurança ativa
        shielded = chess.Board("4k3/8/8/8/8/8/5PPP/3Q2K1 w - - 0 1")
        exposed  = chess.Board("4k3/8/8/8/8/8/8/3Q2K1 w - - 0 1")
        self.assertGreater(
            ai._king_safety_bonus(shielded, chess.WHITE),
            ai._king_safety_bonus(exposed,  chess.WHITE),
            "Escudo de peões deve gerar bônus maior que rei exposto."
        )

    def test_open_files_penalized(self):
        """Rei com colunas abertas adjacentes deve pontuar menos que rei protegido."""
        open_king   = chess.Board("4k3/8/8/8/8/8/8/4KQ2 w - - 0 1")
        closed_king = chess.Board("4k3/8/8/8/8/8/3PPP2/3QK3 w - - 0 1")
        self.assertGreater(
            ai._king_safety_bonus(closed_king, chess.WHITE),
            ai._king_safety_bonus(open_king,   chess.WHITE),
            "Colunas fechadas perto do rei devem pontuar mais que colunas abertas."
        )


# ---------------------------------------------------------------------------
# minimax
# ---------------------------------------------------------------------------
class TestMinimax(unittest.TestCase):

    def test_captures_hanging_rook(self):
        """Brancas com rainha podendo capturar torre indefesa → valor positivo na profundidade 1."""
        # Rainha branca em d2, torre preta em e3 (indefesa), reis nas bordas
        board = chess.Board("4k3/8/8/8/8/4r3/3Q4/4K3 w - - 0 1")
        deadline = time.monotonic() + 5.0
        val = ai.minimax(board, 1, -math.inf, math.inf, True, deadline, {})
        self.assertGreater(val, 0, "Brancas devem ter avaliação positiva ao capturar a torre.")

    def test_depth_zero_equals_evaluate(self):
        """Na profundidade 0, minimax deve retornar o mesmo que evaluate_board."""
        board = chess.Board()
        deadline = time.monotonic() + 5.0
        # profundidade 0 chama quiescence; para posição sem capturas disponíveis
        # em posição simétrica o resultado deve ser próximo de evaluate_board
        static = ai.evaluate_board(board)
        mini   = ai.minimax(board, 0, -math.inf, math.inf, True, deadline, {})
        self.assertAlmostEqual(mini, static, delta=2.0)


# ---------------------------------------------------------------------------
# find_best_ai_move — testes de ponta a ponta
# ---------------------------------------------------------------------------
class TestFindBestMove(unittest.TestCase):

    def test_takes_free_queen(self):
        """IA deve capturar rainha adversária completamente indefesa."""
        # Rainha branca em d1, rainha preta em d8 indefesa (rei preto longe em a7)
        board = chess.Board("3q4/k7/8/8/8/8/8/3QK3 w - - 0 1")
        move = ai.find_best_ai_move(board, time_limit=1.0)
        self.assertIsNotNone(move)
        self.assertEqual(
            move.to_square, chess.D8,
            f"Esperado Qxd8 mas obteve {move.uci()}"
        )

    def test_checkmate_in_one(self):
        """IA deve entregar xeque-mate em um lance quando disponível."""
        # Scholar's mate: brancas jogam Qxf7#
        board = chess.Board("r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 4 4")
        move = ai.find_best_ai_move(board, time_limit=1.0)
        self.assertIsNotNone(move)
        self.assertEqual(
            move, chess.Move.from_uci("h5f7"),
            f"Esperado Qxf7# mas obteve {move.uci()}"
        )

    def test_returns_legal_move(self):
        """Qualquer posição deve retornar um lance legal."""
        board = chess.Board()
        move = ai.find_best_ai_move(board, time_limit=0.5)
        self.assertIsNotNone(move)
        self.assertIn(move, board.legal_moves, f"Lance {move.uci()} não é legal.")

    def test_no_moves_returns_none(self):
        """Posição sem lances legais (xeque-mate) deve retornar None."""
        board = chess.Board("r1bqkb1r/pppp1Qpp/2n2n2/4p3/2B1P3/8/PPPP1PPP/RNB1K1NR b KQkq - 0 4")
        self.assertTrue(board.is_checkmate())
        move = ai.find_best_ai_move(board, time_limit=0.5)
        self.assertIsNone(move)


if __name__ == "__main__":
    unittest.main(verbosity=2)
