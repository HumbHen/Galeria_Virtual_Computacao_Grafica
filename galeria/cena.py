"""Planta da sala, obras, materiais e posicionamento dos refletores."""

from dataclasses import dataclass

import numpy as np
from OpenGL import GL

from . import malhas
from .matrizes import escala, normalizar, rotacao_x, rotacao_y, rotacao_z, translacao
from .render import Malha, Material, RAIZ, carregar_textura, rgb

METADE_LARGURA = 5.5
METADE_PROFUNDIDADE = 5.2
ALTURA = 3.62
PEDESTAIS = ((-1.02, -.36), (1.02, -.36))
MEIA_LARGURA_PEDESTAL = .47


@dataclass(frozen=True)
class Quadro:
    arquivo: str
    posicao: tuple
    giro: float = 0.0


QUADROS = (
    Quadro("01.png", (-3.39, 1.77, -5.13)),
    Quadro("02.png", (0.00, 1.77, -5.13)),
    Quadro("03.png", (3.39, 1.77, -5.13)),
    Quadro("04.png", (-5.43, 1.64, -1.78), np.pi / 2),
    Quadro("05.png", (5.43, 1.64, -1.78), -np.pi / 2),
)


@dataclass(frozen=True)
class Spot:
    posicao: np.ndarray
    direcao: np.ndarray
    cor: tuple
    cos_interno: float
    cos_externo: float
    intensidade: float


class Galeria:
    def __init__(self):
        self.cubo = Malha(*malhas.cubo())
        self.plano = Malha(*malhas.quadrado())
        self.toro = Malha(*malhas.toro())
        self.cristal = Malha(*malhas.bipiramide())
        self.objetos = []
        self.texturas = []
        self.luzes = []
        self.moldura = Material(rgb("282522"), especular=.14)
        self.lampada = Material(rgb("343b3d"), especular=.10)
        self.lente = Material(rgb("ffddab"), emissao=.75, especular=0)
        self.bronze = Material(rgb("c88049"), especular=.95, brilho=46)
        self.bronze_claro = Material(rgb("efba70"), especular=.8, brilho=52)
        self.verde = Material(rgb("327a80"), especular=.66, brilho=38)
        self.montar_sala()
        for indice, quadro in enumerate(QUADROS, 1):
            self.montar_quadro(indice, quadro)
        self.montar_pedestais()

    def textura(self, nome, repetir=False):
        identificador, proporcao = carregar_textura(RAIZ / "texturas" / nome, repetir)
        self.texturas.append(identificador)
        return identificador, proporcao

    def caixa(self, posicao, dimensoes, material):
        self.objetos.append((self.cubo, translacao(*posicao) @ escala(*dimensoes), material))

    def montar_sala(self):
        l, p, a = METADE_LARGURA, METADE_PROFUNDIDADE, ALTURA
        cal = Material(rgb("bcb4a4"), especular=0)
        fundo = Material(rgb("354b4a"), especular=.015)
        teto = Material(rgb("a7a093"), especular=0)
        rodape = Material(rgb("605b51"), especular=0)
        piso, _ = self.textura("piso.png", repetir=True)

        self.caixa((0, a / 2, -p - .10), (2 * l, a, .20), fundo)
        self.caixa((0, a / 2, p + .10), (2 * l, a, .20), cal)
        for lado in (-1, 1):
            self.caixa((lado * (l + .10), a / 2, 0), (.20, a, 2 * p + .40), cal)
            self.caixa((lado * (l - .015), .055, 0), (.03, .11, 2 * p), rodape)
        self.caixa((0, .055, -p + .015), (2 * l, .11, .03), rodape)
        self.caixa((0, .055, p - .015), (2 * l, .11, .03), rodape)
        piso_modelo = rotacao_x(-np.pi / 2) @ escala(2 * l, 2 * p, 1)
        self.objetos.append((self.plano, piso_modelo, Material(textura=piso, repeticao=(10, 10))))
        self.caixa((0, a + .06, 0), (2 * l, .12, 2 * p), teto)

        # Trilhos do teto alinham as luminárias às três áreas da sala.
        for z in (-3.46, -.20):
            self.caixa((0, a - .04, z), (9.7, .08, .08), self.lampada)
        self.caixa((0, a - .04, -1.78), (8.3, .08, .08), self.lampada)

        titulo, proporcao = self.textura("titulo.png")
        modelo = translacao(0, 2.90, -p + .008) @ escala(3.80, 3.80 / proporcao, 1)
        self.objetos.append((self.plano, modelo, Material(textura=titulo, emissao=.55, especular=0)))

    def montar_quadro(self, indice, quadro):
        textura, proporcao = self.textura(quadro.arquivo)
        # Encaixe preserva a proporção para fotos horizontais ou verticais.
        largura = min(2.05, 1.34 * proporcao)
        altura = largura / proporcao
        ancora = translacao(*quadro.posicao) @ rotacao_y(quadro.giro)
        self.objetos.extend([
            (self.cubo, ancora @ escala(largura + .13, altura + .13, .065), self.moldura),
            (self.plano, ancora @ translacao(0, 0, .034) @ escala(largura, altura, 1),
             Material(textura=textura, especular=.025, brilho=28)),
        ])
        legenda, proporcao_legenda = self.textura(f"legenda-{indice}.png")
        modelo = ancora @ translacao(0, -altura / 2 - .185, .012) @ escala(.68, .68 / proporcao_legenda, 1)
        self.objetos.append((self.plano, modelo, Material(textura=legenda, emissao=.60, especular=0)))

        frente = np.array([np.sin(quadro.giro), 0, np.cos(quadro.giro)])
        alvo = np.array(quadro.posicao)
        fixacao = alvo + 1.67 * frente
        fixacao[1] = ALTURA - .09
        self.adicionar_spot(fixacao, alvo, 18, 30, 4.1, rgb("ffead5"))

    def montar_pedestais(self):
        plinto = Material(rgb("b5a692"), especular=.03)
        friso = Material(rgb("655344"), especular=.18)
        for i, (x, z) in enumerate(PEDESTAIS):
            self.caixa((x, .04, z), (.94, .08, .94), friso)
            self.caixa((x, .46, z), (.85, .76, .85), plinto)
            self.caixa((x, .875, z), (.94, .07, .94), plinto)
            self.caixa((x, .93, z), (.25, .04, .25), friso)
            legenda, proporcao = self.textura(f"legenda-{6 + i}.png")
            modelo = translacao(x, .71, z + .427) @ escala(.45, .45 / proporcao, 1)
            self.objetos.append((self.plano, modelo, Material(textura=legenda, emissao=.55, especular=0)))
            cor = rgb("ffdeb2") if i == 0 else rgb("d8ecff")
            deslocamento = -.43 if i == 0 else .43
            self.adicionar_spot((x + deslocamento, ALTURA - .09, -.20), (x, 1.42, z), 12, 23, 5.1, cor)

    def adicionar_spot(self, fixacao, alvo, interno, externo, intensidade, cor):
        fixacao = np.array(fixacao)
        direcao = normalizar(np.array(alvo) - fixacao)
        posicao = fixacao + .26 * direcao
        self.luzes.append(Spot(posicao, direcao, cor, np.cos(np.radians(interno)),
                               np.cos(np.radians(externo)), intensidade))

        # O eixo Y local da luminária acompanha o eixo do cone.
        lateral = normalizar(np.cross(direcao, [0, 0, 1]))
        base = np.eye(4, dtype=np.float32)
        base[:3, :3] = np.column_stack((lateral, direcao, np.cross(lateral, direcao)))
        corpo = translacao(*(fixacao + .13 * direcao)) @ base @ escala(.20, .26, .20)
        lente = translacao(*(fixacao + .25 * direcao)) @ base @ escala(.155, .035, .155)
        self.objetos.extend([(self.cubo, corpo, self.lampada), (self.cubo, lente, self.lente)])

    def desenhar(self, renderizador, tempo, spots_ligados):
        for malha, modelo, material in self.objetos:
            # O visor da luminária apaga junto com a contribuição do cone.
            if material is self.lente and not spots_ligados:
                material = self.lampada
            renderizador.desenhar(malha, modelo, material)

        (x, z), (x2, z2) = PEDESTAIS
        orbita = translacao(x, 1.285, z) @ rotacao_y(.38 + tempo * .72)
        renderizador.desenhar(self.toro, orbita @ rotacao_x(.39) @ escala(.78, .78, .78), self.bronze)
        renderizador.desenhar(self.toro, orbita @ rotacao_y(1.44) @ rotacao_z(.45) @ escala(.57, .57, .57),
                              self.bronze_claro)
        dobra = translacao(x2, 1.247, z2) @ rotacao_y(-.36 - tempo * .86) @ rotacao_z(-.16) @ escala(.93, .8, .93)
        renderizador.desenhar(self.cristal, dobra, self.verde)

    def liberar(self):
        for malha in (self.cubo, self.plano, self.toro, self.cristal):
            malha.liberar()
        GL.glDeleteTextures(self.texturas)
