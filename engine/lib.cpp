#include "core.hpp"


extern "C" {
    typedef uint8_t ColorDTO[4];
    typedef float Vector3DTO[3];

    struct TriangleDTO {
        Vector3DTO points[3];
        Vector3DTO normals[3];
        ColorDTO color;
        float specular;
    };

    enum LightType {
        AMBIENT = 0,
        POINT = 1,
        DIRECTION = 2
    };

    struct LightDTO {
        LightType type;
        float intensity;
        Vector3DTO position;
    };

    struct Canvas {
        ColorDTO* pixels;
        int width;
        int height;
    };

    struct ConfigDTO {
        float d;
        float viewSize[2];
        int mode;
        int projection;
    };
}


Color DeserializeColor(ColorDTO color) {
    return {
        .r = color[0],
        .g = color[1],
        .b = color[2],
        .a = color[3],
    };
}


Vector3 DeserializeVector(Vector3DTO vector) {
    return {
        .x = vector[0],
        .y = vector[1],
        .z = vector[2],
    };
}


Triangle DeserializeTriangle(TriangleDTO triangle) {
    return {
        .points = {
            DeserializeVector(triangle.points[0]),
            DeserializeVector(triangle.points[1]),
            DeserializeVector(triangle.points[2]),
        },

        .normals = {
            DeserializeVector(triangle.normals[0]),
            DeserializeVector(triangle.normals[1]),
            DeserializeVector(triangle.normals[2]),
        },

        .color = DeserializeColor(triangle.color),
        .specular = triangle.specular,
    };
}


Light* DeserializeLight(LightDTO light) {
    switch(light.type) {
        case AMBIENT:
            return new AmbientLight(light.intensity);
        break;

        case POINT:
            return new PointLight(light.intensity, DeserializeVector(light.position));
        break;

        default:
            return new DirectionalLight(light.intensity, DeserializeVector(light.position));
        break;
    }
}


Config DeserializeConfig(ConfigDTO config) {
    RenderMode mode;
    ProjectionType projection;

    switch (config.mode) {
        case 1:
            mode = RenderMode::WIREFRAME;
        break;

        case 2:
            mode = RenderMode::FILL;
        break;
    }

    switch (config.projection) {
        case 1:
            projection = ProjectionType::ISOMETRIC;
        break;

        case 2:
            projection = ProjectionType::PERSPECTIVE;
        break;
    }
    
    return {
        .d = config.d,
        .viewSize = { config.viewSize[0], config.viewSize[1] },
        .mode = mode,
        .projection = projection
    };
}


class CanvasViewport : public IViewport {
private:
    Canvas __canvas;

    bool ValidateCoordinates(int x, int y) {
        if (x < 0 || __canvas.width <= x) {
            return false;
        }

        if (y < 0 || __canvas.height <= y) {
            return false;
        }

        return true;
    }

public:
    CanvasViewport(const Canvas& canvas) : __canvas(canvas)
    {}

    void PutPixel(const CanvasPoint& point, const Color& color) override {
        int cx = __canvas.width / 2, cy = __canvas.height / 2;
        int x = point.x + cx, y = cy - point.y;

        if (!ValidateCoordinates(x, y)) {
            return;
        }

        size_t index = y * __canvas.width + x;

        __canvas.pixels[index][0] = color.r;
        __canvas.pixels[index][1] = color.g;
        __canvas.pixels[index][2] = color.b;
        __canvas.pixels[index][3] = color.a;
    }

    CanvasCoordinate Width() override {
        return __canvas.width;
    }
    CanvasCoordinate Height() override {
        return __canvas.height;
    }
};


extern "C" {
    void Render(
        ConfigDTO config,
        Canvas canvas,
        TriangleDTO* triangles,
        size_t trianglesAmount,
        LightDTO* lights,
        size_t lightsAmount
    ) {
        Renderer renderer(DeserializeConfig(config));
        CanvasViewport viewport(canvas);
        vector<Triangle> t;
        vector<shared_ptr<Light>> l;

        for (size_t i = 0; i < trianglesAmount; i++) {
            t.push_back(DeserializeTriangle(triangles[i]));
        }

        for (size_t i = 0; i < lightsAmount; i++) {
            shared_ptr<Light> light(DeserializeLight(lights[i]));
            l.push_back(light);
        }

        renderer.Render(viewport, t, l);
    }
}
