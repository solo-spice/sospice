.. _dev-guide:

============
Contributing
============

You can contribute to ``sospice`` by writing code, but also by writing documentation or tests, or even by giving feedback about the project.

Issue Tracking
--------------

All bugs, feature requests, and other issues related to ``sospice`` should be recorded as GitHub `issues <https://github.com/solo-spice/sospice/issues>`__.

All conversation regarding these issues should take place on the issue tracker.
When a merge request resolves an issue, the issue will be closed and the appropriate merge request will be referenced.
Issues will not be closed without a reason given.

Creating a fork
---------------

If you would like to contribute to ``sospice``, you will first need to create a `fork <https://docs.github.com/en/get-started/quickstart/fork-a-repo>`__
of the main ``sospice`` repository under your GitHub username.

Next, clone your fork of ``sospice`` to your local machine:

.. code:: shell

    git clone https://github.com/<your_username>/sospice.git
    cd sospice

Now add the main ``sospice`` repository as an upstream repository:

.. code:: shell

    git remote add upstream https://github.com/solo-spice/sospice.git

You can now keep your fork up to date with main repository by running

.. code:: shell

    git pull upstream main

Installation
-------------

If you're using the `Miniconda Python distribution <https://docs.conda.io/en/latest/miniconda.html>`__,
create a new environment for ``sospice`` development:

.. code-block:: shell

    conda create --name sospice-dev pip
    conda activate sospice-dev

If you're using another python installation, you can also use `virtual environments <https://docs.python.org/3/tutorial/venv.html>`__,
for example with ``venv``:

.. code-block:: shell

    python -m venv venv
    . venv/bin/activate

Next, install the needed dependencies:

.. code-block:: shell

    cd sospice
    pip install -r requirements.txt

This includes all of the dependencies for the package as well as ``pytest`` for running tests and ``sphinx`` for building the docs.

To make sure everything is working alright, you can run the tests; see :ref:`tests` for more details regarding running the tests.

.. _tests:

Testing
-------

To run the tests:

.. code:: shell

    make test

This will generate report showing which tests passed and which failed (if any), as well of a summary of the test coverage.
``sospice`` uses the `pytest <https://pytest.org/en/latest/>`__ framework for discovering and running all of the tests.

Additions to the codebase should be accompanied by appropriate tests such that the test coverage of the entire package does not decrease.
You can check which lines are covered by tests by running,

.. code:: shell

    make test-htmlcov

and then opening the file ``./htmlcov/index.html`` in a web browser.

Tests should be added to the directory in the appropriate subpackage, e.g. for ``calibrate``, the tests should be placed in ``calibrate/tests``.
Your tests can be added to an existing file or placed in a new file following the naming convention ``test_*.py``.
This organization allows the tests to be automatically discovered by pytest.

Making a contribution
---------------------

If you want to add a feature or bugfix to ``sospice``, start by first switching to the develop branch of your fork, and making sure it is up to date with the develop branch of the main repository (this will help to prevent potential file conflicts).

.. code:: shell

    git switch develop
    git pull upstream develop

Next, create a new branch and switch to it:

.. code:: shell

    git checkout -b my-new-feature

Your changes should include tests for your new feature (see :ref:`tests`), so that the code coverage of the tests does not decrease, and all tests should pass. After you have made your changes, commit them,

.. code:: shell

    git add changed_file_1.py changed_file_2.py
    git commit -m "short description of my change"

The commit step will run “pre-commit” actions, with additional checks and code reformatting; please review these changes and re-commit them if necessary.

You can then push changes to GitHub:

.. code:: shell

    git push origin my-new-feature

Once you see the changes in GitHub, create a `pull request <https://docs.github.com/en/pull-requests>`__
against the main ``sospice`` repository.
Others will likely have comments and suggestions regarding your proposed changes.
You can make these changes using the instructions listed above.

At least another ``sospice`` developer must approve your changes before the code can be merged.
Additionally, all automated tests should pass and all conversations should be resolved.
Once these steps are complete, the code can be merged and you can delete  your branch ``my-new-feature``.

Documentation
-------------

All documentation is written in `reStructuredText <https://docutils.sourceforge.io/rst.html>`__ and rendered using `Sphinx <https://www.sphinx-doc.org/en/master/>`__.
Documentation strings are automatically pulled from all modules, functions and classes to create the API documentation (not working yet).
You can build and test the documentation locally by running

.. code:: shell

    make doc-html

This will run Sphinx on the restructured text files in order to create the HTML version of the documentation.
The built documentation, in HTML format, is in ``docs/_build/html``.

Best practices
--------------

All contributors to the ``sospice`` codebase should follow the `SunPy developer's guide`_.
This guide lays out a set of best practices for contributing, reviewing, testing, and documenting code.
All contributions to ``sospice`` must adhere to the `Python in Heliophysics Community Standards <https://doi.org/10.5281/zenodo.2529130>`__.

.. _`SunPy developer's guide`: https://docs.sunpy.org/en/latest/dev_guide/index.html
