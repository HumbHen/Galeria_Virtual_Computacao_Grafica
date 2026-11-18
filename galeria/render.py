"""Envia malhas, matrizes, materiais e luzes para o pipeline OpenGL."""

import ctypes
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from OpenGL import GL
from OpenGL.GL.shaders import compileProgram, compileShader
from PIL import Image, ImageOps

RAIZ = Path(__file__).resolve().parent.parent


def rgb(hexadecimal):
    """Converte uma cor de projeto sRGB para RGB linear."""
    canais = [int(hexadecimal[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    return tuple(c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4 for c in canais)


class Malha:
    def __init__(self, vertices, indices):
        vertices = np.array(vertices, dtype=np.float32)
        indices = np.array(indices, dtype=np.uint32)
        self.total_indices = len(indices)

        self.vao = GL.glGenVertexArrays(1)
        self.vbo = GL.glGenBuffers(1)
        self.ebo = GL.glGenBuffers(1)

        GL.glBindVertexArray(self.vao)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.vbo)
        GL.glBufferData(GL.GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL.GL_STATIC_DRAW)
        GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, self.ebo)
        GL.glBufferData(GL.GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, GL.GL_STATIC_DRAW)

        passo = 8 * vertices.itemsize
        for local, tamanho, inicio in [(0, 3, 0), (1, 3, 3), (2, 2, 6)]:
            GL.glEnableVertexAttribArray(local)
            GL.glVertexAttribPointer(local, tamanho, GL.GL_FLOAT, GL.GL_FALSE, passo,
                                     ctypes.c_void_p(inicio * vertices.itemsize))
        GL.glBindVertexArray(0)

    def desenhar(self):
        GL.glBindVertexArray(self.vao)
        GL.glDrawElements(GL.GL_TRIANGLES, self.total_indices, GL.GL_UNSIGNED_INT, None)

    def liberar(self):
        GL.glDeleteBuffers(2, [self.vbo, self.ebo])
        GL.glDeleteVertexArrays(1, [self.vao])


def carregar_textura(arquivo, repetir=False):
    # Sequência de upload e filtros trilineares do cubo_textura.py (Aula 17).
    with Image.open(arquivo) as original:
        orientada = ImageOps.exif_transpose(original).convert("RGBA")
    largura, altura = orientada.size
    pixels = orientada.transpose(Image.Transpose.FLIP_TOP_BOTTOM).tobytes()

    textura = GL.glGenTextures(1)
    GL.glBindTexture(GL.GL_TEXTURE_2D, textura)
    GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_SRGB8_ALPHA8, largura, altura, 0,
                    GL.GL_RGBA, GL.GL_UNSIGNED_BYTE, pixels)
    borda = GL.GL_REPEAT if repetir else GL.GL_CLAMP_TO_EDGE
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, borda)
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T, borda)
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR_MIPMAP_LINEAR)
    GL.glGenerateMipmap(GL.GL_TEXTURE_2D)
    GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
    return int(textura), largura / altura


@dataclass(frozen=True)
class Material:
    cor: tuple = (1.0, 1.0, 1.0)
    textura: int = 0
    repeticao: tuple = (1.0, 1.0)
    especular: float = .05
    brilho: float = 20.0
    emissao: float = 0.0


class Renderizador:
    def __init__(self):
        pasta = RAIZ / "shaders"
        self.programa = compileProgram(
            compileShader((pasta / "galeria.vert").read_text(encoding="utf-8"), GL.GL_VERTEX_SHADER),
            compileShader((pasta / "galeria.frag").read_text(encoding="utf-8"), GL.GL_FRAGMENT_SHADER),
        )
        self.locais = {}
        GL.glEnable(GL.GL_DEPTH_TEST)
        GL.glEnable(GL.GL_CULL_FACE)
        GL.glEnable(GL.GL_MULTISAMPLE)
        GL.glClearColor(.08, .10, .11, 1)

    def local(self, nome):
        if nome not in self.locais:
            self.locais[nome] = GL.glGetUniformLocation(self.programa, nome)
        return self.locais[nome]

    def definir_luzes(self, luzes):
        GL.glUseProgram(self.programa)
        for i, luz in enumerate(luzes):
            prefixo = f"uSpots[{i}]."
            GL.glUniform3f(self.local(prefixo + "posicao"), *luz.posicao)
            GL.glUniform3f(self.local(prefixo + "direcao"), *luz.direcao)
            GL.glUniform3f(self.local(prefixo + "cor"), *luz.cor)
            GL.glUniform1f(self.local(prefixo + "cosInterno"), luz.cos_interno)
            GL.glUniform1f(self.local(prefixo + "cosExterno"), luz.cos_externo)
            GL.glUniform1f(self.local(prefixo + "intensidade"), luz.intensidade)

    def iniciar_quadro(self, largura, altura, camera, vista, projecao, spots_ligados):
        GL.glViewport(0, 0, largura, altura)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
        GL.glUseProgram(self.programa)
        GL.glUniformMatrix4fv(self.local("uVista"), 1, GL.GL_FALSE, np.ascontiguousarray(vista.T))
        GL.glUniformMatrix4fv(self.local("uProjecao"), 1, GL.GL_FALSE, np.ascontiguousarray(projecao.T))
        GL.glUniform3f(self.local("uCamera"), *camera)
        GL.glUniform1i(self.local("uSpotsLigados"), spots_ligados)
        GL.glUniform1i(self.local("uTextura"), 0)
        GL.glActiveTexture(GL.GL_TEXTURE0)

    def desenhar(self, malha, modelo, material):
        # Inversa transposta mantém a normal perpendicular sob escala não uniforme.
        normal = np.linalg.inv(modelo[:3, :3]).T
        GL.glUniformMatrix4fv(self.local("uModelo"), 1, GL.GL_FALSE, np.ascontiguousarray(modelo.T))
        GL.glUniformMatrix3fv(self.local("uNormal"), 1, GL.GL_FALSE, np.ascontiguousarray(normal.T))
        GL.glUniform3f(self.local("uCor"), *material.cor)
        GL.glUniform2f(self.local("uRepeticao"), *material.repeticao)
        GL.glUniform1f(self.local("uEspecular"), material.especular)
        GL.glUniform1f(self.local("uBrilho"), material.brilho)
        GL.glUniform1f(self.local("uEmissao"), material.emissao)
        GL.glUniform1i(self.local("uTemTextura"), material.textura != 0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, material.textura)
        malha.desenhar()

    def liberar(self):
        GL.glDeleteProgram(self.programa)
