import numpy as np
import pandas as pd

from sklearn.cluster import DBSCAN
from sklearn import metrics
from sklearn.neighbors import NearestNeighbors
from sklearn.metrics import silhouette_samples, silhouette_score
from sklearn.metrics import davies_bouldin_score
from sklearn.metrics import calinski_harabasz_score

import random
import logging



def cluster_positions():
    cleft_angle_data = pd.read_csv("https://raw.githubusercontent.com/histofyi/notebooks/main/data/nonamer_cleft_chi1_chi2.csv", 
                              sep=",", 
                              encoding='latin-1',
                              index_col = ["complex_id"])
    #logging.warn(cleft_angle_data)
    for row in cleft_angle_data:
        cleft_angle_data[row] = pd.to_numeric(cleft_angle_data[row], errors='coerce').fillna(361).astype(np.int64)

    logging.warn(cleft_angle_data.columns.values)

    positions = []

    for item in cleft_angle_data.columns.values:
        if item.split('_')[0][1:] not in positions:
            positions.append(item.split('_')[0][1:])
    logging.warn(positions)

    pymol_string = 'select byres chain A and ('

    for position in positions:
        pymol_string += 'resi ' + position + ' or '

    pymol_string += ')'

    logging.warn (pymol_string)

    return None, False, ['null_method']