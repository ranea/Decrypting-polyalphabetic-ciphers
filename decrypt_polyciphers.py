#!/usr/bin/env python3

import sys
from operator import itemgetter
from itertools import zip_longest
import string
import logging as log
import argparse
from collections import Counter
from math import gcd

# TODO
#   finish decryptText, guessPeriod description
#   clean KasiskiMethod function
#   how many ngrams and periods do i have to take in kassiski methods?
#   implement guessPeriod
#   implement manual analysis in decryptText and guessPeriod
#   clean decryptText

def cleanText(text):
    """ Removes the punctuation symbol and whitespaces from text """
    cleantext = text
    chars_to_removed = string.punctuation + string.whitespace
    for c in chars_to_removed:
        cleantext = cleantext.replace(c,'')
    return cleantext

def getNgrams(text):
    """ Gets the n-grams that are repetead in the text.
    The output is a list of list where each (sub)list
    contains all the grams of the same length
    that are repetead and its occurrences.
    The list and each (sub)list are sorted in reversed order
    with respect to the length and the number of occurrences.

    Example:
        >>> getNgrams("abcxabc)
        [[('abc', 2)], [('ab', 2), ('bc', 2)], [('a', 2), ('b', 2), ('c', 2)]]
    """
    ngrams = []
    for j in range(3,int(len(text)/2+1)):
        jgrams = {}
        for i in range(len(text)-j+1):
            currentgram = text[i:i+j]
            jgrams[currentgram] = jgrams.get(currentgram,0) + 1
        # removes the jgrams that aren't repetead
        for k,v in list(jgrams.items()):
            if v == 1:
                del jgrams[k]
        if jgrams:
            ngrams.append( sorted(jgrams.items(), key=itemgetter(1), reverse=True) )
        else:
            break

    return list(reversed(ngrams))

def KasiskiMethod(text, ngrams):
    """Calculates the possible periods of a polyalphabetic substitution ciphers
    usign Kasiski's method.
    """
    distances = []
    possible_periods = []

    for ngram in ngrams:
        first_occurrence = text.find(ngram)
        second_occurrence = text.find(ngram,first_occurrence+1)
        distance = second_occurrence-first_occurrence
        distances.append(distance)
        log.debug('Distance of %s: %s-%s=%s',ngram,second_occurrence,first_occurrence,distance)

        for possible_period in range(2,distance+1):
            if distance % possible_period == 0:
                possible_periods.append(possible_period)

    return possible_periods, distances

def indexOfCoincidence(text):
    """Calculates the index of coincidence of text normalized"""
    frequency_of_letters = Counter(text)
    log.debug('Frequency of letters: %s', frequency_of_letters)
    ic = 0
    n = len(text)
    for f in frequency_of_letters.values():
        ic +=  (f*(f-1))/(n*(n-1))

    return float("{0:.6f}".format(ic))

def averageIndexOfCoincidece(text,period):
    """Calculates the indices of coincidence of subsequences of the text
    and computes the average. The i-subsequence is calculated
    joining the letters i+0*period,i+1*period,i+2*period,...

    For example, if period=2 and text="defendtheeastwallcastle":
        subsequence1 = dfnteatalate
        subsequence2 = eedheswlcsl
    """

    subsequences = [[] for i in range(period)]
    for pos,letter in enumerate(text):
        subsequences[pos%period].append(letter)

    for index,subseq in enumerate(subsequences):
        log.debug('Subsequence %s: %s',index,''.join(subseq))

    avg_ic = sum( [indexOfCoincidence(subseq) for subseq in subsequences] )/period

    return float("{0:.6f}".format(avg_ic))

def guessPeriod(periods_with_ocurrences,period_closest_english_ic,period_closest_ciphertext_ic):
    periods = [period for period,_ in periods_with_ocurrences]
    ocurrences = [ocurrences for _,ocurrences in periods_with_ocurrences]
    total_ocurrences = sum(ocurrences)
    log.debug('Total ocurrences: %s',total_ocurrences)

    periods_with_confidence = []
    for period,ocurrences in periods_with_ocurrences:
        confidence = 90*ocurrences/total_ocurrences #"{0:.2f}%".format(90*ocurrences/total_ocurrences)
        periods_with_confidence.append( [period,confidence] )
    log.debug('(step=1) Periods with confidence: %s', periods_with_confidence)

    distances_respect_period_closest_english_ic = [float("{0:.6f}".format(abs(period_closest_english_ic-period))) for period in periods]
    min_value = min(distances_respect_period_closest_english_ic)
    min_index = distances_respect_period_closest_english_ic.index(min_value)
    periods_with_confidence[min_index][1] += 5
    log.debug('(step=2) Periods with confidence: %s', periods_with_confidence)

    distances_respect_period_closest_ciphertext_ic = [float("{0:.6f}".format(abs(period_closest_ciphertext_ic-period))) for period in periods]
    min_value = min(distances_respect_period_closest_ciphertext_ic)
    min_index = distances_respect_period_closest_ciphertext_ic.index(min_value)
    periods_with_confidence[min_index][1] += 5
    log.debug('(step=3) Periods with confidence: %s', periods_with_confidence)

    periods_with_confidence = [(period,"{0:.2f}%".format(confidence)) for period,confidence in periods_with_confidence]

    return periods_with_confidence

def decryptText(text,period):
    """ DESCRIPTION """

    subsequences = [[] for i in range(period)]
    for pos,letter in enumerate(text):
        subsequences[pos%period].append(letter)

    keyword = ""
    alphabet = string.ascii_uppercase
    subsequences = [''.join(subseq) for subseq in subsequences]
    subsequences_decrypted = ['' for i in range(len(subsequences))]
    for index, subseq in enumerate(subsequences):
        frequency_of_letters = Counter(subseq)
        most_common_letters = frequency_of_letters.most_common(5)
        most_common_letters.sort(key=itemgetter(1,0),reverse=True)
        most_common_letter = most_common_letters[0][0]

        log.debug('Encrypted subsequence %s: %s',index,subseq)
        log.debug('Most common letters: %s', most_common_letters)
        log.debug('Supossing Enc(E) = %s', most_common_letter)

        ## cipher = vigener
        offset = (ord(most_common_letter) - ord('E'))%len(alphabet)
        # if index == 3:
        #     log.debug('###########################################################')
        #     offset = (ord(most_common_letter) - ord('T'))%len(alphabet)
        # if index == 1:
        #     log.debug('###########################################################')
        #     offset = (ord(most_common_letter) - ord('O'))%len(alphabet)
        keyletter = chr(ord('A')+offset)

        log.debug('Keyletter: %s <-> %s', keyletter, offset)

        subseq_deciphered = subseq
        for pos, letter in enumerate(alphabet):
            log.debug('Enc(%s) = %s',alphabet[(pos-offset)%len(alphabet)],letter)
            subseq_deciphered = subseq_deciphered.replace(letter,alphabet[(pos-offset)%len(alphabet)].lower())

        ## cipher = substitution
        # most_common_english_letter = "etrinoa"
        # n = len(most_common_english_letter)
        # for cipherletter_with_ocurrences,plainletter in zip(frequency_of_letters.most_common(n),most_common_english_letter):
        #     subseq = subseq.replace(cipherletter_with_ocurrences[0] , plainletter)

        log.debug('Decrypted subsequence %s: %s',index,subseq_deciphered)
        subsequences_decrypted[index] = subseq_deciphered
        keyword += keyletter

    subsequences_decrypted_mixed = zip_longest(*subsequences_decrypted,fillvalue='')
    subsequences_decrypted_mixed = [''.join(subseq_mix) for subseq_mix in subsequences_decrypted_mixed]

    plaintext = ''.join(subsequences_decrypted_mixed)

    return keyword, plaintext


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="decrypt a Vigenère ciphered text")
    parser.add_argument("-m", "--manual", action="store_true", help="interacts with the user")
    parser.add_argument("-i", "--input-file", type=str, help="the input file with the encrypted text")
    parser.add_argument("-o","--output-file", type=str, help="the output file with the decrypted text")
    parser.add_argument("-v", "--verbosity", action="store_true", help="increase output verbosity")
    args = parser.parse_args()

    if not args.manual and not args.verbosity and not args.input_file and not args.output_file:
        banner = "Note: if you want to read/write from/to a file, print more information or interact  \
        \nwith the decryption, use command-line arguments. For more information, type: \
        \n\n\tpython3 " + sys.argv[0] + " --help\n"
        print(banner)

    if args.verbosity:
        log.addLevelName( log.INFO, "\033[1;36m%s\033[1;0m" % log.getLevelName(log.INFO))
        log.addLevelName( log.WARNING, "\033[1;31m%s\033[1;0m" % log.getLevelName(log.WARNING))
        log.addLevelName( log.DEBUG, "\033[1;33m%s\033[1;0m" % log.getLevelName(log.DEBUG))
        log.basicConfig(format="%(levelname)s: %(message)s", level=log.DEBUG)
    else:
        log.addLevelName( log.INFO, "\033[1;36m%s\033[1;0m" % log.getLevelName(log.INFO))
        log.addLevelName( log.WARNING, "\033[1;31m%s\033[1;0m" % log.getLevelName(log.WARNING))
        log.basicConfig(format="%(levelname)s: %(message)s", level=log.INFO)

    if args.input_file:
        with open(args.input_file) as filehandler:
            ciphertext = filehandler.read()
            log.debug('Ciphertext: %s',ciphertext)
    else:
        ciphertext = input("Introduce the ciphertext: ")
        print()

    log.debug('Ciphertext: %s',ciphertext)
    clean_ciphertext = cleanText(ciphertext).upper()
    log.debug('Clean ciphertext: %s',clean_ciphertext)

    ngrams = getNgrams(clean_ciphertext)
    log.debug('n-grams: %s',ngrams)

    if not ngrams:
        log.warning("Kasiski's method failed: no ngrams (n>=3) found. Aborting...")
        sys.exit(1)

    all_possible_periods = []
    for jgrams in ngrams:
        jgrams_without_ocurrences = [jgram[0] for jgram in jgrams]
        possible_periods, distances = KasiskiMethod(clean_ciphertext,jgrams_without_ocurrences)
        all_possible_periods +=possible_periods

        j = len(jgrams_without_ocurrences[0])
        log.debug('(n-grams, n=%s) Distances: %s',j,distances)
        log.debug('(n-grams, n=%s) Possible periods: %s',j,possible_periods)

    all_possible_periods = Counter(all_possible_periods).most_common(5)
    if all_possible_periods[0][1] == 1:
        log.warning("Kasiski's method failed: insufficient ngrams. Aborting...")
        sys.exit(1)

    for k,v in all_possible_periods: # remove possible periods that have only one occurence
        if v == 1:
            del all_possible_periods[k]
    log.debug('Periods with more occurrences as a factor of distances of ngrams: %s...',all_possible_periods)

    all_possible_periods_without_ocurrences = [a_p_p[0] for a_p_p in all_possible_periods]
    log.info("Periods guessed usign Kasiski's Method %s",all_possible_periods_without_ocurrences)

    avg_ics = []
    for period in all_possible_periods_without_ocurrences:
        avg_ics.append(averageIndexOfCoincidece(clean_ciphertext,period))
    log.debug('Average IC values: %s',avg_ics)

    english_ic = 0.66895
    distances_respect_english_ic = [float("{0:.6f}".format(abs(english_ic-avg_ic))) for avg_ic in avg_ics]
    min_value = min(distances_respect_english_ic)
    min_index = distances_respect_english_ic.index(min_value)
    period_closest_english_ic = all_possible_periods_without_ocurrences[min_index]
    log.debug('English IC: %s',english_ic)
    log.debug('Distances respect to english IC: %s',distances_respect_english_ic)
    log.info('Period with closest IC to english IC: %s',period_closest_english_ic)

    ciphertext_ic = indexOfCoincidence(clean_ciphertext)
    periods_ic = [0.0066,0.0520,0.0473,0.0450,0.0436,0.0427,0.0420,0.0415,0.0411,0.0408,
        0.0405,0.0403,0.0402,0.0400,0.0399,0.0397,0.0396,0.0396,0.0395,0.0394 ]
    distances_respect_periods_ic = [float("{0:.6f}".format(abs(ciphertext_ic-p_ic))) for p_ic in periods_ic]
    min_value = min(distances_respect_periods_ic)
    min_index = distances_respect_periods_ic.index(min_value)
    period_closest_ciphertext_ic = min_index+1
    log.debug('Ciphertext IC: %s',ciphertext_ic)
    log.debug('Periods IC: %s',periods_ic)
    log.debug('Distances respect to periods IC: %s',distances_respect_english_ic)
    log.info('Period with closest IC to ciphertext IC: %s', period_closest_ciphertext_ic)

    periods_with_confidence = guessPeriod(all_possible_periods,period_closest_english_ic,period_closest_ciphertext_ic)
    log.info('Guessed periods: %s', periods_with_confidence)

    if not args.manual:
        guessed_period = periods_with_confidence[0][0]
        key, plaintext = decryptText(clean_ciphertext,guessed_period)
        log.info('Key: %s',key)
        log.info('Decrypted text: %s',plaintext)
    else:
        while True:
            print()
            guessed_period = int(input("Introduce period: "))
            print()
            key, plaintext = decryptText(clean_ciphertext,guessed_period)

            log.info('Key: %s',key)
            log.info('Decrypted text: %s',plaintext)

            print()
            option = input("Try another period [y/N]: ")
            if not option.upper() == 'Y':
                break

    if args.output_file:
        with open(args.input_file,'w') as filehandler:
            filehandler.write(key)
            filehandler.write(plaintext)
