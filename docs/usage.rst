Usage
=====

Encrypt an AASX package
-----------------------

.. code-block:: python

   from aas_holo_shard.core import shamir

   aas_bytes = open("example.aasx", "rb").read()
   encrypted, shares = shamir.encrypt_and_split(aas_bytes, threshold=3, total=5)

Decrypt with shares
-------------------

.. code-block:: python

   recovered = shamir.reconstruct_and_decrypt(encrypted, shares[:3])

BaSyx integration
-----------------

The `aas_holo_shard.aas.parser` module includes optional helpers for BaSyx.
If you have the BaSyx SDK installed, you can load structured AASX contents
using the `load_aasx_basyx` helper.

.. code-block:: python

   from aas_holo_shard.aas import parser

   object_store, file_store = parser.load_aasx_basyx("example.aasx")
