import numpy as np
import os
import subprocess

from . import google
from . import exam
from . import latex


##################################################################################################
# latex functions
# from . import latex_tools as latex
# from . import latex_tools as latex

##################################################################################################
# homework class

class homework:
    
    """Class for formatting and saving homework answers in LaTeX or Gradescope formats. This class allows for storing, formatting, and exporting answers as LaTeX commands or Gradescope-compatible strings."""

    def __init__(self, filename=None):
        
        """Initializes an instance of the `homework` class.

        Args:
            filename (str, optional): Name of the LaTeX file to save answers to. Default is None.

        Attributes:
            filename (str): File name for the LaTeX output file.
            latex_answers (dict): Dictionary for storing answers as LaTeX commands.
        """

        # Set filename attribute
        self.filename = filename

        # Initialize dictionary to store answers for LaTeX file
        self.latex_answers = dict()

    def add_latex_answer(self, name, value, precision=4):
        
        """Adds an answer as a LaTeX command to the `latex_answers` dictionary.

        Args:
            name (str): Name of the new LaTeX command. Must conform to LaTeX naming conventions.
            value (str or numeric): Answer to be stored. Strings are stored as-is, numeric values are formatted.
            precision (int): Number of decimal places to round numeric values. Default is 4.

        Returns:
            None

        Adds:
            self.latex_answers[name]: The formatted value as a LaTeX command.
        """

        # If value is a string, do not format
        if type(value) == str:
            self.latex_answers[name] = value

        # If value is numeric, format to string with appropriate number of trailing decimals
        else:
            self.latex_answers[name] = ('{0:.' + str(precision) + 'f}').format(value)

    def gs_answer(self, value, tolerance=8, precision=0.005):
        
        """Generates a Gradescope-compatible formatted string for an answer.

        Args:
            value (str or numeric): Answer to format for Gradescope.
            tolerance (float): Error tolerance for the answer. Default is 8.
            precision (float): Precision for rounding numeric values. Default is 0.005.

        Returns:
            str: A Gradescope-compatible formatted string.
        """

        # If value is a string, do not format
        if type(value) == str:
            return '[____](=' + value + '+-' + str(tolerance) + ')'

        # If value is numeric, format to string with appropriate number of trailing decimals and tolerance
        else:
            return '[____](=' + str(np.round(value, precision)) + '+-' + str(tolerance) + ')'

    def write_answer_file(self, filename):
        
        """Exports LaTeX answers as new commands in a `.tex` file.

        Args:
            filename (str): Name of the LaTeX file to save answers to. Appends `.tex` if missing.

        Returns:
            None
        """

        # Append '.tex' if missing
        if not filename.endswith('.tex'):
            filename += '.tex'

        # Create and save file
        with open(filename, 'w') as newfile:
            # Iterate over elements of self.latex_answers
            for key, item in self.latex_answers.items():
                newfile.write('\\newcommand{\\' + key + '}{' + item + '}\n')


def notebook_to_python(notebook_name):
	
	"""Exports a Jupyter Notebook file to a Python script.

    Args:
        notebook_name (str): Name of the Jupyter Notebook file (with or without `.ipynb` extension).

    Returns:
        None
    """

	if not notebook_name.endswith('.ipynb'):
		notebook_name = notebook_name+'.ipynb'
	shell_command = 'jupyter nbconvert --to script \"'+notebook_name+'\"'
	print(shell_command)
	subprocess.call(shell_command, shell=True)

def notebook_to_html(notebook_name,execute=False):
	
	"""Exports a Jupyter Notebook file to an HTML file.

    Args:
        notebook_name (str): Name of the Jupyter Notebook file (with or without `.ipynb` extension).
        execute (bool): Whether to execute the notebook before converting. Default is False.

    Returns:
        None
    """

	if not notebook_name.endswith('.ipynb'):
		notebook_name = notebook_name+'.ipynb'
	if execute:
		shell_command = 'jupyter nbconvert --execute --to html \"'+notebook_name+'\"'
	else:
		shell_command = 'jupyter nbconvert --to html \"'+notebook_name+'\"'
	print(shell_command)
	subprocess.call(shell_command, shell=True)