# Known-Sigma (protected) omnibus noncentrality: lambda = d' C' (C S C')^+ C d, C = centering on n=9 channels.
# Channel 0 = ON (its own cluster); channels 1..8 = controls in clusters of size c. Marginal variance fixed at v+tau^2.
import numpy as np
v,tau,s=10.,3.,10.; n=9
def Sigma(rho,c):
    S=v*np.eye(n)+tau**2*rho*np.ones((n,n))
    B=np.zeros((n,n)); B[0,0]=1
    for g in range(0,8,c): B[1+g:1+g+c,1+g:1+g+c]=1
    return S+tau**2*(1-rho)*B
C=np.eye(n)-np.ones((n,n))/n
def lam(S,d): O=C@S@C.T; z=C@d; return float(z@np.linalg.pinv(O,rcond=1e-10)@z)
on=np.zeros(n); on[0]=s
aligned=on.copy(); aligned[1:5]+=s           # shift one whole cluster of 4
mis=on.copy(); mis[[1,2,5,6]]+=s             # shift 2 controls in each of two clusters
print("rho  c | plain(ON only) | aligned r=4 | misaligned r=4")
for rho in (0.,.5,.9):
    for c in (1,2,4):
        S=Sigma(rho,c); print(f"{rho:.1f}  {c} | {lam(S,on):7.2f}        | {lam(S,aligned):7.2f}     | {lam(S,mis):7.2f}")
