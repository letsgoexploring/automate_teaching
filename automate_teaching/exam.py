import pandas as pd
import numpy as np
from copy import deepcopy
import os
import string
import re
from pathlib import Path


def make_answer_key(exam):
    """Creates an answer key for the given multiple choice exam.

    Args:
        exam (mc_exam): An exam object containing elements, options, and a 
            `correct_string` to identify correct answers.

    Returns:
        dict: A dictionary representing the answer key.
    """

    answer_key = deepcopy(exam.elements)

    for key,value in exam.elements.items():
        if isinstance(value,mc_question):
            
            for n,option in enumerate(exam.elements[key].options):
                if exam.correct_string in option:
                    answer_key[key].options[n] = '\\item \\hl{'+option.replace('\\item','').lstrip().replace(exam.correct_string,'').replace('\\%','PERCENTSIGNHERE').replace('%','').replace('PERCENTSIGNHERE','\\%')+'}'+' %'+exam.correct_string
            
        
        else:
            for sub_key,sub_value in value.elements.items():
    
                for n,option in enumerate(exam.elements[key].elements[sub_key].options):
                    if exam.correct_string in option:
                        answer_key[key].elements[sub_key].options[n] = '\\item \\hl{'+option.replace('\\item','').lstrip().replace(exam.correct_string,'').replace('\\%','PERCENTSIGNHERE').replace('%','').replace('PERCENTSIGNHERE','\\%')+'}'+' %'+exam.correct_string
        
    return answer_key
        
        
    
class mc_question:
    """Defines a class for storing and managing the content of a multiple-choice question."""
    
    def __init__(self,question_string=None,correct_string=None):
        """Initializes an mc_question instance.

        Parses the question string to extract the question header, options, 
        and settings for shuffling, "all of the above," and "none of the above."

        Args:
            question_string (str, optional): The full content of the multiple-choice question, 
                including options. Defaults to None.
            correct_string (str, optional): The marker indicating the correct answer. Defaults to None.
        """
        
        def get_question_split_point(question_string):
            """Finds the index of the end of the first pair of braces in the question string.

            Args:
                question_string (str): A string containing the entire content of a multiple-choice question.

            Returns:
                int: The index of the split point, where the question header ends and the options begin.
            """
        
            # Initialize counts of left and right braces
            left_brace_count = 0
            right_brace_count = 0
        
            # Boolean to identify whether an outer brace is currently unclosed.
            open_outer_brace = False
        
            # Iterate over characters in question_string and find first pair of outer braces    
            for i,char in enumerate(question_string):
                if char=='{':
                    left_brace_count+=1
                    if open_outer_brace == False:
                        open_outer_brace = True
                elif char=='}':
                    right_brace_count+=1
        
                # Escape if the end of the first pair was found.
                if left_brace_count-right_brace_count==0 and open_outer_brace:
                    
                    break
                
        
            return i+1

        self.correct_string = correct_string
    
        if question_string is not None:

            self.question_string = question_string
            
            split_point = get_question_split_point(self.question_string)
            self.question_header = self.question_string[:split_point]

            if 'noshuffle' in self.question_header:
                self.to_shuffle = False
            else:
                self.to_shuffle = True


            options = question_string[split_point:].lstrip().rstrip()[1:-1].lstrip().rstrip()

            self.all_of_above = False
            self.none_of_above = False
            
            self.all_of_above_correct = False
            self.none_of_above_correct = False
            
            
            if '\\all' in options:
                self.all_of_above=True
                
                for option_line in options.split('\n'):
                    if '\\all' in option_line and self.correct_string in option_line:
                        self.all_of_above_correct = True
                        options = options.replace(option_line,'')
                        break
                
                options = options.replace('\\all','')
            
            if '\\none' in options:
                self.none_of_above = True
                
                for option_line in options.split('\n'):
                    if '\\none' in option_line and self.correct_string in option_line:
                        self.none_of_above_correct = True
                        options = options.replace(option_line,'')
                        break
                
                options = options.replace('\\none','')
            
            options = options.lstrip().rstrip()
            
            options = options.split('\\item')[1:]
            
            for n in range(len(options)):
                options[n] = '\\item '+options[n].lstrip().rstrip()
            
            self.options = options


    def shuffle_options(self,rng):
        """Shuffles the options of the question if shuffling is desired.

        Args:
            rng (numpy.random.Generator): A random number generator for shuffling.

        Returns:
            mc_question: A new mc_question instance with shuffled options.
        """
    
        new_question = deepcopy(self)
    
        if self.to_shuffle:

            options = np.r_[self.options]
    
            N_options = len(self.options)
    
            choice = rng.choice(np.arange(N_options),replace=False,size=N_options)
    
            new_question.options = options[choice].tolist()
    
        return new_question
        
    def add_periods(self, include_equations=True, correct_string=None):
        """Adds periods to the end of each option if not already present.
        If an equation already ends with a period inside $, no new period is added.
        """
        for n, option in enumerate(self.options):
            option_text = (
                option.replace('\\item', '')
                .lstrip()
                .replace(correct_string or '', '')
                .replace('\\%', 'PERCENTSIGNHERE')
                .replace('%', '')
                .replace('PERCENTSIGNHERE', '\\%')
                .rstrip()
            )

            # 🧠 Detect if the text already ends with a period (outside or inside math)
            already_has_period = option_text.endswith('.')

            if not already_has_period:
                # Check for math at the end, e.g., $y=x$ or $y=x.$
                m = re.search(r'\$(.*?)\$', option_text)
                if m:
                    inner_math = m.group(1).strip()
                    # ✅ If math ends with a period, do NOT add another
                    if not inner_math.endswith('.'):
                        if include_equations:
                            option_text += '.'
                else:
                    # No math environment — add a period normally
                    option_text += '.'

            if correct_string and correct_string in option:
                option_text += ' %' + self.correct_string

            self.options[n] = '\\item ' + option_text
    
    
    def capitalize_first(self,correct_string=None):
        """Capitalizes the first letter of each option.

        Args:
            correct_string (str, optional): The marker for the correct answer. Defaults to None.
        """
    
        for n,option in enumerate(self.options):
        
            option_text = option.replace('\\item','').lstrip().replace(correct_string,'').replace('\\%','PERCENTSIGNHERE').replace('%','').replace('PERCENTSIGNHERE','\\%').rstrip()
            
            option_text = option_text[0].upper() + option_text[1:]
            
            if correct_string in option:
            
                option_text+=' %'+self.correct_string
            
            self.options[n] = '\\item '+option_text


class mc_group:
    """Defines a class for storing and managing a group of multiple-choice questions."""
    
    def __init__(self, group_lines, correct_string):
        """Initializes an mc_group instance."""
        self.correct_string = correct_string
        self.group_lines = group_lines
        self.group_string = ''.join(group_lines).strip()

        # Extract count and header
        self.group_count, self.group_header = self._get_group_count_and_header(self.group_string)

        self.elements = {}
        index = 0
        open_group = False
        actual_count = 0

        for n, line in enumerate(self.group_lines):
            if line.lstrip().startswith('%'):
                continue

            if (('\\shuffle' in line or '\\noshuffle' in line)
                and not open_group):
                length = self._get_question_length(self.group_lines, n)
                start = n
                end = n + length
                question_string = ''.join(self.group_lines[start:end]).strip()
                mc = mc_question(question_string, correct_string=self.correct_string)
                self.elements[index] = mc
                index += 1
                actual_count += 1

        if actual_count != self.group_count:
            print(
                f"⚠️ Warning: stated {self.group_count} but found {actual_count} "
                f"in group:\n{self.group_header}\n"
            )

        self.group_count = actual_count

    # ---------------------------------------------------------------------
    def _get_question_length(self, mc_lines, starting_line_number):
        """Count how many lines a single question spans."""
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

    def _get_group_count_and_header(self, group_string):
        """Extracts the group count and header from the LaTeX group line."""
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

    # ---------------------------------------------------------------------
    def shuffle_questions(self, rng):
        new_group = deepcopy(self)
        reordered_keys = rng.choice(list(new_group.elements.keys()), replace=False, size=len(new_group.elements))
        reordered_elements = {j + 1: new_group.elements[key] for j, key in enumerate(reordered_keys)}
        new_group.elements = reordered_elements
        return new_group

    def shuffle_options(self, rng):
        new_group = deepcopy(self)
        for key, value in self.elements.items():
            new_group.elements[key] = value.shuffle_options(rng)
        return new_group

    def add_periods(self, include_equations=True, correct_string=None):
        for key, value in self.elements.items():
            self.elements[key].add_periods(include_equations=True, correct_string=correct_string)

    def capitalize_first(self, correct_string=None):
        for key, value in self.elements.items():
            self.elements[key].capitalize_first(correct_string=correct_string)


class mc_exam:
    """Defines a class for storing the content of a multiple choice exam."""

    def __init__(self, exam_file=None, exam_lines=None, correct_string='CORRECT', seed=None):
        self.correct_string = correct_string
        # Keep filename short if exam_file is a path
        self.filepath = Path(exam_file).resolve() if exam_file else None
        self.filename = self.filepath.name if exam_file else None
        
        self.rng = np.random.default_rng(seed=seed)

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

        self.elements = {}
        index = 0
        open_group = False

        for n, line in enumerate(self.mc_lines):
            if line.lstrip().startswith('%'):
                continue

            if 'begin{mcgroup}' in line:
                group_start = n
                open_group = True
            elif 'end{mcgroup}' in line:
                group_end = n
                open_group = False
                group_lines = self.mc_lines[group_start:group_end]
                self.elements[index] = mc_group(group_lines, correct_string=self.correct_string)
                index += 1
            elif (('\\shuffle' in line or '\\noshuffle' in line)
                  and not open_group):
                length = self.get_question_length(self.mc_lines, n)
                start = n
                end = n + length
                question_string = ''.join(self.mc_lines[start:end]).strip()
                mc = mc_question(question_string, correct_string=self.correct_string)
                self.elements[index] = mc
                index += 1

        self.question_count = sum(
            1 if isinstance(v, mc_question) else len(v.elements)
            for v in self.elements.values()
        )

        self.answer_key = make_answer_key(self)
        self.mc_answer_letters = self._compute_answer_key_letters()

    # ---------------------------------------------------------
    def _filter_visibility(self, text, reveal=False):
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        if reveal:
            text = re.sub(r'(?s)\\begin\s*\{examonly\}.*?\\end\s*\{examonly\}', '', text)
        else:
            text = re.sub(r'(?s)\\begin\s*\{keyonly\}.*?\\end\s*\{keyonly\}', '', text)
        return text

    def get_question_length(self, mc_lines, starting_line_number):
        """Count how many lines a single question spans."""
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

    def print_exam(self):
        """Prints the content of the exam to the console."""

        question_count = 0
        for key,value in self.elements.items():
            if isinstance(value,mc_question):
                question_count+=1
        
                print('Question '+ str(question_count)+'\n\n')
                print(value.question_header)
                print()
                for o in value.options:
                    print(o)
        
                print('\n----------------------------\n')
            else:
                for sub_key,sub_value in value.elements.items():
                    question_count+=1
                    print('Question '+ str(question_count)+'\n\n')
                    print(sub_value.question_header)
                    print()
                    for o in sub_value.options:
                        print(o)
            
                    print('\n----------------------------\n')

    def print_answer_key(self):
        """Prints the answer key for the exam to the console."""

        question_count = 0
        for key,value in self.answer_key.items():
            if isinstance(value,mc_question):
                question_count+=1
        
                print('Question '+ str(question_count)+'\n\n')
                print(value.question_header)
                print()
                for o in value.options:
                    print(o)
        
                print('\n----------------------------\n')
            else:
                for sub_key,sub_value in value.elements.items():
                    question_count+=1
                    print('Question '+ str(question_count)+'\n\n')
                    print(sub_value.question_header)
                    print()
                    for o in sub_value.options:
                        print(o)
            
                    print('\n----------------------------\n')

    def show_duplicates(self):
        """Displays any duplicate options in the exam questions."""

        def duplicated(options,question_number):
            """Identifies and prints duplicate options for a specific question.

            Args:
                options (list): List of options for the question.
                question_number (int): The question number being checked for duplicates.
            """

            options = pd.Series(options)
        
            duplicated = options[options.duplicated()]
        
            if len(duplicated)>0:
                print('Question '+str(question_number))
            
            for d in duplicated:
                print(d)
        
            if len(duplicated)>0:
                print()
    
    
        question_count = 0
        for key,value in self.elements.items():
            if isinstance(value,mc_question):
                question_count+=1
        
                duplicated(value.options,question_number=question_count)
        
            else:
                for sub_key,sub_value in value.elements.items():
                    question_count+=1
                    duplicated(sub_value.options,question_number=question_count)

    def to_latex(self, key=False):
        """Return the full LaTeX string for this multiple-choice exam, without writing to disk."""
        if key:
            output = self.export_key_to_string()
        else:
            output = self.export_exam_to_string()
        return output

    def export_exam_to_string(self):
        """Return LaTeX for the student MC exam (answers hidden), as a string."""
        output = ''
        output += self.exam_header
        output += '\\begin{mcquestions}\n\n'

        for key, value in self.elements.items():
            if isinstance(value, mc_question):
                output += value.question_header + '\n{\n'
                for option in value.options:
                    output += '\t' + option + '\n'
                if value.all_of_above:
                    output += '\t\\item All of the above.\n'
                if value.none_of_above_correct:
                    output += '\t\\item None of the above.\n'
                output += '}\n\n'
            else:
                output += '\n% BEGIN MC GROUP BLOCK\n'
                output += f'\\begin{{mcgroup}}{{{value.group_count}}}{{{value.group_header}}}\n\n'
                for sub_key, sub_value in value.elements.items():
                    output += sub_value.question_header + '{\n'
                    for option in sub_value.options:
                        output += '\t' + option + '\n'
                    if getattr(sub_value, "all_of_above", False):
                        output += '\t\\item All of the above.\n'
                    if getattr(sub_value, "none_of_above_correct", False):
                        output += '\t\\item None of the above.\n'
                    output += '}\n\n'
                output += '% END MC GROUP BLOCK\n\\end{mcgroup}\n\n\n'

        output += '\\end{mcquestions}\n\n'
        output += self.exam_footer

        # 🚫 Remove key-only blocks from header/body/footer
        output = self._filter_visibility(output, reveal=False)
        return output

    def export_key_to_string(self):
        """Return LaTeX for the MC answer key (answers revealed), as a string."""
        output = ''
        output += self.exam_header
        output += '\\begin{mcquestions}\n\n'

        # Use the prebuilt self.answer_key (already has \hl on correct choices)
        for key, value in self.answer_key.items():
            if isinstance(value, mc_question):
                output += value.question_header + '\n{\n'
                for option in value.options:
                    output += '\t' + option + '\n'
                # If original had all/none flags, include them where appropriate.
                if getattr(self.elements[key], "all_of_above", False):
                    # label becomes next item; highlight if marked correct
                    text = '\\item All of the above.'
                    if getattr(self.elements[key], "all_of_above_correct", False):
                        text = '\\item \\hl{All of the above.} % ' + self.correct_string
                    output += '\t' + text + '\n'
                if getattr(self.elements[key], "none_of_above", False):
                    text = '\\item None of the above.'
                    if getattr(self.elements[key], "none_of_above_correct", False):
                        text = '\\item \\hl{None of the above.} % ' + self.correct_string
                    output += '\t' + text + '\n'
                output += '}\n\n'
            else:
                # group
                grp = self.elements[key]
                output += '\n% BEGIN MC GROUP BLOCK\n'
                output += f'\\begin{{mcgroup}}{{{grp.group_count}}}{{{grp.group_header}}}\n\n'
                for sub_key, sub_value in value.elements.items():
                    output += sub_value.question_header + '{\n'
                    for option in sub_value.options:
                        output += '\t' + option + '\n'
                    orig = grp.elements[sub_key]
                    if getattr(orig, "all_of_above", False):
                        text = '\\item All of the above.'
                        if getattr(orig, "all_of_above_correct", False):
                            text = '\\item \\hl{All of the above.} % ' + self.correct_string
                        output += '\t' + text + '\n'
                    if getattr(orig, "none_of_above", False):
                        text = '\\item None of the above.'
                        if getattr(orig, "none_of_above_correct", False):
                            text = '\\item \\hl{None of the above.} % ' + self.correct_string
                        output += '\t' + text + '\n'
                    output += '}\n\n'
                output += '% END MC GROUP BLOCK\n\\end{mcgroup}\n\n\n'

        output += '\\end{mcquestions}\n\n'
        output += self.exam_footer

        # 🚫 Remove exam-only blocks from header/body/footer
        output = self._filter_visibility(output, reveal=True)
        return output


    def export_key(self, filename=None):
        """Exports the multiple-choice answer key with correct answers highlighted.
        Hides exam-only blocks and includes key-only content.
        """
        if filename is None:
            filename = str(self.filename).replace('.tex', '') + '_Key.tex'
        self.key_filename = filename

        output = ''.join([self.exam_header, '\\begin{mcquestions}\n\n'])

        for key, value in self.elements.items():
            if isinstance(value, mc_question):
                output += self.answer_key[key].question_header + '\n{\n'
                for option in self.answer_key[key].options:
                    output += '\t' + option + '\n'
                if self.answer_key[key].all_of_above_correct:
                    output += '\t\\item \\hl{All of the above.} %' + self.correct_string + '\n'
                elif self.answer_key[key].all_of_above:
                    output += '\t\\item All of the above.\n'
                if self.answer_key[key].none_of_above_correct:
                    output += '\t\\item \\hl{None of the above.} %' + self.correct_string + '\n'
                elif self.answer_key[key].none_of_above:
                    output += '\t\\item None of the above.\n'
                output += '}\n\n'
            else:
                output += f'\n% BEGIN MC GROUP BLOCK\n\\begin{{mcgroup}}{{{value.group_count}}}{{{value.group_header}}}\n\n'
                for sub_key, sub_value in value.elements.items():
                    output += self.answer_key[key].elements[sub_key].question_header + '{\n'
                    for option in self.answer_key[key].elements[sub_key].options:
                        output += '\t' + option + '\n'
                    if self.answer_key[key].elements[sub_key].all_of_above_correct:
                        output += '\t\\item \\hl{All of the above.} %' + self.correct_string + '\n'
                    elif self.answer_key[key].elements[sub_key].all_of_above:
                        output += '\t\\item All of the above.\n'
                    if self.answer_key[key].elements[sub_key].none_of_above_correct:
                        output += '\t\\item \\hl{None of the above.} %' + self.correct_string + '\n'
                    elif self.answer_key[key].elements[sub_key].none_of_above:
                        output += '\t\\item None of the above.\n'
                    output += '}\n\n'
                output += '% END MC GROUP BLOCK\n\\end{mcgroup}\n\n\n'

        output += '\\end{mcquestions}\n\n'
        output += ''.join(self.exam_footer) if isinstance(self.exam_footer, list) else str(self.exam_footer)

        # 🧹 Hide exam-only and reveal key-only content
        output = self._filter_visibility(output, reveal=True)

        with open(filename, 'w', encoding='utf-8') as newfile:
            newfile.write(output)

        print(f"✅ Exported MC key: {filename}")
        return output


    def export_exam(self,filename=None):
        """Exports the exam content to a LaTeX file.

        Args:
            filename (str, optional): Path to save the LaTeX file. Defaults to the original filename with an appended suffix.
        """
        
        if filename is None:
            
            filename = str(self.filename).replace('.tex', '') + '.tex'

        output = ''

        output +=self.exam_header
        
        output +='\\begin{mcquestions}\n\n'
        
        for key,value in self.elements.items():
            if isinstance(value,mc_question):
                # self.question_count+=1
        
                output+= self.elements[key].question_header+'\n{\n'
                
                for option in self.elements[key].options:
                    output+='\t'+option+'\n'
                if self.elements[key].all_of_above:
                    output+='\t\\item All of the above.\n'
                if self.elements[key].none_of_above_correct:
                    output+='\t\\item None of the above.\n'
                output+='}\n\n'
            
            else:
                output+='\n% BEGIN MC GROUP BLOCK\n\\begin{mcgroup}{'+str(value.group_count)+'}{'+value.group_header+'}\n\n'
                
                for sub_key,sub_value in value.elements.items():
                    
                    output+= self.elements[key].elements[sub_key].question_header+'{\n'
        
                    for option in self.elements[key].elements[sub_key].options:
                        output+='\t'+option+'\n'
                    if self.elements[key].elements[sub_key].all_of_above:
                        output+='\t\\item All of the above.\n'
                    if self.elements[key].elements[sub_key].none_of_above_correct:
                        output+='\t\\item None of the above.\n'
                    output+='}\n\n'
        
                output+='% END MC GROUP BLOCK\n\\end{mcgroup}\n\n\n'
        
        output += '\\end{mcquestions}\n\n'
        output += self.exam_footer

        # 🧹 Remove key-only blocks (since this is the student version)
        output = self._filter_visibility(output, reveal=False)

        with open(filename, 'w', encoding='utf-8') as newfile:
            newfile.write(output)

        self.filepath = Path(filename).resolve()
        self.filename = str(self.filepath)

        print(f"✅ Exported MC exam: {filename}")
        return output
            
            
    def shuffle_questions(self,filename=None,seed=None,shuffle_within_groups=True):
        """Shuffles the questions in the exam.

        Args:
            filename (str, optional): Path to save the shuffled exam.
            seed (int, optional): Random seed for reproducibility.
            shuffle_within_groups (bool): Whether to shuffle questions within groups.
        
        Returns:
            mc_exam: A new instance with shuffled questions.
        """

        new_exam = deepcopy(self)
        
        if filename is not None:
            new_exam.filename = filename

        else:
            new_exam.filename = self.filename.replace('.tex','')+'_questions_shuffled'+'.tex'

        if seed is not None:
            
            self.rng = np.random.default_rng(seed=seed)

        
        # Get keys of which elements are MC questions and which are question groups
        mc_question_keys = []
        mc_group_keys = []
        
        for key,value in self.elements.items():
        
            if isinstance(value,mc_question):
        
                mc_question_keys.append(key)
        
            else:
        
                mc_group_keys.append(key)
        
        # Randomly select a MC question to out at top of exam
        first_choice = self.rng.choice(np.arange(len(mc_question_keys)))
        
        # Array that will store the new element ordering
        reordered_keys = np.r_[mc_question_keys[first_choice]]
        
        # Remove the chosen elemet from the list of MC question keys
        del mc_question_keys[first_choice]
        
        # Combine keys for remaining MC questions and question groups
        remaining_options = np.r_[mc_question_keys,mc_group_keys]
        
        # Number of choices
        M = len(self.elements) - 1
        
        # Randomly draw the rest of the ordering
        remaining_choices = self.rng.choice(np.arange(M),replace=False,size=M)
        
        # The reordered keys
        reordered_keys = np.r_[reordered_keys,remaining_options[remaining_choices]]
        
        # The reordered elements dictionary
        reordered_elements = {j+1 : self.elements[key] for j,key in enumerate(reordered_keys) }

        new_exam.elements = reordered_elements

        # Reorder the questions in each group
        if shuffle_within_groups:
            for key,value in new_exam.elements.items():
            
                if isinstance(value,mc_group):
                    
                    new_exam.elements[key] = new_exam.elements[key].shuffle_questions(self.rng)


        new_exam.answer_key = make_answer_key(new_exam)
        new_exam.mc_answer_letters = new_exam._compute_answer_key_letters()

        
        
        return new_exam

    def set_seed(self,seed=None):
        """Sets the random seed for reproducibility.

        Args:
            seed (int, optional): Random seed value.
        """

        self.rng = np.random.default_rng(seed=seed)

    def shuffle_options(self, filename=None, seed=None):
        """Shuffles the options within each question.

        Args:
            filename (str, optional): Path to save the shuffled exam.
            seed (int, optional): Random seed for reproducibility.

        Returns:
            mc_exam: A new mc_exam instance with shuffled options.
        """

        # Create a full deep copy so we don't mutate the original
        new_exam = deepcopy(self)

        # ✅ Set the filename
        if filename is not None:
            new_exam.filename = filename
        else:
            new_exam.filename = self.filename.replace('.tex', '') + '_options_shuffled.tex'

        # ✅ Seed the RNG *on the new copy*, not on self
        if seed is not None:
            new_exam.rng = np.random.default_rng(seed=seed)
        else:
            new_exam.rng = np.random.default_rng()

        # ✅ Shuffle each question’s options using the new RNG
        for key, value in new_exam.elements.items():
            new_exam.elements[key] = value.shuffle_options(new_exam.rng)

        # ✅ Rebuild answer key and answer letters after shuffling
        new_exam.answer_key = make_answer_key(new_exam)
        new_exam.mc_answer_letters = new_exam._compute_answer_key_letters()

        # ✅ Return a completely independent shuffled exam
        return deepcopy(new_exam)

    def shuffle_options_and_questions(self,filename=None,seed=None,shuffle_within_groups=True):
        """Shuffles both questions and options in the exam.

        Args:
            filename (str, optional): Path to save the shuffled exam.
            seed (int, optional): Random seed for reproducibility.
            shuffle_within_groups (bool): Whether to shuffle questions within groups.

        Returns:
            mc_exam: A new instance with shuffled options and questions.
        """

        new_exam = deepcopy(self)
        
        if filename is not None:
            new_exam.filename = filename

        else:
            new_exam.filename = self.filename.replace('.tex','')+'_options_shuffled'+'.tex'

        if seed is not None:
            
            self.rng = np.random.default_rng(seed=seed)

        return self.shuffle_options(seed=seed,filename=filename).shuffle_questions(filename=filename,shuffle_within_groups=shuffle_within_groups)

    def add_periods(self,include_equations=True):
        """Adds periods to the end of sentences in the exam answer choices.

        Args:
            include_equations (bool): Whether to include equations in the operation.
        """
    
        for key,value in self.elements.items():

            self.elements[key].add_periods(include_equations=True,correct_string=self.correct_string)

        self.answer_key = make_answer_key(self)
    
    
    def capitalize_first(self):
        """Capitalizes the first letter of each sentence in the exam answer choices."""

        for key,value in self.elements.items():

            self.elements[key].capitalize_first(correct_string=self.correct_string)

        self.answer_key = make_answer_key(self)


    def _compute_answer_key_letters(
        self,
        option_characters=string.ascii_lowercase,
        option_character_format='(CHARACTER)',
    ):
        """Compute and return the answer key as letter labels (A, B, C, D, ...)."""

        key_letters = []
        self.option_characters = option_characters
        self.option_character_format = option_character_format

        for key, item in self.elements.items():
            if isinstance(item, mc_question):
                # find correct answers in single question
                letters = self._letters_for_question(item, option_characters, option_character_format)
                key_letters.append(', '.join(letters))
            else:
                # grouped questions
                for sub_key, sub_value in item.elements.items():
                    letters = self._letters_for_question(sub_value, option_characters, option_character_format)
                    key_letters.append(', '.join(letters))

        return key_letters

    def _letters_for_question(self, q, option_chars, fmt):
        """Return a list of letter labels for one question's correct answers."""
        letters = []
        for n, opt in enumerate(q.options):
            if self.correct_string in opt:
                letters.append(option_chars[n])
        if getattr(q, "all_of_above_correct", False):
            letters.append(option_chars[len(q.options)])
        if getattr(q, "none_of_above_correct", False):
            letters.append(option_chars[len(q.options) + 1])
        if fmt is not None:
            letters = [fmt.replace("CHARACTER", l) for l in letters]
        return letters


# ----------------------------------------------------------
# Step 1: Simple split into MCExam and FRExam
# ----------------------------------------------------------

class MCExam(mc_exam):
    """Wrapper around mc_exam for pure multiple-choice exams."""

    def __init__(self, exam_file=None, **kwargs):
        if exam_file:
            self.filepath = Path(exam_file).resolve()
            self.filename = self.filepath.name   # <-- only the short file name
            exam_file = str(self.filepath)
        else:
            self.filepath = None
            self.filename = None

        super().__init__(exam_file=exam_file, **kwargs)

    # ----------------------------------------------------------
    @classmethod
    def from_string(cls, tex, correct_string='CORRECT', seed=None, source_path=None, filename_hint=None):
        """Build an MCExam directly from a LaTeX string (no file needed)."""
        self = cls.__new__(cls)
        self.correct_string = correct_string
        self.rng = np.random.default_rng(seed=seed)
        self.filepath = Path(source_path).resolve() if source_path else None
        self.filename = filename_hint or (self.filepath.name if self.filepath else None)
        self.exam_header = ""
        self.exam_footer = ""

        # Normalize and isolate inner mcquestions environment if present
        tex = tex.replace('\r\n', '\n').replace('\r', '\n')
        m = re.search(r'\\begin\{mcquestions\}(.*?)\\end\{mcquestions\}', tex, flags=re.DOTALL)
        inner = m.group(1) if m else tex

        # Remove commented lines
        self.mc_lines = [ln for ln in inner.splitlines() if not ln.lstrip().startswith('%')]

        # --- Parse questions and groups exactly as in mc_exam.__init__ ---
        self.elements = {}
        index = 0
        open_group = False

        for n, line in enumerate(self.mc_lines):
            if line.lstrip().startswith('%'):
                continue
            if 'begin{mcgroup}' in line:
                group_start = n
                open_group = True
            elif 'end{mcgroup}' in line:
                group_end = n
                open_group = False
                group_lines = self.mc_lines[group_start:group_end]
                self.elements[index] = mc_group(group_lines, correct_string=self.correct_string)
                index += 1
            elif (('\\shuffle' in line or '\\noshuffle' in line) and not open_group):
                length = mc_exam.get_question_length(self, self.mc_lines, n)
                start = n
                end = n + length
                question_string = ''.join(self.mc_lines[start:end]).strip()
                mc = mc_question(question_string, correct_string=self.correct_string)
                self.elements[index] = mc
                index += 1

        # Build metadata
        self.question_count = sum(
            1 if isinstance(v, mc_question) else len(v.elements)
            for v in self.elements.values()
        )
        self.answer_key = make_answer_key(self)
        self.mc_answer_letters = self._compute_answer_key_letters()

        return self


class FRExam:
    r"""Handles free-response (FR) exams using \question[points] syntax."""

    def __init__(self, filename=None):
        self.filepath = Path(filename).resolve() if filename else None
        self.filename = str(self.filepath) if filename else None
        self.questions = []
        self.question_files = []
        self.exam_header = ""
        self.exam_footer = ""

        if filename:
            self.load_exam(filename)

    # ---------------------------------------------------------
    @classmethod
    def from_string(cls, tex, source_path=None, filename_hint=None):
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

        lines = inner.splitlines()
        cleaned = []
        skip_block = False
        for line in lines:
            stripped = line.lstrip()
            if stripped.startswith('%\\question'):
                skip_block = True
                continue
            if skip_block:
                if stripped == "" or stripped.startswith('\\question'):
                    skip_block = False
                continue
            if stripped.startswith('%'):
                continue
            cleaned.append(line)

        body = "\n".join(cleaned)
        self._extract_questions_from_text(body, self.filename or "(inline)")
        return self

        self.filepath = Path(filename).resolve() if filename else None
        self.filename = str(self.filepath) if filename else None
        self.questions = []        # list of dicts: {"file", "points", "text"}
        self.question_files = []
        self.exam_header = ""
        self.exam_footer = ""

        if filename:
            self.load_exam(filename)

    # ---------------------------------------------------------
    def _filter_visibility(self, text, reveal=False):
        """
        Remove or reveal content depending on output type (exam vs key).

        - In exam version (reveal=False): remove keyonly blocks entirely.
        - In key version   (reveal=True): remove examonly blocks entirely.
        This version handles any whitespace, newlines, and indentation.
        """
        # Normalize line endings first (in case of \r\n)
        text = text.replace('\r\n', '\n').replace('\r', '\n')

        if reveal:
            # Remove examonly blocks completely
            text = re.sub(
                r'(?s)\\begin\s*\{examonly\}.*?\\end\s*\{examonly\}',
                '',
                text
            )
        else:
            # Remove keyonly blocks completely
            text = re.sub(
                r'(?s)\\begin\s*\{keyonly\}.*?\\end\s*\{keyonly\}',
                '',
                text
            )

        return text

    def _replace_answer_envs(self, text, reveal=False):
        r"""
        Replace or remove all \begin{answer}...\end{answer} blocks safely.
        Works even if the block includes \input{} or TikZ code.
        """
        def repl(m):
            inner = m.group(1).strip()
            if reveal:
                # Add blank lines before and after, plus a LaTeX line break at the end
                return f"\n\n\\\n\n\\emph{{Answer:}} {inner}\n\n\\\n\n"
            else:
                return ""

        return re.sub(
            r'\\begin\{answer\}(.*?)\\end\{answer\}',
            repl,
            text,
            flags=re.DOTALL
        )

    def _expand_question_inputs(self, text, base_dir):
        """
        Replace \\input{...} with file contents ONLY if that file contains '\\question'.
        Leaves figure/TikZ inputs inside answers untouched.
        """
        def repl(m):
            raw = m.group(0)             # the literal \input{...}
            fname = m.group(1)
            qpath = base_dir / (fname if fname.endswith(".tex") else f"{fname}.tex")
            try:
                content = qpath.read_text(encoding="utf-8")
            except Exception:
                return raw  # leave as-is if unreadable

            # Only inline if this file actually contains a \question
            if r'\question' in content:
                return content
            else:
                return raw

        return re.sub(r'\\input\{([^}]+)\}', repl, text)

    def load_exam(self, filename):
        r"""Load and parse free-response questions from a .tex file,
        skipping commented-out \question blocks.
        """
        text = self.filepath.read_text(encoding="utf-8")

        # --- Remove commented-out question blocks line by line ---
        # --- Remove commented or fully empty question blocks safely ---
        lines = text.splitlines()
        cleaned_lines = []
        skip_block = False

        for line in lines:
            stripped = line.lstrip()

            # If this line itself starts with a comment or a commented question → skip it
            if stripped.startswith('%') or stripped.startswith('%\\question'):
                continue

            # If we’re currently skipping a commented block, continue until blank or next question
            if skip_block:
                if stripped == "" or stripped.startswith('\\question'):
                    skip_block = False
                continue

            # Detect start of a *real* question
            if stripped.startswith('\\question'):
                cleaned_lines.append(line)
                continue

            # Keep normal lines (not comments)
            cleaned_lines.append(line)

        body = "\n".join(cleaned_lines)

        body = "\n".join(cleaned_lines)

        # Match any uncommented \question[...] line and capture the full token
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
            block = f"{token} {snippet}"
            self._extract_questions_from_text(block, filename)

    # ---------------------------------------------------------
    def _extract_questions_from_text(self, text, source):
        r"""Find all \question[...] blocks within a given text, preserving layout commands."""
        # Capture any layout commands that appear *before* the first question
        leading_layout = ""
        m_leading = re.match(r'^\s*((?:\\newpage|\\clearpage|\\vspace\*?\{[^}]*\}\s*)+)', text)
        if m_leading:
            leading_layout = m_leading.group(1)
            text = text[m_leading.end():]  # remove them from the text, but keep separately

        # Find all question occurrences (with possible internal layout)
        pattern = re.compile(
            r'((?:\\newpage|\\clearpage|\\vspace\*?\{[^}]*\}\s*)*)'  # layout before question
            r'(\\question(?:\[\d+\])?)', 
            re.DOTALL
        )

        matches = list(pattern.finditer(text))
        for i, match in enumerate(matches):
            prefix_spacing = match.group(1) or ""
            question_token = match.group(2)
            start = match.end()

            # Get text until next question or end
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            question_body = text[start:end].strip()

            # Extract points
            m_points = re.match(r'\\question\[(\d+)\]', question_token)
            points = int(m_points.group(1)) if m_points else None

            # For the first question in the file, attach any leading \newpage
            if i == 0 and leading_layout:
                prefix_spacing = leading_layout + prefix_spacing

            full_text = f"{prefix_spacing}{question_token} {question_body}"

            self.questions.append({
                "file": str(source),
                "points": points,
                "text": full_text.strip()
            })

    # ---------------------------------------------------------
        # ---------------------------------------------------------
    def reveal_answers(self, text=None):
        """Reveal answers defined with \\begin{answer} ... \\end{answer}."""
        if text is None and self.questions:
            text = "\n\n".join(q["text"] for q in self.questions)

        # Use the robust environment replacer
        text = self._replace_answer_envs(text, reveal=True)

        # Hide exam-only blocks
        text = self._filter_visibility(text, reveal=True)
        return text

    # ---------------------------------------------------------
    def export_exam(self, filename=None):
        """Export the free-response exam version (answers hidden)."""
        if filename is None:
            filename = str(Path(self.filename).with_name("FR_Exam.tex"))

        # Ensure output folder exists
        Path(filename).parent.mkdir(parents=True, exist_ok=True)

        body_parts = []
        for q in self.questions:
            text = q["text"]

            # 1️⃣ Remove answer environments first
            text = self._replace_answer_envs(text, reveal=False)
            # 2️⃣ Then hide key-only blocks
            text = self._filter_visibility(text, reveal=False)

            body_parts.append(text.strip())

        content = (
            self.exam_header
            + "\n\\begin{frquestions}\n"
            + "\n\n".join(body_parts)
            + "\n\\end{frquestions}\n"
            + self.exam_footer
        )

        # 🧹 Final cleanup — remove keyonly blocks from header/footer too
        content = self._filter_visibility(content, reveal=False)

        Path(filename).write_text(content, encoding="utf-8")
        self.filepath = Path(filename).resolve()
        self.filename = str(self.filepath)

        print(f"✅ Exported FR exam (no answers): {filename}")

    # ---------------------------------------------------------
    def to_latex(self, key=False):
        """Return the full LaTeX string for this free-response exam."""
        body_parts = []

        for q in self.questions:
            text = q["text"]

            if key:
                text = self._replace_answer_envs(text, reveal=True)
                text = self._filter_visibility(text, reveal=True)
            else:
                text = self._replace_answer_envs(text, reveal=False)
                text = self._filter_visibility(text, reveal=False)

            body_parts.append(text.strip())

        body = "\n\n".join(body_parts)
        return (
            self.exam_header
            + "\n\\begin{frquestions}\n"
            + body
            + "\n\\end{frquestions}\n"
            + self.exam_footer
        )

    # ---------------------------------------------------------
    def export_key(self, filename=None):
        """Export the answer key version (answers revealed)."""
        if filename is None:
            filename = str(Path(self.filename).with_name("FR_Key.tex"))

        Path(filename).parent.mkdir(parents=True, exist_ok=True)

        body_parts = []
        for q in self.questions:
            text = q["text"]

            # 1️⃣ Replace answer environments first (reveal them)
            text = self._replace_answer_envs(text, reveal=True)
            # 2️⃣ Then remove exam-only blocks
            text = self._filter_visibility(text, reveal=True)

            body_parts.append(text.strip())

        content = (
            self.exam_header
            + "\n\\begin{frquestions}\n"
            + "\n\n".join(body_parts)
            + "\n\\end{frquestions}\n"
            + self.exam_footer
        )

        # 🧹 Final cleanup — remove examonly blocks from header/footer too
        content = self._filter_visibility(content, reveal=True)

        Path(filename).write_text(content, encoding="utf-8")

        self.filepath = Path(filename).resolve()
        self.filename = str(self.filepath)

        print(f"✅ Exported FR key (answers revealed): {filename}")

    # ---------------------------------------------------------
    def summary(self, max_chars=80):
        """Print a summary of all parsed free-response questions in order."""
        if not self.questions:
            print("⚠️ No questions loaded.")
            return

        print("\n📝 Free-Response Exam Summary")
        print("-" * 60)

        for i, q in enumerate(self.questions, 1):
            # Compact preview of the question text
            preview = re.sub(r'\s+', ' ', q["text"]).strip()
            preview = preview[:max_chars] + ("..." if len(preview) > max_chars else "")
            pts = f"[{q['points']} pts]" if q.get("points") else ""
            print(f"{i:>2}. {pts:<8} {Path(q['file']).name:<30} {preview}")

        print("-" * 60)
        print(f"Total questions: {len(self.questions)}\n")

class MixedExam:
    """Combines MCExam and FRExam outputs into a single LaTeX document."""

    def __init__(self, filename, mc=None, fr=None, correct_string="CORRECT", seed=None):
        """
        Args:
            filename (str): Path to the main exam LaTeX file.
            mc (MCExam, optional): Pre-parsed multiple-choice exam.
            fr (FRExam, optional): Pre-parsed free-response exam.
            correct_string (str): Marker for correct MC answers.
            seed (int, optional): Random seed for reproducibility.
        """
        # from .exam import MCExam, FRExam

        self.filepath = Path(filename).resolve()
        self.filename = self.filepath.name  # only the short name
        self.file_text = self.filepath.read_text(encoding="utf-8")
        base_dir = self.filepath.parent
        self.correct_string = correct_string
        self.seed = seed
        
        self._source_path = Path(self.filepath).resolve()  # remember original source file
        self._frozen_export_base = False                   # default: no explicit base
        self._base_path_for_exports = None                 # will hold explicit base when set

        # Accept preloaded objects
        self.mc = mc
        self.fr = fr

        # --- Detect MC section ---
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
                        print(f"📘 Including MC file: {mc_path.name}")
                        text = mc_path.read_text(encoding="utf-8")

                        # Clean commented-out shuffle/noshuffle blocks
                        lines = text.splitlines()
                        cleaned_lines = []
                        skip_block = False
                        brace_depth = 0

                        for line in lines:
                            stripped = line.lstrip()
                            if (not skip_block) and (stripped.startswith('%\\shuffle') or stripped.startswith('%\\noshuffle')):
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
                        print(f"⚠️ MC file not found: {mc_path}")

                # ✅ Build MC exam from string directly (no temp file)
                merged_mc_tex = "\\begin{mcquestions}\n" + merged + "\\end{mcquestions}\n"
                self.mc = MCExam.from_string(
                    merged_mc_tex,
                    correct_string=correct_string,
                    seed=seed,
                    source_path=self.filepath,
                    filename_hint=self.filename,
                )

            elif "\\begin{mcquestions}" in self.file_text:
                print("📘 Detected inline MC questions in main file")
                self.mc = MCExam(self.filename, correct_string=correct_string, seed=seed)

        # --- Detect FR section ---
        if self.fr is None:
            fr_input = re.search(r'\\input\{([^}]*(?:fr[_]?questions)[^}]*)\}', self.file_text)
            if fr_input:
                fr_path = base_dir / (fr_input.group(1) + ("" if fr_input.group(1).endswith(".tex") else ".tex"))
                if fr_path.exists():
                    print(f"📝 Auto-loading FR section from {fr_path.name}")
                    text = fr_path.read_text(encoding="utf-8")

                    lines = text.splitlines()
                    cleaned_lines = []
                    skip_block = False

                    for line in lines:
                        stripped = line.lstrip()
                        if not skip_block and stripped.startswith('%\\question'):
                            skip_block = True
                            continue

                        if skip_block:
                            if stripped == "" or stripped.startswith('\\question'):
                                skip_block = False
                            continue

                        cleaned_lines.append(line)

                    cleaned_text = "\n".join(cleaned_lines)

                    # ✅ Store inline FR LaTeX directly in memory
                    self.fr_text = cleaned_text

                    # ✅ Build FR exam directly from string, no file creation
                    self.fr = FRExam.from_string(
                        cleaned_text,
                        source_path=self.filepath,
                        filename_hint=self.filename,
                    )
                else:
                    print(f"⚠️ FR file not found: {fr_path}")
            elif "\\begin{frquestions}" in self.file_text:
                print("📝 Detected inline FR questions in main file")
                self.fr = FRExam(self.filename)

    # ----------------------------------------------------------------------
    def _filter_visibility(self, text, reveal=False):
        """Applies FR/MC-style visibility filtering to mixed exam LaTeX."""
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        if reveal:
            text = re.sub(r'(?s)\\begin\s*\{examonly\}.*?\\end\s*\{examonly\}', '', text)
        else:
            text = re.sub(r'(?s)\\begin\s*\{keyonly\}.*?\\end\s*\{keyonly\}', '', text)
        return text

    def _replace_answer_envs(self, text, reveal=False):
        """Replaces or removes \\begin{answer}...\\end{answer} blocks safely."""
        def repl(m):
            inner = m.group(1).strip()
            if reveal:
                # Match FRExam’s spacing convention
                return f"\n\n\\\n\n\\emph{{Answer:}} {inner}\n\n\\\n\n"
            else:
                return ""
        return re.sub(r'\\begin\{answer\}(.*?)\\end\{answer\}', repl, text, flags=re.DOTALL)

    def _expand_question_inputs(self, text, base_dir):
        """Expand \\input{...} files *only* if they contain \\question commands."""
        def repl(m):
            fname = m.group(1)
            qpath = base_dir / (fname if fname.endswith(".tex") else f"{fname}.tex")
            try:
                content = qpath.read_text(encoding="utf-8")
            except Exception:
                return m.group(0)
            return content if r'\question' in content else m.group(0)
            # Only match \input lines that are NOT commented out
        return re.sub(r'(?m)^\s*(?!%)\\input\{([^}]+)\}', repl, text)

    # --- replace MixedExam.shuffle_options with this version ---
    def shuffle_options(self, seed=None, filename=None):
        """
        Return a new MixedExam object with shuffled MC options,
        preserving FR questions and structure.
        If `filename` is provided, it becomes the new exam's base path
        for later export_exam/export_key calls.
        """
        from copy import deepcopy
        new_exam = deepcopy(self)
        new_exam.mc = new_exam.mc.shuffle_options(seed=seed)

        # ✅ Handle filename and directory properly
        if filename:
            out_path = Path(filename).expanduser().resolve()
            out_path.parent.mkdir(parents=True, exist_ok=True)
            new_exam.filepath = out_path
            new_exam.filename = out_path.name
            # Mark this as the base for later exports
            new_exam._base_path_for_exports = out_path
            new_exam._frozen_export_base = True
        else:
            new_exam._frozen_export_base = False
            new_exam._base_path_for_exports = None

        print(f"✅ Shuffled MC options with seed={seed}")
        return new_exam

    # ----------------------------------------------------------------------
    def to_latex(self, key=False):
        """Return full LaTeX string for mixed exam (MC + FR combined)."""
        mc_inner = fr_inner = ""

        if self.mc:
            mc_tex = self.mc.to_latex(key=key)
            mc_inner = self._extract_body(mc_tex, "mcquestions")

        if self.fr:
            fr_tex = self.fr.to_latex(key=key)
            fr_inner = self._extract_body(fr_tex, "frquestions")

        combined = self._assemble_exam(mc_inner, fr_inner)
        combined = self._replace_answer_envs(combined, reveal=key)
        combined = self._filter_visibility(combined, reveal=key)
        return combined

    def _extract_body(self, latex_text, env_name):
        """Extracts the inner content of a LaTeX environment (like mcquestions)."""
        m = re.search(rf'\\begin\{{{env_name}\}}(.*?)\\end\{{{env_name}\}}', latex_text or "", flags=re.DOTALL)
        return m.group(1).strip() if m else latex_text or ""

    def _assemble_exam(self, mc_inner, fr_inner):
        """Insert MC and FR content into the LaTeX template cleanly."""
        text = self.file_text

        # --- Replace all uncommented \input lines for MC with the merged block ---
        # (This avoids nested environments and removes leftover \input lines.)
        
        text = re.sub(
            r'(?m)^[ \t]*(?!%)\\input\{[^}]*mc[^}]*\}.*?$',
            "",  # remove all MC input lines
            text,
        )

        # Build a full MC environment wrapper (so we always have begin/end)
        mc_block = f"\\begin{{mcquestions}}\n{mc_inner.strip()}\n\\end{{mcquestions}}\n"

        # Insert the merged MC block after the MC header comment if present
        if re.search(r'(?m)^% BEGIN MULTIPLE CHOICE QUESTIONS', text):
            text = re.sub(
                r'(?m)^% BEGIN MULTIPLE CHOICE QUESTIONS.*?\n',
                lambda m: m.group(0) + mc_block,
                text,
            )
        else:
            # Fallback: insert MC block before FR section or at the end
            text = re.sub(
                r'(?m)^\\begin\{frquestions\}',
                mc_block + '\n\\begin{frquestions}',
                text,
                count=1,
            )

        # Remove any now-empty or comment-only mcquestions environments left behind
        text = re.sub(
            r'(?ms)^\\begin\{mcquestions\}[\s%]*?(?:%.*?\n|\s)*?\\end\{mcquestions\}',
            '',
            text
        )

        # --- Replace all uncommented \input lines for FR with merged block ---
        text = re.sub(
            r'(?m)^[ \t]*(?!%)\\input\{[^}]*fr[^}]*\}.*?$',
            "",  # remove FR input lines
            text,
        )

        # The merged FR inner content (already stripped of wrappers)
        fr_block = fr_inner.strip()

        # Insert FR questions immediately *inside* the existing frquestions environment
        text = re.sub(
            r'(?ms)(\\begin\{frquestions\}\s*)',
            lambda m: m.group(1) + fr_block + "\n\n",
            text,
        )

        # 🧹 Normalize any accidental double \begin or \end lines
        text = re.sub(
            r'(?ms)\\begin\{frquestions\}\s*\\begin\{frquestions\}',
            r'\\begin{frquestions}',
            text,
        )
        text = re.sub(
            r'(?ms)\\end\{frquestions\}\s*\\end\{frquestions\}',
            r'\\end{frquestions}',
            text,
        )

        # ✅ Ensure exactly one blank line after the final \end{frquestions}
        text = re.sub(
            r'(\\end\{frquestions\})(?!\n\n)',
            r'\1\n\n',
            text
        )

        # ✅ Ensure exactly one blank line after the final \end{frquestions}
        text = re.sub(
            r'(\\end\{frquestions\})(?!\n\n)',
            r'\1\n\n',
            text
        )

        return text

    # ----------------------------------------------------------------------
    # --- replace MixedExam.export_exam with this version ---
    def export_exam(self, filename=None):
        """Export the mixed student version (no FR answers, no keyonly content)."""
        if filename:
            out_path = Path(filename).expanduser().resolve()
        elif getattr(self, "_frozen_export_base", False) and getattr(self, "_base_path_for_exports", None):
            # Use the frozen base exactly
            out_path = self._base_path_for_exports
        else:
            base = Path(self._source_path if hasattr(self, "_source_path") else self.filepath)
            stem = re.sub(r"_Exported(_Key)?$", "", base.stem)
            out_path = base.with_name(f"{stem}_Exported.tex")

        tex = self.to_latex(key=False)
        tex = self._filter_visibility(tex, reveal=False)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(tex, encoding="utf-8")

        print(f"✅ Exported mixed exam (no answers): {out_path}")
        


    def export_key(self, filename=None):
        """Export the mixed instructor key (FR answers shown, includes keyonly)."""
        if filename:
            out_path = Path(filename).expanduser().resolve()
        elif getattr(self, "_frozen_export_base", False) and getattr(self, "_base_path_for_exports", None):
            base = self._base_path_for_exports
            out_path = base.with_name(f"{base.stem}_Key{base.suffix}")
        else:
            base = Path(self._source_path if hasattr(self, "_source_path") else self.filepath)
            stem = re.sub(r"_Exported(_Key)?$", "", base.stem)
            out_path = base.with_name(f"{stem}_Exported_Key.tex")

        tex = self.to_latex(key=True)
        tex = self._filter_visibility(tex, reveal=True)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(tex, encoding="utf-8")

        print(f"✅ Exported mixed exam key: {out_path}")

    # ----------------------------------------------------------------------
    def summary(self):
        """Print a short summary of the mixed exam contents."""
        print("\n📘 Mixed Exam Summary")
        print("=" * 60)
        if self.mc:
            print(f"Multiple Choice: {getattr(self.mc, 'question_count', 'unknown')} questions")
        if self.fr:
            print(f"Free Response: {len(self.fr.questions)} questions")

    def verify_integrity(self, latex_text=None):
        """Basic consistency checks for the mixed exam."""
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
                messages.append(f"✅ {env}: found 1 begin / 1 end.")
            else:
                ok = False
                messages.append(f"❌ {env}: found {b} \\begin and {e} \\end.")

        leftover_inputs = re.findall(r'\\input\{[^}]*\}', latex_text)
        if leftover_inputs:
            ok = False
            messages.append(f"⚠️ Unresolved \\input statements found: {len(leftover_inputs)}")

        print("\n🔍 Mixed Exam Integrity Check")
        print("=" * 50)
        for msg in messages:
            print(msg)
        print("=" * 50)
        print("✅ Exam structure looks consistent!\n" if ok else "⚠️ Exam may have inconsistencies.\n")
        return ok