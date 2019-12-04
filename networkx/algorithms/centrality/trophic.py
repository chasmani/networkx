"""Trophic levels"""
import numpy as np
import networkx as nx

from networkx.utils import not_implemented_for

__all__ = ['trophic_levels']


@not_implemented_for('undirected')
def trophic_levels(G, weight='weight'):
    """Compute the trophic levels of nodes.

    The trophic level of a node $i$ is

    .. math::

        s_i = 1 + \frac{1}{k_^{in}_i \sum_{j} a_{ij} s_j

    where $k_^{in}_i$ is the in-degree of i

    .. math::

        k^{in}_i = \sum_{j} a_{ij}

    and nodes with $k_^{in}_i = 0$ have $s_i = 1$ by convention.

    These are calculated using the method outlined in Stephen Levine (1980) J. theor. Biol. 83, 195-207

    Parameters
    ----------
    G : DiGraph
        A directed networkx graph

    Returns
    -------
    nodes : dict
        Dictionary of nodes with trophic level as the vale.
    """
    # find adjacency matrix
    a = nx.adjacency_matrix(G, weight=weight).T
    a = np.asarray(a.todense())

    # drop rows/columns where in-degree is zero
    rowsum = np.sum(a, axis=1)
    p = a[rowsum != 0][:, rowsum != 0]
    # normalise so sum of in-degree weights is 1 along each row
    p = p / rowsum[rowsum != 0][:, np.newaxis]

    # calculate trophic levels
    nn = p.shape[0]
    i = np.eye(nn)
    n = np.linalg.inv(i - p)
    y = n.sum(axis=1) + 1

    levels = {}

    # all nodes with in-degree zero have trophic level == 1
    zero_node_ids = (node_id for node_id, degree in G.in_degree if degree == 0)
    for node_id in zero_node_ids:
        levels[node_id] = 1

    # all other nodes have levels as calculated
    nonzero_node_ids = (node_id for node_id, degree in G.in_degree if degree != 0)
    for i, node_id in enumerate(nonzero_node_ids):
        levels[node_id] = y[i]

    return levels


# trophic_difference for each edge is $x_ij = s_i - s_j$
# trophic_coherence is the standard deviation of trophic distances