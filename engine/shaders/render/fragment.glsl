#version 330

in vec3 frag_color;
in float frag_intensity;

out vec4 color;

void main() {
    color = vec4(frag_color * frag_intensity, 1.0); // convert to RGBA format
}
