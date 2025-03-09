"""A 2-3 Tree implementation.

--------------------------------------------------------------------------------
Note:

This implementation has a declarative "pure functional" style. This is
almost certainly *not* an efficient implementation of 2-3 Trees but I,
personally, find it easier to get a *correct* implementation with a
declarative style. A more efficient 2-3 Tree implementation is one
possible target for improving the overall performance of the plugin.
--------------------------------------------------------------------------------

"""
from collections import namedtuple

# --------------------------------------------------------------------------------
# Tree Node Types
# --------------------------------------------------------------------------------

# Contains no data and has no child nodes.
Empty = namedtuple('Empty', [])

# Contains one (key, value) pair and exactly two child nodes. If one
# child node is Empty then both must be Empty.
ONode = namedtuple('ONode', ['key', 'value', 'left', 'right'])

# Contains two (key, value) pairs and exactly three child nodes. If
# one child node is Empty then all three must be Empty.
TNode = namedtuple('TNode', ['low_key', 'low_value', 'high_key', 'high_value', 'left', 'middle', 'right'])

Tree = Empty

def insert(T, key, value):
    """Inserts a new (key, value) pair into tree T decending
    recursively if necessary accoring to the type of node the value is
    being inserted into.

    Returns a new tree.

    """

    # --------------------------------------------------------------------------------
    # Inserting into an Empty node (recursive base case)
    # --------------------------------------------------------------------------------
    if type(T) == Empty:
        return ONode(key, value, Empty(), Empty())

    # --------------------------------------------------------------------------------
    # Inserting into an ONode
    # --------------------------------------------------------------------------------
    if type(T) == ONode:
        (k, v, left, right) = T
        if type(left) == Empty and key < k:
            return TNode(key, value, k, v, Empty(), Empty(), Empty())

        if type(left) == Empty:
            return TNode(k, v, key, value, Empty(), Empty(), Empty())

        if key < k:
            L = insert(left, key, value)
            if type(left) == TNode and type(L) == ONode:
                (Lk, Lv, Ll, Lr) = L
                return TNode(Lk, Lv, k, v, L, right)
            else:
                return ONode(k, v, L, right)

        if key > k:
            R = insert(right, key, value)
            if type(right) == TNode and type(R) == ONode:
                (Rk, Rv, Rl, Rr) = R
                return TNode(k, v, Rk, Rv, left, Rl, Rr)
            else:
                return ONode(k, v, left, R)

    # --------------------------------------------------------------------------------
    # Inserting into an TNode
    # --------------------------------------------------------------------------------
    if type(T) == TNode:
        (k1, v1, k2, v2, left, middle, right) = T

        if type(left) == Empty and key < k1:
            return ONode(k1, v1, ONode(key, value, Empty(), Empty()), ONode(k2, v2, Empty(), Empty()))

        if type(left) == Empty and key < k2:
            return ONode(key, value, ONode(k1, v2, Empty(), Empty()), ONode(k2, v2, Empty(), Empty()))
            
        if type(left) == Empty and key > k2:
            return ONode(k2, v2, ONode(k1, v1, Empty(), Empty()), ONode(key, value, Empty(), Empty()))

        if key < k1:
            L = insert(left, key, value)
            if type(left) == TNode and type(L) == ONode:
                return ONode(k1, v1, L, ONode(k2, v2, middle, right))
            else:
                return TNode(k1, v1, k2, v2, L, middle, right)

        if key < k2:
            M = insert(middle, key, value)
            if type(middle) == TNode and type(M) == ONode:
                (Mk, Mv, Ml, Mr) = M
                return ONode(Mk, Mv, ONode(k1, v1, left, Ml), ONode(k2, v2, Mr, right))
            else:
                return TNode(k1, v1, k2, v2, left, M, right)
            
        if key > k2:
            R = insert(right, key, value)
            if type(right) == TNode and type(R) == ONode:
                return ONode(k2, v2, ONode(k1, v1, left, middle), R)
            else:
                return TNode(k1, v1, k2, v2, left, middle, R)

def search(T, key, low=None, high=None):
    """Searches tree T for 'key'.

    Since the exact key may not be in the tree the search keeps track
    of the lower and upper bounds as it searches.

    Returns the bounds as a tuple (low, high) where each bound is a
    (key, value) pair.

    """

    # --------------------------------------------------------------------------------
    # Searching an Empty Node (recursive base case)
    # --------------------------------------------------------------------------------
    if type(T) == Empty:
        return (low, high)

    # --------------------------------------------------------------------------------
    # Searching an ONode
    # --------------------------------------------------------------------------------
    if type(T) == ONode:
        (k, v, l, r) = T
        res = (k, v)
        if key == k:
            return (res, res)

        if key < k:
            return search(l, key, low or res, res)

        if key > k:
            return search(r, key, res, high or res)

    # --------------------------------------------------------------------------------
    # Searching an TNode
    # --------------------------------------------------------------------------------
    if type(T) == TNode:
        (k1, v1, k2, v2, l, m, r) = T
        res1 = (k1, v1)
        res2 = (k2, v2)
        if key == k1:
            return (res1, res1)

        if key == k2:
            return (res2, res2)

        if key < k1:
            return search(l, key, low or res1, res1)

        if key < k2:
            return search(m, key, res1, res2)

        if key > k2:
            return search(r, key, res2, high or res2)
