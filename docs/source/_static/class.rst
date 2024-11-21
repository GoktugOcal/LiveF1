{{ fullname }}
{{ underline }}

{{ docstring }}

{% if methods %}
Functions Summary
-----------------

.. list-table:: 
   :widths: 30 70
   :header-rows: 1

   * - Function Name
     - Description
   {% for method in methods %}
   * - :meth:`{{ method.fullname }}`
     - {{ method.docstring | escape | eol_escape }}
   {% endfor %}
{% endif %}

Attributes Summary
------------------

{% if attributes %}
.. list-table:: 
   :widths: 30 70
   :header-rows: 1

   * - Attribute Name
     - Description
   {% for attr in attributes %}
   * - ``{{ attr.name }}``
     - {{ attr.docstring | escape | eol_escape }}
   {% endfor %}
{% else %}
No attributes documented.
{% endif %}

Details
-------

.. automethod:: {{ fullname }}
   :noindex:
   :undoc-members:
   :inherited-members:
