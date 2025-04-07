``exam`` module
===============

.. py:module:: exam
   :synopsis: This module provides functionality for managing multiple-choice exams, including question shuffling, answer key generation, and LaTeX export.

Functions
---------

.. py:function:: make_answer_key(exam)

   Creates an answer key for the given multiple-choice exam.

   :param exam: An exam object containing elements, options, and a `correct_string` to identify correct answers.
   :type exam: mc_exam
   :return: A dictionary representing the answer key.
   :rtype: dict

Classes
-------

.. py:class:: mc_question

   Defines a class for storing and managing the content of a multiple-choice question.

   .. py:method:: __init__(question_string=None, correct_string=None)

      Initializes an mc_question instance.

      :param question_string: The full content of the multiple-choice question, including options. Defaults to None.
      :type question_string: str, optional
      :param correct_string: The marker indicating the correct answer. Defaults to None.
      :type correct_string: str, optional

   .. py:method:: shuffle_options(rng)

      Shuffles the options of the question if shuffling is desired.

      :param rng: A random number generator for shuffling.
      :type rng: numpy.random.Generator
      :return: A new mc_question instance with shuffled options.
      :rtype: mc_question

   .. py:method:: add_periods(include_equations=True, correct_string=None)

      Adds periods to the end of each option if not already present.

      :param include_equations: Whether to include periods for options ending with equations. Defaults to True.
      :type include_equations: bool, optional
      :param correct_string: The marker for the correct answer. Defaults to None.
      :type correct_string: str, optional

   .. py:method:: capitalize_first(correct_string=None)

      Capitalizes the first letter of each option.

      :param correct_string: The marker for the correct answer. Defaults to None.
      :type correct_string: str, optional

.. py:class:: mc_group

   Defines a class for storing and managing a group of multiple-choice questions.

   .. py:method:: __init__(group_lines, correct_string)

      Initializes an mc_group instance.

      :param group_lines: Lines from a LaTeX file between \begin{mcquestions} and \end{mcquestions}.
      :type group_lines: list
      :param correct_string: The marker indicating the correct answer for questions in the group.
      :type correct_string: str

   .. py:method:: shuffle_questions(rng)

      Shuffles the order of questions within the group.

      :param rng: A random number generator for shuffling.
      :type rng: numpy.random.Generator
      :return: A new mc_group instance with shuffled questions.
      :rtype: mc_group

   .. py:method:: shuffle_options(rng)

      Shuffles the options for each question in the group.

      :param rng: A random number generator for shuffling.
      :type rng: numpy.random.Generator
      :return: A new mc_group instance with shuffled options for each question.
      :rtype: mc_group