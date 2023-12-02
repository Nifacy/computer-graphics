#version 330

in vec4 frag_color;
in float frag_intensity;

out vec4 color;

void main() {
    color = vec4(frag_color.xyz * frag_intensity, frag_color.a);
}
