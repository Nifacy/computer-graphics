#include <iostream>
#include <algorithm>
#include <vector>
#include <tuple>
#include <cmath>
#include <memory>

using namespace std;

using SceneCoordinate = float;
using CanvasCoordinate = int;

struct Color {
    unsigned char r = 0;
    unsigned char g = 0;
    unsigned char b = 0;
    unsigned char a = 0;
};

using Canvas = vector<vector<Color>>;


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
    AmbientLight(double intensity) : Light(intensity) {}

    float ComputeIntensity(const Vector3& P, const Vector3& N, float specular) override {
        return 1.0;
    }
};


class PointLight : public Light {
public:
    Vector3 position;
    PointLight(double intensity, const Vector3& position) : Light(intensity), position(position)
    {}

    float ComputeIntensity(const Vector3& P, const Vector3& N, float specular) override {
        Vector3 L = P - position;
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
    DirectionalLight(double intensity, const Vector3& direction) : Light(intensity), direction(direction)
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


class Viewport {
private:
    vector<vector<SceneCoordinate>> __zbuffer;
    Canvas & __canvas;
    CanvasPoint __center;
    CanvasPoint __size;

    bool CanBeChanged(const CanvasPoint& point, SceneCoordinate z) {
        CanvasCoordinate x = point.x - __center.x, y = point.y - __center.y;

        if ((x < 0) || (y < 0) || (__size.x <= x) || (__size.y <= y)) {
            return false;
        }

        if (z > __zbuffer[y][x]) {
            __zbuffer[y][x] = z;
            return true;
        }

        return false;
    }

public:
    Viewport(Canvas & canvas) : 
        __zbuffer(canvas.size(), vector<SceneCoordinate>(canvas[0].size(), 0.0f)),
        __canvas(canvas),
        __center { -static_cast<int>(canvas[0].size()) / 2, -static_cast<int>(canvas.size()) / 2 },
        __size { static_cast<int>(canvas[0].size()), static_cast<int>(canvas.size()) }
    { }

    void PutPixel(const CanvasPoint& point, SceneCoordinate z, const Color& color) {
        if (CanBeChanged(point, z)) {
            CanvasCoordinate x = point.x - __center.x, y = point.y - __center.y;
            __canvas[__size.y - y - 1][x] = color;
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

    void DrawLine(Viewport& viewport, const Line& line, const Color& color) {
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

    void DrawBorderedTriangle(Viewport& viewport, const Triangle& triangle) {
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
        Viewport& viewport,
        const Triangle& triangle,
        const vector<shared_ptr<Light>>& lights
    ) {
        if (IsBackFacing(triangle)) {
            return;
        }

        Vector3 v = triangle.points[1] - triangle.points[0];
        Vector3 w = triangle.points[2] - triangle.points[0];
        Vector3 n = v.Cross(w);
        Vector3 p = (triangle.points[0] + triangle.points[1] + triangle.points[2]) * (1.0f / 3.0f);

        float lighting = ComputeLighting(p, n, lights, triangle.specular);

        Color color {
            (unsigned char) min(255.0f, triangle.color.r * lighting),
            (unsigned char) min(255.0f, triangle.color.g * lighting),
            (unsigned char) min(255.0f, triangle.color.b * lighting),
            triangle.color.a
        };

        CanvasCoordinate canvasSize[] { viewport.Width(), viewport.Height() };
        pair<CanvasPoint, SceneCoordinate> points[3];

        for (int i = 0; i < 3; i++) {
            points[i] = {
                ProjectPoint(canvasSize, triangle.points[i]),
                triangle.points[i].z,
            };
        }

        sort(
            points, points + 3,
            [] (auto a, auto b) { return a.first.y < b.first.y; }
        );

        CanvasPoint p0 = points[0].first, p1 = points[1].first, p2 = points[2].first;
        float z0 = points[0].second, z1 = points[1].second, z2 = points[2].second;

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

        for (int i = 0; i <= (p2.y - p0.y); i++) {
            CanvasCoordinate x1 = x02[i], x2 = x012[i];
            if (x2 < x1) swap(x1, x2);
            vector<float> zs;
            Interpolate(x1, z02[i], x2, z012[i], zs);

            for (int j = 0; j <= x2 - x1; j++) {
                viewport.PutPixel(
                    { x1 + j, p0.y + i },
                    zs[j],
                    color
                );
            }
        }

    }

    void DrawFilledTriangle(
        Viewport& viewport,
        const Triangle& triangle,
        const vector<shared_ptr<Light>>& lights
    ) {
        Vector3 a = triangle.points[0], b = triangle.points[1], c = triangle.points[2];

        if (IsOutOfVisibleRange(a) && IsOutOfVisibleRange(b)) {
            a = CutLine({a, c}).begin;
            b = CutLine({b, c}).begin;
            DrawFilledTriangleImpl(viewport, { { a, b, c }, triangle.color }, lights);
        
        } else if (IsOutOfVisibleRange(a) && IsOutOfVisibleRange(c)) {
            a = CutLine({a, b}).begin;
            c = CutLine({b, c}).end;
            DrawFilledTriangleImpl(viewport, { { a, b, c }, triangle.color }, lights);
        
        } else if (IsOutOfVisibleRange(b) && IsOutOfVisibleRange(c)) {
            b = CutLine({a, b}).end;
            c = CutLine({a, c}).end;
            DrawFilledTriangleImpl(viewport, { { a, b, c }, triangle.color }, lights);

        } else if (IsOutOfVisibleRange(a)) {
            Vector3 a1 = CutLine({a, b}).begin;
            Vector3 a2 = CutLine({a, c}).begin;
            DrawFilledTriangleImpl(viewport, { {a1, b, c}, triangle.color }, lights);
            DrawFilledTriangleImpl(viewport, { {a2, b, c}, triangle.color }, lights);

        } else if (IsOutOfVisibleRange(b)) {
            Vector3 b1 = CutLine({a, b}).end;
            Vector3 b2 = CutLine({b, c}).begin;
            DrawFilledTriangleImpl(viewport, { {a, b1, c}, triangle.color }, lights);
            DrawFilledTriangleImpl(viewport, { {a, b2, c}, triangle.color }, lights);
        
        } else if (IsOutOfVisibleRange(c)) {
            Vector3 c1 = CutLine({a, c}).end;
            Vector3 c2 = CutLine({b, c}).end;
            DrawFilledTriangleImpl(viewport, { {a, b, c1}, triangle.color }, lights);
            DrawFilledTriangleImpl(viewport, { {a, b, c2}, triangle.color }, lights);
        
        } else {
            DrawFilledTriangleImpl(viewport, triangle, lights);
        }
    }

public:
    Renderer(const Config& config) : __config(config)
    { }

    void Render(Canvas& canvas, const vector<Triangle>& triangles, const vector<shared_ptr<Light>>& lights) {
        Viewport viewport(canvas);
        int i = 0;

        for (const Triangle& triangle : triangles) {
            if (__config.mode == RenderMode::WIREFRAME) {
                DrawBorderedTriangle(viewport, triangle);
            }
            else {
                DrawFilledTriangle(viewport, triangle, lights);
            }
            i++;
        }
    }
};

void PrintCanvas(const Canvas & canvas) {
    for (size_t j = 0; j < canvas.size(); j++) {
        for (size_t i = 0; i < canvas[j].size(); i++) {
            const Color& color = canvas[j][i];
            cout.write(reinterpret_cast<const char*>(&(color.r)), sizeof(color.r));
            cout.write(reinterpret_cast<const char*>(&(color.g)), sizeof(color.g));
            cout.write(reinterpret_cast<const char*>(&(color.b)), sizeof(color.b));
            cout.write(reinterpret_cast<const char*>(&(color.a)), sizeof(color.a));
        }
    }

    cout.write("\n", 1);
    cout.flush();
}

void ReadConfig(Config& config) {
    string renderMode, projectionType;

    cin >> config.d;
    cin >> config.viewSize[0] >> config.viewSize[1];
    cin >> renderMode >> projectionType;

    if (renderMode == "wireframe") {
        config.mode = RenderMode::WIREFRAME;
    } else {
        config.mode = RenderMode::FILL;
    }

    if (projectionType == "isometric") {
        config.projection = ProjectionType::ISOMETRIC;
    } else {
        config.projection = ProjectionType::PERSPECTIVE;
    }
}


void ReadLights(vector<shared_ptr<Light>>& lights) {
    size_t lightObjectAmount;
    string type;

    cin >> lightObjectAmount;

    while (lightObjectAmount > 0) {
        cin >> type;

        if (type == "ambient") {
            double intensity;
            cin >> intensity;
            lights.push_back(make_shared<AmbientLight>(intensity));
        }

        else if (type == "point") {
            double intensity;
            Vector3 position;
            cin >> intensity >> position.x >> position.y >> position.z;
            lights.push_back(make_shared<PointLight>(intensity, position));
        }

        else if (type == "directional") {
            double intensity;
            Vector3 direction;
            cin >> intensity >> direction.x >> direction.y >> direction.z;
            lights.push_back(make_shared<DirectionalLight>(intensity, direction));
        }

        lightObjectAmount--;
    }
}


void ReadTriangles(vector<Triangle>& triangles) {
    int trianglesAmount;
    int r, g, b;

    cin >> trianglesAmount;
    triangles.resize(trianglesAmount);

    for (Triangle& triangle : triangles) {
        for (Vector3& point : triangle.points) {
            cin >> point.x >> point.y >> point.z;
        }

        cin >> r >> g >> b;
        triangle.color = {
            static_cast<unsigned char>(r),
            static_cast<unsigned char>(g),
            static_cast<unsigned char>(b),
            255
        };

        cin >> triangle.specular;
    }
}


int main() {
    ios_base::sync_with_stdio(false);
    cin.tie(0);
    cout.tie(0);

    while (!cin.eof()) {
        Config config;
        CanvasCoordinate width, height;
        vector<Triangle> triangles;
        vector<shared_ptr<Light>> lights;

        ReadConfig(config);
        cin >> width >> height;

        ReadLights(lights);
        ReadTriangles(triangles);

        Renderer renderer(config);
        Canvas canvas(height, vector<Color>(width));

        renderer.Render(canvas, triangles, lights);
        PrintCanvas(canvas);
    }

    return 0;
}
