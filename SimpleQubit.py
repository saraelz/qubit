import json
import gdspy
from jsonschema import validate, ValidationError


class SimpleQubit:
    """
    This class defines a simple circuit layout. It has three components:
    junction, wires, and connections.
    """

    def __init__(
        self,
        connection_radius: float,
        junction_width: float,
        junction_height: float,
        junction_offset: float,
        wire_width: float,
        wire_height: float,
        wire_layer: int,
        junction_layer: int,
        connection_layer: int
    ):
        self.connection_radius = connection_radius
        self.junction_width = junction_width
        self.junction_height = junction_height
        self.wire_width = wire_width
        self.wire_height = wire_height
        self.junction_offset = junction_offset
        self.wire_layer = wire_layer
        self.connection_layer = connection_layer
        self.junction_layer = junction_layer
        self.layout = None
        self.gds_library = None

    def draw(self) -> gdspy.Cell:
        """
        Draw circuit in gds library

        Returns:
            gdspy.Cell: Cell from gds library which contains all components of circuit
        """
        # The GDSII file is called a library, which contains multiple cells.
        self.gds_library = gdspy.GdsLibrary()
        layout = self.gds_library.new_cell("CIRCUIT")
        repeated_component = self.gds_library.new_cell("WIRE_CONNECTION")

        # Create a cell with a component that is used repeatedly.
        w = gdspy.Rectangle(
            (0, 0), (self.wire_width, self.wire_height), layer=self.wire_layer
        )

        c = gdspy.Round(
            (0, self.wire_height), self.connection_radius, layer=self.connection_layer
        )
        repeated_component.add([c, w])

        # Create the layout using repeated components and junction.
        j = gdspy.Rectangle(
            (0, 0),
            (self.junction_width, self.junction_height),
            layer=self.junction_layer,
        )
        wc1 = gdspy.CellReference(
            repeated_component, (0 + self.junction_offset, self.junction_height)
        )
        wc2 = gdspy.CellReference(
            repeated_component,
            (self.junction_width - self.junction_offset, 0),
            rotation=180,
        )
        layout.add([j, wc1, wc2])
        self.layout = layout
        return self.layout

    def to_gds(self, filename: str = "output.gds") -> None:
        """
        Export GDS library to gds file.

        Args:
            filename (str): This is the name of the file export.
        Returns:
            None
        """
        if not self.gds_library:
            self.draw()
        self.gds_library.write_gds(filename)

    def to_svg(self, filename: str = "output.svg") -> None:
        """
        Export cell that contains the qubit layout to svg file.

        Args:
            filename (str): This is the name of the file export.
        Returns:
            None
        """
        if not self.layout:
            self.draw()

        self.layout.write_svg(filename)

    def get_polygonsets(self) -> list:
        """
        Get a list of all polygon instances drawn in the cell that contains the qubit layout.

        Returns:
            list[PolygonSet]
        """
        if not self.layout:
            self.draw()
        return self.layout.get_polygonsets()

    @classmethod
    def get_json_schema(cls):
        """
        Get the json schema used for the class.

        Returns:
            dict: json schema data
        """
        schema = {
            "type": "object",
            "properties": {
                "junction": {
                    "type": "object",
                    "properties": {
                        "junction_width": {"type": "number"},
                        "junction_height": {"type": "number"},
                        "junction_offset": {"type": "number"},
                    },
                    "required": [
                        "junction_width",
                        "junction_height",
                        "junction_offset",
                    ],
                },
                "wire": {
                    "type": "object",
                    "properties": {
                        "wire_width": {"type": "number"},
                        "wire_height": {"type": "number"},
                    },
                    "required": ["wire_width", "wire_height"],
                },
                "connection": {
                    "type": "object",
                    "properties": {"connection_radius": {"type": "number"}},
                    "required": ["connection_radius"],
                },
                "layers": {
                    "type": "object",
                    "properties": {
                        "junction_layer": {"type": "number"},
                        "connection_layer": {"type": "number"},
                        "wire_layer": {"type": "number"},
                    },
                    "required": ["junction_layer", "connection_layer", "wire_layer"],
                },
            },
            "required": ["junction", "wire", "connection", "layers"],
        }
        return schema

    def to_json(self, filename=None) -> str:
        """
        Serialize instance of SimpleQubit into a json in string or file format.

        Args:
            filename (str): Optional name of the file to be written. 
                If None, then do not export to file.
        Returns:
            str: The json data of the instance.
        """
        data = {
            "junction": {
                "junction_width": self.junction_width,
                "junction_height": self.junction_height,
                "junction_offset": self.junction_offset,
            },
            "wire": {
                "wire_width": self.wire_width,
                "wire_height": self.wire_height,
            },
            "connection": {"connection_radius": self.connection_radius},
            "layers": {
                "junction_layer": self.junction_layer,
                "wire_layer": self.wire_layer,
                "connection_layer": self.connection_layer,
            },
        }
        json_string = json.dumps(data)
        if filename is not None:
            with open(filename, "w") as json_file:
                json_file.write(json_string)
        return json_string

    @classmethod
    def from_json(cls, json_string: str):
        """
        Deserialize the json data. Initialize the class from a json.

        Args:
            json_string (str): The json data of the instance.
        Returns:
            SimpleQubit: new instance of SimpleQubit
        """
        data = json.loads(json_string)
        try:
            validate(instance=data, schema=cls.get_json_schema())
        except ValidationError as e:
            print("Validation testing failed. Json file is not compliant with schema.")
            return None
        return cls(
            **data["junction"], **data["wire"], **data["connection"], **data["layers"]
        )

    @classmethod
    def from_json_file(cls, filename: str):
        """
        Deserialize the json data by converting a json file to an instance of SimpleQubit.

        Args:
            filename (str): The name of the json file.
        Returns:
            SimpleQubit: new instance of SimpleQubit
        """
        try:
            with open(filename, "r") as json_file:
                json_string = json_file.read()
                return cls.from_json(json_string)
        except Exception as e:
            print(f"Could not read the json file {json_file}. \nException: {e}")
            return None


if __name__ == "__main__":
    # Define a basic test case to initialize class instance.
    layers = {"connection_layer": 0, "wire_layer": 1, "junction_layer": 2}
    q = SimpleQubit(
        junction_width=2.0,
        junction_height=0.4,
        wire_width=0.3,
        wire_height=10.0,
        connection_radius=4.0,
        junction_offset=1 / 5,
        **layers,
    )
    q.draw()
    q.serialize("first_test.json")
    q.from_json_file("first_test.json")
