import os
import ttp_templates
from typing import Optional, Dict

from ttp import ttp


class AsaTemplates:
    """
    Class augmenting of TTP-templates to implement looking into the template directory for a template
    then defaulting back to the ttp-template if found,
    I would have liked to override the get_template function but the ttp-templates is not a class
    """

    def __init__(self, template_dir: Optional[str] = None):
        if template_dir:
            self.template_dir = template_dir
        elif os.path.isdir(os.path.join(os.path.dirname(__file__), "ttp_templates")):
            self.template_dir = os.path.join(os.path.dirname(__file__), "ttp_templates")
        else:
            self.template_dir = None

    @staticmethod
    def _search_directory():
        return os.path.join(os.path.dirname(__file__), "templates/ttp_templates"), \
               os.path.dirname(ttp_templates.__file__)

    def get_template(self, path: Optional[str] = None,
                     platform: Optional[str] = None,
                     command: Optional[str] = None,
                     yang: Optional[str] = None,
                     misc: Optional[str] = None,
                     ) -> str:
        """
        Function to locate template file and return it's content

        **Valid combinations of template location**

        ``path`` attribute is always more preferred

        * ``path="./misc/foo/bar.txt"``
        * ``platform="cisco_ios", command="show version"``
        * ``yang="ietf-interfaces", platform="cisco_ios"``
        * ``misc="foo_folder/bar_template.txt"``

        :param path: OS path to template to load or to the directory with templates
        :param platform: name of the platform to load template for
        :param command: command to load template for
        :param yang: name of YANG module to load template for
        :param misc: OS path to template within repository misc folder
        """

        try:
            template = self.find_template(path, platform, command, yang, misc)
            return ttp_templates.get_template(path=template)
        except FileNotFoundError:
            raise FileNotFoundError("Template not found")

    def find_template(self, path: Optional[str] = None,
                      platform: Optional[str] = None,
                      command: Optional[str] = None,
                      yang: Optional[str] = None,
                      misc: Optional[str] = None,
                      ) -> str:
        """
            Function to locate template file and return it's path

            **Valid combinations of template location**

            ``path`` attribute is always more preferred

            * ``path="./misc/foo/bar.txt"``
            * ``platform="cisco_ios", command="show version"``
            * ``yang="ietf-interfaces", platform="cisco_ios"``
            * ``misc="foo_folder/bar_template.txt"``

            :param path: OS path to template to load or to the directory with templates
            :param platform: name of the platform to load template for
            :param command: command to load template for
            :param yang: name of YANG module to load template for
            :param misc: OS path to template within repository misc folder
            """
        if path:
            if os.path.isfile(path):
                return path
            elif os.path.isdir(path) and ((platform and command) or (yang and platform)):
                for dirpath, dirnames, filenames in os.walk(path):
                    for filename in filenames:
                        if filename == self.get_intended_filename(platform, command, yang):
                            return os.path.join(dirpath, filename)
        elif self.template_dir and ((platform and command) or (yang and platform)):
            for dirpath, dirnames, filenames in os.walk(self.template_dir):
                for filename in filenames:
                    if filename == self.get_intended_filename(platform, command, yang):
                        return os.path.join(dirpath, filename)
        elif (platform and command) or (yang and platform):
            ttp_templates_path = os.path.dirname(ttp_templates.__file__)
            for dirpath, dirnames, filenames in os.walk(ttp_templates_path):
                for filename in filenames:
                    if filename == self.get_intended_filename(platform, command, yang):
                        return os.path.join(dirpath, filename)
        elif misc:
            return os.path.join(self.template_dir, misc)
        else:
            raise FileNotFoundError("Template not found")

    @staticmethod
    def get_intended_filename(platform: Optional[str] = None,
                              command: Optional[str] = None,
                              yang: Optional[str] = None):
        """
        Function to return the intended filename for a template
        :param platform: name of the platform to load template for
        :param command: command to load template for
        :param yang: name of YANG module to load template for
        :return: intended filename
        """
        if not platform:
            raise ValueError("Platform is required")

        platform = platform.lower()
        for symbol in [" ", "-"]:
            platform = platform.replace(symbol, "_")

        if command:
            command = command.lower()
            command = command.replace("|", "pipe")
            for symbol in [" ", "-"]:
                command = command.replace(symbol, "_")
            path = f"{platform}_{command}.txt"
        elif yang:
            yang = yang.lower()
            for symbol in [" "]:
                yang = yang.replace(symbol, "_")
            path = f"{yang}_{platform}.txt"
        else:
            raise ValueError("Command or YANG module is required")
        return path

    def get_structured_data(self, data: str, path: Optional[str] = None,
                            platform: Optional[str] = None,
                            command: Optional[str] = None,
                            yang: Optional[str] = None,
                            misc: Optional[str] = None,
                            structure: Optional[str] = "list",
                            template_vars: Optional[Dict] = None,
                            ) -> dict:
        """
        Function to return structured data from a template

        **Valid combinations of template location**

        ``path`` attribute is always more preferred

        * ``path="./misc/foo/bar.txt"``
        * ``platform="cisco_ios", command="show version"``
        * ``yang="ietf-interfaces", platform="cisco_ios"``
        * ``misc="foo_folder/bar_template.txt"``

        :param data: data to parse
        :param path: OS path to template to load or to the directory with templates
        :param platform: name of the platform to load template for
        :param command: command to load template for
        :param yang: name of YANG module to load template for
        :param misc: OS path to template within repository misc folder
        :param structure: structure of the output data, can be ``list`` or ``dict``
        :param template_vars: dictionary of variables to be used in the template
        :return: structured data
        """
        template = self.get_template(path, platform, command, yang, misc)
        parser = ttp(data=data, template=template, vars=template_vars)
        parser.parse(one=True)

        return parser.result(structure=structure)
