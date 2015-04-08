import math

class Logistic():
    """A simple logistic regression classifier that can only use prepared weights
    """

    def __init__(self, weight):
        self.weight = weight

    def classify(self, vector):
        lsum = 0
        for i in range(len(vector)):
            lsum += self.weight[i] * vector[i]
        elinear = math.exp(lsum)
        prob = 1.0 / (1 + elinear)
        if prob > 0.5:
            return 1
        else:
            return 0
