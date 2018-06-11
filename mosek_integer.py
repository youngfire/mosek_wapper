import sys
import mosek
import mosek_g
# Since the actual value of Infinity is ignores, we define it solely
# for symbolic purposes:



class mosek_integerp(object):
    def __init__(self, params):
        self._INF = mosek_g.INF
        self.c_vector = params['c_vector']
        self.A_matrix = list(map(list, zip(*params['A_matrix'])))
        self.buc = params['buc']
        self.blc = params['blc']
        self.bux = params['bux']
        self.blx = params['blx']
        self.initial = params.get('initial', None)
        self.minimize = params.get('minimize', True)
        self.integ_index = params.get('integ_index', [])
        self.silent = params.get('silent', True)
        self.bkc = []
        self.bkx = []
        self.asub = []
        self.aval = []
        self.numcon = len(self.buc)
        self.numvar = len(self.bux)
        self.xx = None
        self.opti = None
        self.max_time = params.get('max_time', 60)
        

    def streamprinter(self, text):
        sys.stdout.write(text)
        sys.stdout.flush()

    def fit(self, ):
        with mosek.Env() as env:
            with env.Task(0, 0) as task:
                if self.silent is False:
                    task.set_Stream(mosek.streamtype.log, self.streamprinter)
                for i, j in zip(self.blc, self.buc):
                    if i <= -self._INF and j>= self._INF:
                        self.bkc.append(mosek.boundkey.fr)
                    elif i > -self._INF and j>= self._INF:
                        self.bkc.append(mosek.boundkey.lo)
                    elif i > -self._INF and j < self._INF:
                        self.bkc.append(mosek.boundkey.ra)
                    elif i <= -self._INF and j < self._INF:
                        self.bkc.append(mosek.boundkey.up)
                    elif i == j and i > -self._INF and j < self._INF:
                        self.bkc.append(mosek.boundkey.fx)
                for i, j in zip(self.blx, self.bux):
                    if i <= -self._INF and j>= self._INF:
                        self.bkx.append(mosek.boundkey.fr)
                    elif i > -self._INF and j>= self._INF:
                        self.bkx.append(mosek.boundkey.lo)
                    elif i > -self._INF and j < self._INF:
                        self.bkx.append(mosek.boundkey.ra)
                    elif i <= -self._INF and j < self._INF:
                        self.bkx.append(mosek.boundkey.up)
                    elif i == j and i > -self._INF and j < self._INF:
                        self.bkx.append(mosek.boundkey.fx)

                for A_vec in self.A_matrix:
                    asub_tmp = []
                    aval_tmp = []
                    for i, elm in enumerate(A_vec):
                        if elm != 0:
                            asub_tmp.append(i)
                            aval_tmp.append(float(elm))
                    self.asub.append(asub_tmp)
                    self.aval.append(aval_tmp)

                task.appendcons(self.numcon)
                task.appendvars(self.numvar)

                for i in range(self.numvar):
                    # Set the linear term c_i in the objective.
                    task.putcj(i, self.c_vector[i])
                    # Set the bounds on variable i
                    # blx[i] <= x_i <= bux[i]
                    task.putvarbound(i, self.bkx[i], self.blx[i], self.bux[i])
                    # Input column i of A
                    task.putacol(i, self.asub[i], self.aval[i])

                for i in range(self.numcon):
                    task.putconbound(i, self.bkc[i], self.blc[i], self.buc[i])

                if self.minimize is True:
                    task.putobjsense(mosek.objsense.minimize)
                else:
                    task.putobjsense(mosek.objsense.maximize)

                # Define variables to be integers
                # A list of variable indexes for which the variable type should be changed
                if len(self.integ_index)>0:
                    task.putvartypelist(self.integ_index, [mosek.variabletype.type_int] * len(self.integ_index))
                if self.initial:
                    # Construct an initial feasible solution from the
                    # values of the integer valuse specified
                    task.putintparam(mosek.iparam.mio_construct_sol, mosek.onoffkey.on)
                    # Assign values 0,2,0 to integer variables. Important to
                    # assign a value to all integer constrained variables.
                    task.putxxslice(mosek.soltype.itg, 0, len(self.initial), self.initial)
                # Set max solution time 
                task.putdouparam(mosek.dparam.mio_max_time, self.max_time);

                task.optimize()

                task.solutionsummary(mosek.streamtype.msg)
                prosta = task.getprosta(mosek.soltype.itg)
                solsta = task.getsolsta(mosek.soltype.itg)

                result = "Do not finished."
                if solsta in [mosek.solsta.integer_optimal, mosek.solsta.near_integer_optimal]:
                    self.xx = [0.] * self.numvar
                    task.getxx(mosek.soltype.itg, self.xx)
                    print("Optimal solution: %s" % self.xx)
                    result = {"x":self.xx}
                    return 0, result
                elif solsta == mosek.solsta.dual_infeas_cer:
                    result = "Primal or dual infeasibility."
                elif solsta == mosek.solsta.prim_infeas_cer:
                    result = "Primal or dual infeasibility."
                elif solsta == mosek.solsta.near_dual_infeas_cer:
                    result = "Primal or dual infeasibility."
                elif solsta == mosek.solsta.near_prim_infeas_cer:
                    result = "Primal or dual infeasibility."
                elif mosek.solsta.unknown:
                    if prosta == mosek.prosta.prim_infeas_or_unbounded:
                        result = "Problem status Infeasible or unbounded."
                    elif prosta == mosek.prosta.prim_infeas:
                        result = "Problem status Infeasible."
                    elif prosta == mosek.prosta.unkown:
                        result = "Problem status unkown."
                    else:
                        result = "Other problem status."
                else:
                    result = "Other solution sta."
                print(result)
                return -1, result

if __name__ == '__main__':
    params = {"c_vector"  : [7,10,1,5],
              "A_matrix"  : [[1,1,1,1]],
              "blc"  : [-mosek_g.INF],
              "buc"  : [2.5],
              "blx"  : [0,0,0,0],
              "bux"  : [mosek_g.INF, mosek_g.INF,mosek_g.INF,mosek_g.INF],
              "minimize" :False,
              "integ_index" :[0,1,2],
              "silent": False
            }
    a = mosek_integerp(params)
    a.fit()