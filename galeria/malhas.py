"""Malhas criadas por código. Cada vértice tem posição, normal e UV."""

import numpy as np

from .matrizes import normalizar

UV_QUAD = [(0, 0), (1, 0), (1, 1), (0, 1)]


def quadrado():
    vertices = [
        (*ponto, 0, 0, 1, *uv)
        for ponto, uv in zip(
            [(-.5, -.5, 0), (.5, -.5, 0), (.5, .5, 0), (-.5, .5, 0)], UV_QUAD
        )
    ]
    return vertices, [0, 1, 2, 0, 2, 3]


def cubo():
    vertices, indices = [], []
    for normal, eixo_u, eixo_v in [
        ((0, 0, 1), (1, 0, 0), (0, 1, 0)),
        ((0, 0, -1), (-1, 0, 0), (0, 1, 0)),
        ((1, 0, 0), (0, 0, -1), (0, 1, 0)),
        ((-1, 0, 0), (0, 0, 1), (0, 1, 0)),
        ((0, 1, 0), (1, 0, 0), (0, 0, -1)),
        ((0, -1, 0), (1, 0, 0), (0, 0, 1)),
    ]:
        base = len(vertices)
        for u, v in UV_QUAD:
            ponto = 0.5 * np.array(normal) + (u - 0.5) * np.array(eixo_u) + (v - 0.5) * np.array(eixo_v)
            vertices.append((*ponto, *normal, u, v))
        indices.extend(base + i for i in (0, 1, 2, 0, 2, 3))
    return vertices, indices


def toro(fatias=64, lados=24, raio=0.39, tubo=0.086):
    """Superfície de dois parâmetros, com o anel no plano XY."""
    vertices, indices = [], []
    for i in range(fatias + 1):
        u = i / fatias
        cu, su = np.cos(2 * np.pi * u), np.sin(2 * np.pi * u)
        for j in range(lados + 1):
            v = j / lados
            cv, sv = np.cos(2 * np.pi * v), np.sin(2 * np.pi * v)
            normal = (cu * cv, su * cv, sv)
            posicao = (raio * cu + tubo * normal[0], raio * su + tubo * normal[1], tubo * sv)
            vertices.append((*posicao, *normal, u, v))
            if i < fatias and j < lados:
                a = i * (lados + 1) + j
                b = a + lados + 1
                indices.extend((a, b, b + 1, a, b + 1, a + 1))
    return vertices, indices


def bipiramide(lados=5):
    """Faces independentes dão ao cristal arestas com normais descontínuas."""
    vertices, indices = [], []
    angulos = np.arange(lados) * (2 * np.pi / lados)
    cintura = [(np.cos(a) * .36, .04, -np.sin(a) * .36) for a in angulos]
    topo, base = (.11, .60, -.05), (-.05, -.39, .04)
    for i, atual in enumerate(cintura):
        seguinte = cintura[(i + 1) % lados]
        for pontos in ((topo, atual, seguinte), (base, seguinte, atual)):
            a, b, c = np.array(pontos)
            normal = normalizar(np.cross(b - a, c - a))
            for ponto in pontos:
                indices.append(len(vertices))
                vertices.append((*ponto, *normal, 0, 0))
    return vertices, indices
