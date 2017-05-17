import numpy as np
import matplotlib.pyplot as plt

# evenly sampled time at 200ms intervals
t = np.arange(0., 50., 0.2)

# red dashes, blue squares and green triangles
plt.plot(t, 100 + 1400*2.7**(-t), 'r', 100 + 1400*2.7**(-t/2), 'b', 100 + 1400*2.7**(-t/4), 'g')
plt.show()