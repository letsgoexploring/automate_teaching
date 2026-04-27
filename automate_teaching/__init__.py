"""automate_teaching — utilities for exam generation, LaTeX compilation, and Google API integration."""

import numpy as np
import subprocess

from . import google_api
from . import exam
from . import latex


class Homework:
    """Format and export homework answers as LaTeX commands or Gradescope strings.

    Provides methods for storing numeric or string answers, formatting them
    for LaTeX output files, and generating Gradescope-compatible answer strings.
    """

    def __init__(self, filename=None):
        """Initialize a Homework instance.

        Args:
            filename (str, optional): Default filename for LaTeX output.
                Defaults to None.
        """
        self.filename = filename
        self.latex_answers = {}

    def add_latex_answer(self, name, value, precision=4):
        """Add an answer as a LaTeX newcommand entry.

        String values are stored as-is. Numeric values are rounded and
        formatted with the specified number of decimal places.

        Args:
            name (str): Name of the LaTeX command. Must conform to LaTeX
                naming conventions (letters only, no numbers or symbols).
            value (str or numeric): The answer to store.
            precision (int, optional): Decimal places for numeric values.
                Defaults to 4.
        """
        if isinstance(value, str):
            self.latex_answers[name] = value
        else:
            self.latex_answers[name] = ('{0:.' + str(precision) + 'f}').format(value)

    def gs_answer(self, value, tolerance=8, precision=2):
        """Return a Gradescope-compatible formatted answer string.

        Args:
            value (str or numeric): The answer to format.
            tolerance (float, optional): Numeric tolerance for grading.
                Defaults to 8.
            precision (int, optional): Number of decimal places for numeric
                rounding. Defaults to 2.

        Returns:
            str: A Gradescope answer string of the form '[____](=value+-tolerance)'.
        """
        if isinstance(value, str):
            return '[____](=' + value + '+-' + str(tolerance) + ')'
        return '[____](=' + str(np.round(value, precision)) + '+-' + str(tolerance) + ')'

    def write_answer_file(self, filename):
        """Write all stored answers to a LaTeX file as newcommand definitions.

        Appends '.tex' to the filename if it is not already present.

        Args:
            filename (str): Destination file path.
        """
        if not filename.endswith('.tex'):
            filename += '.tex'

        with open(filename, 'w', encoding='utf-8') as newfile:
            for key, item in self.latex_answers.items():
                newfile.write('\\newcommand{\\' + key + '}{' + item + '}\n')


def notebook_to_python(notebook_name):
    """Export a Jupyter notebook to a Python script using nbconvert.

    Args:
        notebook_name (str): Path to the notebook file, with or without
            the '.ipynb' extension.
    """
    if not notebook_name.endswith('.ipynb'):
        notebook_name = notebook_name + '.ipynb'
    subprocess.run(
        ['jupyter', 'nbconvert', '--to', 'script', notebook_name],
        check=True,
    )


def notebook_to_html(notebook_name, execute=False):
    """Export a Jupyter notebook to an HTML file using nbconvert.

    Args:
        notebook_name (str): Path to the notebook file, with or without
            the '.ipynb' extension.
        execute (bool, optional): If True, execute the notebook before
            converting. Defaults to False.
    """
    if not notebook_name.endswith('.ipynb'):
        notebook_name = notebook_name + '.ipynb'

    cmd = ['jupyter', 'nbconvert', '--to', 'html']
    if execute:
        cmd.append('--execute')
    cmd.append(notebook_name)

    subprocess.run(cmd, check=True)
