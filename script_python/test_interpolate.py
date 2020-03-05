import numpy as np
import scipy as sc
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d

# x = np.linspace(0, 4, 12)
# y = np.cos(x ** 2 / 3 + 4)
# print(x)
# print(y)
#
# plt.plot(x, y, 'o')
# plt.show()
#
# print("----------------")
# f1 = sc.interpolate.interp1d(x, y, kind='linear')
# f2 = sc.interpolate.interp1d(x, y, kind='cubic')
# xnew = np.linspace(0, 4, 30)
# plt.plot(x, y, 'o', xnew, f1(xnew), '-', xnew, f2(xnew), '--')
# plt.legend(['data', 'linear', 'cubic', 'nearest'], loc='best')
# plt.show()
print("----------------")
x = np.linspace(-3, 3, 50)
y = np.exp(-x ** 2) + 0.1 * np.random.rand(50)
plt.plot(x, y, 'ro', ms=5)

spl = sc.interpolate.UnivariateSpline(x, y)
xs = np.linspace(-3, 3, 1000)
# plt.plot(xs, spl(xs), 'g', lw=3)

spl.set_smoothing_factor(0.1)
plt.plot(xs, spl(xs), 'b', lw=3)

# f2 = sc.interpolate.interp1d(x, y, kind='cubic')
# plt.plot(xs, 'g', f2(xs), '--')
plt.show()
print("_--------------------")

f1 = sc.interpolate.interp1d(x, y, kind='linear')
f2 = sc.interpolate.interp1d(x, y, kind='cubic')
alpha = np.linspace(-3, 3, 20)

plt.plot(x, y, 'o')
plt.plot(alpha, f1(alpha), '-')
plt.plot(alpha, f2(alpha), '--')
plt.legend(['data', 'linear', 'cubic', 'nearest'], loc='best')
plt.xlabel('x')
plt.ylabel('y')
plt.show()
