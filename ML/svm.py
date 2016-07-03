"""
Support Vector Machine for classification
"""

import math
import numpy as np
import cvxopt

#Useful Kernels
def linear_kernel(**kwargs):
    def f(x1, x2):
        return np.inner(x1, x2)
    return f

def polynomial_kernel(power, coef, **kwargs):
    def f(x1, x2):
        return (np.inner(x1, x2) + coef)**power
    return f

def rbf_kernel(gamma, **kwargs):
    def f(x1, x2):
        distance = np.linalg.norm(x1-x2) ** 2
        return np.exp(-gamma * distance)
    return f

class SupportVectorMachine(object):

    def __init__(self, C=0, kernel=linear_kernel, power=2, gamma=0.02, coef=1):
        """
        Args:
            C (float): weight of penalty for misclassified points in soft-margin error
                if C == 0, then hard-margin SVM is used
            kernel: {linear_kernel, polynomial_kernel, rbf_kernel}
                kernel method to use
            power (int): exponent in polynomial kernel
            gamma (float): rbf parameter
            coef (float): offset parameter in polynomial kernel

        Attributes:
            learned (bool): Keeps track of if perceptron has been fit
            SValphas (list): alphas associated with the model's support vectors
            SVinputs (list): input values of model's support vectors
            SVoutputs (list): output values of model's support vectors
            self.intercept (float): intercept value of model
        """
        self.C = C
        self.kernel = kernel(power=power, gamma=gamma, coef=coef)
        self.power = power
        self.gamma = gamma
        self.coef = coef
        self.learned = False
        self.SValphas = []
        self.SVinputs = []
        self.SVoutputs = []
        self.intecept = np.NaN

    def fit(self, X, y):
        """
        Args:
            X (np.ndarray): Training data of shape[n_samples, n_features]
            y (np.ndarray): Target values of shape[n_samples, 1]
            reg_parameter (float): float to determine strength of regulatrization  penalty
                if 0, then no linear regression without regularization is performed

        Returns:
            self: Returns an instance of self

        Raises:
            ValueError if y contains values other than 0 and 1
        """
        n_samples, n_features = np.shape(X)

        kernel_values = np.zeros((n_samples, n_samples))
        for row in range(n_samples):
            for col in range(n_samples):
                kernel_values[row, col] = self.kernel(X[row, :], X[col, :])

        # Use cvxopt to solve SVM optimization problem
        P = cvxopt.matrix(np.outer(y, y) * kernel_values, tc='d')
        q = cvxopt.matrix(np.ones(n_samples) * -1)
        A = cvxopt.matrix(y, (1, n_samples),  tc='d')
        b = cvxopt.matrix(0, tc='d')

        if self.C > 0:
            G_max = np.identity(n_samples) * -1
            G_min = np.identity(n_samples)
            G = cvxopt.matrix(np.vstack((G_max, G_min)))
            h_max = cvxopt.matrix(np.zeros(n_samples))
            h_min = cvxopt.matrix(np.ones(n_samples) * self.C)
            h = cvxopt.matrix(np.vstack((h_max, h_min)))
            
        else:
            G = cvxopt.matrix(np.identity(n_samples) * -1)
            h = cvxopt.matrix(np.zeros(n_samples))

        minimization = cvxopt.solvers.qp(P, q, G, h, A, b)
        alphas = np.ravel(minimization['x'])
        #Extract support vectors
        for index, alpha in enumerate(alphas):
            if alpha > 10**-6:
                self.SValphas.append(alpha)
                self.SVinputs.append(X[index, :])
                self.SVoutputs.append(y[index])
        # Use first support vector to calculate intercept
        self.intercept = self.SVoutputs[0]
        for SV in range(len(self.SValphas)):
            self.intercept -= self.SValphas[SV] * self.SVoutputs[SV] * self.kernel(self.SVinputs[SV], self.SVinputs[0])
        self.learned = True
        return self

    def predict(self, x):
        """
        Args:
            X (np.ndarray): Training data of shape[n_samples, n_features]

        Returns:
            prediction (np.ndarray): shape[n_samples, 1]
                Returns predicted values

        Raises:
            ValueError if model has not been fit
        """
        if not self.learned:
            raise NameError('Fit model first')
        prediction = 0
        for SV in range(len(self.SValphas)):
            prediction += self.SValphas[SV] * self.SVoutputs[SV] * self.kernel(self.SVinputs[SV], x)
        prediction += self.intercept
        return np.sign(prediction)