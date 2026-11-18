"""Transformações em coordenadas homogêneas, com vetores-coluna."""

import numpy as np


def normalizar(vetor):
    return vetor / np.linalg.norm(vetor)


def translacao(x, y, z):
    matriz = np.eye(4, dtype=np.float32)
    matriz[:3, 3] = (x, y, z)
    return matriz


def escala(x, y, z):
    return np.diag([x, y, z, 1]).astype(np.float32)


def rotacao_x(angulo):
    c, s = np.cos(angulo), np.sin(angulo)
    return np.array([[1, 0, 0, 0], [0, c, -s, 0], [0, s, c, 0], [0, 0, 0, 1]],
                    dtype=np.float32)


def rotacao_y(angulo):
    c, s = np.cos(angulo), np.sin(angulo)
    return np.array([[c, 0, s, 0], [0, 1, 0, 0], [-s, 0, c, 0], [0, 0, 0, 1]],
                    dtype=np.float32)


def rotacao_z(angulo):
    c, s = np.cos(angulo), np.sin(angulo)
    return np.array([[c, -s, 0, 0], [s, c, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]],
                    dtype=np.float32)


def perspectiva(fov, aspecto, perto, longe):
    # Matriz de perspectiva usada no exemplo cubo_textura.py (Aula 17).
    f = 1.0 / np.tan(fov / 2.0)
    profundidade = perto - longe
    return np.array([
        [f / aspecto, 0, 0, 0],
        [0, f, 0, 0],
        [0, 0, (longe + perto) / profundidade, (2 * longe * perto) / profundidade],
        [0, 0, -1, 0],
    ], dtype=np.float32)


def olhar_de(posicao, frente):
    direita = normalizar(np.cross(frente, [0, 1, 0]))
    acima = np.cross(direita, frente)
    matriz = np.eye(4, dtype=np.float32)
    matriz[:3, :3] = [direita, acima, -frente]
    matriz[:3, 3] = -matriz[:3, :3] @ posicao
    return matriz
