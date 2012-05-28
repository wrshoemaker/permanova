#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (C) 2010 - 2012, University of New Orleans
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Author: Johnny Brown

import numpy as np
import random as r
from itertools import permutations, product, chain

from scipy import stats
stats.ss = lambda l: sum(a*a for a in l)

def above_diagonal(n):
    row = xrange(n)
    for i in row:
        for j in xrange(i+1,n):
            yield i,j
    

def permanova_oneway(dm, levels, permutations = 200):
    """ 
    Performs one-way permutational ANOVA on the given distance matrix.

    One-way permanova tests the null hypothesis that distances between levels of
    the variable are not significantly different from distances within levels of
    the variable.

    The test-statistic is a multivariate analogue to Fisher's F-ratio and is 
    calculated directly from any symmetric distance or dissimilarity matrix. 
    P-values are then obtained using permutations.

    Parameters
    ----------
    dm : array_like
        The distance matrix of observations x observations. Represents a 
        symmetric n x n matrix with zeros on the diagonal.

    levels : array_like
        An array indicating the levels of the variable at each observation, such
        that levels[i] == levels[j] means that dm[i] and dm[j] are rows 
        corresponding to observations in the same level or treatment.

    permutations : int
        The number of permutations used to compute the p-value. Default is 200.
        If there are less than ``permutations`` unique permutations, then all of 
        them will be used

    Returns
    -------
    F-value : float
        The computed F-value of the test.
    p-value : float
        The associated p-value from the F-distribution, generated by permuting 
        the levels

    Notes
    -----
    It is assumed that all sample groups are the same size, n. 

    For example, if the values in levels are placebo, 5mg, and 10mg, then each 
    value must occur n times in the levels array, and 
    3n == len(levels) == len(dm) == len(dm[i]) (for all 0 <= i < len(dm))
    
    The algorithm is from Anderson[2] 

    References
    ----------
    .. [1] Lowry, Richard.  "Concepts and Applications of Inferential
           Statistics". Chapter 14. http://faculty.vassar.edu/lowry/ch14pt1.html

    .. [2] Anderson, Marti. A new method for non-parametric multivariate analysis 
           of variance. 2001. 
           http://stg-entsoc.bivings.com/PDF/MUVE/6_NewMethod_MANOVA1_2.pdf
    """
    bigf = f_oneway(dm,levels)

    above = below = 0
    nf = 0

    #TODO make this pretty with math and functions
    #perms = r.sample(list(perm_unique(levels)),permutations)
    shuffledlevels = list(levels)#copy list so we can shuffle it
    
    for i in xrange(permutations):
        r.shuffle(shuffledlevels)
        f = f_oneway(dm,shuffledlevels)
        
        if f >= bigf:
            above += 1

        #debug
        ## print shuffledlevels
        ## print f

    p = above/float(permutations)

    return (bigf,p)

#FIXME the right way to reuse code for one-way and n-way is to add an arg f such that
#f(levels[i],levels[j]) returns True iff dm[i][j] should be included in the
#desired sum of squares
def f_oneway(dm,levels):
    bign = len(levels)#number of observations
    dm = np.asarray(dm)#distance matrix
    a = len(set(levels))#number of levels
    n = bign/a#number of observations per level
    
    assert dm.shape == (bign,bign) #check the dist matrix is square and the size
                                   #corresponds to the length of levels

    #total sum of squared distances                                   
    sst = np.sum(stats.ss(r) for r in 
              (s[n+1:] for n,s in enumerate(dm[:-1])) )/float(bign)

    #sum of within-group squares
    #itertools.combinations(xrange(len(dm)),2)#top half of dm
    ssw = np.sum((dm[i][j]**2 for i,j in  
               product(xrange(len(dm)),xrange(1,len(dm)))
               if i<j and levels[i] == levels[j]))/float(n)

    ssa = sst - ssw

    fstat = (ssa/float(a-1))/(ssw/float(bign-a))
    #print (fstat,sst,ssa,ssw,a,bign,n)

    return fstat

def permanova_twoway(dm,levels,permutations=200):
    """
    factorial two-way manova
    
    dm is the dist. matrix as usual
    levels is a list of ordered pairs [(a1,b1),(a2,b2),...,(ax,by)]
    where ax gives the a-level of an observation and by gives the b-level
    """

    bigf_i, bigf_a, bigf_b = f_twoway(dm,levels)

    above_i = above_a = above_b = 0

    #TODO make this pretty with math and functions
    #perms = r.sample(list(perm_unique(levels)),permutations)
    shuffledlevels = list(levels)#copy list so we can shuffle it

    a_levels = list([l[0] for l in levels])
    b_levels = list([l[1] for l in levels])
    
    #permutations
    for i in xrange(permutations):
        #All these are probably the wrong way to do the permutations. Wrong as in
        #incorrect
        ## r.shuffle(a_levels)
        ## r.shuffle(b_levels)
        ## shuffledlevels = zip(a_levels,b_levels)

        r.shuffle(shuffledlevels)
        
        f_i, f_a, f_b = f_twoway(dm,shuffledlevels)

        if f_i > bigf_i:
            above_i += 1

    for i in xrange(permutations):
        r.shuffle(a_levels)

        f_i, f_a, f_b = f_twoway(dm,zip(a_levels, [l[1] for l in levels]))

        if f_a > bigf_a:
            above_a += 1

    for i in xrange(permutations):
        r.shuffle(b_levels)

        f_i, f_a, f_b = f_twoway(dm,zip([l[0] for l in levels], b_levels))
            
        if f_b > bigf_b:
            above_b += 1



    p_i,p_a,p_b = [ above/float(permutations) for above in 
                    [above_i, above_a, above_b]]

    return (p_i, p_a, p_b)

    
    
def f_twoway(dm, levels):
    
    bign = len(levels)#number of observations
    dm = np.asarray(dm)#distance matrix
    l = len(set(levels))#number of levels
    a = len(set([l[0] for l in levels]))#number of a-levels
    b = len(set([l[1] for l in levels]))#number of b-levels
    n = bign/float(a*b)#number of observations per level

    #sum of all distances
    ## sst = np.sum(stats.ss(r) for r in 
    ##         (s[n+1:] for n,s in enumerate(dm[:-1])) )/float(bign)
    sst = stats.ss(chain(*(r[i+1:] for i,r in enumerate(dm))))/float(bign)

    #same level of both a and b (error, within-group)
    ssr = np.sum((dm[i][j]**2 for i,j in  
               product(xrange(len(dm)),xrange(1,len(dm)))
               if i<j and levels[i] == levels[j]))/float(n)

    #same level of a
    sswa = np.sum((dm[i][j]**2 for i,j in  
               product(xrange(len(dm)),xrange(1,len(dm)))
               if i<j and levels[i][0] == levels[j][0]))/float(b*n)

    #same level of b
    sswb = np.sum((dm[i][j]**2 for i,j in
               product(xrange(len(dm)),xrange(1,len(dm)))
               if i<j and levels[i][1] == levels[j][1]))/float(a*n)

    
    ssa = sst - sswa
    ssb = sst - sswb
    ssab = sst - ssa - ssb - ssr #interaction s-squares

    #these should each be separate functions?
    f_interaction = (ssab/float((a-1)*(b-1)))/(ssr/float(bign - a*b))
    f_a = (ssa/float((a-1)))/(ssr/float(bign - a*b))
    f_b = (ssb/float((b-1)))/(ssr/float(bign - a*b))

    return (f_interaction,f_a,f_b)
    
def f_stat(dm,levels, df_numerator, df_denominator, included_numerator, included_denominator):
    
    bign = len(dm)

    distances_numerator = (dm[i][j] for i,j in above_diagonal(bign) 
                           if included_numerator(levels[i], levels[j]))
    numerator = stats.ss(distances_numerator)/float(df_numerator)

    distances_denominator = (dm[i][j] for i,j in above_diagonal(bign)
                             if included_denominator(levels[i], levels[j]))
    denominator = stats.ss(distances_numerator)/float(df_denominator)

    return numerator/denominator


