``exam`` module
===============

.. py:module:: exam
   :synopsis: Provides classes for managing multiple-choice and free-response exams, including question shuffling, answer key generation, and LaTeX export.

Functions
---------

.. py:function:: make_answer_key(exam)

   Creates an answer key for a multiple-choice exam by wrapping each correct
   answer option in a ``\hl{}`` command for highlighting.

   :param exam: An ``MCExam`` instance whose elements will be copied and annotated.
   :type exam: MCExam
   :return: A deep copy of ``exam.elements`` with correct options highlighted.
   :rtype: dict

Classes
-------

.. py:class:: MCQuestion(question_string=None, correct_string=None)

   Stores and manages the content of a single multiple-choice question.

   The ``\all`` and ``\none`` special tokens are recognised only when they
   appear on a ``\item`` line, so occurrences of those strings elsewhere in
   the question body are not misread as answer choices. Detected tokens are
   removed from the options list and tracked as boolean flags so they are
   always appended last during export.

   :param question_string: The full LaTeX content of the question, including
      its options block. Defaults to None.
   :type question_string: str, optional
   :param correct_string: The marker that identifies the correct answer
      (e.g., ``'CORRECT'``). Defaults to None.
   :type correct_string: str, optional

   .. py:attribute:: correct_string
      :type: str

      The marker token used to identify correct answer options.

   .. py:attribute:: question_string
      :type: str

      The original full LaTeX string for the question.

   .. py:attribute:: question_header
      :type: str

      The ``\shuffle{...}`` or ``\noshuffle{...}`` header portion of the question.

   .. py:attribute:: to_shuffle
      :type: bool

      Whether the options should be shuffled. False when ``\noshuffle`` is used.

   .. py:attribute:: options
      :type: list of str

      List of answer option strings (each prefixed with ``\item``). The
      ``\all`` and ``\none`` options are not stored here; they are tracked
      as boolean flags and appended during export.

   .. py:attribute:: all_of_above
      :type: bool

      Whether an "All of the above" option is present.

   .. py:attribute:: none_of_above
      :type: bool

      Whether a "None of the above" option is present.

   .. py:attribute:: all_of_above_correct
      :type: bool

      Whether "All of the above" is the correct answer.

   .. py:attribute:: none_of_above_correct
      :type: bool

      Whether "None of the above" is the correct answer.

   .. py:method:: shuffle_options(rng)

      Returns a new ``MCQuestion`` with answer options in a randomized order.
      The ``\all`` and ``\none`` options are unaffected because they are stored
      as flags and always appended last during export.

      :param rng: Random number generator used for shuffling.
      :type rng: numpy.random.Generator
      :return: A new ``MCQuestion`` instance with options reordered.
      :rtype: MCQuestion

   .. py:method:: add_periods(include_equations=True, correct_string=None)

      Adds a period to the end of each option's main text if one is absent.
      When an option ends with a LaTeX math expression (``$...$``), a period
      is appended only when ``include_equations`` is True. The correct-answer
      token is moved to the very end of the comment.

      :param include_equations: Whether to add a period after trailing math
         expressions. Defaults to True.
      :type include_equations: bool, optional
      :param correct_string: Override for the correct-answer token. Defaults
         to None, which falls back to ``self.correct_string``.
      :type correct_string: str, optional
      :return: None

   .. py:method:: capitalize_first(correct_string=None)

      Capitalizes the first letter of each option's main text.

      :param correct_string: Override for the correct-answer token (accepted
         for a consistent signature but unused here). Defaults to None.
      :type correct_string: str, optional
      :return: None


.. py:class:: MCGroup(group_lines, correct_string)

   Stores and manages a group of related multiple-choice questions delimited
   by ``\begin{mcgroup}{N}{header}`` and ``\end{mcgroup}`` in the LaTeX source.

   :param group_lines: Lines of LaTeX that make up the group block, excluding
      the ``\end{mcgroup}`` line.
   :type group_lines: list of str
   :param correct_string: The marker for correct answers, passed through to
      each ``MCQuestion``.
   :type correct_string: str

   .. py:attribute:: correct_string
      :type: str

      The marker token used to identify correct answer options.

   .. py:attribute:: group_header
      :type: str

      The descriptive header text from the ``\begin{mcgroup}{N}{header}`` line.

   .. py:attribute:: group_count
      :type: int

      The number of questions in the group (taken from the parsed source and
      corrected to match the actual count if they differ).

   .. py:attribute:: elements
      :type: dict

      Mapping of integer index to ``MCQuestion`` objects within this group.

   .. py:method:: shuffle_questions(rng)

      Returns a new ``MCGroup`` with questions in a randomized order.

      :param rng: Random number generator used for shuffling.
      :type rng: numpy.random.Generator
      :return: A deep copy of this group with questions reordered.
      :rtype: MCGroup

   .. py:method:: shuffle_options(rng)

      Returns a new ``MCGroup`` with each question's options shuffled.

      :param rng: Random number generator used for shuffling.
      :type rng: numpy.random.Generator
      :return: A deep copy of this group with options reordered.
      :rtype: MCGroup

   .. py:method:: add_periods(include_equations=True, correct_string=None)

      Adds periods to option text for all questions in the group. See
      ``MCQuestion.add_periods`` for full parameter details.

      :param include_equations: Whether to add a period after trailing math
         expressions. Defaults to True.
      :type include_equations: bool, optional
      :param correct_string: Override for the correct-answer token. Defaults
         to None.
      :type correct_string: str, optional
      :return: None

   .. py:method:: capitalize_first(correct_string=None)

      Capitalizes the first letter of each option for all questions in the group.

      :param correct_string: Override for the correct-answer token. Defaults
         to None.
      :type correct_string: str, optional
      :return: None


.. py:class:: MCExam(exam_file=None, exam_lines=None, correct_string='CORRECT', seed=None)

   Stores and manages the content of a multiple-choice exam. Reads a LaTeX
   file, isolates the ``mcquestions`` environment, and parses it into
   ``MCQuestion`` and ``MCGroup`` objects. Also builds the answer key and
   computes letter labels.

   When ``exam_file`` is None the instance is initialized to a valid empty
   state. The preferred way to build an ``MCExam`` from a string rather than
   a file is ``MCExam.from_string()``.

   :param exam_file: Path to the LaTeX exam file. Defaults to None.
   :type exam_file: str, optional
   :param exam_lines: Pre-read lines (currently unused; kept for API
      compatibility). Defaults to None.
   :type exam_lines: list of str, optional
   :param correct_string: Marker for the correct answer. Defaults to
      ``'CORRECT'``.
   :type correct_string: str, optional
   :param seed: Seed for the internal random number generator. Defaults to None.
   :type seed: int, optional

   .. py:attribute:: correct_string
      :type: str

      The marker token used to identify correct answer options.

   .. py:attribute:: filepath
      :type: pathlib.Path

      Resolved absolute path to the source file, or None if no file was given.

   .. py:attribute:: filename
      :type: str

      Name of the source file, or None if no file was given.

   .. py:attribute:: elements
      :type: dict

      Mapping of integer index to ``MCQuestion`` or ``MCGroup`` objects in
      source order.

   .. py:attribute:: answer_key
      :type: dict

      Deep copy of ``elements`` with correct options wrapped in ``\hl{}``.

   .. py:attribute:: mc_answer_letters
      :type: list of str

      One entry per question (or sub-question). Each entry is a
      comma-separated string of correct-answer letter labels
      (e.g., ``'(b)'``).

   .. py:attribute:: question_count
      :type: int

      Total number of individual questions, counting each sub-question within
      a group separately.

   .. py:method:: from_string(tex, correct_string='CORRECT', seed=None, source_path=None, filename_hint=None)
      :classmethod:

      Builds an ``MCExam`` directly from a LaTeX string without a file on disk.

      :param tex: LaTeX source containing an ``mcquestions`` environment, or
         raw question content.
      :type tex: str
      :param correct_string: Marker for the correct answer. Defaults to
         ``'CORRECT'``.
      :type correct_string: str, optional
      :param seed: Seed for the internal RNG. Defaults to None.
      :type seed: int, optional
      :param source_path: Path of the originating file, used to set
         ``self.filepath``. Defaults to None.
      :type source_path: str, optional
      :param filename_hint: Short filename to assign to ``self.filename``.
         Defaults to None.
      :type filename_hint: str, optional
      :return: A fully initialized ``MCExam`` instance.
      :rtype: MCExam

   .. py:method:: print_exam()

      Prints the content of the exam to the console.

      :return: None

   .. py:method:: print_answer_key()

      Prints the answer key for the exam to the console.

      :return: None

   .. py:method:: show_duplicates()

      Displays any duplicate answer options found across all exam questions.

      :return: None

   .. py:method:: to_latex(key=False)

      Returns the full LaTeX string for this exam without writing to disk.

      :param key: If True, return the answer key version. Defaults to False.
      :type key: bool, optional
      :return: Complete LaTeX source for the exam or answer key.
      :rtype: str

   .. py:method:: export_exam(filename=None)

      Exports the student exam to a LaTeX file.

      :param filename: Destination path. Defaults to the original filename.
      :type filename: str, optional
      :return: The LaTeX string that was written.
      :rtype: str

   .. py:method:: export_key(filename=None)

      Exports the answer key with correct answers highlighted to a LaTeX file.

      :param filename: Destination path. Defaults to the original filename
         with ``'_Key'`` appended before the extension.
      :type filename: str, optional
      :return: The LaTeX string that was written.
      :rtype: str

   .. py:method:: export_mc_answers_to_text(filename=None, header_text=None, mc_start=1)

      Exports the MC answer letters to a plain-text file. Each line contains
      a question number and its correct-answer letter, e.g. ``'1. (b)'``.

      :param filename: Destination path. Defaults to the original filename
         with ``'_MC_Answers.txt'`` appended before the extension.
      :type filename: str, optional
      :param header_text: A title line written at the top of the file, followed
         by a blank line. Defaults to None.
      :type header_text: str, optional
      :param mc_start: The global question number assigned to the first MC
         question. Useful when MC questions do not start at question 1 in the
         overall exam. Defaults to 1.
      :type mc_start: int, optional
      :return: The text that was written to the file.
      :rtype: str

   .. py:method:: shuffle_questions(filename=None, seed=None, shuffle_within_groups=True)

      Returns a new exam with questions shuffled. When at least one standalone
      ``MCQuestion`` exists, one is always placed first; the remaining
      standalone questions and any ``MCGroup`` objects are then randomly
      interleaved. When the exam contains only ``MCGroup`` objects, all groups
      are shuffled without the forced-first-question step.

      :param filename: Filename for the returned exam object. Defaults to the
         original stem with ``'_questions_shuffled.tex'`` appended.
      :type filename: str, optional
      :param seed: Random seed for reproducibility. Defaults to None.
      :type seed: int, optional
      :param shuffle_within_groups: Whether to also shuffle questions within
         each ``MCGroup``. Defaults to True.
      :type shuffle_within_groups: bool, optional
      :return: A new ``MCExam`` instance with shuffled questions.
      :rtype: MCExam

   .. py:method:: shuffle_options(filename=None, seed=None)

      Returns a new exam with answer options shuffled within each question.
      The ``\all`` and ``\none`` options always remain at the end because they
      are stored as flags and appended during export.

      :param filename: Filename for the returned exam object. Defaults to the
         original stem with ``'_options_shuffled.tex'`` appended.
      :type filename: str, optional
      :param seed: Random seed for reproducibility. Defaults to None.
      :type seed: int, optional
      :return: A new ``MCExam`` instance with shuffled options.
      :rtype: MCExam

   .. py:method:: shuffle_options_and_questions(filename=None, seed=None, shuffle_within_groups=True)

      Returns a new exam with both options and questions shuffled.

      :param filename: Filename for the returned exam object. Defaults to the
         original stem with ``'_options_shuffled.tex'`` appended.
      :type filename: str, optional
      :param seed: Random seed for reproducibility. Defaults to None.
      :type seed: int, optional
      :param shuffle_within_groups: Whether to shuffle questions within groups.
         Defaults to True.
      :type shuffle_within_groups: bool, optional
      :return: A new ``MCExam`` instance with shuffled options and questions.
      :rtype: MCExam

   .. py:method:: add_periods(include_equations=True)

      Adds periods to the end of answer choice text throughout the exam.

      :param include_equations: Whether to add a period after trailing math
         expressions. Defaults to True.
      :type include_equations: bool, optional
      :return: None

   .. py:method:: capitalize_first()

      Capitalizes the first letter of each answer choice throughout the exam.

      :return: None

   .. py:method:: set_seed(seed=None)

      Sets the random seed for the exam's internal random number generator.

      :param seed: Seed value. Defaults to None.
      :type seed: int, optional
      :return: None


.. py:class:: FRExam(filename=None)

   Handles free-response exams using the ``\question[points]`` syntax. Reads a
   LaTeX file and parses all ``\question`` blocks into a list of question dicts.
   ``\input{}`` commands that reference files containing a ``\question`` token
   are expanded automatically; figure and TikZ inputs inside answer blocks are
   left untouched.

   :param filename: Path to the LaTeX exam file. If provided, the file is read
      and parsed immediately. Defaults to None.
   :type filename: str, optional

   .. py:attribute:: filepath
      :type: pathlib.Path

      Resolved absolute path to the source file, or None if no file was given.

   .. py:attribute:: filename
      :type: str

      Name of the source file, or None if no file was given.

   .. py:attribute:: questions
      :type: list of dict

      List of parsed question dicts. Each dict has keys ``'file'`` (source
      filename), ``'points'`` (int or None), and ``'text'`` (full LaTeX string
      for the question).

   .. py:method:: from_string(tex, source_path=None, filename_hint=None)
      :classmethod:

      Builds an ``FRExam`` directly from a LaTeX string without a file on disk.
      When ``source_path`` is provided its parent directory is used to resolve
      any ``\input{}`` commands that reference sub-files containing a
      ``\question`` token.

      :param tex: LaTeX source containing free-response question content.
      :type tex: str
      :param source_path: Path of the originating file, used to resolve
         relative ``\input{}`` paths. Defaults to None.
      :type source_path: str, optional
      :param filename_hint: Short filename to assign to ``self.filename``.
         Defaults to None.
      :type filename_hint: str, optional
      :return: A fully initialized ``FRExam`` instance.
      :rtype: FRExam

   .. py:method:: to_latex(key=False)

      Returns the full LaTeX string for this free-response exam.

      :param key: If True, reveal answer environments. Defaults to False.
      :type key: bool, optional
      :return: Complete LaTeX source for the exam or answer key.
      :rtype: str

   .. py:method:: export_exam(filename=None)

      Exports the student exam version (answers hidden) to a LaTeX file.

      :param filename: Destination path. Defaults to ``'FR_Exam.tex'`` in the
         same directory as the source file.
      :type filename: str, optional
      :return: None

   .. py:method:: export_key(filename=None)

      Exports the answer key version (answers revealed) to a LaTeX file.

      :param filename: Destination path. Defaults to ``'FR_Key.tex'`` in the
         same directory as the source file.
      :type filename: str, optional
      :return: None

   .. py:method:: reveal_answers(text=None)

      Returns the exam text with ``\begin{answer}...\end{answer}`` blocks
      expanded.

      :param text: LaTeX text to process. Defaults to the concatenated text of
         all stored questions.
      :type text: str, optional
      :return: LaTeX text with answer environments expanded.
      :rtype: str

   .. py:method:: summary(max_chars=80)

      Prints a summary of all parsed free-response questions, showing the
      question number, point value, source file, and a short preview of the
      question text.

      :param max_chars: Maximum number of characters to show in the question
         preview. Defaults to 80.
      :type max_chars: int, optional
      :return: None


.. py:class:: Exam(filename, mc=None, fr=None, correct_string='CORRECT', seed=None)

   Combines ``MCExam`` and ``FRExam`` content into a single LaTeX document.
   Auto-detects MC and FR sections from ``\input{}`` statements or inline
   environments. Pre-built ``MCExam`` and ``FRExam`` objects may be passed
   directly to bypass auto-detection.

   :param filename: Path to the main exam LaTeX file.
   :type filename: str
   :param mc: Pre-parsed multiple-choice exam. Defaults to None (auto-detect).
   :type mc: MCExam, optional
   :param fr: Pre-parsed free-response exam. Defaults to None (auto-detect).
   :type fr: FRExam, optional
   :param correct_string: Marker for correct MC answers. Defaults to
      ``'CORRECT'``.
   :type correct_string: str, optional
   :param seed: Random seed for reproducibility. Defaults to None.
   :type seed: int, optional

   .. py:attribute:: mc
      :type: MCExam or None

      The multiple-choice portion of the exam.

   .. py:attribute:: fr
      :type: FRExam or None

      The free-response portion of the exam.

   .. py:method:: shuffle_options(seed=None, filename=None)

      Returns a new ``Exam`` with shuffled MC options, preserving FR questions.

      :param seed: Random seed for reproducibility. Defaults to None.
      :type seed: int, optional
      :param filename: If provided, sets the base path for subsequent
         ``export_exam`` and ``export_key`` calls.
      :type filename: str, optional
      :return: A deep copy of this ``Exam`` with MC options shuffled.
      :rtype: Exam

   .. py:method:: to_latex(key=False)

      Returns the full LaTeX string for the combined MC and FR exam. Raises
      ``ValueError`` if the assembled output does not contain exactly one
      ``mcquestions`` and one ``frquestions`` environment.

      :param key: If True, produce the answer key version. Defaults to False.
      :type key: bool, optional
      :return: Complete LaTeX source for the exam or answer key.
      :rtype: str
      :raises ValueError: If an environment appears more or fewer than once.

   .. py:method:: export_exam(filename=None)

      Exports the combined student exam (no answers, no key-only content) to
      a LaTeX file.

      :param filename: Destination path. Defaults to the source filename with
         ``'_Exported'`` appended before the extension.
      :type filename: str, optional
      :return: None

   .. py:method:: export_key(filename=None)

      Exports the combined instructor key (FR answers shown, key-only content
      included) to a LaTeX file.

      :param filename: Destination path. Defaults to the source filename with
         ``'_Exported_Key'`` appended before the extension.
      :type filename: str, optional
      :return: None

   .. py:method:: export_mc_answers_to_text(filename=None, header_text=None)

      Exports the MC answer letters to a plain-text file with correct question
      numbering, even when FR questions precede the MC section. Scans the
      assembled exam to determine whether ``frquestions`` appears before
      ``mcquestions``, and if so counts the FR questions to compute the MC
      start number automatically.

      :param filename: Destination path. Defaults to the source filename with
         ``'_MC_Answers.txt'`` appended before the extension.
      :type filename: str, optional
      :param header_text: A title line written at the top of the file, followed
         by a blank line. Defaults to None.
      :type header_text: str, optional
      :return: The text that was written to the file, or None if there are no
         MC questions.
      :rtype: str or None

   .. py:method:: summary()

      Prints a short summary of the combined exam's MC and FR content.

      :return: None

   .. py:method:: verify_integrity(latex_text=None)

      Runs basic consistency checks on the combined exam LaTeX. Verifies that
      each expected environment appears exactly once and that no unresolved
      ``\input`` statements remain.

      :param latex_text: LaTeX text to check. Defaults to
         ``self.to_latex(key=False)``.
      :type latex_text: str, optional
      :return: True if all checks pass, False otherwise.
      :rtype: bool
