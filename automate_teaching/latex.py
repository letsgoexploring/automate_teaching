"""Utilities for generating LaTeX environments and compiling LaTeX documents on macOS."""

import subprocess
import shutil
import os
from pathlib import Path


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _is_command_available(command):
    """Check whether a command is available in the system PATH.

    Args:
        command (str): The command name to check (e.g., 'pdflatex').

    Returns:
        bool: True if the command is found, False otherwise.
    """
    return shutil.which(command) is not None


# ---------------------------------------------------------------------------
# LaTeX environment builders
# ---------------------------------------------------------------------------

def make_figure(
    image_filename,
    position='h',
    caption=None,
    label='',
    hspace='0cm',
    height='6.5cm',
    width=None,
    caption_top=True,
    center_image=True,
    filename=None,
):
    """Build a LaTeX figure environment string.

    Args:
        image_filename (str): Path to the image file, as it will appear
            in the LaTeX source.
        position (str, optional): Float position specifier ('h', 't', 'b',
            'p'). Defaults to 'h'.
        caption (str, optional): Caption text. Defaults to None.
        label (str, optional): Label for cross-referencing. Defaults to ''.
        hspace (str, optional): Horizontal offset applied before the image.
            Defaults to '0cm'.
        height (str, optional): Image height (LaTeX dimension string).
            Defaults to '6.5cm'.
        width (str, optional): Image width (LaTeX dimension string).
            Defaults to None.
        caption_top (bool, optional): If True, place the caption above the
            image. Defaults to True.
        center_image (bool, optional): If True, wrap the image in a center
            environment. Defaults to True.
        filename (str, optional): If provided, write the LaTeX string to
            this file. Defaults to None.

    Returns:
        str: LaTeX source for the figure environment.
    """
    figure = '\\begin{figure}[' + position + ']\n'

    if caption is not None and caption_top:
        figure += '\\caption{\\label{' + label + '} ' + caption + '}\n'

    if center_image:
        figure += '\\begin{center}\n'

    figure += '\\hspace*{' + hspace + '}\\includegraphics['
    if height is not None:
        figure += 'height = ' + height
    if width is not None and height is not None:
        figure += ','
    if width is not None:
        figure += 'width = ' + width
    figure += ']{' + image_filename + '}\n'

    if caption is not None and not caption_top:
        figure += '\\caption{' + caption + '}\n'
    if center_image:
        figure += '\\end{center}\n'
    figure += '\\end{figure}'

    if filename is not None:
        try:
            with open(filename, 'w', encoding='utf-8') as nf:
                nf.write(figure)
        except OSError:
            print('Invalid path: ' + filename)

    return figure


def make_tabular(
    data,
    table_spec='',
    row_format=None,
    column_format=None,
    hlines=None,
    clines=None,
    pos='c',
    filename=None,
):
    """Build a LaTeX tabular environment string.

    Args:
        data (numpy.ndarray): 2-D array of cell values. Each element is
            converted to a string.
        table_spec (str, optional): Column alignment string (e.g., 'lcc').
            Defaults to ''.
        row_format (dict, optional): Row-level formatting. Keys are
            1-based row numbers; values are lists of LaTeX command names
            (without the leading backslash). Example: ``{1: ['textbf']}``
            bolds the first row. Defaults to None (no row formatting).
        column_format (dict, optional): Column-level formatting. Same
            structure as row_format but applied per column. Defaults to
            None (no column formatting).
        hlines (list, optional): 1-based row numbers below which a
            horizontal rule is drawn. Use 0 for a rule above the first
            row. Defaults to None.
        clines (dict, optional): Partial horizontal rules. Keys are
            1-based row numbers; values are lists of column-range strings
            (e.g., ``{2: ['1-3', '5-6']}``). Defaults to None.
        pos (str, optional): Vertical alignment of the tabular relative
            to surrounding text ('b', 'c', 't'). Defaults to 'c'.
        filename (str, optional): If provided, write the LaTeX string to
            this file. Defaults to None.

    Returns:
        str: LaTeX source for the tabular environment.
    """
    if row_format is None:
        row_format = {}
    if column_format is None:
        column_format = {}
    if hlines is None:
        hlines = []
    if clines is None:
        clines = {}

    def shift_keys_down_one(dictionary):
        """Return a copy of dictionary with all integer keys decremented by 1.

        Args:
            dictionary (dict): Mapping with integer keys.

        Returns:
            dict: New mapping with keys shifted down by 1.
        """
        return {int(key) - 1: value for key, value in dictionary.items()}

    row_format = shift_keys_down_one(row_format)
    column_format = shift_keys_down_one(column_format)
    clines = shift_keys_down_one(clines)
    hlines = [int(h) - 1 for h in hlines]

    tabular = '\\begin{tabular}[' + pos + ']{' + table_spec + '}'

    if -1 in hlines:  # original value 0 → shifted to -1
        tabular += '\\hline'
    tabular += '\n'

    for row_number, row in enumerate(data):
        row = [str(r) for r in row]

        for col_idx, commands in column_format.items():
            prefix = ''.join('\\' + f + '{' for f in commands)
            row[col_idx] = prefix + row[col_idx] + '}' * len(commands)

        if row_number in row_format:
            commands = row_format[row_number]
            prefix = ''.join('\\' + f + '{' for f in commands)
            row = [prefix + r + '}' * len(commands) for r in row]

        tabular += ' & '.join(row) + '\\\\'

        if row_number in hlines:
            tabular += '\\hline'

        if row_number in clines:
            for fmt_string in clines[row_number]:
                tabular += '\\cline{' + str(fmt_string) + '}'

        tabular += '\n'

    tabular += '\\end{tabular}'

    if filename is not None:
        try:
            with open(filename, 'w', encoding='utf-8') as nf:
                nf.write(tabular)
        except OSError:
            print('Invalid path: ' + filename)

    return tabular


def make_table(
    data,
    table_spec='',
    row_format=None,
    column_format=None,
    hlines=None,
    clines=None,
    position='h',
    caption=None,
    label='',
    caption_top=True,
    center_table=True,
    filename=None,
):
    """Build a LaTeX table environment containing a tabular environment.

    Args:
        data (numpy.ndarray): 2-D array of cell values.
        table_spec (str, optional): Column alignment string. Defaults to ''.
        row_format (dict, optional): Row-level formatting; see make_tabular.
            Defaults to None.
        column_format (dict, optional): Column-level formatting; see
            make_tabular. Defaults to None.
        hlines (list, optional): Row numbers for horizontal rules; see
            make_tabular. Defaults to None.
        clines (dict, optional): Partial horizontal rules; see make_tabular.
            Defaults to None.
        position (str, optional): Float position specifier. Defaults to 'h'.
        caption (str, optional): Caption text. Defaults to None.
        label (str, optional): Label for cross-referencing. Defaults to ''.
        caption_top (bool, optional): If True, place caption above the
            table body. Defaults to True.
        center_table (bool, optional): If True, wrap tabular in a center
            environment. Defaults to True.
        filename (str, optional): If provided, write the LaTeX string to
            this file. Defaults to None.

    Returns:
        str: LaTeX source for the table environment.
    """
    tabular = make_tabular(
        data,
        table_spec=table_spec,
        row_format=row_format,
        column_format=column_format,
        hlines=hlines,
        clines=clines,
    )

    table = '\\begin{table}[' + position + ']\n'

    if caption is not None and caption_top:
        table += '\\caption{\\label{' + label + '} ' + caption + '}\n'

    if center_table:
        table += '\\begin{center}\n'
    table += tabular + '\n'

    if caption is not None and not caption_top:
        table += '\\caption{' + caption + '}\n'
    if center_table:
        table += '\\end{center}\n'
    table += '\\end{table}'

    if filename is not None:
        try:
            with open(filename, 'w', encoding='utf-8') as nf:
                nf.write(table)
        except OSError:
            print('Invalid path: ' + filename)

    return table


def DataFrame_to_array(df, include_index=True, include_column_headers=True, keep_index_name=True):
    """Convert a pandas DataFrame to a NumPy array with optional headers.

    Args:
        df (pandas.DataFrame): Input DataFrame.
        include_index (bool, optional): Whether to include the row index
            as the first column. Defaults to True.
        include_column_headers (bool, optional): Whether to include column
            headers as the first row. Defaults to True.
        keep_index_name (bool, optional): Whether to preserve the index
            name in the top-left cell. Defaults to True.

    Returns:
        numpy.ndarray: Array representation of the DataFrame, with headers
            and index prepended according to the selected options.
    """
    if df.index.name is None or not keep_index_name:
        df.index.name = ''

    retval = df.reset_index().T.reset_index().T.to_numpy()

    if not include_index:
        retval = retval[:, 1:]

    if not include_column_headers:
        retval = retval[1:]

    return retval


# ---------------------------------------------------------------------------
# LaTeX compilation
# ---------------------------------------------------------------------------

def compile_latex(x=None, compiler='pdflatex', keep_aux=False):
    """Compile one or more LaTeX files.

    Args:
        x (str, list, or None, optional): What to compile.

            - None — compile all ``.tex`` files in the current directory.
            - str (directory path) — compile all ``.tex`` files in that
              directory.
            - str (file path) — compile a single ``.tex`` file.
            - list or tuple — compile each file in the sequence.

            Defaults to None.
        compiler (str, optional): LaTeX compiler executable to use.
            Common choices are ``'pdflatex'``, ``'lualatex'``, and
            ``'xelatex'``. Defaults to ``'pdflatex'``.
        keep_aux (bool, optional): If False, delete auxiliary files after
            compilation. If True, keep them (useful for debugging).
            Defaults to False.

    Raises:
        RuntimeError: If the requested compiler is not found in PATH.
        ValueError: If a string argument is neither a valid directory nor a
            ``.tex`` file.
        TypeError: If ``x`` is not None, a string, or a list/tuple.
    """
    if not _is_command_available(compiler):
        raise RuntimeError(f"'{compiler}' is not installed or not found in PATH.")

    # Determine the list of files to compile
    if x is None:
        files_to_compile = [f for f in os.listdir('.') if f.endswith('.tex')]
    elif isinstance(x, str):
        path = Path(x)
        if path.is_dir():
            files_to_compile = sorted(str(f) for f in path.glob('*.tex'))
        elif path.is_file() and path.suffix == '.tex':
            files_to_compile = [str(path)]
        else:
            raise ValueError(f"Unrecognized input path: {x}")
    elif isinstance(x, (list, tuple)):
        files_to_compile = list(x)
    else:
        raise TypeError("`x` must be None, a string path, or a list of filenames.")

    if not files_to_compile:
        print("No .tex files found to compile.")
        return

    for tex_file in files_to_compile:
        tex_path = Path(tex_file)
        print("Compiling: " + tex_path.name)
        try:
            run_args = dict(
                cwd=tex_path.parent,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            cmd = [compiler, '-interaction=nonstopmode', tex_path.name]
            subprocess.run(cmd, **run_args)
            subprocess.run(cmd, **run_args)  # second pass for references
            print("Compiled: " + tex_path.with_suffix('.pdf').name)
        except subprocess.CalledProcessError:
            print("Compilation failed for: " + str(tex_path))

    search_dirs = {Path(f).resolve().parent for f in files_to_compile}

    if not keep_aux:
        aux_exts = (
            '.aux', '.log', '.out', '.gz', '.snm', '.nav',
            '.toc', '.blg', '.bbl', '.vrb', '.fdb_latexmk', '.fls', '.synctex.gz',
        )
        deleted = 0
        for d in search_dirs:
            for ext in aux_exts:
                for f in d.glob(f'*{ext}'):
                    try:
                        f.unlink()
                        deleted += 1
                    except OSError:
                        pass
        if deleted:
            print(f"Deleted {deleted} auxiliary files.")
    else:
        print("Auxiliary files kept.")


def pdf_latex(file_name, compiler='pdflatex', keep_aux=False):
    """Compile a LaTeX file with BibTeX support (four-pass compilation).

    Runs the compiler twice, then BibTeX, then the compiler twice more to
    resolve all cross-references and bibliography entries.

    Args:
        file_name (str): Path to the ``.tex`` file to compile.
        compiler (str, optional): LaTeX compiler executable. Defaults to
            ``'pdflatex'``.
        keep_aux (bool, optional): If False, delete auxiliary files after
            compilation. Defaults to False.

    Raises:
        RuntimeError: If the compiler or bibtex is not found in PATH, or
            if any compilation step fails.
    """
    if not _is_command_available(compiler):
        raise RuntimeError(f"'{compiler}' is not installed or not found in PATH.")
    if not _is_command_available('bibtex'):
        raise RuntimeError("'bibtex' is not installed or not found in PATH.")

    tex_path = Path(file_name).resolve()
    workdir = tex_path.parent
    tex_name = tex_path.name
    bib_name = tex_path.stem + '.aux'

    compiler_cmd = [compiler, '-interaction=nonstopmode', tex_name]
    bibtex_cmd = ['bibtex', bib_name]

    run_args = dict(cwd=workdir, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    try:
        subprocess.run(compiler_cmd, **run_args)
        subprocess.run(compiler_cmd, **run_args)
        subprocess.run(bibtex_cmd, **run_args)
        subprocess.run(compiler_cmd, **run_args)
        subprocess.run(compiler_cmd, **run_args)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Compilation error in {tex_name}: {e}") from e

    if not keep_aux:
        clean_aux_files(file_name)


def clean_aux_files(file_name):
    """Delete LaTeX auxiliary files in the same directory as the given file.

    The following extensions are removed: .aux, .log, .out, .gz, .snm,
    .nav, .toc, .blg, .bbl, .vrb.

    Args:
        file_name (str): Path to any file in the target directory. The
            directory containing this file is cleaned; the file itself is
            not deleted.
    """
    aux_exts = {'.aux', '.log', '.out', '.gz', '.snm', '.nav', '.toc', '.blg', '.bbl', '.vrb'}
    folder = Path(file_name).resolve().parent
    for f in folder.iterdir():
        if f.suffix in aux_exts:
            try:
                f.unlink()
            except OSError:
                pass


def make_handout(slides_file_name, handout_file_name):
    r"""Generate a Beamer handout file from a slides file.

    Inserts 'handout,' into the \documentclass options on the first line
    of the slides file so that overlay animations are collapsed. The
    insertion is done by regex rather than a fixed character offset, so
    the function is robust to slight variations in whitespace or option
    ordering on the documentclass line.

    Raises ValueError if the first line of the source file does not
    contain a \documentclass declaration with an options block (i.e. the
    pattern '\documentclass[' is not found there), because silently
    corrupting the output file would be worse than failing loudly.

    Args:
        slides_file_name (str): Path to the original Beamer slides file,
            with or without the '.tex' extension.
        handout_file_name (str): Path for the generated handout file,
            with or without the '.tex' extension.

    Raises:
        ValueError: If the first non-empty line of the source file does
            not contain a \documentclass options block.
    """
    if not slides_file_name.endswith('.tex'):
        slides_file_name += '.tex'
    if not handout_file_name.endswith('.tex'):
        handout_file_name += '.tex'

    with open(slides_file_name, encoding='utf-8') as old_file:
        lines = old_file.readlines()

    if not lines:
        raise ValueError('Slides file is empty: ' + slides_file_name)

    first_line = lines[0]
    if '\\documentclass[' not in first_line:
        raise ValueError(
            'First line of ' + slides_file_name +
            ' does not contain \\documentclass[...]. Cannot insert handout option.'
        )

    # Insert 'handout,' immediately after the opening bracket of the options list.
    lines[0] = first_line.replace('\\documentclass[', '\\documentclass[handout,', 1)

    with open(handout_file_name, 'w', encoding='utf-8') as new_file:
        new_file.writelines(lines)


def python_script(script):
    """Execute one or more Python scripts as subprocesses.

    Args:
        script (str or list of str): Filename or list of filenames of
            Python scripts to run. The '.py' extension is appended
            automatically if absent.
    """
    if isinstance(script, str):
        script = [script]

    for s in script:
        if not s.endswith('.py'):
            s = s + '.py'
        subprocess.run(['python3', s], check=True)
