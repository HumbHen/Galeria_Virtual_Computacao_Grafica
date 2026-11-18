#version 330 core

const int TOTAL_SPOTS = 7;

struct Spotlight {
    vec3 posicao;
    vec3 direcao;
    vec3 cor;
    float cosInterno;
    float cosExterno;
    float intensidade;
};

uniform Spotlight uSpots[TOTAL_SPOTS];
uniform bool uSpotsLigados;
uniform vec3 uCamera;
uniform vec3 uCor;
uniform vec2 uRepeticao;
uniform bool uTemTextura;
uniform sampler2D uTextura;
uniform float uEspecular;
uniform float uBrilho;
uniform float uEmissao;

in vec3 vPosicao;
in vec3 vNormal;
in vec2 vUV;
out vec4 corFinal;

vec3 paraSRGB(vec3 cor) {
    vec3 baixa = cor * 12.92;
    vec3 alta = 1.055 * pow(max(cor, vec3(0.0)), vec3(1.0 / 2.4)) - 0.055;
    return mix(alta, baixa, lessThanEqual(cor, vec3(0.0031308)));
}

void main() {
    vec4 amostra = uTemTextura ? texture(uTextura, vUV * uRepeticao) : vec4(1.0);
    if (amostra.a < 0.5) {
        discard;
    }

    // A textura sRGB chega convertida para RGB linear pelo OpenGL.
    vec3 base = uCor * amostra.rgb;
    vec3 normal = normalize(vNormal);
    vec3 observador = normalize(uCamera - vPosicao);
    vec3 acumulada = base * (0.35 + uEmissao);

    if (uSpotsLigados) {
        for (int i = 0; i < TOTAL_SPOTS; i++) {
            Spotlight luz = uSpots[i];
            vec3 paraLuz = luz.posicao - vPosicao;
            float distancia = max(length(paraLuz), 0.001);
            vec3 L = paraLuz / distancia;
            // A direção do cone aponta da fonte para a obra.
            float cosseno = dot(-L, luz.direcao);
            float cone = smoothstep(luz.cosExterno, luz.cosInterno, cosseno);
            if (cone <= 0.0) {
                continue;
            }
            float difusa = max(dot(normal, L), 0.0);
            float especular = 0.0;
            if (difusa > 0.0) {
                vec3 reflexo = reflect(-L, normal);
                especular = uEspecular * pow(max(dot(reflexo, observador), 0.0), uBrilho);
            }
            float atenuacao = luz.intensidade / (1.0 + 0.12 * distancia + 0.23 * distancia * distancia);
            acumulada += cone * atenuacao * luz.cor * (base * difusa + vec3(especular));
        }
    }
    corFinal = vec4(paraSRGB(clamp(acumulada, 0.0, 1.0)), 1.0);
}
