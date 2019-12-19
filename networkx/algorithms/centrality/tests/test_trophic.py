"""Test trophic levels, trophic differences and trophic coherence
"""
import numpy as np
import pytest

import networkx as nx
from networkx.testing import almost_equal


def test_trophic_levels():
    """Trivial example
    """
    G = nx.DiGraph()
    G.add_edge("a", "b")
    G.add_edge("b", "c")

    d = nx.trophic_levels(G)
    assert d == {"a": 1, "b": 2, "c": 3}


def test_trophic_levels_levine():
    """Example from Figure 5 in Stephen Levine (1980) J. theor. Biol. 83, 195-207
    """
    S = nx.DiGraph()
    S.add_edge(1, 2, weight=1.0)
    S.add_edge(1, 3, weight=0.2)
    S.add_edge(1, 4, weight=0.8)
    S.add_edge(2, 3, weight=0.2)
    S.add_edge(2, 5, weight=0.3)
    S.add_edge(4, 3, weight=0.6)
    S.add_edge(4, 5, weight=0.7)
    S.add_edge(5, 4, weight=0.2)

    # save copy for later, test intermediate implementation details first
    S2 = S.copy()

    # drop nodes of in-degree zero
    z = [nid for nid, d in S.in_degree if d == 0]
    for nid in z:
        S.remove_node(nid)

    # find adjacency matrix
    q = nx.linalg.graphmatrix.adjacency_matrix(S).T

    expected_q = np.array([
        [0, 0, 0., 0],
        [0.2, 0, 0.6, 0],
        [0, 0, 0, 0.2],
        [0.3, 0, 0.7, 0]
    ])
    assert np.array_equal(q.todense(), expected_q)

    # must be square, size of number of nodes
    assert len(q.shape) == 2
    assert q.shape[0] == q.shape[1]
    assert q.shape[0] == len(S)

    nn = q.shape[0]

    i = np.eye(nn)
    n = np.linalg.inv(i - q)
    y = np.dot(np.asarray(n), np.ones(nn))

    expected_y = np.array([1, 2.07906977, 1.46511628, 2.3255814])
    assert np.allclose(y, expected_y)

    expected_d = {
        1: 1,
        2: 2,
        3: 3.07906977,
        4: 2.46511628,
        5: 3.3255814
    }

    d = nx.trophic_levels(S2)

    for nid, level in d.items():
        expected_level = expected_d[nid]
        assert almost_equal(expected_level, level)


def test_trophic_levels_simple():
    matrix_a = np.array([[0, 0], [1, 0]])
    G = nx.from_numpy_matrix(matrix_a, create_using=nx.DiGraph)
    d = nx.trophic_levels(G)
    assert almost_equal(d[0], 2)
    assert almost_equal(d[1], 1)


def test_trophic_levels_more_complex():
    matrix = np.array([
        [0, 1, 0, 0],
        [0, 0, 1, 0],
        [0, 0, 0, 1],
        [0, 0, 0, 0]
    ])
    G = nx.from_numpy_matrix(matrix, create_using=nx.DiGraph)
    d = nx.trophic_levels(G)
    expected_result = [1, 2, 3, 4]
    for ind in range(4):
        assert almost_equal(d[ind], expected_result[ind])


    matrix = np.array([
        [0, 1, 1, 0],
        [0, 0, 1, 1],
        [0, 0, 0, 1],
        [0, 0, 0, 0]
    ])
    G = nx.from_numpy_matrix(matrix, create_using=nx.DiGraph)
    d = nx.trophic_levels(G)

    expected_result = [1, 2, 2.5, 3.25]
    print("Calculated result: ", d)
    print("Expected Result: ", expected_result)

    for ind in range(4):
        assert almost_equal(d[ind], expected_result[ind])


def test_trophic_levels_even_more_complex():
    # Another, bigger matrix
    matrix = np.array([
        [0, 0, 0, 0, 0],
        [0, 1, 0, 1, 0],
        [1, 0, 0, 0, 0],
        [0, 1, 0, 0, 0],
        [0, 0, 0, 1, 0]
    ])

    # Generated this linear system using pen and paper:
    K = np.array([
        [1, 0, -1, 0, 0],
        [0, 0.5, 0, -0.5, 0],
        [0, 0, 1, 0, 0],
        [0, -0.5, 0, 1, -0.5],
        [0, 0, 0, 0, 1],
    ])
    result_1 = np.ravel(np.matmul(np.linalg.inv(K), np.ones(5)))
    G = nx.from_numpy_matrix(matrix, create_using=nx.DiGraph)
    result_2 = nx.trophic_levels(G)

    for ind in range(5):
        assert almost_equal(result_1[ind], result_2[ind])


def test_trophic_levels_singular_matrix():
    """Should raise an error with graphs with only non-basal nodes
    """
    matrix = np.identity(4)
    G = nx.from_numpy_matrix(matrix, create_using=nx.DiGraph)
    with pytest.raises(np.linalg.LinAlgError):
        nx.trophic_levels(G)


def test_trophic_differences():
    matrix_a = np.array([[0, 1], [0, 0]])
    G = nx.from_numpy_matrix(matrix_a, create_using=nx.DiGraph)
    diffs = nx.trophic_differences(G)
    assert almost_equal(diffs[(0, 1)], 1)

    matrix_b = np.array([
        [0, 1, 1, 0],
        [0, 0, 1, 1],
        [0, 0, 0, 1],
        [0, 0, 0, 0]
    ])
    G = nx.from_numpy_matrix(matrix_b, create_using=nx.DiGraph)
    diffs = nx.trophic_differences(G)

    assert almost_equal(diffs[(0, 1)], 1)
    assert almost_equal(diffs[(0, 2)], 1.5)
    assert almost_equal(diffs[(1, 2)], 0.5)
    assert almost_equal(diffs[(1, 3)], 1.25)
    assert almost_equal(diffs[(2, 3)], 0.75)


def test_trophic_coherence_no_cannibalism():
    matrix_a = np.array([[0, 1], [0, 0]])
    G = nx.from_numpy_matrix(matrix_a, create_using=nx.DiGraph)
    q = nx.trophic_coherence(G, cannibalism=False)
    assert almost_equal(q, 0)

    matrix_b = np.array([
        [0, 1, 1, 0],
        [0, 0, 1, 1],
        [0, 0, 0, 1],
        [0, 0, 0, 0]
    ])
    G = nx.from_numpy_matrix(matrix_b, create_using=nx.DiGraph)
    q = nx.trophic_coherence(G, cannibalism=False)
    assert almost_equal(q, np.std([1, 1.5, 0.5, 0.75, 1.25]))

    matrix_c = np.array([
        [0, 1, 1, 0],
        [0, 1, 1, 1],
        [0, 0, 0, 1],
        [0, 0, 0, 1]
    ])
    G = nx.from_numpy_matrix(matrix_c, create_using=nx.DiGraph)
    q = nx.trophic_coherence(G, cannibalism=False)
    # Ignore the -link
    assert almost_equal(q, np.std([1, 1.5, 0.5, 0.75, 1.25]))


def test_trophic_coherence_cannibalism():
    matrix_a = np.array([[0, 1], [0, 0]])
    G = nx.from_numpy_matrix(matrix_a, create_using=nx.DiGraph)
    q = nx.trophic_coherence(G, cannibalism=True)
    assert almost_equal(q, 0)

    matrix_b = np.array([
        [0, 0, 0, 0, 0],
        [0, 1, 0, 1, 0],
        [1, 0, 0, 0, 0],
        [0, 1, 0, 0, 0],
        [0, 0, 0, 1, 0]
    ])
    G = nx.from_numpy_matrix(matrix_b, create_using=nx.DiGraph)
    q = nx.trophic_coherence(G, cannibalism=True)
    assert almost_equal(q, 2)

    matrix_c = np.array([
        [0, 1, 1, 0],
        [0, 0, 1, 1],
        [0, 0, 0, 1],
        [0, 0, 0, 0]
    ])
    G = nx.from_numpy_matrix(matrix_c, create_using=nx.DiGraph)
    q = nx.trophic_coherence(G, cannibalism=True)
    # Ignore the -link
    assert almost_equal(q, np.std([1, 1.5, 0.5, 0.75, 1.25]))
