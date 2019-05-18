from __future__ import division, print_function
import time
import mmtbx.model
import iotbx.pdb
from libtbx.utils import null_out
from libtbx.test_utils import approx_equal

import cctbx.geometry_restraints.process_nonbonded_proxies as pnp



def obtain_model(raw_records):
  '''
  Helper function to obtain model class from raw records
  '''
  params = mmtbx.model.manager.get_default_pdb_interpretation_params()
  params.pdb_interpretation.allow_polymer_cross_special_position=True
  pdb_inp = iotbx.pdb.input(lines=raw_records.split("\n"), source_info=None)
  model = mmtbx.model.manager(
    model_input = pdb_inp,
    pdb_interpretation_params = params,
    build_grm   = True,
    log         = null_out())
  return model


def get_clashes_result(raw_records):
  '''
  Helper function to get clashes results from raw records
  '''
  params = mmtbx.model.manager.get_default_pdb_interpretation_params()
  params.pdb_interpretation.allow_polymer_cross_special_position=True
  params.pdb_interpretation.clash_guard.nonbonded_distance_threshold = None
  pdb_inp = iotbx.pdb.input(lines=raw_records.split("\n"), source_info=None)
  model = mmtbx.model.manager(
    model_input = pdb_inp,
    pdb_interpretation_params = params,
    build_grm   = True,
    log         = null_out())
  pnps = pnp.manager(model = model)
  clashes = pnps.get_clashes()
  return clashes


def test_overlap_atoms():
  '''
  Test that overlapping atoms are being counted
  '''
  clashes = get_clashes_result(raw_records=raw_records_5)
  results = clashes.get_results()
  assert(results.n_clashes == 6), 'Overlapping atoms are not counted properly.'
  assert(results.clashscore == 1500), 'Clashscore is wrong'


def test_inline_overlaps():
  '''
  Test non-bonded overlaps of C with H-C.
  Check when valid overlaps and when it's considered to be inline

  - test when all are in the same residue
  - test when C and H-C are in different residues
  '''
  clashes = get_clashes_result(raw_records=raw_records_2)
  results = clashes.get_results()
  assert(results.n_clashes == 4), 'Total nonbonded overlaps are incorrect.'
  assert approx_equal(results.clashscore, 85.11, eps=0.1), 'Wrong clashscore.'


def test_vdw_dist():
  '''
  Test that overlaps are identified properly

  Test overlaps that are set to be on the limit of the
  overlap distance 0.40

  Test evaluation of vdw distances. if the parameters
  1)  assume_hydrogens_all_missing=False
  2)  hard_minimum_nonbonded_distance=0.0
  are not set properly, the number of overlaps will change
  '''

  clashes = get_clashes_result(raw_records=raw_records_0)
  results = clashes.get_results()
  assert(results.n_clashes == 2)
  assert approx_equal(results.clashscore, 38.46, eps=0.1)
  assert(results.n_clashes_sym == 2)
  assert approx_equal(results.clashscore_sym, 38.46, eps=0.1)
  assert(results.n_clashes_macro_mol == 0)
  assert(results.clashscore_macro_mol == 0)

  clashes = get_clashes_result(raw_records=raw_records_1)
  results = clashes.get_results()
  assert(results.n_clashes == 4)
  assert approx_equal(results.clashscore, 28.77, eps=0.1)
  assert(results.n_clashes_sym == 0)
  assert approx_equal(results.clashscore_sym, 0, eps=0.1)
  assert(results.n_clashes_macro_mol == 4)
  assert approx_equal(results.clashscore_macro_mol, 28.77, eps=0.1)


def test_inline_angle():
  '''
  Test cos_vec(u,v)
  '''
  u = (40.196,3.261,-48.474)
  v = (39.466,4.279,-52.202)
  w = (37.407,5.077,-51.025)
  result = pnp.cos_vec(u, v, w)
  expected = 0.5072
  msg = 'The difference is: {}'.format(result - expected)
  assert approx_equal(result, expected, eps=0.001), msg


def test_1_5_overlaps():
  '''
  Test if 1_5 overlaps are correctly identified
  '''
  model = obtain_model(raw_records_0)
  hd_sel = model.get_hd_selection()
  grm = model.get_restraints_manager().geometry
  full_connectivity_table = grm.shell_sym_tables[0].full_simple_connectivity()

  outstring = '1-5 Interaction test error. {}'
  # check that direction of function calling does not matter
  tst = pnp.check_if_1_5_interaction(21, 33,hd_sel,full_connectivity_table)
  msg = 'Test results depend on atoms order'
  assert(tst), msg
  tst = pnp.check_if_1_5_interaction(33, 21,hd_sel,full_connectivity_table)
  assert(tst), msg
  # check 1-4 interaction
  tst = pnp.check_if_1_5_interaction(33, 20,hd_sel,full_connectivity_table)
  msg = 'Test fails on 1-4 interaction'
  assert(not tst), msg
  # check 1-6 interaction
  tst = pnp.check_if_1_5_interaction(33, 38,hd_sel,full_connectivity_table)
  msg = 'Test fails on 1-6 interaction'
  assert(not tst), msg
  # 1-5 interaction of atoms other than hydrogen
  tst = pnp.check_if_1_5_interaction(38, 25,hd_sel,full_connectivity_table)
  msg = 'Test fails on 1-5 non hydrogen interaction'
  assert(not tst), msg
  # 1-5 interaction of two hydrogens
  tst = pnp.check_if_1_5_interaction(33, 31,hd_sel,full_connectivity_table)
  msg = 'Test fails on 1-5 two hydrogen interaction'
  assert(not tst), msg


raw_records_0 = """
CRYST1   80.020   97.150   49.850  90.00  90.00  90.00 C 2 2 21
ATOM   1271  N   ILE A  83      31.347   4.310 -43.960  1.00  9.97           N
ATOM   1272  CA  ILE A  83      32.076   3.503 -44.918  1.00 19.49           C
ATOM   1273  C   ILE A  83      32.062   4.261 -46.243  1.00 15.26           C
ATOM   1274  O   ILE A  83      31.006   4.660 -46.740  1.00 16.12           O
ATOM   1275  CB  ILE A  83      31.486   2.080 -45.048  1.00 18.05           C
ATOM   1276  CG1 ILE A  83      32.328   1.263 -46.027  1.00 17.98           C
ATOM   1277  CG2 ILE A  83      30.020   2.134 -45.469  1.00 28.62           C
ATOM   1278  CD1 ILE A  83      32.130  -0.226 -45.888  1.00 38.88           C
ATOM   1279  H   ILE A  83      30.735   4.798 -44.316  1.00  9.97           H
ATOM   1280  HA  ILE A  83      32.999   3.421 -44.630  1.00 19.49           H
ATOM   1281  HB  ILE A  83      31.534   1.655 -44.178  1.00 18.05           H
ATOM   1282 HG12 ILE A  83      32.087   1.512 -46.933  1.00 17.98           H
ATOM   1283 HG13 ILE A  83      33.266   1.454 -45.871  1.00 17.98           H
ATOM   1284 HG21 ILE A  83      29.627   1.256 -45.347  1.00 28.62           H
ATOM   1285 HG22 ILE A  83      29.554   2.783 -44.919  1.00 28.62           H
ATOM   1286 HG23 ILE A  83      29.967   2.392 -46.402  1.00 28.62           H
ATOM   1287 HD11 ILE A  83      33.003  -0.644 -45.858  1.00 38.88           H
ATOM   1288 HD12 ILE A  83      31.654  -0.404 -45.062  1.00 38.88           H
ATOM   1289 HD13 ILE A  83      31.608  -0.541 -46.640  1.00 38.88           H
ATOM   1290  N   ILE A  84      33.252   4.542 -46.758  1.00 11.36           N
ATOM   1291  CA  ILE A  84      33.381   5.290 -47.993  1.00  9.27           C
ATOM   1292  C   ILE A  84      33.906   4.417 -49.101  1.00 11.06           C
ATOM   1293  O   ILE A  84      34.881   3.694 -48.921  1.00 14.52           O
ATOM   1294  CB  ILE A  84      34.308   6.508 -47.813  1.00 11.89           C
ATOM   1295  CG1 ILE A  84      33.730   7.436 -46.746  1.00  9.03           C
ATOM   1296  CG2 ILE A  84      34.471   7.257 -49.132  1.00 10.52           C
ATOM   1297  CD1 ILE A  84      34.436   8.761 -46.632  1.00 12.96           C
ATOM   1298  H   ILE A  84      34.002   4.308 -46.408  1.00 11.36           H
ATOM   1299  HA  ILE A  84      32.515   5.625 -48.269  1.00  9.27           H
ATOM   1300  HB  ILE A  84      35.179   6.198 -47.520  1.00 11.89           H
ATOM   1301 HG12 ILE A  84      32.800   7.587 -46.942  1.00  9.03           H
ATOM   1302 HG13 ILE A  84      33.808   6.995 -45.886  1.00  9.03           H
ATOM   1303 HG21 ILE A  84      35.193   7.898 -49.045  1.00 10.52           H
ATOM   1304 HG22 ILE A  84      34.688   6.643 -49.848  1.00 10.52           H
ATOM   1305 HG23 ILE A  84      33.642   7.718 -49.335  1.00 10.52           H
ATOM   1306 HD11 ILE A  84      33.911   9.335 -46.052  1.00 12.96           H
ATOM   1307 HD12 ILE A  84      35.300   8.606 -46.229  1.00 12.96           H
ATOM   1308 HD13 ILE A  84      34.530   9.185 -47.497  1.00 12.96           H
ATOM   1309  N   THR A  85      33.228   4.470 -50.242  1.00 17.41           N
ATOM   1310  CA  THR A  85      33.615   3.692 -51.411  1.00 14.87           C
ATOM   1311  C   THR A  85      33.743   4.584 -52.633  1.00 15.68           C
ATOM   1312  O   THR A  85      33.232   5.702 -52.660  1.00 10.37           O
ATOM   1313  CB  THR A  85      32.581   2.585 -51.737  1.00 13.04           C
ATOM   1314  OG1 THR A  85      31.285   3.169 -51.914  1.00 19.63           O
ATOM   1315  CG2 THR A  85      32.524   1.546 -50.626  1.00 14.50           C
ATOM   1316  H   THR A  85      32.530   4.957 -50.365  1.00 17.41           H
ATOM   1317  HA  THR A  85      34.473   3.268 -51.259  1.00 14.87           H
ATOM   1318  HB  THR A  85      32.872   2.178 -52.553  1.00 13.04           H
ATOM   1319  HG1 THR A  85      31.049   3.564 -51.211  1.00 19.63           H
ATOM   1320 HG21 THR A  85      32.000   0.780 -50.908  1.00 14.50           H
ATOM   1321 HG22 THR A  85      33.420   1.251 -50.402  1.00 14.50           H
ATOM   1322 HG23 THR A  85      32.116   1.932 -49.835  1.00 14.50           H
"""

raw_records_1 = """\
CRYST1   80.020   97.150   49.850  90.00  90.00  90.00 C 2 2 21
HETATM 1819  N   NPH A 117      23.870  15.268 -50.490  1.00 25.06           N
HETATM 1820  CA  NPH A 117      23.515  14.664 -49.210  1.00 22.94           C
HETATM 1821  CB  NPH A 117      23.658  15.702 -48.113  1.00 21.44           C
HETATM 1822  SG  NPH A 117      25.281  16.410 -47.839  1.00 31.29           S
HETATM 1823  CD  NPH A 117      25.498  16.310 -46.059  0.50 33.70           C
HETATM 1824  CE  NPH A 117      26.971  16.492 -45.820  0.50 39.92           C
HETATM 1825  OZ  NPH A 117      27.815  15.348 -45.806  0.50 43.26           O
HETATM 1826  NZ  NPH A 117      27.411  17.709 -45.649  0.50 43.87           N
HETATM 1827  C6  NPH A 117      28.830  18.015 -45.436  0.50 51.14           C
HETATM 1828  C5  NPH A 117      29.800  17.009 -45.411  0.50 51.26           C
HETATM 1829  C6A NPH A 117      29.195  19.344 -45.262  0.50 52.54           C
HETATM 1830  C4A NPH A 117      31.137  17.332 -45.219  0.50 52.42           C
HETATM 1831  C10 NPH A 117      30.543  19.684 -45.064  0.50 54.23           C
HETATM 1832  C7  NPH A 117      28.201  20.331 -45.288  0.50 53.28           C
HETATM 1833  C4  NPH A 117      32.087  16.314 -45.202  0.50 53.40           C
HETATM 1834  C1A NPH A 117      31.522  18.669 -45.046  0.50 55.19           C
HETATM 1835  N10 NPH A 117      30.892  21.027 -44.889  0.50 53.87           N
HETATM 1836  C8  NPH A 117      28.549  21.670 -45.111  0.50 54.83           C
HETATM 1837  C3  NPH A 117      33.439  16.599 -45.020  0.50 53.96           C
HETATM 1838  N1  NPH A 117      32.879  18.963 -44.861  0.50 57.78           N
HETATM 1839  C9  NPH A 117      29.889  22.011 -44.911  0.50 55.29           C
HETATM 1840  C2  NPH A 117      33.832  17.924 -44.852  0.50 55.79           C
HETATM 1841  C   NPH A 117      22.061  14.206 -49.245  1.00 23.82           C
HETATM 1842  O   NPH A 117      21.158  15.023 -49.423  1.00 24.62           O
HETATM 1843  HZ  NPH A 117      26.743  18.445 -45.689  0.50 43.87           H
HETATM 1844  HD3 NPH A 117      24.961  17.137 -45.534  0.50 33.70           H
HETATM 1845  HD2 NPH A 117      25.185  15.321 -45.644  0.50 33.70           H
HETATM 1846  HC2 NPH A 117      34.904  18.122 -44.711  0.50 55.79           H
HETATM 1847  HB3 NPH A 117      22.975  16.550 -48.341  1.00 21.44           H
HETATM 1848  HB2 NPH A 117      23.315  15.232 -47.181  1.00 21.44           H
HETATM 1849  H9  NPH A 117      30.113  23.063 -44.748  0.50 55.29           H
HETATM 1850  H8  NPH A 117      27.786  22.458 -45.117  0.50 54.83           H
HETATM 1851  H7  NPH A 117      27.137  20.098 -45.429  0.50 53.28           H
HETATM 1852  H5  NPH A 117      29.623  15.938 -45.543  0.50 51.26           H
HETATM 1853  H4  NPH A 117      31.708  15.307 -45.324  0.50 53.40           H
HETATM 1854  H3  NPH A 117      34.196  15.804 -45.008  0.50 53.96           H
ATOM   1855  N   VAL A 118      21.831  12.913 -49.037  1.00 28.67           N
ATOM   1856  CA  VAL A 118      20.474  12.371 -49.062  1.00 33.96           C
ATOM   1857  C   VAL A 118      20.069  11.729 -47.737  1.00 36.17           C
ATOM   1858  O   VAL A 118      20.854  11.018 -47.109  1.00 40.12           O
ATOM   1859  CB  VAL A 118      20.297  11.336 -50.209  1.00 39.91           C
ATOM   1860  CG1 VAL A 118      18.831  10.915 -50.336  1.00 38.68           C
ATOM   1861  CG2 VAL A 118      20.791  11.918 -51.524  1.00 43.67           C
ATOM   1862  H   VAL A 118      22.442  12.328 -48.879  1.00 28.67           H
ATOM   1863  HA  VAL A 118      19.848  13.087 -49.232  1.00 33.96           H
ATOM   1864  HB  VAL A 118      20.823  10.546 -50.010  1.00 39.91           H
ATOM   1865 HG11 VAL A 118      18.723  10.392 -51.146  1.00 38.68           H
ATOM   1866 HG12 VAL A 118      18.585  10.381 -49.564  1.00 38.68           H
ATOM   1867 HG13 VAL A 118      18.277  11.710 -50.381  1.00 38.68           H
ATOM   1868 HG21 VAL A 118      20.576  11.302 -52.242  1.00 43.67           H
ATOM   1869 HG22 VAL A 118      20.352  12.770 -51.676  1.00 43.67           H
ATOM   1870 HG23 VAL A 118      21.751  12.045 -51.474  1.00 43.67           H
ATOM   1871  N   MET A 119      18.829  11.986 -47.328  1.00 39.11           N
ATOM   1872  CA  MET A 119      18.273  11.449 -46.092  1.00 39.84           C
ATOM   1873  C   MET A 119      16.761  11.361 -46.256  1.00 45.51           C
ATOM   1874  O   MET A 119      16.066  12.375 -46.173  1.00 45.08           O
ATOM   1875  CB  MET A 119      18.616  12.370 -44.916  1.00 46.77           C
ATOM   1876  CG  MET A 119      19.314  11.688 -43.740  1.00 45.80           C
ATOM   1877  SD  MET A 119      18.225  10.980 -42.492  1.00 41.41           S
ATOM   1878  CE  MET A 119      17.987   9.359 -43.118  1.00 44.09           C
ATOM   1879  H   MET A 119      18.277  12.482 -47.762  1.00 39.11           H
ATOM   1880  HA  MET A 119      18.637  10.566 -45.922  1.00 39.84           H
ATOM   1881  HB2 MET A 119      19.202  13.071 -45.238  1.00 46.77           H
ATOM   1882  HB3 MET A 119      17.801  12.765 -44.571  1.00 46.77           H
ATOM   1883  HG2 MET A 119      19.854  10.965 -44.091  1.00 45.80           H
ATOM   1884  HG3 MET A 119      19.885  12.336 -43.300  1.00 45.80           H
ATOM   1885  HE1 MET A 119      17.086   9.072 -42.908  1.00 44.09           H
ATOM   1886  HE2 MET A 119      18.121   9.364 -44.078  1.00 44.09           H
ATOM   1887  HE3 MET A 119      18.627   8.768 -42.693  1.00 44.09           H
ATOM   1888  N   LYS A 120      16.265  10.152 -46.521  1.00 52.01           N
ATOM   1889  CA  LYS A 120      14.834   9.908 -46.706  1.00 55.50           C
ATOM   1890  C   LYS A 120      14.220  10.827 -47.764  1.00 61.07           C
ATOM   1891  O   LYS A 120      13.324  11.621 -47.467  1.00 63.20           O
ATOM   1892  CB  LYS A 120      14.079  10.073 -45.381  1.00 57.57           C
ATOM   1893  CG  LYS A 120      14.393   9.026 -44.324  1.00 62.80           C
ATOM   1894  CD  LYS A 120      13.804   9.426 -42.977  1.00 66.61           C
ATOM   1895  CE  LYS A 120      14.483  10.683 -42.438  1.00 72.33           C
ATOM   1896  NZ  LYS A 120      13.902  11.173 -41.155  1.00 69.78           N
ATOM   1897  H   LYS A 120      16.747   9.444 -46.600  1.00 52.01           H
ATOM   1898  HA  LYS A 120      14.711   8.993 -47.004  1.00 55.50           H
ATOM   1899  HB2 LYS A 120      14.293  10.951 -45.043  1.00 57.57           H
ATOM   1900  HB3 LYS A 120      13.127  10.019 -45.560  1.00 57.57           H
ATOM   1901  HG2 LYS A 120      14.005   8.177 -44.587  1.00 62.80           H
ATOM   1902  HG3 LYS A 120      15.354   8.943 -44.230  1.00 62.80           H
ATOM   1903  HD2 LYS A 120      12.857   9.611 -43.082  1.00 66.61           H
ATOM   1904  HD3 LYS A 120      13.940   8.707 -42.340  1.00 66.61           H
ATOM   1905  HE2 LYS A 120      15.421  10.490 -42.285  1.00 72.33           H
ATOM   1906  HE3 LYS A 120      14.396  11.408 -43.068  1.00 72.33           H
ATOM   1907  HZ1 LYS A 120      14.332  11.905 -40.886  1.00 69.78           H
ATOM   1908  HZ2 LYS A 120      13.041  11.368 -41.266  1.00 69.78           H
ATOM   1909  HZ3 LYS A 120      13.977  10.546 -40.528  1.00 69.78           H
ATOM   1910  N   GLY A 121      14.729  10.739 -48.990  1.00 62.98           N
ATOM   1911  CA  GLY A 121      14.207  11.559 -50.072  1.00 61.51           C
ATOM   1912  C   GLY A 121      14.804  12.947 -50.225  1.00 57.12           C
ATOM   1913  O   GLY A 121      15.145  13.351 -51.339  1.00 61.31           O
ATOM   1914  H   GLY A 121      15.372  10.216 -49.218  1.00 62.98           H
ATOM   1915  HA2 GLY A 121      14.350  11.088 -50.908  1.00 61.51           H
ATOM   1916  HA3 GLY A 121      13.250  11.662 -49.955  1.00 61.51           H
ATOM   1917  N   VAL A 122      14.909  13.687 -49.123  1.00 48.05           N
ATOM   1918  CA  VAL A 122      15.464  15.042 -49.144  1.00 40.46           C
ATOM   1919  C   VAL A 122      16.907  15.047 -49.643  1.00 37.52           C
ATOM   1920  O   VAL A 122      17.717  14.230 -49.217  1.00 47.57           O
ATOM   1921  CB  VAL A 122      15.397  15.699 -47.740  1.00 38.05           C
ATOM   1922  CG1 VAL A 122      16.099  17.054 -47.747  1.00 31.26           C
ATOM   1923  CG2 VAL A 122      13.940  15.863 -47.312  1.00 35.36           C
ATOM   1924  H   VAL A 122      14.663  13.425 -48.342  1.00 48.05           H
ATOM   1925  HA  VAL A 122      14.938  15.586 -49.751  1.00 40.46           H
ATOM   1926  HB  VAL A 122      15.842  15.127 -47.095  1.00 38.05           H
ATOM   1927 HG11 VAL A 122      15.813  17.560 -46.970  1.00 31.26           H
ATOM   1928 HG12 VAL A 122      17.059  16.917 -47.715  1.00 31.26           H
ATOM   1929 HG13 VAL A 122      15.857  17.530 -48.557  1.00 31.26           H
ATOM   1930 HG21 VAL A 122      13.910  16.341 -46.469  1.00 35.36           H
ATOM   1931 HG22 VAL A 122      13.466  16.365 -47.994  1.00 35.36           H
ATOM   1932 HG23 VAL A 122      13.540  14.985 -47.210  1.00 35.36           H
ATOM   1933  N   THR A 123      17.222  15.963 -50.553  1.00 32.61           N
ATOM   1934  CA  THR A 123      18.571  16.046 -51.098  1.00 28.67           C
ATOM   1935  C   THR A 123      19.130  17.463 -51.045  1.00 29.81           C
ATOM   1936  O   THR A 123      18.492  18.416 -51.489  1.00 32.53           O
ATOM   1937  CB  THR A 123      18.627  15.533 -52.561  1.00 29.86           C
ATOM   1938  OG1 THR A 123      18.176  14.175 -52.612  1.00 31.25           O
ATOM   1939  CG2 THR A 123      20.054  15.598 -53.103  1.00 32.10           C
ATOM   1940  H   THR A 123      16.675  16.546 -50.870  1.00 32.61           H
ATOM   1941  HA  THR A 123      19.160  15.485 -50.579  1.00 28.67           H
ATOM   1942  HB  THR A 123      18.059  16.085 -53.121  1.00 29.86           H
ATOM   1943  HG1 THR A 123      18.204  13.892 -53.403  1.00 31.25           H
ATOM   1944 HG21 THR A 123      20.120  15.079 -53.920  1.00 32.10           H
ATOM   1945 HG22 THR A 123      20.298  16.517 -53.295  1.00 32.10           H
ATOM   1946 HG23 THR A 123      20.673  15.236 -52.450  1.00 32.10           H
ATOM   1947  N   SER A 124      20.324  17.583 -50.480  1.00 25.77           N
ATOM   1948  CA  SER A 124      21.012  18.858 -50.362  1.00 25.34           C
ATOM   1949  C   SER A 124      22.166  18.863 -51.358  1.00 23.45           C
ATOM   1950  O   SER A 124      22.899  17.881 -51.477  1.00 26.73           O
ATOM   1951  CB  SER A 124      21.543  19.037 -48.938  1.00 24.00           C
ATOM   1952  OG  SER A 124      22.400  20.159 -48.851  1.00 27.42           O
ATOM   1953  H   SER A 124      20.766  16.923 -50.150  1.00 25.77           H
ATOM   1954  HA  SER A 124      20.410  19.588 -50.567  1.00 25.34           H
ATOM   1955  HB2 SER A 124      20.793  19.168 -48.338  1.00 24.00           H
ATOM   1956  HB3 SER A 124      22.034  18.250 -48.682  1.00 24.00           H
ATOM   1957  HG  SER A 124      21.984  20.856 -49.068  1.00 27.42           H
"""

raw_records_2 = '''
CRYST1   80.020   97.150   49.850  90.00  90.00  90.00 C 2 2 21
HETATM 1819  N   NPH A 117      24.064  15.944 -50.623  1.00 25.06           N
HETATM 1820  CA  NPH A 117      23.709  15.340 -49.343  1.00 22.94           C
HETATM 1821  CB  NPH A 117      23.852  16.378 -48.246  1.00 21.44           C
HETATM 1822  SG  NPH A 117      25.475  17.086 -47.972  1.00 31.29           S
HETATM 1823  CD  NPH A 117      25.692  16.986 -46.192  0.50 33.70           C
HETATM 1824  CE  NPH A 117      27.165  17.168 -45.953  0.50 39.92           C
HETATM 1825  OZ  NPH A 117      28.009  16.024 -45.939  0.50 43.26           O
HETATM 1826  NZ  NPH A 117      27.605  18.385 -45.782  0.50 43.87           N
HETATM 1827  C6  NPH A 117      29.024  18.691 -45.569  0.50 51.14           C
HETATM 1828  C5  NPH A 117      29.994  17.685 -45.544  0.50 51.26           C
HETATM 1829  C6A NPH A 117      29.389  20.020 -45.395  0.50 52.54           C
HETATM 1830  C4A NPH A 117      31.331  18.008 -45.352  0.50 52.42           C
HETATM 1831  C10 NPH A 117      30.737  20.360 -45.197  0.50 54.23           C
HETATM 1832  C7  NPH A 117      28.395  21.007 -45.421  0.50 53.28           C
HETATM 1833  C4  NPH A 117      32.281  16.990 -45.335  0.50 53.40           C
HETATM 1834  C1A NPH A 117      31.716  19.345 -45.179  0.50 55.19           C
HETATM 1835  N10 NPH A 117      31.086  21.703 -45.022  0.50 53.87           N
HETATM 1836  C8  NPH A 117      28.743  22.346 -45.244  0.50 54.83           C
HETATM 1837  C3  NPH A 117      33.633  17.275 -45.153  0.50 53.96           C
HETATM 1838  N1  NPH A 117      33.073  19.639 -44.994  0.50 57.78           N
HETATM 1839  C9  NPH A 117      30.083  22.687 -45.044  0.50 55.29           C
HETATM 1840  C2  NPH A 117      34.026  18.600 -44.985  0.50 55.79           C
HETATM 1841  C   NPH A 117      22.255  14.882 -49.378  1.00 23.82           C
HETATM 1842  O   NPH A 117      21.352  15.699 -49.556  1.00 24.62           O
HETATM 1843  HZ  NPH A 117      26.937  19.121 -45.822  0.50 43.87           H
HETATM 1844  HD3 NPH A 117      25.155  17.813 -45.667  0.50 33.70           H
HETATM 1845  HD2 NPH A 117      25.379  15.997 -45.777  0.50 33.70           H
HETATM 1846  HC2 NPH A 117      35.098  18.798 -44.844  0.50 55.79           H
HETATM 1847  HB3 NPH A 117      23.169  17.226 -48.474  1.00 21.44           H
HETATM 1848  HB2 NPH A 117      23.509  15.908 -47.314  1.00 21.44           H
HETATM 1849  H9  NPH A 117      30.307  23.739 -44.881  0.50 55.29           H
HETATM 1850  H8  NPH A 117      27.980  23.134 -45.250  0.50 54.83           H
HETATM 1851  H7  NPH A 117      27.331  20.774 -45.562  0.50 53.28           H
HETATM 1852  H5  NPH A 117      29.817  16.614 -45.676  0.50 51.26           H
HETATM 1853  H4  NPH A 117      31.902  15.983 -45.457  0.50 53.40           H
HETATM 1854  H3  NPH A 117      34.390  16.480 -45.141  0.50 53.96           H
ATOM   1947  N   SER B 124      20.843  16.929 -50.266  1.00 25.77           N
ATOM   1948  CA  SER B 124      21.084  18.355 -50.408  1.00 25.34           C
ATOM   1949  C   SER B 124      22.267  18.540 -51.353  1.00 23.45           C
ATOM   1950  O   SER B 124      23.277  17.846 -51.239  1.00 26.73           O
ATOM   1951  CB  SER B 124      21.398  18.973 -49.044  1.00 24.00           C
ATOM   1952  OG  SER B 124      21.849  20.306 -49.179  1.00 27.42           O
ATOM   1953  H   SER B 124      21.437  16.527 -49.790  1.00 25.77           H
ATOM   1954  HA  SER B 124      20.306  18.795 -50.781  1.00 25.34           H
ATOM   1955  HB2 SER B 124      20.592  18.968 -48.505  1.00 24.00           H
ATOM   1956  HB3 SER B 124      22.084  18.454 -48.612  1.00 24.00           H
ATOM   1957  HG  SER B 124      21.258  20.773 -49.552  1.00 27.42           H
'''

raw_records_5 = """
CRYST1   20.000   20.000   20.000  90.00  90.00  90.00 P 1
ATOM      1  N   LYS     1       5.000   5.000   5.000  1.00 20.00           N
ATOM      1  N   LYS     2       6.000   5.000   5.000  1.00 20.00           N
ATOM      1  N   LYS     3       5.000   5.500   5.500  1.00 20.00           N
ATOM      1  N   LYS     4       5.000   5.500   5.500  1.00 20.00           N
"""


if (__name__ == "__main__"):
  t0 = time.time()
  test_1_5_overlaps()
  test_inline_angle()
  test_inline_overlaps()
  test_overlap_atoms()
  test_vdw_dist()
  print("OK. Time: %8.3f"%(time.time()-t0))