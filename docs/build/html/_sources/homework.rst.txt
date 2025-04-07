``homework`` class
==================

.. This class formats and saves homework answers in LaTeX or Gradescope formats.

.. py:class:: homework(filename=None)

   Initializes an instance of the `homework` class.

   :param filename: Name of the LaTeX file to save answers to. Default is None.
   :type filename: str, optional

Attributes
----------
.. py:attribute:: filename
   :type: str

   File name for the LaTeX output file.

.. py:attribute:: latex_answers
   :type: dict

   Dictionary for storing answers as LaTeX commands.

Methods
-------
.. py:method:: add_latex_answer(name, value, precision=4)

   Adds an answer as a LaTeX command to the `latex_answers` dictionary.

   :param name: Name of the new LaTeX command. Must conform to LaTeX naming conventions.
   :type name: str
   :param value: Answer to be stored. Strings are stored as-is, numeric values are formatted.
   :type value: str or numeric
   :param precision: Number of decimal places to round numeric values. Default is 4.
   :type precision: int, optional
   :returns: None
   :rtype: None

   Adds:
      - :py:attr:`latex_answers[name]`: The formatted value as a LaTeX command.

.. py:method:: gs_answer(value, tolerance=8, precision=0.005)

   Generates a Gradescope-compatible formatted string for an answer.

   :param value: Answer to format for Gradescope.
   :type value: str or numeric
   :param tolerance: Error tolerance for the answer. Default is 8.
   :type tolerance: float, optional
   :param precision: Precision for rounding numeric values. Default is 0.005.
   :type precision: float, optional
   :return: A Gradescope-compatible formatted string.
   :rtype: str

.. py:method:: write_answer_file(filename)

   Exports LaTeX answers as new commands in a `.tex` file.

   :param filename: Name of the LaTeX file to save answers to. Appends `.tex` if missing.
   :type filename: str
   :returns: None
   :rtype: None