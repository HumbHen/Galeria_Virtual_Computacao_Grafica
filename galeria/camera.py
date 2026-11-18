"""Câmera em primeira pessoa com altura fixa e colisões no plano XZ."""

import glfw
import numpy as np

from .cena import METADE_LARGURA, METADE_PROFUNDIDADE, MEIA_LARGURA_PEDESTAL, PEDESTAIS
from .matrizes import olhar_de, perspectiva


class Camera:
    def __init__(self):
        self.reiniciar()

    def reiniciar(self):
        self.posicao = np.array((0.0, 1.59, 4.30), dtype=np.float32)
        self.yaw = -np.pi / 2
        self.pitch = np.radians(-2)
        self.ultimo_cursor = None

    def mover_mouse(self, janela, x, y):
        if self.ultimo_cursor is not None:
            anterior_x, anterior_y = self.ultimo_cursor
            self.yaw += (x - anterior_x) * .0022
            self.pitch = np.clip(self.pitch + (anterior_y - y) * .0022,
                                 np.radians(-85), np.radians(85))
        self.ultimo_cursor = (x, y)

    def mover_teclado(self, janela, dt):
        def pressionada(tecla):
            return glfw.get_key(janela, tecla) == glfw.PRESS

        frente = pressionada(glfw.KEY_W) - pressionada(glfw.KEY_S)
        lado = pressionada(glfw.KEY_D) - pressionada(glfw.KEY_A)
        if frente == 0 and lado == 0:
            return

        f = np.array([np.cos(self.yaw), np.sin(self.yaw)])
        direita = np.array([-f[1], f[0]])
        passo = (frente * f + lado * direita) * (2.45 * dt / np.hypot(frente, lado))
        x, _, z = self.posicao
        for eixo, destino in ((0, x + passo[0]), (2, z + passo[1])):
            candidato = self.posicao.copy()
            candidato[eixo] = destino
            if self.posicao_livre(candidato[0], candidato[2]):
                self.posicao = candidato

    @staticmethod
    def posicao_livre(x, z):
        raio = .26
        if abs(x) > METADE_LARGURA - raio or abs(z) > METADE_PROFUNDIDADE - raio:
            return False
        # Distância do centro da câmera ao ponto mais perto de cada pedestal.
        for cx, cz in PEDESTAIS:
            dx = max(0, abs(x - cx) - MEIA_LARGURA_PEDESTAL)
            dz = max(0, abs(z - cz) - MEIA_LARGURA_PEDESTAL)
            if dx * dx + dz * dz < raio * raio:
                return False
        return True

    def vista(self):
        frente = np.array([
            np.cos(self.yaw) * np.cos(self.pitch),
            np.sin(self.pitch),
            np.sin(self.yaw) * np.cos(self.pitch),
        ])
        return olhar_de(self.posicao, frente)

    def projecao(self, largura, altura):
        return perspectiva(np.radians(50), largura / altura, .07, 35)
