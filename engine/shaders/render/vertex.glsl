#version 330

uniform vec2 viewSize;

in vec3 in_vert;
in vec3 in_color;

out vec3 frag_color;

void main() {
    vec3 v = in_vert;
    v = vec3(v.x / v.z, -v.y / v.z, v.z / 100.0); // project point on view

    // fit point coordinates to viewSize
    if (viewSize.y < 1.0) {
        v = vec3(v.x * viewSize.y, v.y, v.z);
    } else {
        v = vec3(v.x, v.y / viewSize.y, v.z);
    }

    gl_Position = vec4(v, 1.0);
    frag_color = in_color;
}
