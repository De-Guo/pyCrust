#!/usr/bin/env python3
"""
Create images related to Mars for the Hydrostatic flattening paper with a
lithosphere
"""
import numpy as np
import os

import pyshtools

import pyMoho
from Hydrostatic import HydrostaticShapeLith
from Hydrostatic import HydrostaticShape

# ==== MAIN FUNCTION ====


def main():

    d_lith = 150.e3
    rho_crust = 2900.
    d_sigma = 45.e3
    lmax_hydro = 2

    gravfile = 'Data/gmm3_120_sha.tab'
    topofile = 'Data/MarsTopo719.shape'

    potential = pyshtools.SHGravCoeffs.from_file(gravfile, header_units='km')
    omega = pyshtools.constant.omega_mars.value
    potential.omega = omega

    print('Gravity file = {:s}'.format(gravfile))
    print('Lmax of potential coefficients = {:d}'.format(potential.lmax))
    print('Reference radius (km) = {:f}'.format(potential.r0 / 1.e3))
    print('GM = {:e}'.format(potential.gm))
    print('Mass = {:e}'.format(potential.mass))
    print('Omega = {:e}'.format(potential.omega))

    lmax_calc = 90
    lmax = 359

    topo = pyshtools.SHCoeffs.from_file(topofile, lmax=lmax)
    topo.r0 = topo.coeffs[0, 0, 0]

    print('Topography file = {:s}'.format(topofile))
    print('Lmax of topography coefficients = {:d}'.format(topo.lmax))
    print('Reference radius (km) = {:f}\n'.format(topo.r0 / 1.e3))

    # --- read 1D reference interior model ---
    model_name = ['DWThot', 'DWThotCrust1', 'DWThotCrust1r', 'EH45Tcold',
                  'EH45TcoldCrust1', 'EH45TcoldCrust1r', 'EH45ThotCrust2',
                  'EH45ThotCrust2r', 'LFAK', 'SANAK', 'TAYAK', 'DWAK',
                  'ZG_DW']
    spec = 'Data/Mars-reference-interior-models/Smrekar/'
    interior_file = [spec + name + '.deck' for name in model_name]

    for file in interior_file:
        print('=== Reading model {:s} ==='.format(file))
        with open(file, 'r') as f:
            lines = f.readlines()
            print(lines[0].strip())
            data = lines[1].split()
            if float(data[2]) != 1:
                raise RuntimeError('Program not capable of reading polynomial ' +
                                   'files')
            num_file = int(lines[2].split()[0])
            crust_index_file = int(lines[2].split()[3])
            core_index_file = int(lines[2].split()[2])
            i_crust_file = crust_index_file - 1
            i_core_file = core_index_file - 1

            radius = np.zeros(num_file)
            rho = np.zeros(num_file)
            num = 0

            for i in range(0, num_file-1):
                data = lines[i+3].split()
                rb = float(data[0])
                rhob = float(data[1])
                data = lines[i+4].split()
                rt = float(data[0])
                rhot = float(data[1])

                if rb == rt:
                    if i == i_core_file:
                        i_core = num
                    if i == i_crust_file:
                        i_crust = num
                else:
                    radius[num] = rb
                    rho[num] = (rhot + rhob) / 2.
                    num += 1

            radius[num] = rt
            rho[num] = 0.  # the density above the surface is zero
            num += 1
            n = num - 1
            radius = radius[:n+1]
            rho = rho[:n+1]
            r0_model = radius[n]

            print('Surface radius of model (km) = {:f}'.format(r0_model / 1.e3))
            for i in range(0, n+1):
                if radius[i] <= (r0_model - d_lith) and \
                        radius[i+1] > (r0_model - d_lith):
                    if radius[i] == (r0_model - d_lith):
                        i_lith = i
                    elif (r0_model - d_lith) - radius[i] <= radius[i+1] -\
                            (r0_model - d_lith):
                        i_lith = i
                    else:
                        i_lith = i + 1
                    break

            rho_mantle = rho[i_crust-1]
            rho_core = rho[i_core-1]
            print('Mantle density (kg/m3) = {:f}'.format(rho_mantle))
            print('Mantle radius (km) = {:f}'.format(radius[i_crust]/1.e3))
            print('Core density (kg/m3) = {:f}'.format(rho_core))
            print('Core radius (km) = {:f}'.format(radius[i_core]/1.e3))

            print('Assumed depth of lithosphere (km) = {:f}'.format(d_lith / 1.e3))
            print('Actual depth of lithosphere in discretized model (km) = {:f}'
                  .format((r0_model - radius[i_lith]) / 1.e3))

            r_sigma = topo.r0 - d_sigma
            hlm, clm_hydro, mass_model = \
                HydrostaticShapeLith(radius, rho, i_lith, potential, topo,
                                     rho_crust, r_sigma, omega, lmax_hydro)
            print('Percentage of h20 derived from hydrostatic mantle = '
                  '{:f}'.format(clm_hydro.coeffs[0, 2, 0] /
                                potential.coeffs[0, 2, 0]*100))


    # --- read 1D reference interior model ---
    # --- From Rivoldini
    model_dir = 'Data/Mars-reference-interior-models/modelsMQS-2'
    models = os.listdir(model_dir)
    models.sort()

    pmin = 100
    pmax = 0

    for file in models:
        if os.path.splitext(file)[1] != '.dat':
            continue

        print('=== Reading model {:s} ==='.format(file))
        with open(os.path.join(model_dir, file), 'r') as f:
            lines = f.readlines()
            num = len(lines) - 4
            num_dis = num
            radius = np.zeros(num)
            rho = np.zeros(num)
            for i in range(0, num):
                data = lines[i+4].split()
                radius[i] = float(data[0])
                rho[i] = float(data[1])

            r0_model = radius[num-1]
            print('Surface radius of model (km) = {:f}'
                  .format(r0_model / 1.e3))

            for i in range(0, num):
                if radius[i] <= (r0_model - d_lith) and \
                        radius[i+1] > (r0_model - d_lith):
                    if radius[i] == (r0_model - d_lith):
                        i_lith = i
                    elif (r0_model - d_lith) - radius[i] <= radius[i+1] -\
                            (r0_model - d_lith):
                        i_lith = i
                    else:
                        i_lith = i + 1
                    break

            n = num - 1
            rho[n] = 0.  # the density above the surface is zero

            print('Assumed depth of lithosphere (km) = {:f}'
                  .format(d_lith / 1.e3))
            print('Actual depth of lithosphere in discretized model (km) = '
                  '{:f}'.format((r0_model - radius[i_lith]) / 1.e3))

            r_sigma = topo.r0 - d_sigma
            hlm, clm_hydro, mass_model = \
                HydrostaticShapeLith(radius, rho, i_lith, potential, topo,
                                     rho_crust, r_sigma, omega, lmax_hydro)
            percent = clm_hydro.coeffs[0, 2, 0] / potential.coeffs[0, 2, 0]*100
            print('Percentage of h20 derived from hydrostatic mantle = '
                  '{:f}'.format(percent))

            if percent > pmax:
                pmax = percent
            if percent < pmin:
                pmin = percent

    print(pmin, pmax)


# ==== EXECUTE SCRIPT ====


if __name__ == "__main__":
    main()
