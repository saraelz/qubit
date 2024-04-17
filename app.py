import math
import os.path
from dataclasses import dataclass
import gdspy
from SimpleQubit import SimpleQubit
import unittest


@dataclass
class Circle:
    radius: float


@dataclass
class Rectangle:
    width: float
    height: float

    def equals(self, other):
        return (math.isclose(other.width, self.width) and math.isclose(other.height, self.height)) or (math.isclose(other.height,self.width) and math.isclose(other.width,self.height))


def _validate_file(filename: str) -> bool:
    return os.path.isfile(filename)


def _calculate_gdspy_rectangle_dimensions(rectangle: gdspy.polygon.Rectangle) -> Rectangle:
    corners = rectangle.polygons[0]
    dist1 = math.dist(corners[0], corners[1])
    dist2 = math.dist(corners[1], corners[2])
    return Rectangle(dist1, dist2)


class TestSimpleQubit(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.junction = Rectangle(2.0, 0.4)
        self.wire = Rectangle(0.3, 10.0)
        self.connection = Circle(4.0)
        self.offset = self.junction.width / 10.0
        self.layers = {"connection_layer": 0, "wire_layer": 1, "junction_layer": 2}

        self.qubit = SimpleQubit(
            connection_radius=self.connection.radius,
            wire_height=self.wire.height,
            wire_width=self.wire.width,
            junction_offset=self.offset,
            junction_height=self.junction.height,
            junction_width=self.junction.width,
            **self.layers
        )
        self.layout = self.qubit.draw()
        self.shapes = self.qubit.get_polygonsets()

    def test_polygon_count(self):
        self.assertGreaterEqual(len(self.shapes), 5)

    def test_layer_count(self):
        self.assertGreaterEqual(len(self.layout.get_layers()), 3)

    def test_drawing_has_only_expected_layers(self):
        self.assertEqual(set(self.layout.get_layers()), set(self.layers.values()))

    def test_shape_area_greater_than_0(self):
        for shape in self.shapes:
            self.assertGreater(shape.area(), 0)

    def test_shape_type(self):
        for shape in self.shapes:
            self.assertTrue(shape.layers)
            for layer in shape.layers:
                if layer == self.layers["connection_layer"]:
                    self.assertIsInstance(shape, gdspy.polygon.Round)
                elif layer == self.layers["junction_layer"]:
                    self.assertIsInstance(shape, gdspy.polygon.Rectangle)
                elif layer == self.layers["wire_layer"]:
                    self.assertIsInstance(shape, gdspy.polygon.Rectangle)

    def test_shape_dimensions(self):
        for shape in self.shapes:
            self.assertTrue(shape.layers)
            for layer in shape.layers:
                if layer == self.layers["connection_layer"]:
                    actual_radius = math.sqrt(shape.area() / math.pi)
                    self.assertAlmostEqual(self.connection.radius, actual_radius, places=1)
                elif layer == self.layers["junction_layer"]:
                    actual = _calculate_gdspy_rectangle_dimensions(shape)
                    self.assertTrue(Rectangle(self.junction.width, self.junction.height).equals(actual))
                elif layer == self.layers["wire_layer"]:
                    actual = _calculate_gdspy_rectangle_dimensions(shape)
                    self.assertTrue(Rectangle(self.wire.width, self.wire.height).equals(actual))

    def test_offset_range(self):
        self.assertGreater(self.offset, 0)
        self.assertLessEqual(self.offset, self.junction.width / 2)

    def test_polygon_no_gaps(self):
        joined_polygon_set = gdspy.boolean(self.shapes, None, "or", max_points=0)
        test_cell = gdspy.GdsLibrary().new_cell("TEST_POLYGON_NO_GAPS").add(joined_polygon_set)
        test_cell.write_svg('TEST_POLYGON_NO_GAPS.svg')
        self.assertEqual(len(joined_polygon_set.polygons), 1)
        
    def test_svg_export(self):
        output_svg = "output.svg"
        self.qubit.to_svg(filename=output_svg)
        self.assertTrue(_validate_file(filename=output_svg))

    def test_gds_export(self):
        output_gds = "output.gds"
        self.qubit.to_gds(filename=output_gds)
        self.assertTrue(_validate_file(filename=output_gds))

    def test_serialization_and_deserialization(self):
        """
        Returns true if all conditions are met:
        (1) serialize() should write to file
        (2) serialize() should not return ""
        (3) json file exists in directory
        (4) json file matches schema
        (5) deserialize() should not return None object
        """
        output_json = "output.json"
        self.assertTrue(self.qubit.serialize(filename=output_json))
        self.assertTrue(_validate_file(filename=output_json))
        self.assertTrue(self.qubit.from_json_file(filename=output_json))

    def call_draw_function_repeatedly(self):
        self.qubit.draw()
        self.qubit.draw()
        return True


if __name__ == "__main__":
    unittest.main()
