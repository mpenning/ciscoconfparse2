.. _installation:

============
Installation
============

MacOS Prerequisites
-------------------

Tests pass on the latest OSX without doing this, but to get ``scrypt`` to install on MacOS you might need to run this prior to installing ciscoconfparse2:

``export CFLAGS="-I$(brew --prefix openssl)/include"``

``export LDFLAGS="-L$(brew --prefix openssl)/lib"``

pip
---

``pip install -U ciscoconfparse2 >= 0.7.1``

requirements.txt: pypi
----------------------

If you need a direct ``pypi`` dependency entry in your ``requirements.txt``
file, you can include an entry like this.

``ciscoconfparse2 == 0.7.1``

``0.7.1`` is used only as a reference; choose the correct release for your
project.

requirements.txt: github
------------------------

If you need a direct ``git`` dependency entry in your ``requirements.txt``
file, you can include an entry like this (where ``0.7.1`` is a specific
``git tag`` that you want to reference).

``git+https://github.com/mpenning/ciscoconfparse2.git@0.7.1``

``0.7.1`` is used only as a reference; choose the correct release for your
project.
