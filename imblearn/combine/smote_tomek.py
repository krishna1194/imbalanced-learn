"""Class to perform over-sampling using SMOTE and cleaning using Tomek
links."""

# Authors: Guillaume Lemaitre <g.lemaitre58@gmail.com>
#          Christos Aridas
# License: MIT

from __future__ import division

import logging
import warnings

from sklearn.utils import check_X_y

from ..base import SamplerMixin
from ..over_sampling import SMOTE
from ..under_sampling import TomekLinks
from ..utils import check_target_type, hash_X_y


class SMOTETomek(SamplerMixin):
    """Class to perform over-sampling using SMOTE and cleaning using
    Tomek links.

    Combine over- and under-sampling using SMOTE and Tomek links.

    Read more in the :ref:`User Guide <combine>`.

    Parameters
    ----------
    sampling_target : float, str, dict or callable, (default='auto')
        Sampling information to resample the data set.

        - When ``float``, it correspond to the ratio :math:`\\alpha_{os}`
          defined by :math:`N_{rm} = \\alpha_{os} \\times N_{m}` where
          :math:`N_{rm}` and :math:`N_{M}` are the number of samples in the
          minority class after resampling and the number of samples in the
          majority class, respectively.

        .. warning::
           ``float`` is only available for **binary** classification. An error
           is raised for multi-class classification.

        - When ``str``, specify the class targeted by the resampling. The
          number of samples in the different classes will be equalized.
          Possible choices are:

            ``'minority'``: resample only the minority class;

            ``'majority'``: resample only the majority class;

            ``'not minority'``: resample all classes but the minority class;

            ``'not majority'``: resample all classes but the majority class;

            ``'all'``: resample all classes;

            ``'auto'``: equivalent to ``'not majority'``.

        - When ``dict``, the keys correspond to the targeted classes. The
          values correspond to the desired number of samples for each targeted
          class.

        - When callable, function taking ``y`` and returns a ``dict``. The keys
          correspond to the targeted classes. The values correspond to the
          desired number of samples for each class.

    random_state : int, RandomState instance or None, optional (default=None)
        If int, ``random_state`` is the seed used by the random number
        generator; If ``RandomState`` instance, random_state is the random
        number generator; If ``None``, the random number generator is the
        ``RandomState`` instance used by ``np.random``.

    smote : object, optional (default=SMOTE())
        The :class:`imblearn.over_sampling.SMOTE` object to use. If not given,
        a :class:`imblearn.over_sampling.SMOTE` object with default parameters
        will be given.

    tomek : object, optional (default=Tomek())
        The :class:`imblearn.under_sampling.Tomek` object to use. If not given,
        a :class:`imblearn.under_sampling.Tomek` object with default parameters
        will be given.

    ratio : str, dict, or callable
        .. deprecated:: 0.4
           Use the parameter ``sampling_target`` instead. It will be removed in
           0.6.

    Notes
    -----
    The methos is presented in [1]_.

    Supports mutli-class resampling. Refer to SMOTE and TomekLinks regarding
    the scheme which used.

    See :ref:`sphx_glr_auto_examples_combine_plot_smote_tomek.py` and
    :ref:`sphx_glr_auto_examples_combine_plot_comparison_combine.py`.

    See also
    --------
    SMOTEENN : Over-sample using SMOTE followed by under-sampling using Edited
        Nearest Neighbours.

    References
    ----------
    .. [1] G. Batista, B. Bazzan, M. Monard, "Balancing Training Data for
       Automated Annotation of Keywords: a Case Study," In WOB, 10-18, 2003.

    Examples
    --------

    >>> from collections import Counter
    >>> from sklearn.datasets import make_classification
    >>> from imblearn.combine import \
SMOTETomek # doctest: +NORMALIZE_WHITESPACE
    >>> X, y = make_classification(n_classes=2, class_sep=2,
    ... weights=[0.1, 0.9], n_informative=3, n_redundant=1, flip_y=0,
    ... n_features=20, n_clusters_per_class=1, n_samples=1000, random_state=10)
    >>> print('Original dataset shape {}'.format(Counter(y)))
    Original dataset shape Counter({1: 900, 0: 100})
    >>> smt = SMOTETomek(random_state=42)
    >>> X_res, y_res = smt.fit_sample(X, y)
    >>> print('Resampled dataset shape {}'.format(Counter(y_res)))
    Resampled dataset shape Counter({0: 900, 1: 900})

    """

    def __init__(self,
                 sampling_target='auto',
                 random_state=None,
                 smote=None,
                 tomek=None,
                 ratio=None):
        super(SMOTETomek, self).__init__()
        self.sampling_target = sampling_target
        self.random_state = random_state
        self.smote = smote
        self.tomek = tomek
        self.ratio = ratio
        self.logger = logging.getLogger(__name__)

    def _validate_estimator(self):
        "Private function to validate SMOTE and ENN objects"

        if self.smote is not None:
            if isinstance(self.smote, SMOTE):
                self.smote_ = self.smote
            else:
                raise ValueError('smote needs to be a SMOTE object.'
                                 'Got {} instead.'.format(type(self.smote)))
        # Otherwise create a default SMOTE
        else:
            self.smote_ = SMOTE(
                sampling_target=self.sampling_target,
                random_state=self.random_state,
                ratio=self.ratio)

        if self.tomek is not None:
            if isinstance(self.tomek, TomekLinks):
                self.tomek_ = self.tomek
            else:
                raise ValueError('tomek needs to be a TomekLinks object.'
                                 'Got {} instead.'.format(type(self.tomek)))
        # Otherwise create a default TomekLinks
        else:
            self.tomek_ = TomekLinks(sampling_target='all')

    @property
    def ratio_(self):
        # FIXME: remove in 0.6
        warnings.warn("'ratio' and 'ratio_' are deprecated. "
                      "Use 'sampling_target' and 'sampling_target_' instead.",
                      DeprecationWarning)
        return self.sampling_target_

    def fit(self, X, y):
        """Find the classes statistics before to perform sampling.

        Parameters
        ----------
        X : {array-like, sparse matrix}, shape (n_samples, n_features)
            Matrix containing the data which have to be sampled.

        y : array-like, shape (n_samples,)
            Corresponding label for each sample in X.

        Returns
        -------
        self : object,
            Return self.

        """
        y = check_target_type(y)
        X, y = check_X_y(X, y, accept_sparse=['csr', 'csc'])
        self.sampling_target_ = self.sampling_target
        self.X_hash_, self.y_hash_ = hash_X_y(X, y)

        return self

    def _sample(self, X, y):
        """Resample the dataset.

        Parameters
        ----------
        X : {array-like, sparse matrix}, shape (n_samples, n_features)
            Matrix containing the data which have to be sampled.

        y : array-like, shape (n_samples,)
            Corresponding label for each sample in X.

        Returns
        -------
        X_resampled : {ndarray, sparse matrix}, shape \
(n_samples_new, n_features)
            The array containing the resampled data.

        y_resampled : ndarray, shape (n_samples_new,)
            The corresponding label of `X_resampled`

        """
        self._validate_estimator()

        X_res, y_res = self.smote_.fit_sample(X, y)
        return self.tomek_.fit_sample(X_res, y_res)
