import json
from pathlib import Path

# from PetroGeoSim.models import Model
from PetroGeoSim.properties import Property


class Templates:
    """Offers a way to work with templates of inputs and results.

    Can show and get all the specified input and result properties,
    that are stored in 'templates' folder.

    Attributes
    ----------
    templates : dict
        Exposure in seconds.
    available : tuple
        Available templates from `templates` folder.

    Methods
    -------
    load(code)
        Represent the photo in the given colorspace.
    show()
        Change the photo's gamma exposure.
    get(*props)
        Change the photo's gamma exposure.
    create(n=1.0)
        Change the photo's gamma exposure.
    """

    __slots__ = ("templates", "available")

    def __init__(self) -> None:
        self.templates = {}
        self.available = tuple(
            temp.stem for temp in Path('PetroGeoSim/templates/').iterdir()
        )

    def load(self, code: str) -> None:
        """Loads input and result Properties.

        All input and result Properties for a specified
        language code (ru, en, de, etc.) are loaded at once.

        Parameters
        ----------
        code : str
            A language code that matches a JSON file with localized templates.

        Raises
        ------
        KeyError
            There is no template for the provided code.

        Examples
        --------
        >>> template.load('en')
        """

        if code not in self.available:
            raise KeyError(f"No template found for code {code}")

        with open(f"PetroGeoSim/templates/{code}.json",
                  "r", encoding='utf8') as fp:
            self.templates = json.load(fp=fp)

    def show(self) -> None:
        """Prints all loaded input and result Properties.

        If nothing was loaded, prints an empty string.

        Examples
        --------
        >>> template.show()
        Inputs:
        * Areas
        * Reservoir thickness
        * Porosity
        * Oil saturation
        * Net-to-gross
        * Formation volume factor
        * Oil density
        * Geometric correction factor
        Results:
        * Total hydrocarbons in-place
        """

        result = ''
        if self.templates:
            result = '\n'.join(
                (key+":\n* "+'\n* '.join(value)
                    for key, value in self.templates.items())
            )

        print(result)

    def get(self, *props: tuple[str]) -> dict:
        """Returns input and result Properties.

        The Properties to get are specified as positional arguments.

        Returns
        -------
        dict
            A dictionary with requested properties in the following format:
            Readable name -> Initialized Property object.

        Examples
        --------
        >>> template.get('Water saturation', 'Oil-water contact')

        """

        template_props = {}

        for opt in props:
            if opt in self.templates["Inputs"]:
                template_props[opt] = Property(
                    opt, self.templates["Inputs"][opt]
                )
            if opt in self.templates["Results"]:
                var, eq = self.templates["Results"][opt]
                template_props[opt] = Property(
                    opt, var, equation=eq
                )
            else:
                print(
                    f"Found invalid template name: {opt}\nSkipping..."
                )

        return template_props

    def create(self, name: str, variable: str, formula: str, code: str = 'ru'):
        """
        Creates new input or/and result Properties and
        add them to a specified language code JSON.
        """
        pass
