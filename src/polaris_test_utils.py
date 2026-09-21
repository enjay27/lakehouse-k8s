"""
polaris_test_utils.py  --  COMPATIBILITY ALIAS for `nb_support`.

The implementation moved to `nb_support.py` on 2026-09-21. Notebooks import
`nb_support` (environment, identity, logging, results) plus `polaris_rest`
(REST operations); nothing new should import this name.

This is a module ALIAS, not a re-export. `from nb_support import *` would copy
values at import time, and this module's most important names -- POLARIS_URL,
REALM, BASE_CAT, BASE_MGMT, BUCKET -- start as None and are only assigned when
`init_env()` runs. A star-import shim would therefore hand every existing
caller a permanent None, which is exactly the bug that made
`polaris_availability_test` build every URL as "None/watchdog-catalog/...".
Replacing this entry in `sys.modules` makes `polaris_test_utils` and
`nb_support` the same module object, so a global assigned through one is
visible through the other.
"""

import sys

import nb_support

sys.modules[__name__] = nb_support
