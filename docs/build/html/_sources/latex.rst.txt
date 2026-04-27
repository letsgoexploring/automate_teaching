``latex`` module
================

This module provides utilities for managing LaTeX files, including compilation, creating figures and tables, and handling Beamer slides.

.. py:function:: compile_latex(x=None, compiler='pdflatex', keep_aux=False)

   Compiles one or more LaTeX files.

   :param x: What to compile.

      - ``None`` — compile all ``.tex`` files in the current directory.
      - ``str`` (directory path) — compile all ``.tex`` files in that directory.
      - ``str`` (file path) — compile a single ``.tex`` file.
      - ``list`` or ``tuple`` — compile each file in the sequence.

      Defaults to None.
   :type x: str, list, or None, optional
   :param compiler: LaTeX compiler executable to use. Common choices are
      ``'pdflatex'``, ``'lualatex'``, and ``'xelatex'``. Defaults to
      ``'pdflatex'``.
   :type compiler: str, optional
   :param keep_aux: If False, delete auxiliary files after compilation. If
      True, keep them (useful for debugging). Defaults to False.
   :type keep_aux: bool, optional
   :raises RuntimeError: If the requested compiler is not found in PATH.
   :raises ValueError: If a string argument is neither a valid directory nor
      a ``.tex`` file.
   :raises TypeError: If ``x`` is not None, a string, or a list/tuple.

.. py:function:: pdf_latex(file_name, compiler='pdflatex', keep_aux=False)

   Compiles a LaTeX file with BibTeX support using a four-pass compilation
   sequence: compiler twice, then BibTeX, then compiler twice more, to resolve
   all cross-references and bibliography entries.

   :param file_name: Path to the ``.tex`` file to compile.
   :type file_name: str
   :param compiler: LaTeX compiler executable. Defaults to ``'pdflatex'``.
   :type compiler: str, optional
   :param keep_aux: If False, delete auxiliary files after compilation.
      Defaults to False.
   :type keep_aux: bool, optional
   :raises RuntimeError: If the compiler or ``bibtex`` is not found in PATH,
      or if any compilation step fails.

.. py:function:: clean_aux_files(file_name)

   Deletes LaTeX auxiliary files in the same directory as the given file.
   Removes files with the following extensions: ``.aux``, ``.log``, ``.out``,
   ``.gz``, ``.snm``, ``.nav``, ``.toc``, ``.blg``, ``.bbl``, ``.vrb``.

   :param file_name: Path to any file in the target directory. The directory
      containing this file is cleaned; the file itself is not deleted.
   :type file_name: str

.. py:function:: make_figure(image_filename, position='h', caption=None, label='', hspace='0cm', height='6.5cm', width=None, caption_top=True, center_image=True, filename=None)

   Builds a LaTeX figure environment string.

   :param image_filename: Path to the image file, as it will appear in the
      LaTeX source.
   :type image_filename: str
   :param position: Float position specifier (``'h'``, ``'t'``, ``'b'``,
      ``'p'``). Defaults to ``'h'``.
   :type position: str, optional
   :param caption: Caption text. Defaults to None.
   :type caption: str, optional
   :param label: Label for cross-referencing. Defaults to ``''``.
   :type label: str, optional
   :param hspace: Horizontal offset applied before the image. Defaults to
      ``'0cm'``.
   :type hspace: str, optional
   :param height: Image height as a LaTeX dimension string. Defaults to
      ``'6.5cm'``.
   :type height: str, optional
   :param width: Image width as a LaTeX dimension string. Defaults to None.
   :type width: str, optional
   :param caption_top: If True, place the caption above the image. Defaults
      to True.
   :type caption_top: bool, optional
   :param center_image: If True, wrap the image in a center environment.
      Defaults to True.
   :type center_image: bool, optional
   :param filename: If provided, write the LaTeX string to this file.
      Defaults to None.
   :type filename: str, optional
   :return: LaTeX source for the figure environment.
   :rtype: str

.. py:function:: make_handout(slides_file_name, handout_file_name)

   Generates a Beamer handout file from a slides file. Inserts ``'handout,'``
   into the ``\documentclass`` options on the first line of the slides file so
   that overlay animations are collapsed.

   Raises ``ValueError`` if the first line of the source file does not contain
   a ``\documentclass[`` declaration, because silently writing a corrupted
   output file would be worse than failing loudly.

   :param slides_file_name: Path to the original Beamer slides file, with or
      without the ``.tex`` extension.
   :type slides_file_name: str
   :param handout_file_name: Path for the generated handout file, with or
      without the ``.tex`` extension.
   :type handout_file_name: str
   :raises ValueError: If the first line of the source file does not contain
      a ``\documentclass[...]`` options block.

.. py:function:: make_tabular(data, table_spec='', row_format=None, column_format=None, hlines=None, clines=None, pos='c', filename=None)

   Builds a LaTeX tabular environment string.

   :param data: 2D array of cell values. Each element is converted to a string.
   :type data: numpy.ndarray
   :param table_spec: Column alignment string (e.g., ``'lcc'``). Defaults to
      ``''``.
   :type table_spec: str, optional
   :param row_format: Row-level formatting. Keys are 1-based row numbers;
      values are lists of LaTeX command names without the leading backslash.
      For example, ``{1: ['textbf']}`` bolds the first row. Defaults to None.
   :type row_format: dict, optional
   :param column_format: Column-level formatting. Same structure as
      ``row_format`` but applied per column. Defaults to None.
   :type column_format: dict, optional
   :param hlines: 1-based row numbers below which a horizontal rule is drawn.
      Use 0 for a rule above the first row. Defaults to None.
   :type hlines: list, optional
   :param clines: Partial horizontal rules. Keys are 1-based row numbers;
      values are lists of column-range strings (e.g.,
      ``{2: ['1-3', '5-6']}``). Defaults to None.
   :type clines: dict, optional
   :param pos: Vertical alignment of the tabular relative to surrounding text
      (``'b'``, ``'c'``, ``'t'``). Defaults to ``'c'``.
   :type pos: str, optional
   :param filename: If provided, write the LaTeX string to this file.
      Defaults to None.
   :type filename: str, optional
   :return: LaTeX source for the tabular environment.
   :rtype: str

.. py:function:: make_table(data, table_spec='', row_format=None, column_format=None, hlines=None, clines=None, position='h', caption=None, label='', caption_top=True, center_table=True, filename=None)

   Builds a LaTeX table environment containing a tabular environment.

   :param data: 2D array of cell values.
   :type data: numpy.ndarray
   :param table_spec: Column alignment string. Defaults to ``''``.
   :type table_spec: str, optional
   :param row_format: Row-level formatting; see ``make_tabular``. Defaults to
      None.
   :type row_format: dict, optional
   :param column_format: Column-level formatting; see ``make_tabular``.
      Defaults to None.
   :type column_format: dict, optional
   :param hlines: Row numbers for horizontal rules; see ``make_tabular``.
      Defaults to None.
   :type hlines: list, optional
   :param clines: Partial horizontal rules; see ``make_tabular``. Defaults to
      None.
   :type clines: dict, optional
   :param position: Float position specifier. Defaults to ``'h'``.
   :type position: str, optional
   :param caption: Caption text. Defaults to None.
   :type caption: str, optional
   :param label: Label for cross-referencing. Defaults to ``''``.
   :type label: str, optional
   :param caption_top: If True, place caption above the table body. Defaults
      to True.
   :type caption_top: bool, optional
   :param center_table: If True, wrap the tabular in a center environment.
      Defaults to True.
   :type center_table: bool, optional
   :param filename: If provided, write the LaTeX string to this file.
      Defaults to None.
   :type filename: str, optional
   :return: LaTeX source for the table environment.
   :rtype: str

.. py:function:: DataFrame_to_array(df, include_index=True, include_column_headers=True, keep_index_name=True)

   Converts a pandas DataFrame to a NumPy array with optional headers and
   index column, suitable for passing directly to ``make_tabular`` or
   ``make_table``.

   :param df: Input DataFrame.
   :type df: pandas.DataFrame
   :param include_index: Whether to include the row index as the first column.
      Defaults to True.
   :type include_index: bool, optional
   :param include_column_headers: Whether to include column headers as the
      first row. Defaults to True.
   :type include_column_headers: bool, optional
   :param keep_index_name: Whether to preserve the index name in the top-left
      cell. Defaults to True.
   :type keep_index_name: bool, optional
   :return: Array representation of the DataFrame, with headers and index
      prepended according to the selected options.
   :rtype: numpy.ndarray

.. py:function:: python_script(script)

   Executes one or more Python scripts as subprocesses. Appends ``.py`` to
   any filename that does not already have that extension.

   :param script: Filename or list of filenames of Python scripts to run.
   :type script: str or list of str
