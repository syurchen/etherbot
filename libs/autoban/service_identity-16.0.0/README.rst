===========================================
Service Identity Verification for pyOpenSSL
===========================================

.. image:: https://travis-ci.org/pyca/service_identity.svg?branch=master
  :target: https://travis-ci.org/pyca/service_identity

.. image:: https://codecov.io/github/pyca/service_identity/coverage.svg?branch=master
  :target: https://codecov.io/github/pyca/service_identity

.. image:: https://www.irccloud.com/invite-svg?channel=%23cryptography-dev&amp;hostname=irc.freenode.net&amp;port=6697&amp;ssl=1
    :target: https://www.irccloud.com/invite?channel=%23cryptography-dev&amp;hostname=irc.freenode.net&amp;port=6697&amp;ssl=1

.. begin

**TL;DR**: Use this package if you use pyOpenSSL_ and don’t want to be MITM_\ ed.

``service_identity`` aspires to give you all the tools you need for verifying whether a certificate is valid for the intended purposes.

In the simplest case, this means *host name verification*.
However, ``service_identity`` implements `RFC 6125`_ fully and plans to add other relevant RFCs too.

``service_identity``\ ’s documentation lives at `Read the Docs <https://service-identity.readthedocs.org/>`_, the code on `GitHub <https://github.com/pyca/service_identity>`_.


.. _Twisted: https://twistedmatrix.com/
.. _pyOpenSSL: https://pypi.python.org/pypi/pyOpenSSL/
.. _MITM: https://en.wikipedia.org/wiki/Man-in-the-middle_attack
.. _`RFC 6125`: http://www.rfc-editor.org/info/rfc6125
