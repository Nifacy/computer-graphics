#version 330

uniform float intensity;
uniform vec3 direction;

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
    float n_dot_l = dot(in_normal, direction);
    float result = 0.0;

    if (n_dot_l > 0) {
        result += intensity * n_dot_l / (length(in_normal) * length(direction));
    }

    if (in_specular != 0.0) {
        vec3 R = in_normal * 2 * dot(in_normal, direction) - direction;
        float r_dot_v = dot(R, -in_vert);

        if (r_dot_v > 0.0) {
            result += pow(r_dot_v / (length(R) * length(in_vert)), in_specular);
        }
    }

    out_vert = in_vert;
    out_normal = in_normal;
    out_color = in_color;
    out_intensity = in_intensity + intensity * result;
    out_specular = in_specular;
}
