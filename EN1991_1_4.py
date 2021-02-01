# coding: utf-8
# script to calculate wind speed profiles according to Eurocode EN1991-1-4

# TODO: add function to prompt inputs and share results,
# TODO: add uk NA, add Cp, Cf
# TODO: Create site class, structure class?

import csv
import webbrowser

import numpy as np

rho = 1.225  # density kg/m3
co = 1.  # flat terrain


class OutOfScopeError(ValueError):
    """Not covered by the code, possibly because the input parameters are out of bounds"""


class Site():
    def __init__(self, terrain: str, vb0: float):
        self.z0 = z0[terrain]
        self.zmin = zmin[terrain]
        self.vb0 = vb0


class Structure():
    def __init__(self, site: Site, height: float):
        self.cr = cr(height, site.z0, site.zmin)
        self.iu = iu(height, site.z0, site.zmin)


z = np.empty([1])

z0 = {'O': 0.003, 'I': 0.01, 'II': 0.05, 'III': 0.3, 'IV': 1.}

zmin = {'O': 1., 'I': 1., 'II': 2., 'III': 5., 'IV': 10.}


def cr(z, z0, zmin):
    """Calculate mean wind speed ratio at a given height"""
    if z < zmin:
        z = zmin
    return 0.19 * (z0 / 0.05) ** 0.07 * np.log(z / z0)


def iu(z, z0, zmin):
    """Calclate turbulence intensity at a given height"""
    if z < zmin:
        z = zmin
    return 1 / (co * np.log(z / z0))


def qp(U, iu):
    """Calculate peak dynamic pressure from mean wind speed and turbulence intensity"""
    qp = 0.5 * rho * (U ** 2.) * (1 + 7 * iu)
    return qp


def UbFR(dept, commune):
    """lookup base wind speed by dept and commune from FR national annexe"""
    if commune == '':
        raise ValueError
    dept = str(dept)
    if len(dept) == 1:
        dept = '0' + dept
    reg = []
    regions = {}
    Ubs = {'1': 22, '2': 24, '3': 26, '4': 28}
    csvfile = open('data/DeptNumRegion.csv', encoding='utf')
    a = csv.reader(csvfile, dialect='excel', delimiter=';')
    for l in a:
        if dept.upper() == l[0]:
            global region, deptname
            reg = l[2]
            deptname = l[1]
    csvfile.close()

    if len(reg) > 1:
        with open('data/CantonNumRegion.csv', encoding='utf') as cantonfile:
            a = csv.reader(cantonfile, dialect='excel', delimiter=';')
            for l in a:
                if l[1].upper() == deptname.upper():
                    if commune.upper() in l:
                        reg = l[2]
                    else:
                        l = next(a)
                        if commune.upper() in l[2:]:
                            reg = l[2]
                        else:
                            reg = l[1]

    if len(reg) == 1:
        Ub = Ubs[reg[0]]
        return Ub
    else:
        return reg


z0NAFR = {'O': 0.005, 'II': 0.05, 'IIIa': 0.2, 'IIIb': 0.5, 'IV': 1.}

zminNAFR = {'O': 1., 'II': 2., 'IIIa': 5., 'IIIb': 9., 'IV': 15.}

def radiusNAFR(z: float) -> float:
    """radius for the evaltuation of roughness according to the French National annex"""
    return max(23*z**1.2,300)

radiusNABE = radiusNAFR

Vb0NAFR = {1: 22., 2: 24., 3: 26., 4: 28.}

cprobFR = {50: 1., 25: .97, 10: .92, 5: .88, 2: .82}


def iuFR(z, z0, zmin):
    if z < zmin:
        z = zmin
    kI = 1 - 0.0002 * (np.log10(z0) + 3) ** 6
    return kI / (co * np.log(z / z0))


def CdirFR(dept, dir):
    dept = str(dept)
    if len(dept) == 1:
        dept = '0' + dept
    reg = []
    regions = {}
    Cdirs = {'1': [10, 150, 0.7], '2': [70, 150, 0.7], '3': [50, 250, 0.85]}
    csvfile = open('data/FRNA_Cdir_dept.csv', encoding='utf')
    a = csv.reader(csvfile, dialect='excel', delimiter=';')
    for l in a:
        if dept.upper() == l[0]:
            reg = l[2]
            if dir >= Cdirs[reg][0]:
                if dir <= Cdirs[reg][1]:
                    return Cdirs[reg][2]
                else:
                    return 1.
            else:
                return 1.
    raise ValueError
    csvfile.close()


def power_law(z, C, alpha):
    """Helper function for Austrian national annexe"""
    return C * (z / 10) ** alpha


terrainAT = {'II': {'qp': {'C': 2.1, 'alpha': 0.24}, 'cr': {'C': 1.0, 'alpha': 0.3}, 'iu': {'C': 0.18, 'alpha': -0.15},
                    'zmin': 5.}, 'III': {'qp': {'C': 1.75, 'alpha': 0.29}, 'cr': {'C': 0.593, 'alpha': 0.42},
                                         'iu': {'C': 0.29, 'alpha': -0.21}, 'zmin': 10.},
             'IV': {'qp': {'C': 1.2, 'alpha': 0.38}, 'cr': {'C': 0.263, 'alpha': 0.64},
                    'iu': {'C': 0.46, 'alpha': -0.32}, 'zmin': 15.}}


def zminAT(z, terrain):
    zmin = terrainAT[terrain]['zmin']
    if z < zmin:
        z = zmin
    return z


def crAT(z, terrain):
    if terrain == 'O' or terrain == 'I':
        terrain = 'II'
    z = zminAT(z, terrain)
    vals = terrainAT[terrain]['cr']
    C = vals['C']
    a = vals['alpha']
    return (power_law(z, C, a)) ** 0.5


def qpAT(z, terrain, qb):
    if terrain == 'O' or terrain == 'I':
        terrain = 'II'
    z = zminAT(z, terrain)
    vals = terrainAT[terrain]['qp']
    C = vals['C']
    a = vals['alpha']
    return qb * power_law(z, C, a)


def iuAT(z, terrain):
    if terrain == 'O' or terrain == 'I':
        terrain = 'II'
    z = zminAT(z, terrain)
    vals = terrainAT[terrain]['iu']
    C = vals['C']
    a = vals['alpha']
    return power_law(z, C, a)


def CdirBE(dir=0):
    dirs = [0, 22.5, 37.75, 45, 56.25, 90, 120, 150, 180, 270]
    Cdirs = [1.00, 1.00, 0.95, 0.90, 0.85, 0.85, 0.90, 0.95, 1.00, 1.00]
    return np.interp(dir, dirs, Cdirs)


def UbGB(nth, est, alt):
    '''Returns basic wind velocity from UK coordinates
    nth,est are Northing and Easting in m'''
    calt = alt / 1000.
    ln0 = 0
    lt0 = -100000
    if nth < lt0 or nth > 1300000 or est < ln0 or est > 700000:
        return ValueError
    lnstp = 35000.
    ltstp = 36842.1053
    ilat = (nth - lt0) // ltstp
    ilon = (est - ln0) // lnstp
    Umap = np.genfromtxt('data/FigureNA1.csv', delimiter=',')
    lats = np.array(
        [-100, -63.15789474, -26.31578947, 10.52631579, 47.36842105, 84.21052632, 121.0526316, 157.8947368, 194.7368421,
         231.5789474, 268.4210526, 305.2631579, 342.1052632, 378.9473684, 415.7894737, 452.6315789, 489.4736842,
         526.3157895, 563.1578947, 600, 636.8421053, 673.6842105, 710.5263158, 747.3684211, 784.2105263, 821.0526316,
         857.8947368, 894.7368421, 931.5789474, 968.4210526, 1005.263158, 1042.105263, 1078.947368, 1115.789474,
         1152.631579, 1189.473684, 1226.315789, 1263.157895, 1300])
    lons = Umap[:, 0]
    lats *= 1000
    lons *= 1000
    Umap = Umap[:, 1:]
    ln1 = Umap[ilon, :]
    ln2 = Umap[ilon + 1, :]
    Ue = np.interp(nth, lats, ln1)
    Uf = np.interp(nth, lats, ln2)
    Ub = Ue + (Uf - Ue) * (est - lons[ilon]) / (lons[ilon + 1] - lons[ilon])
    return Ub * (1 + calt)


def CdirGB(dir):
    Cdirs = [0.78, 0.73, 0.73, 0.74, 0.73, 0.8, 0.85, 0.93, 1., 0.99, 0.91, 0.82, 0.78]
    a = Cdirs[int(dir / 30)]
    b = Cdirs[int(dir / 30) + 1] - a
    return a + b * (dir % 30) / 30


def dimparams(w1, w2, h):
    pass


def zonescale(b, h):
    return min(b, 2 * h)


def cparea(cp1, cp10, a):
    '''interpolate between Cp1 and Cp10 on a log (area) scale. Cp constant beyond bounds.'''
    return np.interp(np.log10(a), [np.log10(1), np.log10(10)], [cp1, cp10])


def cpwall(d, h, zone, size=1):
    """cp on vertical walls"""
    hd = h / d
    print('hd=', hd)
    hdlist = list(reversed([5, 1, 0.25]))
    table7p1_1 = {'A': [-1.4, -1.4, -1.4], 'B': [-0.8, -0.8, -0.8], 'C': [-.5, -.5, -.5], 'D': [0.8, 0.8, 0.7],
                  'E': [-0.7, -0.5, -0.3]}
    table7p1_10 = {'A': [-1.2, -1.2, -1.2], 'B': [-1.1, -1.1, -1.1], 'C': [-.5, -.5, -.5], 'D': [1., 1., 1.],
                   'E': [-0.7, -0.5, -0.3]}
    cp1 = np.interp(hd, hdlist, list(reversed(table7p1_1[zone])))
    cp10 = np.interp(hd, hdlist, list(reversed(table7p1_10[zone])))
    return cparea(cp1, cp10, size)


def cpint(d=None, h=None, mu=None, case='conservative'):
    if case == 'conservative':
        return [-0.3, 0.2]
    elif case == 'not dominant':
        hd = h / d
        cpip25 = np.interp(mu, [0.33, 0.9], [0.35, -0.3])
        cpi1 = np.interp(mu, [0.33, 0.95], [0.35, -0.5])
        return np.interp(hd, [0.25, 1], [cpip25, cpi1])


def correlcp(d, h):
    hd = h / d
    return np.interp(hd, [1, 5], [0.85, 1.])


def cf_monopitch_canopy(inclination: float, blockage: float) -> tuple:
    """From Table 7.6"""
    if not (0 <= inclination <= 30):
        raise OutOfScopeError
    if not (0 <= blockage <= 1):
        raise OutOfScopeError
    cf_max = np.interp(inclination,
                       [0, 5, 10, 15, 20, 25, 30],
                       [0.2, 0.4, 0.5, 0.7, 0.8, 1.0, 1.2],
                       )
    cf_min_open = np.interp(inclination,
                            [0, 5, 10, 15, 20, 25, 30],
                            [-0.5, -0.7, -0.9, -1.1, -1.3, -1.6, -1.8],
                            )
    cf_min_closed = np.interp(inclination,
                              [0, 5, 30],
                              [-1.3, -1.4, -1.4],
                              )
    cf_min = np.interp(blockage, [0, 1], [cf_min_open, cf_min_closed])
    return cf_max, cf_min


def cp_monopitch_canopy(inclination: float, blockage: float, zone: str) -> tuple:
    """From Table 7.6"""
    cp_values = {'A': {'max': [0.5, 0.8, 1.2, 1.4, 1.7, 2.0, 2.2],
                       'min_0': [-0.6, -1.1, -1.5, -1.8, -2.2, -2.6, -3.0],
                       'min_1': [-1.5, -1.6, -1.6, -1.6, -1.6, -1.5, -1.5],
                       },
                 'B': {'max': [1.8, 2.1, 2.4, 2.7, 2.9, 3.1, 3.2],
                       'min_0': [-1.3, -1.7, -2.0, -2.4, -2.8, -3.2, -3.8],
                       'min_1': [-1.8, -2.2, -2.6, -2.9, -2.9, -2.5, -2.2],
                       },
                 'C': {'max': [1.1, 1.3, 1.6, 1.8, 2.1, 2.3, 2.4],
                       'min_0': [-1.4, -1.8, -2.1, -2.5, -2.9, -3.2, -3.6],
                       'min_1': [-2.2, -2.5, -2.7, -3.0, -3.0, -2.8, -2.7],
                       },
                 }
    inclinations = [0,5,10,15,20,25,30]
    cp_max = np.interp(inclination, inclinations, cp_values[zone]['max'])
    cp_min_0 = np.interp(inclination, inclinations, cp_values[zone]['min_0'])
    cp_min_1 = np.interp(inclination, inclinations, cp_values[zone]['min_1'])
    cp_min = np.interp(blockage, [0,1], [cp_min_0, cp_min_1])
    return (cp_max, cp_min)


# ANNEXE B CsCd

def alpha(z0: float) -> float:
    return 0.67 + 0.05 * np.log(z0)


def l_turb(z: float, zmin: float, alpha: float) -> float:
    lt = 300
    zt = 200
    z = max(z, zmin)
    return lt * (z / zt) ** alpha


def fl(n1: float, v_moy: float, l_turb) -> float:
    return (n1 * l_turb) / v_moy


def Sl(n1: float, fl: float) -> float:
    return (6.8 * fl) / ((1 + 10.2 * fl) ** (5 / 3))


def strouhal(b, d=None, shape='circle'):
    """ Strouhal number from table E.1 incomplete."""
    db = d / b
    if shape == 'circle':
        return 0.18
    elif shape == 'rectangle':

        if db < 0.5 or db > 10:
            raise ValueError
        else:
            return np.interp(db, [1, 2, 3, 3.5, 5, 10], [0.12, 0.06, 0.06, 0.15, 0.11, 0.09])
    elif shape == 'isect':  # wind parallel to web
        if db < 1 or db > 2:
            raise ValueError
        else:
            return np.interp(db, [1, 1.5, 2], [.11, .10, .14])
    else:
        raise ValueError()


def reynolds(b, v):
    return b * v / 15e-6


def vcrit(b, n, st):
    """Calculate critical wind speed for vortex shedding.

    args:
        b = crosswind dimension in m
        n = natural frequency in Hz
        st = Strouhal number

    returns:
        critical wind velocity for resonance due to vortex shedding in m/s."""
    return b * n / st


if __name__ == '__main__':
    webbrowser.open(
        'https://educnet.enpc.fr/pluginfile.php/11069/mod_folder/content/0/EC1-1-4%20vent.pdf?forcedownload=1')
