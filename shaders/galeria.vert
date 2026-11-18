#version 330 core

layout(location = 0) in vec3 aPosicao;
layout(location = 1) in vec3 aNormal;
layout(location = 2) in vec2 aUV;

uniform mat4 uModelo;
uniform mat4 uVista;
uniform mat4 uProjecao;
uniform mat3 uNormal;

out vec3 vPosicao;
out vec3 vNormal;
out vec2 vUV;

void main() {
    vec4 mundo = uModelo * vec4(aPosicao, 1.0);
    vPosicao = mundo.xyz;
    vNormal = uNormal * aNormal;
    vUV = aUV;
    gl_Position = uProjecao * uVista * mundo;
}
