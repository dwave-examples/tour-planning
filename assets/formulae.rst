
Formulas used in the README File
================================

Exercise
--------

.. math::

    \sum_{i=0}^{L-1} l_i s_i \sum_{j=0}^{M-1} x_{i,j} v_{j}

where

* :math:`L`: Number of legs in the tour.
* :math:`M`: Number of available modes of locomotion.
* :math:`l_i`: Length of leg :math:`i`.
* :math:`s_i`: Steepness of leg :math:`i`.
* :math:`x_{i,j}`: Binary variable representing that locomotion mode `j` is selected for leg :math:`i`.
* :math:`v_j`: Value of exercise set for locomotion mode `j`.

One-Hot Constraint
------------------

.. math::

    \forall i=0 ..L-1: \sum_{j=0}^{M-1} x_{i,j} = 1

Cost
----

.. math::

    \sum_{i=0}^{L-1} l_i \sum_{j=0}^{M-1} x_{i,j} c_{j}

where :math:`c_j` is the cost for locomotion mode `j`.

Time
----

.. math::

    \sum_{i=0}^{L-1} l_i \sum_{j=0}^{M-1} x_{i,j} / s_{j}

where math:`s_j` is the speed for locomotion mode `j`.

Toll Constraint
---------------

.. math::

    \forall i=0 ..L-1, \text{toll} = 1: x_{i,drive} = 0

Slope Constraint
----------------

.. math::

    \forall i=0 ..L-1: \text{slope}_i * x_{i,cycle} <= \text{maximum slope}

    \forall i=0 ..L-1: \text{slope}_i * x_{i,walk} <= \text{maximum slope}
