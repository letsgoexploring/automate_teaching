import pandas as pd
import numpy as np
from copy import deepcopy
import os
import string


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
        
    def add_periods(self,include_equations=True,correct_string=None):
        """Adds periods to the end of each option if not already present.

        Args:
            include_equations (bool, optional): Whether to include periods for options ending with equations. Defaults to True.
            correct_string (str, optional): The marker for the correct answer. Defaults to None.
        """
    
        for n,option in enumerate(self.options):
        
            option_text = option.replace('\\item','').lstrip().replace(correct_string,'').replace('\\%','PERCENTSIGNHERE').replace('%','').replace('PERCENTSIGNHERE','\\%').rstrip()
            
            if not option_text.endswith('.'):
            
                if option_text.endswith('$') and  include_equations:
                    option_text +='.'
            
                elif not option_text.endswith('$'):
                    option_text +='.'
            
            if correct_string in option:
            
                option_text+=' %'+self.correct_string
            
            self.options[n] = '\\item '+option_text
    
    
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


class mc_group():
    """Defines a class for storing and managing a group of multiple-choice questions."""
    
    def __init__(self,group_lines,correct_string):
        r"""Initializes an mc_group instance.

        Parses a group of multiple-choice questions, extracting headers, counts, and individual questions.

        Args:
            group_lines (list): Lines from a LaTeX file between \begin{mcquestions} and \end{mcquestions}.
            correct_string (str): The marker indicating the correct answer for questions in the group.
        """

        def get_question_length(mc_lines,starting_line_number):
            """Determines the number of lines a single question occupies.

            Args:
                mc_lines (list): Lines from the LaTeX file.
                starting_line_number (int): The starting index of the question.

            Returns:
                int: The number of lines the question occupies.
            """

            self.correct_string = correct_string
        
            # Total lines in the MC question list
            total_lines = len(mc_lines)
        
            # Initialize counts of left and right braces
            left_brace_count = 0
            right_brace_count = 0
        
            # Counter for number of outer/base pairs of braces identified. Need to find two
            pairs = 0
        
            # Boolean to identify whether an outer brace is currently unclosed
            open_outer_brace = False
        
            # Iterate over lines in mc_lines after starting_line_number
            for i in range(total_lines-starting_line_number):
        
                # Iterate over characters
                for char in mc_lines[starting_line_number+i]:
        
                    # Make note of a left brace
                    if char=='{':
                        left_brace_count+=1
                        if open_outer_brace == False:
                            open_outer_brace = True
        
                    # Make note of a right brace
                    elif char=='}':
                        right_brace_count+=1
        
                    # If the outer braces were closed on this iteration, add one to pairs
                    if left_brace_count-right_brace_count==0 and open_outer_brace:
                        pairs+=1
                        open_outer_brace = False
        
                    # Escape if the end of the second pair was found.
                    if pairs==2:
                        break
            
                else:
                    continue
                break
        
            return i+1

        def get_group_count_and_header(group_string):
            """Extracts the question count and header from the group string.

            Args:
                group_string (str): A string containing the group definition and its metadata.

            Returns:
                tuple: The count of questions (int) and the group header (str).
            """
            
            # Initialize counts of left and right braces
            left_brace_count = 0
            right_brace_count = 0
            
            # Boolean to identify whether an outer brace is currently unclosed.
            open_outer_brace = False
        
            # Counter for number of outer/base pairs of braces identified. Need to find third pair
            pairs = 0
            
            # Iterate over characters in question_string and find first pair of outer braces    
            for i,char in enumerate(group_string):
                if char=='{':
                    left_brace_count+=1
                    if open_outer_brace == False:
                        open_outer_brace = True
                        if pairs==1:
                            count_start = i+1
                        
                        if pairs==2:
                            text_start = i+1
                            
                elif char=='}':
                    right_brace_count+=1
            
                # Escape if the end of the first pair was found.
                if left_brace_count-right_brace_count==0 and open_outer_brace:
                    pairs+=1
                    open_outer_brace = False
        
                    if pairs==2:
                        count_end = i
        
                # Escape if the end of the third pair was found.
                if pairs==3:
                    text_end = i
                    break
        
        
            try:
                group_count = int(group_string[count_start:count_end])
            except:
                group_count = None
            group_header =  group_string[text_start:text_end]
            
            return group_count,group_header

        
        
        self.group_lines = group_lines

        self.group_string = ''.join(self.group_lines).lstrip().rstrip()

        group_count,self.group_header = get_group_count_and_header(self.group_string)

        self.elements = {}
        index = 0
        
        open_group = False
        
        actual_count = 0
        
        for n,line in enumerate(self.group_lines):
        
            if ('\\shuffle' in line or '\\noshuffle' in line) and open_group == False:
                
                length = get_question_length(mc_lines=self.group_lines,starting_line_number=n)
        
                start = n
                end = n+length
        
                question_string = ''.join(self.group_lines[start:end]).lstrip().rstrip()
                
                mc = mc_question(question_string,correct_string=self.correct_string)
        
                self.elements[index] = mc
                index+=1

                actual_count+=1

        if actual_count != group_count:
            print('Warning: Number of questions in group with this heading does not match number provided in Latex code for exam:\n\n'+self.group_header+'\n')
            print('Stated in exam:  '+str(group_count)+'\n')
            print('Actual in group: '+str(actual_count)+'\n')

        self.group_count = actual_count

    def shuffle_questions(self,rng):
        """Shuffles the order of questions within the group.

        Args:
            rng (numpy.random.Generator): A random number generator for shuffling.

        Returns:
            mc_group: A new mc_group instance with shuffled questions.
        """

        new_group = deepcopy(self)

        # Randomly draw the new ordering
        reordered_keys = rng.choice(list(new_group.elements.keys()),replace=False,size=len(new_group.elements))
        
        # The reordered elements dictionary
        reordered_elements = {j+1 : new_group.elements[key] for j,key in enumerate(reordered_keys)  }
        
        return new_group

    def shuffle_options(self,rng):
        """Shuffles the options for each question in the group.

        Args:
            rng (numpy.random.Generator): A random number generator for shuffling.

        Returns:
            mc_group: A new mc_group instance with shuffled options for each question.
        """
    
        new_group = deepcopy(self)

        for key,value in self.elements.items():

            new_group.elements[key] = value.shuffle_options(rng)
    
        return new_group

    def add_periods(self,include_equations=True,correct_string=None):
        """Adds periods to the end of options in all questions.

        Args:
            include_equations (bool, optional): Whether to include periods for options ending with equations. Defaults to True.
            correct_string (str, optional): The marker for the correct answer. Defaults to None.
        """
    
        for key,value in self.elements.items():

            self.elements[key].add_periods(include_equations=True,correct_string=correct_string)
    
    
    def capitalize_first(self,correct_string=None):
        """Capitalizes the first letter of each option in all questions.

        Args:
            correct_string (str, optional): The marker for the correct answer. Defaults to None.
        """

        for key,value in self.elements.items():

            self.elements[key].capitalize_first(correct_string=correct_string)
        


class mc_exam():

    """Defines a class for storing the content of a multiple choice exam."""

    def __init__(self,exam_file=None,exam_lines=None,correct_string='CORRECT',seed=None):
        """Initializes an mc_exam instance.

        Args:
            exam_file (str, optional): Path to the exam LaTeX file.
            exam_lines (list, optional): List of lines from the exam LaTeX file.
            correct_string (str): Marker string indicating the correct answer.
            seed (int, optional): Random seed for reproducibility.
        """

        self.correct_string = correct_string
        self.filename = exam_file
        self.rng = np.random.default_rng(seed=seed)
        
        def get_question_length(mc_lines,starting_line_number):
        
            r"""Finds the number of lines that a single multiple choice question occupies in a LaTeX file.

            Args:
                mc_lines (list): List of lines read from a LaTeX file, between \begin{mcquestions} and \end{mcquestions}.
                starting_line_number (int): The index of the first line of the question.

            Returns:
                int: The number of lines that the question occupies.
            """
        
            # Total lines in the MC question list
            total_lines = len(mc_lines)
        
            # Initialize counts of left and right braces
            left_brace_count = 0
            right_brace_count = 0
        
            # Counter for number of outer/base pairs of braces identified. Need to find two
            pairs = 0
        
            # Boolean to identify whether an outer brace is currently unclosed
            open_outer_brace = False
        
            # Iterate over lines in mc_lines after starting_line_number
            for i in range(total_lines-starting_line_number):
        
                # Iterate over characters
                for char in mc_lines[starting_line_number+i]:
        
                    # Make note of a left brace
                    if char=='{':
                        left_brace_count+=1
                        if open_outer_brace == False:
                            open_outer_brace = True
        
                    # Make note of a right brace
                    elif char=='}':
                        right_brace_count+=1
        
                    # If the outer braces were closed on this iteration, add one to pairs
                    if left_brace_count-right_brace_count==0 and open_outer_brace:
                        pairs+=1
                        open_outer_brace = False
        
                    # Escape if the end of the second pair was found.
                    if pairs==2:
                        break
            
                else:
                    continue
                break
        
            return i+1

        if exam_file is not None:


            with open (exam_file,'r') as text:
    
                exam_lines = text.readlines()
                self.exam_lines = exam_lines

        

        if self.exam_lines is not None:

            # Remove lines beginning wiath a comment
            comment_lines = []
            for n,line in enumerate(self.exam_lines):
            
                if line.lstrip().startswith('%'):
                    comment_lines.append(n)
                    
            
            for index in sorted(comment_lines, reverse=True):
                del self.exam_lines[index]

            
            for n,line in enumerate(self.exam_lines):
                if line.lstrip().startswith('\\begin{mcquestions}'):
                    
                    self.mc_block_start = n
            
                elif line.lstrip().startswith('\\end{mcquestions}'):
            
                    self.mc_block_end = n

            self.mc_lines = self.exam_lines[self.mc_block_start:self.mc_block_end]
            
            self.exam_header = ''.join(self.exam_lines[:self.mc_block_start])

            self.exam_footer = ''.join(self.exam_lines[self.mc_block_end+1:])

            
            self.elements = {}
            index = 0
            
            open_group = False

            
            for n,line in enumerate(self.mc_lines):
            
                
                if 'begin{mcgroup}' in line:
                    group_start = n
                    open_group=True
            
                elif 'end{mcgroup}' in line:
                    group_end = n
                    open_group=False

                    group_lines = self.mc_lines[group_start:group_end]

                    self.elements[index] = mc_group(group_lines,correct_string=self.correct_string)
                    index+=1
            
                elif ('\\shuffle' in line or '\\noshuffle' in line) and open_group == False:
                    
                    # print(n,'begin question')
                    # open_question = True
                    length = get_question_length(mc_lines=self.mc_lines,starting_line_number=n)
                    # print(n+length,'end question')
            
                    start = n
                    end = n+length
            
                    question_string = ''.join(self.mc_lines[start:end]).lstrip().rstrip()
                    
                    mc = mc_question(question_string,correct_string=self.correct_string)
            
                    self.elements[index] = mc
                    index+=1
            

        self.question_count = 0
        for key,value in self.elements.items():
            if isinstance(value,mc_question):
                self.question_count+=1
            else:
                for sub_key,sub_value in value.elements.items():
                    self.question_count+=1

        
        self.answer_key = make_answer_key(self)

        

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

    def exam_to_latex(self,filename=None):
        """Exports the exam content to a LaTeX file.

        Args:
            filename (str, optional): Path to save the LaTeX file. Defaults to the original filename with an appended suffix.
        """
        
        if filename is None:
            
            filename = self.filename.replace('.tex','')+'.tex'

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
        
        output +='\\end{mcquestions}\n\n'
        
        output +=self.exam_footer
        
        with open(filename,'w') as newfile:
            newfile.write(output)
            
    def answer_key_to_latex(self,filename=None):
        """Exports the answer key to a LaTeX file.

        Args:
            filename (str, optional): Path to save the LaTeX file. Defaults to the original filename with an appended suffix.
        """
        
        if filename is None:
            
            key_filename = self.filename.replace('.tex','')+'_Key'+'.tex'
            self.key_filename = key_filename

        output = ''

        output +=''.join(self.exam_header)
        
        output +='\\begin{mcquestions}\n\n'
        
        for key,value in self.elements.items():
            if isinstance(value,mc_question):
                # self.question_count+=1
        
                output+= self.answer_key[key].question_header+'\n{\n'
                
                for option in self.answer_key[key].options:
                    output+='\t'+option+'\n'
                if self.answer_key[key].all_of_above_correct:
                    output+='\t\\item \\hl{All of the above.} %'+self.correct_string+'\n'
                elif self.answer_key[key].all_of_above:
                    output+='\t\\item All of the above.\n'
                if self.answer_key[key].none_of_above_correct:
                    output+='\t\\item \\hl{None of the above.} %'+self.correct_string+'\n'
                elif self.answer_key[key].none_of_above_correct:
                    output+='\t\\item None of the above.\n'
                output+='}\n\n'
            
            else:
                output+='\n% BEGIN MC GROUP BLOCK\n\\begin{mcgroup}{'+str(value.group_count)+'}{'+value.group_header+'}\n\n'
                
                for sub_key,sub_value in value.elements.items():
                    
                    output+= self.answer_key[key].elements[sub_key].question_header+'{\n'
        
                    for option in self.answer_key[key].elements[sub_key].options:
                        output+='\t'+option+'\n'
                    if self.answer_key[key].elements[sub_key].all_of_above_correct:
                        output+='\t\\item \\hl{All of the above.} %'+self.correct_string+'\n'
                    elif self.answer_key[key].elements[sub_key].all_of_above:
                        output+='\t\\item All of the above.\n'
                    if self.answer_key[key].elements[sub_key].none_of_above_correct:
                        output+='\t\\item \\hl{None of the above.} %'+self.correct_string+'\n'
                    elif self.answer_key[key].elements[sub_key].none_of_above_correct:
                        output+='\t\\item None of the above.\n'
                    output+='}\n\n'
        
                output+='% END MC GROUP BLOCK\n\\end{mcgroup}\n\n\n'
        
        output +='\\end{mcquestions}\n\n'
        
        output +=''.join(self.exam_footer)
        
        with open(key_filename,'w') as newfile:
            newfile.write(output)

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


        
        
        return new_exam

    def set_seed(self,seed=None):
        """Sets the random seed for reproducibility.

        Args:
            seed (int, optional): Random seed value.
        """

        self.rng = np.random.default_rng(seed=seed)

    def shuffle_options(self,filename=None,seed=None):
        """Shuffles the options within each question.

        Args:
            filename (str, optional): Path to save the shuffled exam.
            seed (int, optional): Random seed for reproducibility.

        Returns:
            mc_exam: A new instance with shuffled options.
        """

        new_exam = deepcopy(self)
        
        if filename is not None:
            new_exam.filename = filename

        else:
            new_exam.filename = self.filename.replace('.tex','')+'_options_shuffled'+'.tex'

        if seed is not None:
            
            self.rng = np.random.default_rng(seed=seed)

        

        for key,value in self.elements.items():

            new_exam.elements[key] = self.elements[key].shuffle_options(self.rng)

        new_exam.answer_key = make_answer_key(new_exam)

        return new_exam

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


    def get_answer_key_letters(self,option_characters=string.ascii_lowercase,option_character_format = '(CHARACTER)'):

        """Retrieves the correct letter for each answer in key.

        Args:
            option_characters (str): Characters used to represent options.
            option_character_format (str): Format string for option characters.

        Returns:
            list: Answer key in letter format.
        """
        
        self.option_characters = option_characters
        self.option_character_format = option_character_format
        
        key_letters = []
        
        for key,item in self.elements.items():
            if isinstance(item,mc_question):
                current_question = []
        
                for n,opt in enumerate(self.answer_key[key].options):
                    if self.correct_string in opt:
                        current_question.append(self.option_characters[n])
        
                if self.elements[key].all_of_above_correct:
        
                        n_opt = len(self.answer_key[key].options)
                        
                        current_question.append(self.option_characters[n_opt])
        
                if self.elements[key].all_of_above_correct and self.elements[key].none_of_above_correct:
        
                    current_question.append(self.option_characters[n_opt+1])
        
                if self.option_character_format is not None:
                    current_question = [self.option_character_format.replace('CHARACTER',x) for x in current_question]
        
                key_letters.append(', '.join(current_question))
        
            else:
                for sub_key,sub_value in self.elements[key].elements.items():

                    current_question = []

                    for n,opt in enumerate(self.answer_key[key].elements[sub_key].options):
                        if self.correct_string in opt:
                            current_question.append(self.option_characters[n])
            
                    if self.elements[key].elements[sub_key].all_of_above_correct:
            
                            n_opt = len(self.answer_key[key].elements[sub_key].options)
                            
                            current_question.append(self.option_characters[n_opt])
            
                    if self.elements[key].elements[sub_key].all_of_above_correct and self.elements[key].elements[sub_key].none_of_above_correct:
            
                        current_question.append(self.option_characters[n_opt+1])
            
                    if self.option_character_format is not None:
                        current_question = [self.option_character_format.replace('CHARACTER',x) for x in current_question]
            
                    key_letters.append(', '.join(current_question))

        self.answer_key_letters = key_letters