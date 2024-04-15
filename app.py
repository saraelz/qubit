import pdb
from SimpleQubit import SimpleQubit
import math
from dataclasses import dataclass
import gdspy


def _validate_file(filename: str):
    """
    Test if file exists

    Returns True if file is found
    """
    try:
        with open(filename, 'r') as file:
            return True
    except Exception as e:
        print(f"Could not read the file {filename}. \nException: {e}")
        return False


@dataclass
class Circle:
    radius: float


@dataclass
class Rectangle:
    width: float
    height: float


def main():
    """Initialize Dummy Data"""
    junction = Rectangle(2., .4)
    wire = Rectangle(.3, 10.)
    connection = Circle(4.)
    offset = junction.width/10

    # Define three layers
    layers = {
        "connection_layer": 0,
        "wire_layer": 1,
        "junction_layer": 2
    }

    """Initialize SimpleQubit"""
    q = SimpleQubit(connection_radius=connection.radius, wire_height=wire.height, wire_width=wire.width,
                    junction_offset=offset, junction_height=junction.height, junction_width=junction.width, **layers)
    cell = q.draw()

    """Test cases"""
    polygons = q.get_polygonsets()

    print("Test 1: assert that the circuit has at least 5 polygons for a simple qubit")
    assert len(polygons) >= 5

    print("Test 2: assert that there are at least 3 layers in the qubit layout")
    assert len(cell.get_layers()) >= 3
    print("Test 2b: assert that the actual layers match the expected layers")
    assert (set(cell.get_layers()) == set(layers.values()))

    for shape in polygons:

        print("Test 3: assert that area > 0")
        assert shape.area() > 0

        print("Test 3-10: Check the layers")
        assert shape.layers

        for layer in shape.layers:
            if layer == layers['connection_layer']:
                print("Found Connection layer: Executing connection tests")
                print("Test 4: assert that connection is a round shape type")
                assert isinstance(shape, gdspy.polygon.Round)

                print(
                    "Test 5: calculate radius through area() and ensure that it matches expected_radius")
                actual_radius = round(math.sqrt(shape.area()/math.pi), 1)
                assert 4. == actual_radius

            elif layer == layers['junction_layer']:
                print("Found Junction layer. Executing junction tests...")
                print("Test 6: assert that junction is a rectangular shape type")
                assert isinstance(shape, gdspy.polygon.Rectangle)

                print(
                    "Test 7: get corners of rectangle to compare actual and expected distances")
                corners = shape.polygons[0]
                length = round(math.dist(corners[0], corners[1]), 1)
                width = round(math.dist(corners[1], corners[2]), 1)
                assert (length == junction.width and width == junction.height) or (
                    length == junction.height and width == junction.width)

            elif layer == layers['wire_layer']:
                print("Found Wire layer. Executing Wire tests...")
                print("Test 8: check wire is a rectangular shape type")
                assert isinstance(shape, gdspy.polygon.Rectangle)

                print(
                    "Test 9: get corners of rectangle to compare actual and expected distances")
                corners = shape.polygons[0]
                # import math
                length = round(math.dist(corners[0], corners[1]), 1)
                width = round(math.dist(corners[1], corners[2]), 1)
                assert (length == wire.width and width == wire.height) or (
                    length == wire.height and width == wire.width)

    print("End loop")
    print("Test 11: Check offset is within the appropriate range")
    assert offset > 0 and offset <= junction.width/2

    print("Test 12: Check all polygons connected without gaps between polygons")
    combined_polygon_set = gdspy.boolean(polygons, None, 'or')
    assert len(combined_polygon_set.polygons) == 1

    """Export to svg file and gds file"""
    output_svg = 'output.svg'
    output_gds = 'output.gds'
    output_json = 'output.json'

    print("Test 13: Export svg and check that file exists.")
    q.to_svg(filename=output_svg)
    assert _validate_file(filename=output_svg)

    print("Test 14: Export gds and check that file exists.")
    q.to_gds(filename=output_gds)
    assert _validate_file(filename=output_gds)

    """Json tests"""
    print("Test 15: serialize object, export to json")
    q.serialize(filename=output_json)
    print("Test 15b: check that json file exists")
    assert _validate_file(filename=output_json)
    print('Test 16: validate that json matches json schema and deserialize object from json file')
    q.from_json_file(filename=output_json)

    print('All tests passed.')


if __name__ == "__main__":
    main()
