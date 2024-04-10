import os
import numpy as np
import matplotlib.pyplot as plt
from sklearn.mixture import GaussianMixture
from sklearn.svm import SVC
from matplotlib.patches import Ellipse
from properties import resultspath

""" Script to create the Discriminative vs Generative AI image """

# Create a folder to store the results if it doesn't exist
results_folder = os.path.join(resultspath, 'images') 
os.makedirs(results_folder, exist_ok=True)

def draw_ellipse(position, covariance, ax=None, color='darkblue', alpha=0.2):
   ax = ax or plt.gca()
   U, s, Vt = np.linalg.svd(covariance)
   angle = np.degrees(np.arctan2(U[1, 0], U[0, 0]))
   width, height = 2 * np.sqrt(s)
   for nsig in range(1, 4):
      ax.add_patch(Ellipse(position, nsig * width, nsig * height, angle, color=color, alpha=alpha, edgecolor='black'))

random_state = np.random.RandomState(66)
n_samples = 200
cov = [[1.4, 0.3], [0.3, 1.2]]
cov2 = [[0.8, -0.3], [-0.5, 1.2]]
mean1, mean2 = [2, 2], [-2, -2]
x1 = random_state.multivariate_normal(mean1, cov, n_samples)
x2 = random_state.multivariate_normal(mean2, cov2, n_samples)
X = np.vstack([x1, x2])
y = np.hstack([np.zeros(n_samples), np.ones(n_samples)])

gmm = GaussianMixture(n_components=2, covariance_type='full', random_state=50).fit(X)
svc = SVC(kernel='linear').fit(X, y)

xx, yy = np.meshgrid(np.linspace(X[:, 0].min() - 1, X[:, 0].max() + 1, 100), np.linspace(X[:, 1].min() - 1, X[:, 1].max() + 1, 100))
Z_svc = svc.decision_function(np.c_[xx.ravel(), yy.ravel()]).reshape(xx.shape)

fig, axs = plt.subplots(1, 2, figsize=(8, 4))
axs[0].contourf(xx, yy, Z_svc, levels=[Z_svc.min(), 0, Z_svc.max()], cmap='coolwarm', alpha=0.2)
axs[0].contour(xx, yy, Z_svc, levels=[0], colors='black', linewidths=2)

# Use GMM labels to color points consistently
labels = gmm.predict(X)
colors = ['darkblue' if label == 0 else 'orange' for label in labels]

axs[1].scatter(X[:, 0], X[:, 1], c=colors, s=10)

for ax in axs:
   ax.set_xticks([])
   ax.set_yticks([])
   for spine in ax.spines.values():
      spine.set_visible(True)
      spine.set_linewidth(1.5)

axs[0].scatter(x1[:, 0], x1[:, 1], color='darkblue', s=10)
axs[0].scatter(x2[:, 0], x2[:, 1], color='orange', s=10)

axs[1].set_title('Γενετικό Μοντέλο')
axs[0].set_title('Διακριτικό Μοντέλο')

# Adjust eclipse colors based on the cluster means to match scatter plot colors
for i, (pos, covar, w) in enumerate(zip(gmm.means_, gmm.covariances_, gmm.weights_)):
   color = 'darkblue' if np.linalg.norm(pos - mean1) < np.linalg.norm(pos - mean2) else 'orange'
   draw_ellipse(pos, covar, ax=axs[1], color=color)

plt.tight_layout()
plt.subplots_adjust(wspace=0.1)

plt.savefig(os.path.join(results_folder, 'GenAiImg.eps'), format='eps')
plt.savefig(os.path.join(results_folder, 'GenAiImg.png'), format='png')
plt.show()
