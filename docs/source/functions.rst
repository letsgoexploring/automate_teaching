Other Functions
===============

.. py:function:: notebook_to_python(notebook_name)

   Exports a Jupyter Notebook to a Python script using ``nbconvert``. Appends
   ``.ipynb`` to the filename if it is not already present.

   :param notebook_name: Name of the Jupyter Notebook file, with or without
      the ``.ipynb`` extension.
   :type notebook_name: str
   :return: None

.. py:function:: notebook_to_html(notebook_name, execute=False)

   Exports a Jupyter Notebook to an HTML file using ``nbconvert``. Appends
   ``.ipynb`` to the filename if it is not already present.

   :param notebook_name: Name of the Jupyter Notebook file, with or without
      the ``.ipynb`` extension.
   :type notebook_name: str
   :param execute: Whether to execute the notebook before converting.
      Defaults to False.
   :type execute: bool, optional
   :return: None
