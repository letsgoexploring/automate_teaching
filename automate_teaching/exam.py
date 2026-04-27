import pandas as pd
import numpy as np
from copy import deepcopy
import string
import re
from pathlib import Path

# ---------------------------------------------------------------------------
# Module-level regex constants
# ---------------------------------------------------------------------------

_UNESCAPED_PERCENT_RE = re.compile(r'(?<!\\)%')


# ---------------------------------------------------------------------------
# Module-level LaTeX text helpers
# ---------------------------------------------------------------------------

def _split_option_comment(option):
    """Split one option into (main_text, comment_text, had_comment).

    Splits at the first unescaped '%' after the '\\item' prefix.
    Escaped percents ('\\%') are left in the main text.

    Args:
        option (str): A single answer option string, optionally starting
            with '\\item'.

    Returns:
        tuple: A three-element tuple (main, comment, had_comment) where
            main (str) is the body text before any comment, comment (str)
            is the text after the '%', and had_comment (bool) indicates
            whether a '%' was present.
    """
    s = option.strip()
    body = s[len('\\item'):].lstrip() if s.startswith('\\item') else s
    m = _UNESCAPED_PERCENT_RE.search(body)
    if not m:
        return body.rstrip(), "", False
    main = body[:m.start()].rstrip()
    comment = body[m.end():].strip()
    return main, comment, True


def _has_correct(text, correct_token):
    """Check whether text contains the correct-answer token.

    Uses a word-boundary, case-insensitive search so partial matches
    (e.g., 'INCORRECTLY') are not flagged.

    Args:
        text (str): The text to search.
        correct_token (str): The token to look for (e.g., 'CORRECT').

    Returns:
        bool: True if the token is found as a whole word, False otherwise.
    """
    return re.search(rf'\b{re.escape(correct_token)}\b', text, flags=re.IGNORECASE) is not None


def _strip_correct_tokens(text, correct_token):
    """Remove all occurrences of the correct-answer token from text.

    Args:
        text (str): Source text.
        correct_token (str): The token to remove (e.g., 'CORRECT').

    Returns:
        str: The text with all token occurrences removed and whitespace
            stripped.
    """
    return re.sub(rf'\b{re.escape(correct_token)}\b', '', text, flags=re.IGNORECASE).strip()


def _ensure_trailing_sentence_punct(text):
    """Append a period to text if it does not already end with sentence punctuation.

    Args:
        text (str): Input text.

    Returns:
        str: Text ending with '.', '!', or '?'.
    """
    if not text:
        return text
    return text if text.endswith(('.', '!', '?')) else (text + '.')


def _normalize_comment_tail(raw_comment, is_correct, correct_token):
    """Normalize a LaTeX comment tail for an answer option.

    Removes any existing correct-answer tokens from the comment, ensures
    terminal punctuation, then appends the token at the very end if the
    option is correct.

    Args:
        raw_comment (str): The raw comment text (the part after '%').
        is_correct (bool): Whether this option is the correct answer.
        correct_token (str): The marker string for the correct answer.

    Returns:
        str: The normalized comment tail.
    """
    tail = _strip_correct_tokens(raw_comment, correct_token)
    tail = _ensure_trailing_sentence_punct(tail) if tail else tail
    if is_correct:
        tail = (tail + '  ' + correct_token).strip()
    return tail


def _rebuild_option(main, comment):
    """Reconstruct a single answer option as a LaTeX item string.

    Args:
        main (str): The main body text of the option.
        comment (str): The comment text (without the leading '%'), or an
            empty string if there is no comment.

    Returns:
        str: A string of the form '\\item <main>' or
            '\\item <main> % <comment>'.
    """
    return ('\\item ' + main) if not comment else ('\\item ' + main + ' % ' + comment)


# ---------------------------------------------------------------------------
# Module-level structural helpers (shared across all classes)
# ---------------------------------------------------------------------------

def _get_question_length(mc_lines, starting_line_number):
    """Count the number of lines that a single MC question spans.

    A question is complete once two balanced brace pairs have been closed
    — the header pair and the options-block pair.

    Args:
        mc_lines (list of str): Full list of lines being parsed.
        starting_line_number (int): Index of the line where the question
            begins.

    Returns:
        int: Number of lines from starting_line_number that belong to
            this question.
    """
    total_lines = len(mc_lines)
    left = right = pairs = 0
    open_outer = False

    for i in range(total_lines - starting_line_number):
        for char in mc_lines[starting_line_number + i]:
            if char == '{':
                left += 1
                if not open_outer:
                    open_outer = True
            elif char == '}':
                right += 1
            if left - right == 0 and open_outer:
                pairs += 1
                open_outer = False
            if pairs == 2:
                break
        else:
            continue
        break
    return i + 1


def _filter_visibility(text, reveal=False):
    """Remove LaTeX blocks that should not appear in the current output version.

    Strips 'keyonly' environments from student exams and 'examonly'
    environments from answer keys.

    Args:
        text (str): LaTeX source text.
        reveal (bool, optional): If True, produce the key version (remove
            examonly blocks). If False, produce the student version (remove
            keyonly blocks). Defaults to False.

    Returns:
        str: Filtered LaTeX text.
    """
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    if reveal:
        text = re.sub(r'(?s)\\begin\s*\{examonly\}.*?\\end\s*\{examonly\}', '', text)
    else:
        text = re.sub(r'(?s)\\begin\s*\{keyonly\}.*?\\end\s*\{keyonly\}', '', text)
    return text


def _replace_answer_envs(text, reveal=False):
    r"""Replace or remove all \begin{answer}...\end{answer} blocks.

    Works even when blocks contain \input{} or TikZ code.

    Args:
        text (str): LaTeX source text.
        reveal (bool, optional): If True, replace each block with formatted
            answer text. If False, remove blocks entirely. Defaults to False.

    Returns:
        str: Text with answer environments handled.
    """
    def repl(m):
        inner = m.group(1).strip()
        if reveal:
            return f"\n\n\\\n\n\\emph{{Answer:}} {inner}\n\n\\\n\n"
        return ""

    return re.sub(
        r'\\begin\{answer\}(.*?)\\end\{answer\}',
        repl,
        text,
        flags=re.DOTALL
    )


def _strip_commented_lines(lines, commented_block_prefix='%\\question'):
    """Remove comment lines and skip blocks that begin with a commented token.

    A line starting with '%' is always dropped. A block starting with the
    commented_block_prefix is skipped until a blank line or a real
    '\\question' line is encountered.

    Args:
        lines (list of str): Source lines to filter.
        commented_block_prefix (str, optional): The prefix that signals
            the start of a skip block. Defaults to '%\\question'.

    Returns:
        list of str: Cleaned lines with comments and skip blocks removed.
    """
    cleaned = []
    skip_block = False
    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith(commented_block_prefix):
            skip_block = True
            continue
        if skip_block:
            if stripped == "" or stripped.startswith('\\question'):
                skip_block = False
            continue
        if stripped.startswith('%'):
            continue
        cleaned.append(line)
    return cleaned


def _parse_mc_lines(mc_lines, correct_string):
    """Parse a list of MC question lines into an elements dict.

    Recognises standalone questions (lines containing '\\shuffle' or
    '\\noshuffle') and question groups (delimited by 'begin{mcgroup}' /
    'end{mcgroup}').

    Args:
        mc_lines (list of str): Lines from inside an mcquestions environment,
            with comment lines already removed.
        correct_string (str): Marker token for the correct answer.

    Returns:
        dict: Mapping of integer index to MCQuestion or MCGroup objects,
            in the order they appear in the source.
    """
    elements = {}
    index = 0
    open_group = False
    group_start = 0

    for n, line in enumerate(mc_lines):
        if line.lstrip().startswith('%'):
            continue

        if 'begin{mcgroup}' in line:
            group_start = n
            open_group = True
        elif 'end{mcgroup}' in line:
            group_lines = mc_lines[group_start:n]
            elements[index] = MCGroup(group_lines, correct_string=correct_string)
            index += 1
            open_group = False
        elif ('\\shuffle' in line or '\\noshuffle' in line) and not open_group:
            length = _get_question_length(mc_lines, n)
            question_string = ''.join(mc_lines[n:n + length]).strip()
            elements[index] = MCQuestion(question_string, correct_string=correct_string)
            index += 1

    return elements


def make_answer_key(exam):
    """Create an answer key for a multiple-choice exam.

    Wraps the text of each correct answer option in a LaTeX '\\hl{}'
    command for highlighting.

    Args:
        exam (MCExam): The exam object whose elements will be copied and
            annotated.

    Returns:
        dict: A deep copy of exam.elements with correct options highlighted.
    """
    answer_key = deepcopy(exam.elements)

    def _highlight(option):
        main, comment, had_comment = _split_option_comment(option)
        is_correct = _has_correct((comment or option), exam.correct_string)
        main_clean = main.rstrip()
        norm_comment = (
            _normalize_comment_tail(comment, is_correct, exam.correct_string)
            if (had_comment or is_correct) else ""
        )
        base = '\\item \\hl{' + main_clean + '}' if is_correct else '\\item ' + main_clean
        return base if not norm_comment else base + ' % ' + norm_comment

    for key, value in exam.elements.items():
        if isinstance(value, MCQuestion):
            for n, opt in enumerate(value.options):
                if _has_correct(opt, exam.correct_string):
                    answer_key[key].options[n] = _highlight(opt)
        else:
            for sub_key, sub_value in value.elements.items():
                for n, opt in enumerate(sub_value.options):
                    if _has_correct(opt, exam.correct_string):
                        answer_key[key].elements[sub_key].options[n] = _highlight(opt)

    return answer_key


# ---------------------------------------------------------------------------
# Core data classes
# ---------------------------------------------------------------------------

class MCQuestion:
    """Stores and manages the content of a single multiple-choice question."""

    def __init__(self, question_string=None, correct_string=None):
        """Initialize an MCQuestion instance.

        Parses the question string to extract the question header, answer
        options, and settings for shuffling, 'all of the above', and
        'none of the above'. The '\\all' and '\\none' special tokens are
        recognised only when they appear on a '\\item' line, so that
        occurrences of those strings elsewhere in the question body (e.g.
        'students must answer \\all parts') are not misread as special
        answer choices. Detected tokens are removed from the options list
        and tracked as boolean flags so they can always be appended last
        during export.

        Args:
            question_string (str, optional): The full LaTeX content of the
                question, including its options block. Defaults to None.
            correct_string (str, optional): The marker that identifies the
                correct answer (e.g., 'CORRECT'). Defaults to None.
        """

        def get_question_split_point(question_string):
            """Find the character index that ends the first brace-pair.

            Locates the boundary between the question header (the
            '\\shuffle{...}{...}' portion) and the opening of the options
            block.

            Args:
                question_string (str): The full content of a multiple-choice
                    question.

            Returns:
                int: Index of the character immediately after the closing
                    brace of the first outer brace pair.
            """
            left_brace_count = 0
            right_brace_count = 0
            open_outer_brace = False

            for i, char in enumerate(question_string):
                if char == '{':
                    left_brace_count += 1
                    if not open_outer_brace:
                        open_outer_brace = True
                elif char == '}':
                    right_brace_count += 1

                if left_brace_count - right_brace_count == 0 and open_outer_brace:
                    break

            return i + 1

        self.correct_string = correct_string

        if question_string is not None:
            self.question_string = question_string

            split_point = get_question_split_point(self.question_string)
            self.question_header = self.question_string[:split_point]

            self.to_shuffle = 'noshuffle' not in self.question_header

            options = question_string[split_point:].lstrip().rstrip()[1:-1].lstrip().rstrip()

            self.all_of_above = False
            self.none_of_above = False
            self.all_of_above_correct = False
            self.none_of_above_correct = False

            # Only treat \all and \none as special tokens when they appear on
            # a \item line. This prevents question body text that happens to
            # contain \all (e.g. "students must answer \all parts") from being
            # misread as an "All of the above" answer choice.
            for option_line in options.split('\n'):
                stripped_line = option_line.lstrip()
                if not stripped_line.startswith('\\item'):
                    continue
                if '\\all' in stripped_line:
                    self.all_of_above = True
                    if self.correct_string in stripped_line:
                        self.all_of_above_correct = True
                    options = options.replace(option_line, '')
                elif '\\none' in stripped_line:
                    self.none_of_above = True
                    if self.correct_string in stripped_line:
                        self.none_of_above_correct = True
                    options = options.replace(option_line, '')

            options = options.lstrip().rstrip()
            options = options.split('\\item')[1:]

            for n in range(len(options)):
                options[n] = '\\item ' + options[n].lstrip().rstrip()

            self.options = options

    def shuffle_options(self, rng):
        """Shuffle the answer options of this question.

        The '\\all' and '\\none' options are not stored in self.options (they
        are tracked as flags) and are therefore unaffected by shuffling.
        They will always be appended last during export.

        Args:
            rng (numpy.random.Generator): Random number generator used for
                shuffling.

        Returns:
            MCQuestion: A new MCQuestion instance with options reordered.
        """
        new_question = deepcopy(self)

        if self.to_shuffle:
            options = np.r_[self.options]
            n_options = len(self.options)
            choice = rng.choice(np.arange(n_options), replace=False, size=n_options)
            new_question.options = options[choice].tolist()

        return new_question

    def add_periods(self, include_equations=True, correct_string=None):
        """Add a period to the end of each option's main text if absent.

        When the option ends with a LaTeX math expression ('$...$'), a
        period is appended only when include_equations is True. The
        comment portion is normalized and the correct-answer token is
        moved to the very end of the comment.

        Args:
            include_equations (bool, optional): Whether to add a period
                after trailing math expressions. Defaults to True.
            correct_string (str, optional): Override for the correct-answer
                token. Defaults to None, which falls back to
                self.correct_string.
        """
        corr = correct_string or self.correct_string
        new_opts = []
        for option in self.options:
            main, comment, had_comment = _split_option_comment(option)

            if not main.endswith('.'):
                m = re.search(r'\$(.*?)\$\s*$', main)
                if m:
                    inner = m.group(1).strip()
                    if include_equations and not inner.endswith('.'):
                        main += '.'
                else:
                    main += '.'

            is_correct = _has_correct((comment or option), corr)
            norm_comment = (
                _normalize_comment_tail(comment, is_correct, corr)
                if (had_comment or is_correct) else ""
            )
            new_opts.append(_rebuild_option(main, norm_comment))
        self.options = new_opts

    def capitalize_first(self, correct_string=None):
        """Capitalize the first letter of each option's main text.

        The comment portion is preserved unchanged. Correct-answer token
        placement is left to add_periods or make_answer_key.

        Args:
            correct_string (str, optional): Override for the correct-answer
                token (unused here but accepted for a consistent signature).
                Defaults to None.
        """
        new_opts = []
        for option in self.options:
            main, comment, had_comment = _split_option_comment(option)
            if main:
                main = main[0].upper() + main[1:]
            new_opts.append(_rebuild_option(main, comment if had_comment else ""))
        self.options = new_opts


class MCGroup:
    """Stores and manages a group of related multiple-choice questions."""

    def __init__(self, group_lines, correct_string):
        """Initialize an MCGroup instance.

        Parses the provided LaTeX lines to extract the group header, count,
        and individual MCQuestion objects.

        Args:
            group_lines (list of str): Lines of LaTeX that make up the
                group block (excluding the '\\end{mcgroup}' line).
            correct_string (str): The marker for correct answers, passed
                through to each MCQuestion.
        """
        self.correct_string = correct_string
        self.group_lines = group_lines
        self.group_string = ''.join(group_lines).strip()

        self.group_count, self.group_header = self._get_group_count_and_header(self.group_string)

        # group_lines[0] is the \begin{mcgroup}{N}{header} line itself.
        # Passing it to _parse_mc_lines would trigger the open_group guard
        # and suppress all questions inside, so skip it.
        inner_lines = [
            ln for ln in group_lines[1:]
            if not ln.lstrip().startswith('%')
        ]
        self.elements = _parse_mc_lines(inner_lines, correct_string)
        actual_count = len(self.elements)

        if actual_count != self.group_count:
            print(
                f"Warning: stated {self.group_count} but found {actual_count} "
                f"in group:\n{self.group_header}\n"
            )

        self.group_count = actual_count

    def _get_group_count_and_header(self, group_string):
        """Extract the stated question count and header text from the group string.

        Expects the format '\\begin{mcgroup}{N}{Header text}'.

        Args:
            group_string (str): The full string for the group block.

        Returns:
            tuple: A two-element tuple (group_count, group_header) where
                group_count (int or None) is the stated number of questions
                and group_header (str) is the descriptive header text.
        """
        left = right = pairs = 0
        open_outer = False
        count_start = count_end = text_start = text_end = 0

        for i, char in enumerate(group_string):
            if char == '{':
                left += 1
                if not open_outer:
                    open_outer = True
                    if pairs == 1:
                        count_start = i + 1
                    elif pairs == 2:
                        text_start = i + 1
            elif char == '}':
                right += 1
            if left - right == 0 and open_outer:
                pairs += 1
                open_outer = False
                if pairs == 2:
                    count_end = i
                elif pairs == 3:
                    text_end = i
                    break

        try:
            group_count = int(group_string[count_start:count_end])
        except ValueError:
            group_count = None
        group_header = group_string[text_start:text_end]
        return group_count, group_header

    def shuffle_questions(self, rng):
        """Return a new MCGroup with questions in a randomized order.

        Args:
            rng (numpy.random.Generator): Random number generator used for
                shuffling.

        Returns:
            MCGroup: A deep copy of this group with questions reordered.
        """
        new_group = deepcopy(self)
        reordered_keys = rng.choice(list(new_group.elements.keys()), replace=False, size=len(new_group.elements))
        reordered_elements = {j + 1: new_group.elements[key] for j, key in enumerate(reordered_keys)}
        new_group.elements = reordered_elements
        return new_group

    def shuffle_options(self, rng):
        """Return a new MCGroup with each question's options shuffled.

        Args:
            rng (numpy.random.Generator): Random number generator used for
                shuffling.

        Returns:
            MCGroup: A deep copy of this group with options reordered.
        """
        new_group = deepcopy(self)
        for key, value in self.elements.items():
            new_group.elements[key] = value.shuffle_options(rng)
        return new_group

    def add_periods(self, include_equations=True, correct_string=None):
        """Add periods to option text for all questions in the group.

        Args:
            include_equations (bool, optional): Whether to add a period
                after trailing math expressions. Defaults to True.
            correct_string (str, optional): Override for the correct-answer
                token. Defaults to None.
        """
        for key in self.elements:
            self.elements[key].add_periods(include_equations=include_equations, correct_string=correct_string)

    def capitalize_first(self, correct_string=None):
        """Capitalize the first letter of each option for all questions in the group.

        Args:
            correct_string (str, optional): Override for the correct-answer
                token. Defaults to None.
        """
        for key in self.elements:
            self.elements[key].capitalize_first(correct_string=correct_string)


class MCExam:
    """Stores and manages the content of a multiple-choice exam."""

    def __init__(self, exam_file=None, exam_lines=None, correct_string='CORRECT', seed=None):
        """Initialize an MCExam instance from a LaTeX file.

        Reads the file, isolates the 'mcquestions' environment, and parses
        it into MCQuestion and MCGroup objects stored in self.elements.
        Also builds the answer key and computes letter labels.

        When exam_file is None and exam_lines is also None, self.mc_lines is
        initialised to an empty list so that the instance is in a valid (if
        empty) state. The preferred way to build an MCExam without a file on
        disk is MCExam.from_string().

        Args:
            exam_file (str, optional): Path to the LaTeX exam file.
            exam_lines (list of str, optional): Pre-read lines (currently
                unused; kept for API compatibility).
            correct_string (str, optional): Marker for the correct answer.
                Defaults to 'CORRECT'.
            seed (int, optional): Seed for the internal random number
                generator. Defaults to None.
        """
        self.correct_string = correct_string
        self.filepath = Path(exam_file).resolve() if exam_file else None
        self.filename = self.filepath.name if exam_file else None
        self.rng = np.random.default_rng(seed=seed)

        # Default to empty state so the instance is valid even without a file.
        self.mc_lines = []
        self.exam_header = ''
        self.exam_footer = ''

        if exam_file is not None:
            with open(exam_file, 'r', encoding='utf-8') as f:
                self.exam_lines = f.readlines()

            for n, line in enumerate(self.exam_lines):
                if line.lstrip().startswith('\\begin{mcquestions}'):
                    self.mc_block_start = n
                elif line.lstrip().startswith('\\end{mcquestions}'):
                    self.mc_block_end = n

            self.exam_header = ''.join(self.exam_lines[:self.mc_block_start])
            self.exam_footer = ''.join(self.exam_lines[self.mc_block_end + 1:])

            mc_slice = self.exam_lines[self.mc_block_start:self.mc_block_end]
            self.mc_lines = [ln for ln in mc_slice if not ln.lstrip().startswith('%')]

        self.elements = _parse_mc_lines(self.mc_lines, self.correct_string)

        self.question_count = sum(
            1 if isinstance(v, MCQuestion) else len(v.elements)
            for v in self.elements.values()
        )

        self.answer_key = make_answer_key(self)
        self.mc_answer_letters = self._compute_answer_key_letters()

    def print_exam(self):
        """Print the content of the exam to the console."""
        self._print_questions(self.elements)

    def print_answer_key(self):
        """Print the answer key for the exam to the console."""
        self._print_questions(self.answer_key)

    def _print_questions(self, elements_dict):
        """Print questions from an elements dict to the console.

        Args:
            elements_dict (dict): Mapping of index to MCQuestion or
                MCGroup, as held by self.elements or self.answer_key.
        """
        question_count = 0
        for key, value in elements_dict.items():
            if isinstance(value, MCQuestion):
                question_count += 1
                print('Question ' + str(question_count) + '\n\n')
                print(value.question_header)
                print()
                for o in value.options:
                    print(o)
                print('\n----------------------------\n')
            else:
                for sub_key, sub_value in value.elements.items():
                    question_count += 1
                    print('Question ' + str(question_count) + '\n\n')
                    print(sub_value.question_header)
                    print()
                    for o in sub_value.options:
                        print(o)
                    print('\n----------------------------\n')

    def show_duplicates(self):
        """Display any duplicate answer options found in the exam questions."""

        def duplicated(options, question_number):
            """Identify and print duplicate options for a specific question.

            Args:
                options (list of str): Answer options for the question.
                question_number (int): The question number being checked.
            """
            options = pd.Series(options)
            dupes = options[options.duplicated()]
            if len(dupes) > 0:
                print('Question ' + str(question_number))
            for d in dupes:
                print(d)
            if len(dupes) > 0:
                print()

        question_count = 0
        for key, value in self.elements.items():
            if isinstance(value, MCQuestion):
                question_count += 1
                duplicated(value.options, question_number=question_count)
            else:
                for sub_key, sub_value in value.elements.items():
                    question_count += 1
                    duplicated(sub_value.options, question_number=question_count)

    def to_latex(self, key=False):
        """Return the full LaTeX string for this exam without writing to disk.

        Args:
            key (bool, optional): If True, return the answer key version.
                Defaults to False.

        Returns:
            str: Complete LaTeX source for the exam or answer key.
        """
        if key:
            return self.export_key_to_string()
        return self.export_exam_to_string()

    def _write_mc_options(self, question, output):
        """Append option lines and 'all/none of above' items to an output string.

        The shuffled regular options are written first. '\\all' ('All of the
        above') is always appended next, and '\\none' ('None of the above')
        always comes last, so the ordering is preserved regardless of how
        options were shuffled.

        Args:
            question (MCQuestion): The question whose options to write.
            output (str): The LaTeX string accumulated so far.

        Returns:
            str: The output string with option lines appended.
        """
        for option in question.options:
            output += '\t' + option + '\n'
        if question.all_of_above:
            output += '\t\\item All of the above.\n'
        if question.none_of_above:
            output += '\t\\item None of the above.\n'
        return output

    def _write_all_none_key(self, orig_question, output):
        """Append highlighted 'all/none of above' items for the answer key.

        Writes the items with '\\hl{}' when they are the correct answer,
        or plain text otherwise. Always writes 'all' before 'none'.

        Args:
            orig_question (MCQuestion): The original (un-highlighted)
                question whose flags determine what to write.
            output (str): The LaTeX string accumulated so far.

        Returns:
            str: The output string with all/none items appended.
        """
        if orig_question.all_of_above:
            if orig_question.all_of_above_correct:
                text = '\\item \\hl{All of the above.} % ' + self.correct_string
            else:
                text = '\\item All of the above.'
            output += '\t' + text + '\n'
        if orig_question.none_of_above:
            if orig_question.none_of_above_correct:
                text = '\\item \\hl{None of the above.} % ' + self.correct_string
            else:
                text = '\\item None of the above.'
            output += '\t' + text + '\n'
        return output

    def export_exam_to_string(self):
        """Return LaTeX for the student exam (answers hidden) as a string.

        Returns:
            str: Complete LaTeX source for the student-facing exam.
        """
        output = self.exam_header + '\\begin{mcquestions}\n\n'

        for key, value in self.elements.items():
            if isinstance(value, MCQuestion):
                output += value.question_header + '\n{\n'
                output = self._write_mc_options(value, output)
                output += '}\n\n'
            else:
                output += '\n% BEGIN MC GROUP BLOCK\n'
                output += f'\\begin{{mcgroup}}{{{value.group_count}}}{{{value.group_header}}}\n\n'
                for sub_key, sub_value in value.elements.items():
                    output += sub_value.question_header + '{\n'
                    output = self._write_mc_options(sub_value, output)
                    output += '}\n\n'
                output += '% END MC GROUP BLOCK\n\\end{mcgroup}\n\n\n'

        output += '\\end{mcquestions}\n\n' + self.exam_footer
        return _filter_visibility(output, reveal=False)

    def export_key_to_string(self):
        """Return LaTeX for the answer key (correct answers highlighted) as a string.

        Returns:
            str: Complete LaTeX source for the instructor answer key.
        """
        output = self.exam_header + '\\begin{mcquestions}\n\n'

        for key, value in self.answer_key.items():
            orig = self.elements[key]
            if isinstance(value, MCQuestion):
                output += value.question_header + '\n{\n'
                for option in value.options:
                    output += '\t' + option + '\n'
                output = self._write_all_none_key(orig, output)
                output += '}\n\n'
            else:
                grp = orig
                output += '\n% BEGIN MC GROUP BLOCK\n'
                output += f'\\begin{{mcgroup}}{{{grp.group_count}}}{{{grp.group_header}}}\n\n'
                for sub_key, sub_value in value.elements.items():
                    output += sub_value.question_header + '{\n'
                    for option in sub_value.options:
                        output += '\t' + option + '\n'
                    output = self._write_all_none_key(grp.elements[sub_key], output)
                    output += '}\n\n'
                output += '% END MC GROUP BLOCK\n\\end{mcgroup}\n\n\n'

        output += '\\end{mcquestions}\n\n' + self.exam_footer
        return _filter_visibility(output, reveal=True)

    def export_key(self, filename=None):
        """Export the answer key with correct answers highlighted to a LaTeX file.

        Args:
            filename (str, optional): Destination path. Defaults to the
                original filename with '_Key' appended before the extension.

        Returns:
            str: The LaTeX string that was written.
        """
        if filename is None:
            filename = str(self.filename).replace('.tex', '') + '_Key.tex'
        self.key_filename = filename

        output = self.export_key_to_string()
        Path(filename).write_text(output, encoding='utf-8')
        print("Exported MC key: " + filename)
        return output

    def export_exam(self, filename=None):
        """Export the student exam to a LaTeX file.

        Args:
            filename (str, optional): Destination path. Defaults to the
                original filename.

        Returns:
            str: The LaTeX string that was written.
        """
        if filename is None:
            filename = str(self.filename).replace('.tex', '') + '.tex'

        output = self.export_exam_to_string()
        Path(filename).write_text(output, encoding='utf-8')

        self.filepath = Path(filename).resolve()
        self.filename = str(self.filepath)

        print("Exported MC exam: " + filename)
        return output

    def export_mc_answers_to_text(self, filename=None, header_text=None, mc_start=1):
        """Export the MC answer letters to a plain-text file.

        Each line contains a question number and its correct-answer letter(s),
        e.g. '1. (b)'. The caller can pass mc_start to offset the numbering
        when MC questions do not begin at question 1 in the overall exam.

        Args:
            filename (str, optional): Destination path. Defaults to the
                original filename with '_MC_Answers.txt' appended before
                the extension.
            header_text (str, optional): A title line written at the top of
                the file. A blank line is inserted between the header and
                the answer list. Defaults to None.
            mc_start (int, optional): The global question number assigned to
                the first MC question. Defaults to 1.

        Returns:
            str: The text that was written to the file.
        """
        if filename is None:
            stem = str(self.filename).replace('.tex', '')
            filename = stem + '_MC_Answers.txt'

        lines = []
        if header_text is not None:
            lines.append(header_text)
            lines.append('')

        for i, letters in enumerate(self.mc_answer_letters):
            lines.append(f'{mc_start + i}. {letters}')

        output = '\n'.join(lines) + '\n'
        Path(filename).write_text(output, encoding='utf-8')
        print('Exported MC answers: ' + filename)
        return output

    def shuffle_questions(self, filename=None, seed=None, shuffle_within_groups=True):
        """Return a new exam with questions shuffled.

        When at least one standalone MCQuestion exists, one is always placed
        first; the remaining standalone questions and any MCGroups are then
        randomly interleaved. When the exam contains only MCGroups (no
        standalone questions), all groups are shuffled without the
        forced-first-question step.

        Args:
            filename (str, optional): Filename for the returned exam object.
            seed (int, optional): Random seed for reproducibility.
            shuffle_within_groups (bool, optional): Whether to also shuffle
                questions within each MCGroup. Defaults to True.

        Returns:
            MCExam: A new instance with shuffled questions.
        """
        new_exam = deepcopy(self)

        if filename is not None:
            new_exam.filename = filename
        else:
            new_exam.filename = Path(self.filename).stem + '_questions_shuffled.tex'

        if seed is not None:
            self.rng = np.random.default_rng(seed=seed)

        mc_question_keys = []
        mc_group_keys = []

        for key, value in self.elements.items():
            if isinstance(value, MCQuestion):
                mc_question_keys.append(key)
            else:
                mc_group_keys.append(key)

        if mc_question_keys:
            # Pin one standalone question first, then randomly interleave the rest.
            first_choice = self.rng.choice(np.arange(len(mc_question_keys)))
            reordered_keys = np.r_[mc_question_keys[first_choice]]
            del mc_question_keys[first_choice]

            remaining_options = np.r_[mc_question_keys, mc_group_keys]
            M = len(self.elements) - 1
            if M > 0:
                remaining_choices = self.rng.choice(np.arange(M), replace=False, size=M)
                reordered_keys = np.r_[reordered_keys, remaining_options[remaining_choices]]
        else:
            # Exam has only groups — shuffle them directly.
            M = len(mc_group_keys)
            group_choices = self.rng.choice(np.arange(M), replace=False, size=M)
            reordered_keys = np.array(mc_group_keys)[group_choices]

        reordered_elements = {j + 1: self.elements[key] for j, key in enumerate(reordered_keys)}
        new_exam.elements = reordered_elements

        if shuffle_within_groups:
            for key, value in new_exam.elements.items():
                if isinstance(value, MCGroup):
                    new_exam.elements[key] = new_exam.elements[key].shuffle_questions(self.rng)

        new_exam.answer_key = make_answer_key(new_exam)
        new_exam.mc_answer_letters = new_exam._compute_answer_key_letters()

        return new_exam

    def set_seed(self, seed=None):
        """Set the random seed for the exam's internal random number generator.

        Args:
            seed (int, optional): Seed value. Defaults to None.
        """
        self.rng = np.random.default_rng(seed=seed)

    def shuffle_options(self, filename=None, seed=None):
        """Return a new exam with answer options shuffled within each question.

        The '\\all' and '\\none' options always remain at the end (in that
        order) because they are stored as flags and appended during export
        rather than held in the options list.

        Args:
            filename (str, optional): Filename for the returned exam object.
            seed (int, optional): Random seed for reproducibility.

        Returns:
            MCExam: A new MCExam instance with shuffled options.
        """
        new_exam = deepcopy(self)

        if filename is not None:
            new_exam.filename = filename
        else:
            new_exam.filename = Path(self.filename).stem + '_options_shuffled.tex'

        new_exam.rng = np.random.default_rng(seed=seed)

        for key, value in new_exam.elements.items():
            new_exam.elements[key] = value.shuffle_options(new_exam.rng)

        new_exam.answer_key = make_answer_key(new_exam)
        new_exam.mc_answer_letters = new_exam._compute_answer_key_letters()

        return new_exam

    def shuffle_options_and_questions(self, filename=None, seed=None, shuffle_within_groups=True):
        """Return a new exam with both options and questions shuffled.

        Args:
            filename (str, optional): Filename for the returned exam object.
            seed (int, optional): Random seed for reproducibility.
            shuffle_within_groups (bool, optional): Whether to shuffle
                questions within groups. Defaults to True.

        Returns:
            MCExam: A new instance with shuffled options and questions.
        """
        if filename is not None:
            out_filename = filename
        else:
            out_filename = Path(self.filename).stem + '_options_shuffled.tex'

        if seed is not None:
            self.rng = np.random.default_rng(seed=seed)

        return (
            self.shuffle_options(seed=seed, filename=out_filename)
                .shuffle_questions(filename=out_filename, shuffle_within_groups=shuffle_within_groups)
        )

    def add_periods(self, include_equations=True):
        """Add periods to the end of answer choice text throughout the exam.

        Args:
            include_equations (bool, optional): Whether to add a period
                after trailing math expressions. Defaults to True.
        """
        for key in self.elements:
            self.elements[key].add_periods(include_equations=include_equations, correct_string=self.correct_string)

        self.answer_key = make_answer_key(self)

    def capitalize_first(self):
        """Capitalize the first letter of each answer choice throughout the exam."""
        for key in self.elements:
            self.elements[key].capitalize_first(correct_string=self.correct_string)

        self.answer_key = make_answer_key(self)

    def _compute_answer_key_letters(
        self,
        option_characters=string.ascii_lowercase,
        option_character_format='(CHARACTER)',
    ):
        """Compute letter labels for each correct answer in the exam.

        Args:
            option_characters (str, optional): Characters to use for option
                labels. Defaults to lowercase ASCII.
            option_character_format (str, optional): Format string where
                'CHARACTER' is replaced by the label letter. Defaults to
                '(CHARACTER)'.

        Returns:
            list of str: One entry per question (or sub-question), each
                a comma-separated string of correct-answer letter labels.
        """
        key_letters = []
        self.option_characters = option_characters
        self.option_character_format = option_character_format

        for key, item in self.elements.items():
            if isinstance(item, MCQuestion):
                letters = self._letters_for_question(item, option_characters, option_character_format)
                key_letters.append(', '.join(letters))
            else:
                for sub_key, sub_value in item.elements.items():
                    letters = self._letters_for_question(sub_value, option_characters, option_character_format)
                    key_letters.append(', '.join(letters))

        return key_letters

    def _letters_for_question(self, q, option_chars, fmt):
        """Return formatted letter labels for a single question's correct answers.

        Args:
            q (MCQuestion): The question to evaluate.
            option_chars (str): Character sequence for option labels.
            fmt (str or None): Format string replacing 'CHARACTER' with the
                label, or None to return raw characters.

        Returns:
            list of str: Letter labels (formatted or raw) for each correct
                option, including 'all of above' and 'none of above' when
                applicable.
        """
        letters = []
        for n, opt in enumerate(q.options):
            # Use _has_correct (word-boundary regex) to avoid matching substrings
            # like 'INCORRECTLY' when correct_string is 'CORRECT'.
            if _has_correct(opt, self.correct_string):
                letters.append(option_chars[n])
        if getattr(q, 'all_of_above_correct', False):
            letters.append(option_chars[len(q.options)])
        if getattr(q, 'none_of_above_correct', False):
            letters.append(option_chars[len(q.options) + 1])
        if fmt is not None:
            letters = [fmt.replace('CHARACTER', l) for l in letters]
        return letters

    @classmethod
    def from_string(cls, tex, correct_string='CORRECT', seed=None, source_path=None, filename_hint=None):
        """Build an MCExam directly from a LaTeX string without a file on disk.

        Args:
            tex (str): LaTeX source containing an 'mcquestions' environment
                (or raw question content).
            correct_string (str, optional): Marker for the correct answer.
                Defaults to 'CORRECT'.
            seed (int, optional): Seed for the internal RNG. Defaults to None.
            source_path (str, optional): Path of the originating file, used
                to set self.filepath. Defaults to None.
            filename_hint (str, optional): Short filename to assign to
                self.filename. Defaults to None.

        Returns:
            MCExam: A fully initialized MCExam instance.
        """
        self = cls.__new__(cls)
        self.correct_string = correct_string
        self.rng = np.random.default_rng(seed=seed)
        self.filepath = Path(source_path).resolve() if source_path else None
        self.filename = filename_hint or (self.filepath.name if self.filepath else None)
        self.exam_header = ""
        self.exam_footer = ""

        tex = tex.replace('\r\n', '\n').replace('\r', '\n')
        m = re.search(r'\\begin\{mcquestions\}(.*?)\\end\{mcquestions\}', tex, flags=re.DOTALL)
        inner = m.group(1) if m else tex

        # keepends=True preserves '\n' so LaTeX tables do not collapse
        self.mc_lines = [
            ln for ln in inner.splitlines(keepends=True)
            if not ln.lstrip().startswith('%')
        ]

        self.elements = _parse_mc_lines(self.mc_lines, correct_string)

        self.question_count = sum(
            1 if isinstance(v, MCQuestion) else len(v.elements)
            for v in self.elements.values()
        )
        self.answer_key = make_answer_key(self)
        self.mc_answer_letters = self._compute_answer_key_letters()

        return self


# ---------------------------------------------------------------------------
# Free-response exam
# ---------------------------------------------------------------------------

class FRExam:
    r"""Handles free-response exams using the \question[points] syntax."""

    def __init__(self, filename=None):
        """Initialize an FRExam, optionally loading from a LaTeX file.

        Args:
            filename (str, optional): Path to the LaTeX exam file. If
                provided, the file is read and parsed immediately.
        """
        self.filepath = Path(filename).resolve() if filename else None
        self.filename = str(self.filepath) if filename else None
        self.questions = []
        self.question_files = []
        self.exam_header = ""
        self.exam_footer = ""

        if filename:
            self.load_exam(filename)

    @classmethod
    def from_string(cls, tex, source_path=None, filename_hint=None):
        r"""Build an FRExam directly from a LaTeX string without a file on disk.

        When source_path is provided its parent directory is used to resolve
        any \input{} commands that reference sub-files containing a
        \question token.

        Args:
            tex (str): LaTeX source containing free-response question content.
            source_path (str, optional): Path of the originating file, used
                to resolve relative \input{} paths. Defaults to None.
            filename_hint (str, optional): Short filename to assign to
                self.filename. Defaults to None.

        Returns:
            FRExam: A fully initialized FRExam instance.
        """
        self = cls.__new__(cls)
        self.filepath = Path(source_path).resolve() if source_path else None
        self.filename = filename_hint or (self.filepath.name if self.filepath else None)
        self.questions = []
        self.question_files = []
        self.exam_header = ""
        self.exam_footer = ""

        tex = tex.replace('\r\n', '\n').replace('\r', '\n')
        m = re.search(r'\\begin\{frquestions\}(.*?)\\end\{frquestions\}', tex, flags=re.DOTALL)
        inner = m.group(1) if m else tex

        # Expand \input{} sub-files when a base directory is available.
        base_dir = self.filepath.parent if self.filepath else None
        if base_dir is not None:
            inner = self._expand_question_inputs(inner, base_dir)

        body = "\n".join(_strip_commented_lines(inner.splitlines()))
        self._extract_questions_from_text(body, self.filename or "(inline)")
        return self

    def _expand_question_inputs(self, text, base_dir):
        r"""Expand \input{...} commands, but only for files containing \question.

        Figure and TikZ inputs inside answer blocks are left untouched.

        Args:
            text (str): LaTeX source text.
            base_dir (Path): Directory used to resolve relative file paths.

        Returns:
            str: Text with qualifying \input commands replaced by file
                contents.
        """
        def repl(m):
            raw = m.group(0)
            fname = m.group(1)
            qpath = base_dir / (fname if fname.endswith(".tex") else f"{fname}.tex")
            try:
                content = qpath.read_text(encoding="utf-8")
            except Exception:
                return raw
            return content if r'\question' in content else raw

        return re.sub(r'\\input\{([^}]+)\}', repl, text)

    def load_exam(self, filename):
        r"""Load and parse free-response questions from a LaTeX file.

        Expands \input{} commands that reference files containing a
        \question token before parsing, so that questions stored in
        separate sub-files are included. Figure and TikZ inputs inside
        answer blocks are left untouched. Commented-out \question blocks
        (lines beginning with '%') are skipped automatically.

        Args:
            filename (str): Path to the LaTeX file to read.
        """
        text = self.filepath.read_text(encoding="utf-8")
        # Expand sub-file \input{} commands before stripping comments so
        # that questions stored in separate files are included.
        text = self._expand_question_inputs(text, self.filepath.parent)
        body = "\n".join(_strip_commented_lines(text.splitlines()))

        token_pattern = re.compile(
            r'(?m)^[ \t]*(?<!%)((?:\\question)(?:\[\d+\])?)',
            re.DOTALL
        )
        matches = list(token_pattern.finditer(body))

        for i, match in enumerate(matches):
            token = match.group(1)
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
            snippet = body[start:end].strip()
            self._extract_questions_from_text(f"{token} {snippet}", filename)

    def _extract_questions_from_text(self, text, source):
        r"""Find and store all \question[...] blocks within a text string.

        Preserves leading layout commands (e.g., '\\newpage') that appear
        before the first question.

        Args:
            text (str): LaTeX text to parse for questions.
            source (str): Label indicating the source file or context,
                stored with each question for reference.
        """
        leading_layout = ""
        m_leading = re.match(r'^\s*((?:\\newpage|\\clearpage|\\vspace\*?\{[^}]*\}\s*)+)', text)
        if m_leading:
            leading_layout = m_leading.group(1)
            text = text[m_leading.end():]

        pattern = re.compile(
            r'((?:\\newpage|\\clearpage|\\vspace\*?\{[^}]*\}\s*)*)'
            r'(\\question(?:\[\d+\])?)',
            re.DOTALL
        )

        matches = list(pattern.finditer(text))
        for i, match in enumerate(matches):
            prefix_spacing = match.group(1) or ""
            question_token = match.group(2)
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            question_body = text[start:end].strip()

            m_points = re.match(r'\\question\[(\d+)\]', question_token)
            points = int(m_points.group(1)) if m_points else None

            if i == 0 and leading_layout:
                prefix_spacing = leading_layout + prefix_spacing

            full_text = f"{prefix_spacing}{question_token} {question_body}"

            self.questions.append({
                "file": str(source),
                "points": points,
                "text": full_text.strip()
            })

    def reveal_answers(self, text=None):
        r"""Return the exam text with \begin{answer}...\end{answer} blocks revealed.

        Args:
            text (str, optional): LaTeX text to process. Defaults to the
                concatenated text of all stored questions.

        Returns:
            str: LaTeX text with answer environments expanded.
        """
        if text is None and self.questions:
            text = "\n\n".join(q["text"] for q in self.questions)

        text = _replace_answer_envs(text, reveal=True)
        text = _filter_visibility(text, reveal=True)
        return text

    def _build_fr_body(self, key=False):
        """Build a list of processed question text strings.

        Args:
            key (bool, optional): If True, reveal answer environments.
                Defaults to False.

        Returns:
            list of str: Each element is the processed text of one question.
        """
        body_parts = []
        for q in self.questions:
            text = _replace_answer_envs(q["text"], reveal=key)
            text = _filter_visibility(text, reveal=key)
            body_parts.append(text.strip())
        return body_parts

    def to_latex(self, key=False):
        """Return the full LaTeX string for this free-response exam.

        Args:
            key (bool, optional): If True, reveal answer environments.
                Defaults to False.

        Returns:
            str: Complete LaTeX source for the exam or answer key.
        """
        body = "\n\n".join(self._build_fr_body(key=key))
        return (
            self.exam_header
            + "\n\\begin{frquestions}\n"
            + body
            + "\n\\end{frquestions}\n"
            + self.exam_footer
        )

    def _export(self, filename, key=False):
        """Write a LaTeX file for either the student exam or the answer key.

        Args:
            filename (str): Destination file path.
            key (bool, optional): If True, write the answer key version.
                Defaults to False.
        """
        Path(filename).parent.mkdir(parents=True, exist_ok=True)

        content = (
            self.exam_header
            + "\n\\begin{frquestions}\n"
            + "\n\n".join(self._build_fr_body(key=key))
            + "\n\\end{frquestions}\n"
            + self.exam_footer
        )
        content = _filter_visibility(content, reveal=key)

        Path(filename).write_text(content, encoding="utf-8")
        self.filepath = Path(filename).resolve()
        self.filename = str(self.filepath)

    def export_exam(self, filename=None):
        """Export the student exam version (answers hidden) to a LaTeX file.

        Args:
            filename (str, optional): Destination path. Defaults to
                'FR_Exam.tex' in the same directory as the source file.
        """
        if filename is None:
            filename = str(Path(self.filename).with_name("FR_Exam.tex"))
        self._export(filename, key=False)
        print("Exported FR exam (no answers): " + filename)

    def export_key(self, filename=None):
        """Export the answer key version (answers revealed) to a LaTeX file.

        Args:
            filename (str, optional): Destination path. Defaults to
                'FR_Key.tex' in the same directory as the source file.
        """
        if filename is None:
            filename = str(Path(self.filename).with_name("FR_Key.tex"))
        self._export(filename, key=True)
        print("Exported FR key (answers revealed): " + filename)

    def summary(self, max_chars=80):
        """Print a summary of all parsed free-response questions.

        Args:
            max_chars (int, optional): Maximum number of characters to show
                in the question preview. Defaults to 80.
        """
        if not self.questions:
            print("No questions loaded.")
            return

        print("\nFree-Response Exam Summary")
        print("-" * 60)

        for i, q in enumerate(self.questions, 1):
            preview = re.sub(r'\s+', ' ', q["text"]).strip()
            preview = preview[:max_chars] + ("..." if len(preview) > max_chars else "")
            pts = f"[{q['points']} pts]" if q.get("points") else ""
            print(f"{i:>2}. {pts:<8} {Path(q['file']).name:<30} {preview}")

        print("-" * 60)
        print(f"Total questions: {len(self.questions)}\n")


# ---------------------------------------------------------------------------
# Combined exam
# ---------------------------------------------------------------------------

class Exam:
    """Combines MCExam and FRExam content into a single LaTeX document."""

    def __init__(self, filename, mc=None, fr=None, correct_string="CORRECT", seed=None):
        """Initialize an Exam by loading and parsing a main LaTeX file.

        Auto-detects MC and FR sections from '\\input{}' statements or
        inline environments. Pre-built MCExam and FRExam objects may be
        passed directly to bypass auto-detection.

        Args:
            filename (str): Path to the main exam LaTeX file.
            mc (MCExam, optional): Pre-parsed multiple-choice exam.
                Defaults to None (auto-detect).
            fr (FRExam, optional): Pre-parsed free-response exam.
                Defaults to None (auto-detect).
            correct_string (str, optional): Marker for correct MC answers.
                Defaults to 'CORRECT'.
            seed (int, optional): Random seed for reproducibility.
                Defaults to None.
        """
        self.filepath = Path(filename).resolve()
        self.filename = self.filepath.name
        self.file_text = self.filepath.read_text(encoding="utf-8")
        base_dir = self.filepath.parent
        self.correct_string = correct_string
        self.seed = seed

        self._source_path = self.filepath
        self._frozen_export_base = False
        self._base_path_for_exports = None

        self.mc = mc
        self.fr = fr

        if self.mc is None:
            mc_inputs = re.findall(
                r'(?m)^\s*(?!%)\\input\{([^}]*mc[^}]*)\}',
                self.file_text
            )
            if mc_inputs:
                merged = ""
                for fname in mc_inputs:
                    mc_path = base_dir / (fname if fname.endswith(".tex") else f"{fname}.tex")
                    if mc_path.exists():
                        print("Including MC file: " + mc_path.name)
                        text = mc_path.read_text(encoding="utf-8")

                        # Strip commented-out shuffle/noshuffle blocks by tracking brace depth
                        lines = text.splitlines()
                        cleaned_lines = []
                        skip_block = False
                        brace_depth = 0

                        for line in lines:
                            stripped = line.lstrip()
                            if (not skip_block) and (
                                stripped.startswith('%\\shuffle')
                                or stripped.startswith('%\\noshuffle')
                            ):
                                skip_block = True
                                brace_depth = 0
                                continue

                            if skip_block:
                                brace_depth += line.count('{')
                                brace_depth -= line.count('}')
                                if brace_depth <= 0 and '}' in line:
                                    skip_block = False
                                continue

                            if not stripped.startswith('%'):
                                cleaned_lines.append(line)

                        merged += "\n".join(cleaned_lines) + "\n"
                    else:
                        print("Warning: MC file not found: " + str(mc_path))

                merged_mc_tex = "\\begin{mcquestions}\n" + merged + "\\end{mcquestions}\n"
                self.mc = MCExam.from_string(
                    merged_mc_tex,
                    correct_string=correct_string,
                    seed=seed,
                    source_path=self.filepath,
                    filename_hint=self.filename,
                )

            elif "\\begin{mcquestions}" in self.file_text:
                print("Detected inline MC questions in main file")
                self.mc = MCExam(self.filename, correct_string=correct_string, seed=seed)

        if self.fr is None:
            fr_input = re.search(r'\\input\{([^}]*(?:fr[_]?questions)[^}]*)\}', self.file_text)
            if fr_input:
                fr_fname = fr_input.group(1)
                fr_path = base_dir / (fr_fname if fr_fname.endswith(".tex") else f"{fr_fname}.tex")
                if fr_path.exists():
                    print("Auto-loading FR section from " + fr_path.name)
                    text = fr_path.read_text(encoding="utf-8")
                    cleaned_text = "\n".join(_strip_commented_lines(text.splitlines()))
                    self.fr_text = cleaned_text
                    self.fr = FRExam.from_string(
                        cleaned_text,
                        source_path=self.filepath,
                        filename_hint=self.filename,
                    )
                else:
                    print("Warning: FR file not found: " + str(fr_path))
            elif "\\begin{frquestions}" in self.file_text:
                print("Detected inline FR questions in main file")
                self.fr = FRExam(self.filename)

    def shuffle_options(self, seed=None, filename=None):
        """Return a new Exam with shuffled MC options, preserving FR questions.

        Args:
            seed (int, optional): Random seed for reproducibility.
            filename (str, optional): If provided, sets the base path for
                subsequent export_exam and export_key calls.

        Returns:
            Exam: A deep copy of this Exam with MC options shuffled.
        """
        new_exam = deepcopy(self)
        new_exam.mc = new_exam.mc.shuffle_options(seed=seed)

        if filename:
            out_path = Path(filename).expanduser().resolve()
            out_path.parent.mkdir(parents=True, exist_ok=True)
            new_exam.filepath = out_path
            new_exam.filename = out_path.name
            new_exam._base_path_for_exports = out_path
            new_exam._frozen_export_base = True
        else:
            new_exam._frozen_export_base = False
            new_exam._base_path_for_exports = None

        print("Shuffled MC options with seed=" + str(seed))
        return new_exam

    def to_latex(self, key=False):
        """Return the full LaTeX string for the combined MC and FR exam.

        Raises ValueError if the assembled output does not contain exactly
        one mcquestions and one frquestions environment.

        Args:
            key (bool, optional): If True, produce the answer key version.
                Defaults to False.

        Returns:
            str: Complete LaTeX source for the exam or answer key.
        """
        mc_inner = fr_inner = ""
        if self.mc:
            mc_tex = self.mc.to_latex(key=key)
            mc_inner = self._extract_body(mc_tex, "mcquestions")
        if self.fr:
            fr_tex = self.fr.to_latex(key=key)
            fr_inner = self._extract_body(fr_tex, "frquestions")

        combined = self._assemble_exam(mc_inner, fr_inner)
        combined = _replace_answer_envs(combined, reveal=key)
        combined = _filter_visibility(combined, reveal=key)

        self._assert_single_env(combined, "mcquestions")
        self._assert_single_env(combined, "frquestions")
        return combined

    def _extract_body(self, latex_text, env_name):
        """Extract the inner content of a LaTeX environment.

        Args:
            latex_text (str): LaTeX source that contains the environment.
            env_name (str): Name of the LaTeX environment (e.g.,
                'mcquestions').

        Returns:
            str: Content between the \\begin and \\end tags, or the full
                input text if the environment is not found.
        """
        m = re.search(rf'\\begin\{{{env_name}\}}(.*?)\\end\{{{env_name}\}}', latex_text or "", flags=re.DOTALL)
        return m.group(1).strip() if m else latex_text or ""

    def _assert_single_env(self, text, env):
        """Raise ValueError if the text does not contain exactly one environment block.

        Args:
            text (str): LaTeX source text to check.
            env (str): Environment name to look for.

        Raises:
            ValueError: If the count of begin/end pairs is not exactly one.
        """
        pattern = rf"(?s)\\begin\{{{env}\}}.*?\\end\{{{env}\}}"
        count = len(re.findall(pattern, text))
        if count != 1:
            raise ValueError(f"{env}: expected 1 block, found {count}")

    def _replace_or_insert_env(self, text, env, inner,
                               anchor_comment=None,
                               insert_before_env=None,
                               insert_after_env=None):
        """Replace the first occurrence of an environment or insert it near an anchor.

        Uses a sentinel string to protect the newly inserted block from
        being caught by subsequent substitutions.

        Args:
            text (str): LaTeX source text.
            env (str): Environment name to replace or insert.
            inner (str): Content to place inside the environment.
            anchor_comment (str, optional): Regex matching a comment line
                after which the block should be inserted when no existing
                environment is found. Defaults to None.
            insert_before_env (str, optional): Environment name before which
                to insert when no existing environment is found. Defaults to
                None.
            insert_after_env (str, optional): Environment name after which
                to insert when no existing environment is found. Defaults to
                None.

        Returns:
            str: Updated LaTeX text.
        """
        block = f"\\begin{{{env}}}\n{inner.strip()}\n\\end{{{env}}}\n"
        pattern = rf"(?s)\\begin\{{{env}\}}.*?\\end\{{{env}\}}"
        SENTINEL = f"__AT_{env.upper()}_BLOCK__"

        if re.search(pattern, text):
            text = re.sub(pattern, lambda _m: SENTINEL, text, count=1)
            text = re.sub(pattern, "", text)
            text = text.replace(SENTINEL, block, 1)
            return text

        if anchor_comment and re.search(anchor_comment, text):
            text = re.sub(anchor_comment,
                          lambda m: m.group(0) + "\n" + block,
                          text, count=1)
            return text

        if insert_before_env and re.search(rf"\\begin\{{{insert_before_env}\}}", text):
            text = re.sub(rf"\\begin\{{{insert_before_env}\}}",
                          lambda _m: block + f"\n\\begin{{{insert_before_env}}}",
                          text, count=1)
            return text

        if insert_after_env and re.search(rf"\\end\{{{insert_after_env}\}}", text):
            text = re.sub(rf"\\end\{{{insert_after_env}\}}",
                          lambda _m: f"\\end{{{insert_after_env}}}\n\n{block}",
                          text, count=1)
            return text

        text = re.sub(r"\\end\{document\}",
                      lambda _m: block + "\n\\end{document}",
                      text, count=1)
        return text

    def _assemble_exam(self, mc_inner, fr_inner):
        """Build the final LaTeX output by replacing or inserting MC and FR environments.

        Args:
            mc_inner (str): Inner content for the mcquestions environment.
            fr_inner (str): Inner content for the frquestions environment.

        Returns:
            str: Assembled LaTeX document text.
        """
        text = self.file_text

        text = re.sub(r'(?m)^[ \t]*(?!%)\\input\{[^}]*mc[^}]*\}.*?$', "", text)
        text = re.sub(r'(?m)^[ \t]*(?!%)\\input\{[^}]*fr[^}]*\}.*?$', "", text)

        mc_inner = (mc_inner or "").strip()
        fr_inner = (fr_inner or "").strip()

        text = self._replace_or_insert_env(
            text,
            env="mcquestions",
            inner=mc_inner,
            anchor_comment=r'(?m)^% BEGIN MULTIPLE CHOICE QUESTIONS.*?$',
            insert_before_env="frquestions",
        )

        text = self._replace_or_insert_env(
            text,
            env="frquestions",
            inner=fr_inner,
            anchor_comment=r'(?m)^% FREE RESPONSE QUESTIONS.*?$',
            insert_after_env="mcquestions",
        )

        # Clean accidental duplicate begin/end lines
        for env in ("frquestions", "mcquestions"):
            text = re.sub(
                rf'(?ms)\\begin\{{{env}\}}\s*\\begin\{{{env}\}}',
                lambda _m, e=env: f'\\begin{{{e}}}',
                text,
            )
            text = re.sub(
                rf'(?ms)\\end\{{{env}\}}\s*\\end\{{{env}\}}',
                lambda _m, e=env: f'\\end{{{e}}}',
                text,
            )

        text = re.sub(r'\n{3,}', '\n\n', text).strip() + "\n"
        return text

    def _resolve_export_path(self, filename, key=False):
        """Determine the output path for an export operation.

        Args:
            filename (str or None): Explicit path supplied by the caller, or
                None to use automatic naming.
            key (bool, optional): If True, append '_Key' to the stem when
                deriving an automatic name. Defaults to False.

        Returns:
            Path: Resolved output path.
        """
        if filename:
            return Path(filename).expanduser().resolve()
        if getattr(self, "_frozen_export_base", False) and getattr(self, "_base_path_for_exports", None):
            base = self._base_path_for_exports
            return base.with_name(f"{base.stem}_Key{base.suffix}") if key else base
        base = Path(self._source_path)
        stem = re.sub(r"_Exported(_Key)?$", "", base.stem)
        suffix = "_Exported_Key.tex" if key else "_Exported.tex"
        return base.with_name(stem + suffix)

    def export_exam(self, filename=None):
        """Export the combined student exam (no answers, no key-only content).

        Args:
            filename (str, optional): Destination path. Defaults to the
                source filename with '_Exported' appended before the
                extension.
        """
        out_path = self._resolve_export_path(filename, key=False)
        tex = _filter_visibility(self.to_latex(key=False), reveal=False)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(tex, encoding="utf-8")
        print("Exported mixed exam (no answers): " + str(out_path))

    def export_key(self, filename=None):
        """Export the combined instructor key (FR answers shown, key-only content included).

        Args:
            filename (str, optional): Destination path. Defaults to the
                source filename with '_Exported_Key' appended before the
                extension.
        """
        out_path = self._resolve_export_path(filename, key=True)
        tex = _filter_visibility(self.to_latex(key=True), reveal=True)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(tex, encoding="utf-8")
        print("Exported mixed exam key: " + str(out_path))

    def export_mc_answers_to_text(self, filename=None, header_text=None):
        """Export the MC answer letters to a plain-text file, with correct
        question numbering even when FR questions precede the MC section.

        Scans the assembled exam LaTeX to determine whether the frquestions
        environment appears before mcquestions, and if so counts the FR
        questions to compute the MC start number.

        Args:
            filename (str, optional): Destination path. Defaults to the
                source filename with '_MC_Answers.txt' before the extension.
            header_text (str, optional): A title line written at the top of
                the file. A blank line is inserted between the header and
                the answer list. Defaults to None.

        Returns:
            str: The text that was written to the file, or None if there are
                no MC questions.
        """
        if self.mc is None:
            print('No MC questions found.')
            return None

        if filename is None:
            base = Path(self._source_path)
            stem = re.sub(r'_Exported(_Key)?$', '', base.stem)
            filename = str(base.with_name(stem + '_MC_Answers.txt'))

        # Determine where MC questions start in the overall question numbering.
        mc_start = 1
        if self.fr is not None:
            assembled = self.to_latex(key=False)
            fr_pos = assembled.find(r'\begin{frquestions}')
            mc_pos = assembled.find(r'\begin{mcquestions}')
            if fr_pos != -1 and mc_pos != -1 and fr_pos < mc_pos:
                mc_start = len(self.fr.questions) + 1

        return self.mc.export_mc_answers_to_text(
            filename=filename,
            header_text=header_text,
            mc_start=mc_start,
        )

    def summary(self):
        """Print a short summary of the combined exam's MC and FR content."""
        print("\nMixed Exam Summary")
        print("=" * 60)
        if self.mc:
            print(f"Multiple Choice: {getattr(self.mc, 'question_count', 'unknown')} questions")
        if self.fr:
            print(f"Free Response: {len(self.fr.questions)} questions")

    def verify_integrity(self, latex_text=None):
        """Run basic consistency checks on the combined exam LaTeX.

        Verifies that each expected environment appears exactly once and
        that no unresolved \\input statements remain.

        Args:
            latex_text (str, optional): LaTeX text to check. Defaults to
                self.to_latex(key=False).

        Returns:
            bool: True if all checks pass, False otherwise.
        """
        if latex_text is None:
            latex_text = self.to_latex(key=False)

        def count_env(env_name):
            begins = len(re.findall(rf'\\begin\{{{env_name}\}}', latex_text))
            ends = len(re.findall(rf'\\end\{{{env_name}\}}', latex_text))
            return begins, ends

        ok = True
        messages = []
        for env in ["mcquestions", "frquestions"]:
            b, e = count_env(env)
            if b == e == 1:
                messages.append(f"OK - {env}: found 1 begin / 1 end.")
            else:
                ok = False
                messages.append(f"ERROR - {env}: found {b} \\begin and {e} \\end.")

        leftover_inputs = re.findall(r'\\input\{[^}]*\}', latex_text)
        if leftover_inputs:
            ok = False
            messages.append(f"Warning: unresolved \\input statements found: {len(leftover_inputs)}")

        print("\nMixed Exam Integrity Check")
        print("=" * 50)
        for msg in messages:
            print(msg)
        print("=" * 50)
        print("Exam structure looks consistent!\n" if ok else "Exam may have inconsistencies.\n")
        return ok
