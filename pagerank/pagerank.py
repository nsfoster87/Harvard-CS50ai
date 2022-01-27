import os
import random
import re
import sys
from numpy.random import choice

DAMPING = 0.85
SAMPLES = 10000


def main():
    if len(sys.argv) != 2:
        sys.exit("Usage: python pagerank.py corpus")
    corpus = crawl(sys.argv[1])
    ranks = sample_pagerank(corpus, DAMPING, SAMPLES)
    print(f"PageRank Results from Sampling (n = {SAMPLES})")
    for page in sorted(ranks):
        print(f"  {page}: {ranks[page]:.4f}")
    ranks = iterate_pagerank(corpus, DAMPING)
    print(f"PageRank Results from Iteration")
    for page in sorted(ranks):
        print(f"  {page}: {ranks[page]:.4f}")


def crawl(directory):
    """
    Parse a directory of HTML pages and check for links to other pages.
    Return a dictionary where each key is a page, and values are
    a list of all other pages in the corpus that are linked to by the page.
    """
    pages = dict()

    # Extract all links from HTML files
    for filename in os.listdir(directory):
        if not filename.endswith(".html"):
            continue
        with open(os.path.join(directory, filename)) as f:
            contents = f.read()
            links = re.findall(r"<a\s+(?:[^>]*?)href=\"([^\"]*)\"", contents)
            pages[filename] = set(links) - {filename}

    # Only include links to other pages in the corpus
    for filename in pages:
        pages[filename] = set(
            link for link in pages[filename]
            if link in pages
        )

    return pages


def transition_model(corpus, page, damping_factor):
    """
    Return a probability distribution over which page to visit next,
    given a current page.

    With probability `damping_factor`, choose a link at random
    linked to by `page`. With probability `1 - damping_factor`, choose
    a link at random chosen from all pages in the corpus.
    """

    probabilities = dict()

    if len(corpus[page]) == 0:
        for this_page in corpus:
            probabilities[this_page] = 1 / len(corpus)
        return probabilities

    for this_page in corpus:
        probabilities[this_page] = (1 - damping_factor) / len(corpus)
        if this_page in corpus[page]:
            probabilities[this_page] += damping_factor / len(corpus[page])
    return probabilities


def sample_pagerank(corpus, damping_factor, n):
    """
    Return PageRank values for each page by sampling `n` pages
    according to transition model, starting with a page at random.

    Return a dictionary where keys are page names, and values are
    their estimated PageRank value (a value between 0 and 1). All
    PageRank values should sum to 1.
    """
    visited_pages = dict()
    page = random.choice(list(corpus.keys()))
    next_transition_model = transition_model(corpus, page, damping_factor)
    for i in range(n):
        visited_pages[page] = visited_pages.get(page, 0) + 1
        trans_keys = []
        trans_values = []
        for probability in next_transition_model:
            trans_keys.append(probability)
            trans_values.append(next_transition_model[probability])
        page = random.choices(trans_keys, trans_values)[0]
        next_transition_model = transition_model(corpus, page, damping_factor)

    ranks = dict()
    for each_page in visited_pages:
        ranks[each_page] = visited_pages[each_page] / n

    return ranks


def iterate_pagerank(corpus, damping_factor):
    """
    Return PageRank values for each page by iteratively updating
    PageRank values until convergence.

    Return a dictionary where keys are page names, and values are
    their estimated PageRank value (a value between 0 and 1). All
    PageRank values should sum to 1.
    """
    ranks = dict()
    for page in corpus:
        ranks[page] = 1 / len(corpus)

    keep_iterating = True
    while keep_iterating:

        new_ranks = ranks.copy()

        for first_page in ranks:
            sum = 0
            for other_page in ranks:
                if other_page == first_page:
                    continue

                # if the page has no links, interpret as linking to all pages
                if len(corpus[other_page]) == 0:
                    sum += (ranks[other_page] / len(corpus))

                if first_page in corpus[other_page]:
                    num_links = len(corpus[other_page])
                    sum += (ranks[other_page] / num_links)

            new_ranks[first_page] = ((1 - damping_factor) / len(ranks)) + (damping_factor * sum)

        keep_iterating = False
        for page_check in new_ranks:
            if abs(ranks[page_check] - new_ranks[page_check]) > 0.001:
                keep_iterating = True
                break
        ranks = new_ranks.copy()

    return ranks
    


if __name__ == "__main__":
    main()
