"""Tests for EN-1991-1-4:2005
Base cscd tests on http://www.sigmundcarlo.net/Demo/EUROCODES_Sigmund_DEMO.pdf
saved in refs folder: """

from pytest import approx

import EN1991_1_4


# TODO : finish example 28-B

def test_radius_FR():
    assert EN1991_1_4.radiusNAFR(5) == approx(300, rel=0.001)
    assert EN1991_1_4.radiusNAFR(15) == approx(593, rel=0.001)
    assert EN1991_1_4.radiusNAFR(50) == approx(2515, rel=0.001)
    assert EN1991_1_4.radiusNAFR(150) == approx(9398, rel=0.001)


def test_cscd_a():
    """from Example 28-A"""
    z_act = 30.
    h_dis = 10.  # displacement height
    v_moy = 36.4  # m/s, 100 ans retour
    n1 = 0.5  # Hz
    terrain = "O"
    z0 = EN1991_1_4.z0_table[terrain]
    zmin = EN1991_1_4.zmin[terrain]
    z = z_act - h_dis
    alpha = EN1991_1_4.alpha(z0)
    assert alpha == approx(0.38, rel=0.01)
    l_turb = EN1991_1_4.l_turb(z, zmin, alpha)
    assert l_turb == approx(125, rel=0.01)
    fl = EN1991_1_4.fl(n1, v_moy, l_turb)
    assert fl == approx(1.7, rel=0.02)
    assert EN1991_1_4.Sl(z, fl) == approx(0.09, rel=0.01)


def test_cscd_b():
    log_dec_damping = 5 / 100
    width = 20  # m
    height = 60  # m
    z = 0.6 * height
    v_moy = 37.4  # m/s mean return period: 50 years,in terrain category “0” at 0.6 H, donc 36 m
    terrain = "O"
    n1 = 0.5  # Hz
    z0 = EN1991_1_4.z0_table[terrain]
    zmin = EN1991_1_4.zmin[terrain]
    alpha = EN1991_1_4.alpha(z0)
    l_turb = EN1991_1_4.l_turb(z, zmin, alpha)
    fl = EN1991_1_4.fl(n1, v_moy, l_turb)
    sl = EN1991_1_4.Sl(z, fl)
    assert alpha == approx(0.38, rel=0.01)
    assert l_turb == approx(156.5, rel=0.01)
    assert fl == approx(2.09, rel=0.01)
    assert sl == approx(0.08, rel=0.01)

"""    assert b_squared == approx(0.793, rel=0.01)
    assert eta_h == approx(3.69, rel=0.01)
    assert eta_b == approx(1.23, rel=0.01)
    assert R_h == approx(0.234, rel=0.01)
    assert R_b == approx(0.511, rel=0.01)
    assert r_squared == approx(0.944, rel=0.01)
    assert kp == approx(3.48, rel=0.01)
    assert cscd == approx(1.102, rel=0.01)"""
