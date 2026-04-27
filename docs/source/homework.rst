``Homework`` class
==================

.. py:class:: Homework(filename=None)

   Formats and exports homework answers as LaTeX commands or Gradescope
   strings.

   :param filename: Default filename for LaTeX output. Defaults to None.
   :type filename: str, optional

Attributes
----------

.. py:attribute:: filename
   :type: str

   File name for the LaTeX output file.

.. py:attribute:: latex_answers
   :type: dict

   Dictionary for storing answers as LaTeX ``\newcommand`` definitions.

Methods
-------

.. py:method:: add_latex_answer(name, value, precision=4)

   Adds an answer as a LaTeX ``\newcommand`` entry to ``latex_answers``.
   String values are stored as-is. Numeric values are rounded and formatted
   with the specified number of decimal places.

   :param name: Name of the LaTeX command. Must conform to LaTeX naming
      conventions (letters only, no numbers or symbols).
   :type name: str
   :param value: Answer to be stored.
   :type value: str or numeric
   :param precision: Number of decimal places for numeric values. Defaults
      to 4.
   :type precision: int, optional
   :return: None

.. py:method:: gs_answer(value, tolerance=8, precision=2)

   Returns a Gradescope-compatible formatted answer string of the form
   ``'[____](=value+-tolerance)'``.

   :param value: Answer to format.
   :type value: str or numeric
   :param tolerance: Numeric tolerance for grading. Defaults to 8.
   :type tolerance: float, optional
   :param precision: Number of decimal places for rounding numeric values.
      Defaults to 2.
   :type precision: int, optional
   :return: A Gradescope-compatible formatted string.
   :rtype: str

.. py:method:: write_answer_file(filename)

   Writes all stored answers to a LaTeX file as ``\newcommand`` definitions.
   Appends ``.tex`` to the filename if it is not already present.

   :param filename: Destination file path.
   :type filename: str
   :return: None
