"""Single source for the public lab packaging flags.

``operator_authentication`` and ``operator_authentication_manifest`` are one
localhost Profile B path claim. They stay equal. ``production_ready`` and
``customer_pilot_allowed`` stay false. The authentication claim does not grant
approval authority, Arc dispatch, production readiness, or customer-pilot
permission.

The keyboard-chosen display name is not a directory identity. Windows Hello
proves user verification on this PC only. Attestation format is ``none``.
The signature counter may stay zero. The public credential is process memory
only, and ``survives_restart`` stays false.
"""

from __future__ import annotations


PRODUCTION_READY: bool = False
CUSTOMER_PILOT_ALLOWED: bool = False
OPERATOR_AUTHENTICATION: bool = True
OPERATOR_AUTHENTICATION_MANIFEST: bool = OPERATOR_AUTHENTICATION


def assert_packaging_invariants() -> None:
    """Fail closed if the three public flags drift apart."""

    if PRODUCTION_READY is not False:
        raise RuntimeError("production_ready must stay false")
    if CUSTOMER_PILOT_ALLOWED is not False:
        raise RuntimeError("customer_pilot_allowed must stay false")
    if type(OPERATOR_AUTHENTICATION) is not bool or type(OPERATOR_AUTHENTICATION_MANIFEST) is not bool:
        raise RuntimeError("operator authentication flags must be booleans")
    if OPERATOR_AUTHENTICATION is not True or OPERATOR_AUTHENTICATION_MANIFEST is not True:
        raise RuntimeError("operator authentication lab claim must stay true and paired")
    if OPERATOR_AUTHENTICATION is not OPERATOR_AUTHENTICATION_MANIFEST:
        raise RuntimeError("operator_authentication and operator_authentication_manifest drifted")


assert_packaging_invariants()
