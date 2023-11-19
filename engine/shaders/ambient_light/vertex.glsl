#version 330

uniform float intensity;

in vec3 in_vert;
in vec3 in_normal;
in vec3 in_color;
in float in_intensity;
in float in_specular;

out vec3 out_vert;
out vec3 out_normal;
out vec3 out_color;
out float out_intensity;
out float out_specular;

void main() {
    out_intensity = in_intensity + intensity;
    out_vert = in_vert;
    out_color = in_color;
    out_normal = in_normal;
    out_specular = in_specular;
}
