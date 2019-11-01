.. _api:

API
===

Here is the documentation for the various components of this program.

.. module:: flfm

Shell File & Directory Objects
------------------------------

Here is a summary of objects related to the filesystem.

.. autosummary::
    :toctree: shell

    flfm.shell.paths
    flfm.shell.uploads
    flfm.shell.rules
    flfm.shell.video

And, here is a more in-depth explanation of each.

.. currentmodule:: flfm.shell.paths

Shell Items
+++++++++++

.. autoclass:: ShellItem
    :members:
    :inherited-members:

Shell Files
+++++++++++

.. inheritance-diagram:: ShellFile

.. autoclass:: ShellFile
    :members:
    :inherited-members:

Shell Directories
+++++++++++++++++

.. inheritance-diagram:: ShellDirectory

.. autoclass:: ShellDirectory
    :members:
    :inherited-members:

Shell Paths
+++++++++++

.. autoclass:: ShellPath
    :members:
    :inherited-members:

Uploaded Files
++++++++++++++

.. currentmodule:: flfm.shell.uploads

.. inheritance-diagram:: UploadedFile

.. autoclass:: UploadedFile
    :members:

Rules and Permissions
+++++++++++++++++++++

.. currentmodule:: flfm.shell.rules

**FUNCTIONS:**

.. autofunction:: read_rules_file

.. autofunction:: enforce_mapped

.. autodecorator:: needs_rules

**CLASSES:**

.. autoclass:: Rules
    :members:
    :inherited-members:


There are also rules and permissions that can exist solely in memory:


Virtual *(in-memory)* Rules and Permissions
+++++++++++++++++++++++++++++++++++++++++++

.. inheritance-diagram:: VirtualRules

.. autoclass:: VirtualRules
    :members:
    :inherited-members:

Directory w/ Rules
++++++++++++++++++

.. autoclass:: MappedDirectory
    :members:
    :inherited-members:

Collection of Directories w/ Rules
++++++++++++++++++++++++++++++++++

.. autoclass:: MappedDirectories
    :members:
    :inherited-members:

Video Files
+++++++++++

.. currentmodule:: flfm.shell.video

.. inheritance-diagram:: VideoFile

.. autoclass:: VideoFile
    :members:

Video Formats
+++++++++++++

.. inheritance-diagram:: MP4File

.. autoclass:: MP4File
    :members:

Viewer & Viewer Cache
---------------------

.. module:: flfm.viewer

Here is a summary of objects related to the viewer.

.. autosummary::
    :toctree: viewer

    flfm.viewer.vcache

And, here is a more in-depth explanation of each.

.. currentmodule:: flfm.viewer.vcache

Cached File
+++++++++++

.. autoclass:: VCFile
    :members:
    :inherited-members:

The Viewer Cache
++++++++++++++++

.. autoclass:: ViewerCache
    :members:
    :inherited-members:
