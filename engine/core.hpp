#include <iostream>
#include <algorithm>
#include <vector>
#include <tuple>
#include <cmath>
#include <memory>
#include <cstdint>


using namespace std;


using SceneCoordinate = float;
using CanvasCoordinate = int;


struct Color {
    uint8_t r = 0;
    uint8_t g = 0;
    uint8_t b = 0;
    uint8_t a = 0;
};


struct Vector3 {
    SceneCoordinate x, y, z;

    Vector3 operator + (const Vector3& other) const {
        return Vector3 {
            x + other.x,
            y + other.y,
            z + other.z,
        };
    }

    Vector3 operator - (const Vector3& other) const {
        return Vector3 {
            x - other.x,
            y - other.y,
            z - other.z,
        };
    }

    Vector3 operator * (float coef) const {
        return Vector3 { x * coef, y * coef, z * coef };
    }

    Vector3 Cross(const Vector3& other) const {
        return Vector3 {
            y * other.z - other.y * z,
            z * other.x - x * other.z,
            x * other.y - other.x * y,
        };
    }

    SceneCoordinate Dot(const Vector3& other) const {
        return x * other.x + y * other.y + z * other.z;
    }

    float Length() const {
        return sqrt(x * x + y * y + z * z);
    }
};


struct CanvasPoint {
    CanvasCoordinate x, y;

    bool operator == (const CanvasPoint& other) const {
        return (x == other.x) && (y == other.y);
    }
};


struct Line {
    Vector3 begin, end;
};


struct Triangle {
    Vector3 points[3] = { {0, 0, 0}, {0, 0, 0}, {0, 0, 0} };
    Vector3 normals[3] = { {0, 0, 0}, {0, 0, 0}, {0, 0, 0} };
    Color color = {0, 0, 0, 0};
    float specular = 0.0;
};


class Light {
public:
    float intensity;
    Light(float intensity) : intensity(intensity) {}

    virtual float ComputeIntensity(const Vector3& P, const Vector3& N, float specular) = 0;
};


class AmbientLight : public Light {
public:
    AmbientLight(float intensity) : Light(intensity) {}

    float ComputeIntensity(const Vector3& P, const Vector3& N, float specular) override {
        return 1.0;
    }
};


class PointLight : public Light {
public:
    Vector3 position;
    PointLight(float intensity, const Vector3& position) : Light(intensity), position(position)
    {}

    float ComputeIntensity(const Vector3& P, const Vector3& N, float specular) override {
        Vector3 L = position - P;
        float n_dot_l = N.Dot(L);
        float result = 0.0;
        float x = 0.0;

        if (n_dot_l > 0) {
            result += n_dot_l / (N.Length() * L.Length());
        }

        if (specular != 0.0) {
            Vector3 R = N * 2 * N.Dot(L) - L;
            float r_dot_v = R.Dot(P * (-1));

            if (r_dot_v > 0.0) {
                result += pow(r_dot_v / (R.Length() * P.Length()), specular);
            }
        }

        return result;
    }
};


class DirectionalLight : public Light {
public:
    Vector3 direction;
    DirectionalLight(float intensity, const Vector3& direction) : Light(intensity), direction(direction)
    {}

    float ComputeIntensity(const Vector3& P, const Vector3& N, float specular) override {
        float n_dot_l = N.Dot(direction);
        float result = 0.0;

        if (n_dot_l > 0) {
            result += intensity * n_dot_l / (N.Length() * direction.Length());
        }

        if (specular != 0.0) {
            Vector3 R = N * 2 * N.Dot(direction) - direction;
            float r_dot_v = R.Dot(P * (-1));

            if (r_dot_v > 0.0) {
                result += pow(r_dot_v / (R.Length() * P.Length()), specular);
            }
        }

        return 0.0;
    }
};


class IViewport {
public:
    virtual void PutPixel(const CanvasPoint& point, const Color& color) = 0;
    virtual CanvasCoordinate Width() = 0;
    virtual CanvasCoordinate Height() = 0;
};


class ViewportWithZBuffer {
private:
    vector<vector<SceneCoordinate>> __zbuffer;
    IViewport & __viewport;
    CanvasPoint __center;
    CanvasPoint __size;

    bool CanBeChanged(const CanvasPoint& point, SceneCoordinate z) {
        CanvasCoordinate x = point.x - __center.x, y = point.y - __center.y;

        if ((x < 0) || (y < 0) || (__size.x <= x) || (__size.y <= y)) {
            return false;
        }

        if (z > __zbuffer[y][x]) {
            __zbuffer[y][x] = z; // < move
            return true;
        }

        return false;
    }

public:
    ViewportWithZBuffer(IViewport & viewport) : 
        __zbuffer(viewport.Height(), vector<SceneCoordinate>(viewport.Width(), 0.0f)),
        __viewport(viewport),
        __center { -static_cast<int>(viewport.Width()) / 2, -static_cast<int>(viewport.Height()) / 2 },
        __size { static_cast<int>(viewport.Width()), static_cast<int>(viewport.Height()) }
    { }

    void PutPixel(const CanvasPoint& point, SceneCoordinate z, const Color& color) {
        if (CanBeChanged(point, z)) {
            CanvasCoordinate x = point.x - __center.x, y = point.y - __center.y;
            __viewport.PutPixel(point, color);
        }
    }

    CanvasCoordinate Width() { return __size.x; }
    CanvasCoordinate Height() { return __size.y; }
};


enum class RenderMode {
    WIREFRAME = 1,
    FILL = 2
};


enum class ProjectionType {
    ISOMETRIC = 1,
    PERSPECTIVE = 2
};


struct Config {
    float d;
    float viewSize[2];
    RenderMode mode;
    ProjectionType projection;
};


class Renderer {
private:
    Config __config;

    bool IsBackFacing(const Triangle& triangle) {
        Vector3 v = triangle.points[1] - triangle.points[0];
        Vector3 w = triangle.points[2] - triangle.points[0];
        Vector3 n = v.Cross(w);
        Vector3 h = (triangle.points[0] + triangle.points[1] + triangle.points[2]) * (1.0f / 3.0f);

        return h.Dot(n) < 0.0f;
    }

    CanvasPoint ToCanvasCoordinates(CanvasCoordinate canvasSize[2], float x, float y) {
        return CanvasPoint {
            static_cast<CanvasCoordinate>(x / __config.viewSize[0] * static_cast<float>(canvasSize[0])),
            static_cast<CanvasCoordinate>(y / __config.viewSize[1] * static_cast<float>(canvasSize[1])),
        };
    }

    CanvasPoint PerspectiveProject(CanvasCoordinate canvasSize[2], Vector3 point) {
        return ToCanvasCoordinates(
            canvasSize,
            point.x * __config.d / point.z,
            point.y * __config.d / point.z
        );
    }

    CanvasPoint IsometricProject(CanvasCoordinate canvasSize[2], Vector3 point) {
        return ToCanvasCoordinates(canvasSize, point.x, point.y);
    }

    CanvasPoint ProjectPoint(CanvasCoordinate canvasSize[2], Vector3 point) {
        if (__config.projection == ProjectionType::ISOMETRIC) {
            return IsometricProject(canvasSize, point);
        }
        return PerspectiveProject(canvasSize, point);
    }

    void Interpolate(int i0, float d0, int i1, float d1, vector<float>& values) {
        if (i0 == i1) {
            values.push_back(d0);
            return;
        }

        values.resize(i1 - i0 + 1);
        float a = (d1 - d0) / static_cast<float>(i1 - i0);
        float d = d0;

        for (int t = i0; t <= i1; t++) {
            values[t - i0] = d;
            d += a;
        }
    }

    bool IsOutOfVisibleRange(Vector3 point) {
        return point.z <= __config.d;
    }

    Line CutLine(const Line& line) {
        Vector3 delta = line.end - line.begin;
        float t = (__config.d - line.begin.z) / delta.z;
        Vector3 point = line.begin + delta * t;

        if ((0.0f <= t) && (t <= 1.0f)) {
            if (delta.z > 0) {
                return { point, line.end };
            }

            return { line.begin, point };
        }

        return line;
    }

    void DrawLine(ViewportWithZBuffer& viewport, const Line& line, const Color& color) {
        CanvasCoordinate canvasSize[] { viewport.Width(), viewport.Height() };
        Line _line = line;

        if (IsOutOfVisibleRange(line.begin) && IsOutOfVisibleRange(line.end)) {
            return;
        }

        if (IsOutOfVisibleRange(line.begin) || IsOutOfVisibleRange(line.end)) {
            _line = CutLine(_line);
        }

        pair<CanvasPoint, SceneCoordinate> a { ProjectPoint(canvasSize, _line.begin), _line.begin.z },
                                           b { ProjectPoint(canvasSize, _line.end), _line.end.z };

        // if it as a point
        if (a.first == b.first) {
            viewport.PutPixel(a.first, a.second, color);
        }

        // if it is a horizontal line
        else if (abs(a.first.x - b.first.x) > abs(a.first.y - b.first.y)) {
            if (a.first.x > b.first.x) {
                swap(a, b);
            }

            vector<float> ys, zs;
            Interpolate(a.first.x, a.first.y, b.first.x, b.first.y, ys);
            Interpolate(a.first.x, a.second, b.first.x, b.second, zs);

            for (int i = 0; i <= b.first.x - a.first.x; i++) {
                viewport.PutPixel(
                    { a.first.x + i, static_cast<int>(ys[i]) },
                    zs[i],
                    color
                );
            }
        }

        // if it is a vertical line
        else {
            if (a.first.y > b.first.y) {
                swap(a, b);
            }

            vector<float> xs, zs;
            Interpolate(a.first.y, a.first.x, b.first.y, b.first.x, xs);
            Interpolate(a.first.y, a.second, b.first.y, b.second, zs);

            for (int i = 0; i <= b.first.y - a.first.y; i++) {
                viewport.PutPixel(
                    { static_cast<int>(xs[i]), a.first.y + i },
                    zs[i],
                    color
                );
            }
        }
    }

    void DrawBorderedTriangle(ViewportWithZBuffer& viewport, const Triangle& triangle) {
        DrawLine(viewport, { triangle.points[0], triangle.points[1] }, triangle.color);
        DrawLine(viewport, { triangle.points[1], triangle.points[2] }, triangle.color);
        DrawLine(viewport, { triangle.points[2], triangle.points[0] }, triangle.color);
    }

    float ComputeLighting(
        const Vector3& p,
        const Vector3& n,
        const vector<shared_ptr<Light>>& lights,
        float specular
    ) {
        float totalIntensity = 0.0;

        for(const shared_ptr<Light>& light : lights) {
            float intensityCoef = light->ComputeIntensity(p, n, specular);
            totalIntensity += intensityCoef * light->intensity;
        }

        return totalIntensity;
    }

    void DrawFilledTriangleImpl(
        ViewportWithZBuffer& viewport,
        const Triangle& triangle,
        const vector<shared_ptr<Light>>& lights
    ) {
        if (IsBackFacing(triangle)) {
            return;
        }

        CanvasCoordinate canvasSize[] { viewport.Width(), viewport.Height() };
        tuple<CanvasPoint, SceneCoordinate, float> points[3];

        for (int i = 0; i < 3; i++) {
            points[i] = {
                ProjectPoint(canvasSize, triangle.points[i]),
                triangle.points[i].z,
                ComputeLighting(
                    triangle.points[i], triangle.normals[i],
                    lights, triangle.specular
                )
            };
        }

        sort(
            points, points + 3,
            [] (auto a, auto b) { return get<0>(a).y < get<0>(b).y; }
        );

        CanvasPoint p0 = get<0>(points[0]), p1 = get<0>(points[1]), p2 = get<0>(points[2]);
        float z0 = get<1>(points[0]), z1 = get<1>(points[1]), z2 = get<1>(points[2]);
        float l0 = get<2>(points[0]), l1 = get<2>(points[1]), l2 = get<2>(points[2]);

        vector<float> x02, x012, x12;
        Interpolate(p0.y, p0.x, p2.y, p2.x, x02);
        Interpolate(p0.y, p0.x, p1.y, p1.x, x012);
        Interpolate(p1.y, p1.x, p2.y, p2.x, x12);
        x012.pop_back();
        x012.insert(x012.end(), x12.begin(), x12.end());

        vector<float> z02, z012, z12;
        Interpolate(p0.y, 1 / z0, p2.y, 1 / z2, z02);
        Interpolate(p0.y, 1 / z0, p1.y, 1 / z1, z012);
        Interpolate(p1.y, 1 / z1, p2.y,  1 / z2, z12);
        z012.pop_back();
        z012.insert(z012.end(), z12.begin(), z12.end());

        vector<float> l02, l012, l12;
        Interpolate(p0.y, l0, p2.y, l2, l02);
        Interpolate(p0.y, l0, p1.y, l1, l012);
        Interpolate(p1.y, l1, p2.y,  l2, l12);
        l012.pop_back();
        l012.insert(l012.end(), l12.begin(), l12.end());

        for (int i = 0; i <= (p2.y - p0.y); i++) {
            CanvasCoordinate x1 = x02[i], x2 = x012[i];
            float l1 = l02[i], l2 = l012[i];
            SceneCoordinate z1 = z02[i], z2 = z012[i];

            if (x2 < x1) {
                swap(x1, x2);
                swap(l1, l2);
                swap(z1, z2);
            }

            vector<float> zs, ls;
            Interpolate(x1, z1, x2, z2, zs);
            Interpolate(x1, l1, x2, l2, ls);

            for (int j = 0; j <= x2 - x1; j++) {
                Color color {
                    (unsigned char) min(255.0f, triangle.color.r * ls[j]),
                    (unsigned char) min(255.0f, triangle.color.g * ls[j]),
                    (unsigned char) min(255.0f, triangle.color.b * ls[j]),
                    triangle.color.a
                };

                viewport.PutPixel(
                    { x1 + j, p0.y + i },
                    zs[j],
                    color
                );
            }
        }

    }

    void DrawFilledTriangle(
        ViewportWithZBuffer& viewport,
        const Triangle& triangle,
        const vector<shared_ptr<Light>>& lights
    ) {
        Vector3 a = triangle.points[0], b = triangle.points[1], c = triangle.points[2];

        if (IsOutOfVisibleRange(a) && IsOutOfVisibleRange(b)) {
            a = CutLine({a, c}).begin;
            b = CutLine({b, c}).begin;

            DrawFilledTriangleImpl(
                viewport,
                {
                    { a, b, c },
                    { triangle.normals[0], triangle.normals[1], triangle.normals[2] },
                    triangle.color 
                },
                lights
            );
        
        } else if (IsOutOfVisibleRange(a) && IsOutOfVisibleRange(c)) {
            a = CutLine({a, b}).begin;
            c = CutLine({b, c}).end;

            DrawFilledTriangleImpl(
                viewport,
                {
                    { a, b, c },
                    { triangle.normals[0], triangle.normals[1], triangle.normals[2]},
                    triangle.color
                },
                lights
            );
        
        } else if (IsOutOfVisibleRange(b) && IsOutOfVisibleRange(c)) {
            b = CutLine({a, b}).end;
            c = CutLine({a, c}).end;

            DrawFilledTriangleImpl(
                viewport,
                {
                    { a, b, c },
                    { triangle.normals[0], triangle.normals[1], triangle.normals[2]},
                    triangle.color 
                },
                lights
            );

        } else if (IsOutOfVisibleRange(a)) {
            Vector3 a1 = CutLine({a, b}).begin;
            Vector3 a2 = CutLine({a, c}).begin;

            DrawFilledTriangleImpl(
                viewport,
                {
                    {a1, b, c},
                    { triangle.normals[0], triangle.normals[1], triangle.normals[2]},
                    triangle.color
                },
                lights
            );

            DrawFilledTriangleImpl(
                viewport,
                {
                    {a2, b, c},
                    { triangle.normals[0], triangle.normals[1], triangle.normals[2]},
                    triangle.color
                },
                lights
            );

        } else if (IsOutOfVisibleRange(b)) {
            Vector3 b1 = CutLine({a, b}).end;
            Vector3 b2 = CutLine({b, c}).begin;

            DrawFilledTriangleImpl(
                viewport,
                {
                    {a, b1, c},
                    { triangle.normals[0], triangle.normals[1], triangle.normals[2]},
                    triangle.color
                },
                lights
            );

            DrawFilledTriangleImpl(
                viewport,
                {
                    {a, b2, c},
                    { triangle.normals[0], triangle.normals[1], triangle.normals[2]},
                    triangle.color
                },
                lights
            );
        
        } else if (IsOutOfVisibleRange(c)) {
            Vector3 c1 = CutLine({a, c}).end;
            Vector3 c2 = CutLine({b, c}).end;

            DrawFilledTriangleImpl(
                viewport,
                {
                    {a, b, c1},
                    { triangle.normals[0], triangle.normals[1], triangle.normals[2]},
                    triangle.color
                },
                lights
            );

            DrawFilledTriangleImpl(
                viewport,
                {
                    {a, b, c2},
                    { triangle.normals[0], triangle.normals[1], triangle.normals[2]},
                    triangle.color
                },
                lights
            );
        
        } else {
            DrawFilledTriangleImpl(viewport, triangle, lights);
        }
    }

public:
    Renderer(const Config& config) : __config(config)
    { }

    void Render(IViewport& viewport, const vector<Triangle>& triangles, const vector<shared_ptr<Light>>& lights) {
        ViewportWithZBuffer extendedViewport(viewport);
        
        for (const Triangle& triangle : triangles) {
            if (__config.mode == RenderMode::WIREFRAME) {
                DrawBorderedTriangle(extendedViewport, triangle);
            }
            else {
                DrawFilledTriangle(extendedViewport, triangle, lights);
            }
        }
    }
};
