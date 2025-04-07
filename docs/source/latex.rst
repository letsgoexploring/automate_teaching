``latex`` module
================

This module provides utilities for managing LaTeX files, including compilation, creating figures, tables, and handling Beamer slides.

.. Functions
.. ---------

.. py:function:: compile(x=None)

   Compiles LaTeX files in the current directory or specified files.

   :param x: Filename or list of filenames to compile. If None, compiles all `.tex` files in the current directory.
   :type x: str or list, optional
   :raises RuntimeError: If `pdflatex` or `bibtex` is not available in the system.

.. py:function:: is_command_available(command)

   Checks if a command is available in the system's PATH.

   :param str command: The command to check.
   :return: True if the command is available, False otherwise.
   :rtype: bool

.. py:function:: make_figure(image_filename, position='h', caption=None, label='', hspace='0cm', height='6.5cm', width=None, caption_top=True, center_image=True, filename=None)

   Constructs a LaTeX figure environment.

   :param str image_filename: Path and filename of the image file.
   :param str position: Position specifier for the figure ('h', 't', 'b', 'p'). Default is 'h'.
   :param caption: Caption for the figure. Default is None.
   :type caption: str, optional
   :param str label: Label for referencing the figure. Default is ''.
   :param str hspace: Horizontal position offset of the image. Default is '0cm'.
   :param str height: Height of the image. Default is '6.5cm'.
   :param str width: Width of the image. Default is None.
   :param bool caption_top: Whether to place the caption above the figure. Default is True.
   :param bool center_image: Whether to center the image in the figure environment. Default is True.
   :param filename: Path to save the generated LaTeX figure file. Default is None.
   :type filename: str, optional
   :return: LaTeX string for the figure environment.
   :rtype: str

.. py:function:: make_handout(slides_file_name, handout_file_name)

   Generates a LaTeX handout file for Beamer slides.

   :param str slides_file_name: Name of the original slides file.
   :param str handout_file_name: Name of the generated handout file.

.. py:function:: make_tabular(data, table_spec='', row_format={}, column_format={}, hlines=[], clines={}, pos='c', filename=None)

   Constructs a LaTeX tabular environment.

   :param numpy.ndarray data: 2D array with data for the table.
   :param str table_spec: Column alignment string for the tabular environment. Default is ''.
   :param dict row_format: Row-specific formatting.
   :param dict column_format: Column-specific formatting.
   :param list hlines: List of row numbers for horizontal lines. Default is [].
   :param dict clines: Dictionary of row numbers and column range strings for clines. Default is {}.
   :param str pos: Vertical positioning specifier ('b', 'c', 't'). Default is 'c'.
   :param filename: Path to save the LaTeX tabular file. Default is None.
   :type filename: str, optional
   :return: LaTeX string for the tabular environment.
   :rtype: str

.. py:function:: make_table(data, table_spec='', row_format={}, column_format={}, hlines=[], clines={}, position='h', caption=None, label='', caption_top=True, center_table=True, filename=None)

   Constructs a LaTeX table environment with tabular content.

   :param numpy.ndarray data: 2D array with data for the table.
   :param str table_spec: Column alignment string for the tabular environment. Default is ''.
   :param dict row_format: Row-specific formatting.
   :param dict column_format: Column-specific formatting.
   :param list hlines: List of row numbers for horizontal lines. Default is [].
   :param dict clines: Dictionary of row numbers and column range strings for clines. Default is {}.
   :param str position: Position specifier for the table ('h', 't', 'b', 'p'). Default is 'h'.
   :param caption: Caption for the table. Default is None.
   :type caption: str, optional
   :param str label: Label for referencing the table. Default is ''.
   :param bool caption_top: Whether to place the caption above the table. Default is True.
   :param bool center_table: Whether to center the table in the environment. Default is True.
   :param filename: Path to save the LaTeX table file. Default is None.
   :type filename: str, optional
   :return: LaTeX string for the table environment.
   :rtype: str

.. py:function:: pdf_latex(file_name)

   Compiles a LaTeX file using `pdflatex`.

   :param str file_name: Name of the LaTeX file to compile.
   :raises RuntimeError: If `pdflatex` or `bibtex` is not available in the system.

.. py:function:: python_script(script)

   Executes a Python script or list of scripts.

   :param script: Filename or list of filenames for Python scripts.
   :type script: str or list
