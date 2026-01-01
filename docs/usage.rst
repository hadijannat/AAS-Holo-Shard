Usage
=====

Encrypt an AASX package (optional dependency)
---------------------------------------------

.. code-block:: python

   from aas_holo_shard.core import shamir

   aas_bytes = open("example.aasx", "rb").read()
   encrypted, shares = shamir.encrypt_and_split(aas_bytes, threshold=3, total=5)

Decrypt with shares
-------------------

.. code-block:: python

   recovered = shamir.reconstruct_and_decrypt(encrypted, shares[:3])

Pure-Python AAS JSON sharding
-----------------------------

Split a target Property by idShort into shards:

.. code-block:: bash

   python aas_shard.py split factory.json MasterKey -n 3 -k 2

Combine any K shards to recover the secret:

.. code-block:: bash

   python aas_shard.py combine MasterKey factory_shard_1.json factory_shard_3.json

BaSyx integration
-----------------

The `aas_holo_shard.aas.parser` module includes optional helpers for BaSyx.
If you have the BaSyx SDK installed, you can load structured AASX contents
using the `load_aasx_basyx` helper.

.. code-block:: python

   from aas_holo_shard.aas import parser

   object_store, file_store = parser.load_aasx_basyx("example.aasx")
