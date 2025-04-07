Other Functions
===============

.. py:function:: notebook_to_python(notebook_name)

   Exports a Jupyter Notebook file to a Python script.

   :param notebook_name: Name of the Jupyter Notebook file (with or without `.ipynb` extension).
   :type notebook_name: str
   :returns: None
   :rtype: None

.. py:function:: notebook_to_html(notebook_name, execute=False)

   Exports a Jupyter Notebook file to an HTML file.

   :param notebook_name: Name of the Jupyter Notebook file (with or without `.ipynb` extension).
   :type notebook_name: str
   :param execute: Whether to execute the notebook before converting. Default is False.
   :type execute: bool, optional
   :returns: None
   :rtype: None