"""Static site generator for peterparker.ca.

One page per public project repository, rendered from that repository's README, plus an
index built from ``projects.yaml``. Private repositories are invisible to the build by
construction: the GitHub API returns nothing for them without a token that can see them,
and the build refuses anything the API does not mark public.
"""

__version__ = "0.1.0"
