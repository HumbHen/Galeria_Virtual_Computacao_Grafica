"""Entre Formas, galeria 3D de Computação Gráfica."""

import sys

import glfw
from OpenGL import GL

from galeria.camera import Camera
from galeria.cena import Galeria
from galeria.render import Renderizador

TITULO = "Entre Formas | WASD + mouse | L: luzes | P: rotação | R: retorno | Esc: sair"


def main():
    if not glfw.init():
        raise RuntimeError("GLFW precisa de uma sessão gráfica para abrir a galeria.")

    try:
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, glfw.TRUE)
        glfw.window_hint(glfw.SAMPLES, 4)
        janela = glfw.create_window(1280, 800, TITULO, None, None)
        if not janela:
            raise RuntimeError("Não foi possível abrir uma janela com OpenGL 3.3 Core.")

        glfw.make_context_current(janela)
        glfw.swap_interval(1)
        glfw.set_input_mode(janela, glfw.CURSOR, glfw.CURSOR_DISABLED)
        if glfw.raw_mouse_motion_supported():
            glfw.set_input_mode(janela, glfw.RAW_MOUSE_MOTION, glfw.TRUE)

        camera = Camera()
        renderizador = Renderizador()
        galeria = Galeria()
        renderizador.definir_luzes(galeria.luzes)
        spots_ligados, animando = True, True
        tempo = 0.0

        def tecla(window, chave, scancode, acao, mods):
            nonlocal spots_ligados, animando
            if acao != glfw.PRESS:
                return
            if chave == glfw.KEY_ESCAPE:
                glfw.set_window_should_close(window, True)
            elif chave == glfw.KEY_L:
                spots_ligados = not spots_ligados
            elif chave == glfw.KEY_P:
                animando = not animando
            elif chave == glfw.KEY_R:
                camera.reiniciar()

        glfw.set_key_callback(janela, tecla)
        glfw.set_cursor_pos_callback(janela, camera.mover_mouse)

        anterior = glfw.get_time()
        while not glfw.window_should_close(janela):
            glfw.poll_events()
            atual = glfw.get_time()
            dt = min(atual - anterior, .05)
            anterior = atual

            largura, altura = glfw.get_framebuffer_size(janela)
            if largura == 0 or altura == 0:
                glfw.wait_events_timeout(.1)
                continue
            camera.mover_teclado(janela, dt)
            if animando:
                tempo += dt
            renderizador.iniciar_quadro(
                largura, altura, camera.posicao, camera.vista(),
                camera.projecao(largura, altura), spots_ligados,
            )
            galeria.desenhar(renderizador, tempo, spots_ligados)
            glfw.swap_buffers(janela)

        galeria.liberar()
        renderizador.liberar()
    finally:
        glfw.terminate()


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, OSError, GL.error.GLError) as erro:
        sys.exit(f"Erro ao iniciar ou executar a galeria: {erro}")
